"""HTTP client for the Roosterly helpdesk: rate limit, retries and typed errors.

Rules (see docs/brief/api_reference.md):
- 503: nothing was saved, so retry with backoff.
- 429: wait Retry-After, then retry.
- Timeout or lost connection on a POST: we do not know if it was saved. Never resend
  blindly; post_decision() checks the ticket with a GET first.
- 409: already handled. Never retry.
- 400/401/404/422: raise ApiError with the server's `problems` list.
"""

import time

import httpx

MIN_INTERVAL = 0.25  # seconds between requests: 4/s, the server allows 5/s
BACKOFF = (0.5, 1, 2, 4, 8)  # waits after a 503 (or a failed GET), then give up
MAX_THROTTLED = 10  # 429s in a row before giving up
MAX_UNKNOWN = 2  # times post_decision checks and resends after an unknown outcome
TIMEOUT = 15.0
PAGE_SIZE = 10
ACTIONS = ("reply", "handoff", "close")


class HelpdeskError(Exception):
    pass


class Unavailable(HelpdeskError):
    """Retries used up on 503/429/network errors."""


class OutcomeUnknown(HelpdeskError):
    """A POST may or may not have been saved (timeout, lost connection, 5xx other than 503)."""


class AlreadyHandled(HelpdeskError):
    """409: the ticket already has an answer. Never retry."""


class ApiError(HelpdeskError):
    """A request the server rejected (400/401/404/422). Retrying will not help."""

    def __init__(self, status: int, error: str, problems: list | None = None):
        self.status, self.error, self.problems = status, error, problems or []
        super().__init__(f"{status} {error}: {self.problems}" if self.problems else f"{status} {error}")


def is_handled(ticket: dict) -> bool:
    """True if GET /tickets/{id} shows the ticket already has a decision.

    Seen live: an open ticket has "handled": null. A handled one has a non-empty value there.
    """
    return bool(ticket.get("handled"))


def _retry_after(resp: httpx.Response) -> float:
    try:
        return max(float(resp.headers.get("Retry-After", 1)), 0.0)
    except ValueError:
        return 1.0


def _api_error(resp: httpx.Response) -> ApiError:
    try:
        data = resp.json()
    except ValueError:
        data = {}
    return ApiError(resp.status_code, str(data.get("error", "error")), data.get("problems"))


class Helpdesk:
    def __init__(self, base_url, key, email, transport=None, sleep=time.sleep, now=time.monotonic):
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {key}", "X-Candidate-Email": email},
            timeout=TIMEOUT,
            transport=transport,
        )
        self._sleep, self._now = sleep, now
        self._last_start = None

    def __repr__(self) -> str:  # never show the headers
        return f"Helpdesk({self._http.base_url})"

    def _wait_turn(self) -> None:
        """Client-side rate limit: at least MIN_INTERVAL between request starts."""
        if self._last_start is not None:
            wait = self._last_start + MIN_INTERVAL - self._now()
            if wait > 0:
                self._sleep(wait)
        self._last_start = self._now()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        backoff = iter(BACKOFF)
        throttled = 0
        while True:
            self._wait_turn()
            try:
                resp = self._http.request(method, path, **kwargs)
            except httpx.TransportError as exc:
                if method == "POST":
                    raise OutcomeUnknown(f"POST {path}: {type(exc).__name__}") from None
                resp = None  # a GET is safe to repeat: treat like a 503

            if resp is not None and resp.status_code == 429:
                throttled += 1
                if throttled > MAX_THROTTLED:
                    raise Unavailable(f"{method} {path}: still rate limited")
                self._sleep(_retry_after(resp))
                continue
            if resp is None or resp.status_code >= 500:
                if resp is not None and resp.status_code != 503 and method == "POST":
                    raise OutcomeUnknown(f"POST {path}: {resp.status_code}")
                delay = next(backoff, None)
                if delay is None:
                    raise Unavailable(f"{method} {path}: unavailable after retries")
                self._sleep(delay)
                continue
            if resp.status_code == 409:
                raise AlreadyHandled(path)
            if resp.status_code >= 400:
                raise _api_error(resp)
            return resp.json()

    # --- reads ---------------------------------------------------------------

    def status(self) -> dict:
        return self._request("GET", "/status")

    def examples(self) -> dict:
        return self._request("GET", "/examples")

    def ticket_page(self, cursor: str | None = None) -> dict:
        params = {"limit": PAGE_SIZE, "status": "open"}
        if cursor:
            params["cursor"] = cursor
        return self._request("GET", "/tickets", params=params)

    def list_open_tickets(self) -> list[dict]:
        """All open tickets, following next_cursor until it is null."""
        tickets, cursor = [], None
        while True:
            page = self.ticket_page(cursor)
            tickets += page["tickets"]
            cursor = page.get("next_cursor")
            if not cursor:
                return tickets

    def get_ticket(self, ticket_id: str) -> dict:
        return self._request("GET", f"/tickets/{ticket_id}")

    # --- writes --------------------------------------------------------------

    def post_decision(self, ticket_id: str, action: str, body: dict) -> None:
        """Send one decision. If the outcome is unknown, GET the ticket before any resend."""
        if action not in ACTIONS:
            raise ValueError(f"unknown action {action!r}")
        path = f"/tickets/{ticket_id}/{action}"
        for _ in range(MAX_UNKNOWN):
            try:
                self._request("POST", path, json=body)
                return
            except OutcomeUnknown:
                if is_handled(self.get_ticket(ticket_id)):
                    return  # the earlier attempt was saved
        self._request("POST", path, json=body)  # last try; may raise OutcomeUnknown

    def practice_reset(self) -> dict:
        return self._request("POST", "/practice/reset")
