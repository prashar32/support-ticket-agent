"""An in-memory helpdesk behind httpx.MockTransport, on a fake clock.

It behaves like the real API (pagination, 409 on a second answer, 422 with `problems`,
429 above 5 requests a second), plus scripted faults for one specific request.
"""

import json
import random
from collections import Counter, deque

import httpx

from agent.helpdesk import Helpdesk

BASE = "https://helpdesk.test"
REQUIRED = ("language", "category", "priority", "reason")
NEEDS = {"reply": "draft_reply", "handoff": "handoff_note"}


class Crash(Exception):
    """Stands in for the process dying (kill -9, power loss) at a chosen point."""


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


def make_ticket(i: int) -> dict:
    body = f"Ticket {i}: hoe werkt het rooster? Mijn IBAN is NL91ABNA0417164300."
    if i % 7 == 0:
        body = f"Ticket {i}: dubbel afgeschreven van kaart 4111 1111 1111 1111."
    return {
        "id": f"T{i:03d}",
        "received_at": "2026-10-05T09:02:00+00:00",
        "channel": "email",
        "customer_plan": "Basis",
        "subject": f"Onderwerp {i}",
        "body": body,
    }


class FakeHelpdesk:
    def __init__(self, n: int = 30, p503: float = 0.0, seed: int = 0, clock: FakeClock | None = None):
        self.tickets = {t["id"]: t for t in (make_ticket(i) for i in range(1, n + 1))}
        self.handled: dict[str, dict] = {}  # ticket id -> {"action": ..., "body": ...}
        self.clock = clock or FakeClock()
        self.p503, self.rng = p503, random.Random(seed)
        self.faults: dict[tuple[str, str], list[str]] = {}
        self.requests: list[tuple[str, str]] = []  # every request that reached the server
        self.statuses: Counter = Counter()
        self._recent: deque = deque()

    def client(self) -> Helpdesk:
        transport = httpx.MockTransport(self.handler)
        return Helpdesk(BASE, "test-key", "me@example.com", transport, self.clock.sleep, self.clock.now)

    def fault(self, method: str, path: str, *names: str) -> None:
        """Queue faults for one request path; each is used once, in order."""
        self.faults.setdefault((method, path), []).extend(names)

    def posts(self, ticket_id: str) -> int:
        return sum(1 for m, p in self.requests if m == "POST" and p.startswith(f"/tickets/{ticket_id}/"))

    # --- server -------------------------------------------------------------------

    def handler(self, request: httpx.Request) -> httpx.Response:
        method, path = request.method, request.url.path
        self.requests.append((method, path))
        queued = self.faults.get((method, path))
        fault = queued.pop(0) if queued else None

        if fault == "crash_before":
            raise Crash(path)
        if fault == "timeout_before":
            raise httpx.ConnectTimeout("connect timeout", request=request)
        if fault == "already_handled":  # someone else answered it a moment ago
            self.handled[path.split("/")[2]] = {"action": "reply", "body": {}}

        resp = self._serve(request, method, path, fault)
        self.statuses[resp.status_code] += 1

        if fault == "timeout_after_save":
            raise httpx.ReadTimeout("read timeout", request=request)
        if fault == "crash_after_save":
            raise Crash(path)
        return resp

    def _serve(self, request, method, path, fault) -> httpx.Response:
        now = self.clock.now()
        self._recent.append(now)
        while self._recent and self._recent[0] <= now - 1.0:
            self._recent.popleft()
        if len(self._recent) > 5:
            return _json(429, {"error": "rate_limited"}, {"Retry-After": "1"})
        if fault == "429":
            return _json(429, {"error": "rate_limited"}, {"Retry-After": "2"})
        if fault == "503" or (path.startswith(("/tickets", "/practice")) and self.rng.random() < self.p503):
            return _json(503, {"error": "service_unavailable"})
        if request.headers.get("Authorization") != "Bearer test-key":
            return _json(401, {"error": "unauthorized"})

        parts = path.strip("/").split("/")
        if method == "GET" and parts == ["status"]:
            return _json(200, self._status())
        if method == "GET" and parts == ["tickets"]:
            return self._page(request.url.params)
        if method == "GET" and len(parts) == 2 and parts[0] == "tickets":
            return self._one(parts[1])
        if method == "POST" and len(parts) == 3 and parts[0] == "tickets":
            return self._decide(parts[1], parts[2], json.loads(request.content or b"{}"))
        if method == "POST" and parts == ["practice", "reset"]:
            self.handled.clear()
            return _json(200, {"reset": True, **self._status()})
        return _json(404, {"error": "not_found"})

    def _status(self) -> dict:  # same keys as the live GET /status
        return {"mode": "practice", "candidate": "Test Candidate", "endpoints": [], "live_ends_at": None,
                "open_tickets": self._open_count(), "handled_tickets": len(self.handled)}  # fmt: skip

    def _open_count(self) -> int:
        return len(self.tickets) - len(self.handled)

    def _page(self, params) -> httpx.Response:
        limit = min(int(params.get("limit", 10)), 10)
        cursor = params.get("cursor")
        ids = sorted(i for i in self.tickets if i not in self.handled and (not cursor or i > cursor))
        page = ids[:limit]
        next_cursor = page[-1] if len(ids) > limit else None
        return _json(200, {"tickets": [self.tickets[i] for i in page], "next_cursor": next_cursor})

    def _one(self, ticket_id: str) -> httpx.Response:
        if ticket_id not in self.tickets:
            return _json(404, {"error": "not_found"})
        # Live shape: the ticket plus "handled" (null while open).
        return _json(200, {**self.tickets[ticket_id], "handled": self.handled.get(ticket_id)})

    def _decide(self, ticket_id: str, action: str, body: dict) -> httpx.Response:
        if ticket_id not in self.tickets or action not in ("reply", "handoff", "close"):
            return _json(404, {"error": "not_found"})
        if ticket_id in self.handled:
            return _json(409, {"error": "already_handled"})
        problems = [f"{f} is required" for f in REQUIRED if not body.get(f)]
        if action in NEEDS and not body.get(NEEDS[action]):
            problems.append(f"{NEEDS[action]} is required for {action}")
        if problems:
            return _json(422, {"error": "validation_failed", "problems": problems})
        self.handled[ticket_id] = {"action": action, "body": body}
        return _json(200, {"ok": True, "id": ticket_id, "action": action})


def _json(status: int, data: dict, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=data, headers=headers)
