"""One pass over the helpdesk: fetch all open tickets, then decide and post each once.

Safe to re-run after a crash at any point:
- a stored decision is never regenerated (the model is called at most once per ticket);
- a ticket left `in_flight` is checked with a GET before anything is resent.
"""

import time
from collections import Counter
from collections.abc import Callable

from agent import journal
from agent.helpdesk import (
    AlreadyHandled,
    ApiError,
    Helpdesk,
    OutcomeUnknown,
    Unavailable,
    is_handled,
)
from agent.logs import write_line

Decider = Callable[[dict], tuple[str, dict]]


class StaleJournal(Exception):
    """The journal says done but the helpdesk shows the ticket open: it was reset behind our back."""

    def __init__(self, ticket_ids: list[str]):
        self.ticket_ids = ticket_ids
        super().__init__(f"{len(ticket_ids)} tickets are done in the journal but open in the helpdesk")


def run(client: Helpdesk, db, decide: Decider, log_file) -> dict[str, int]:
    tickets = client.list_open_tickets()  # all pages first, then process

    stale = [t["id"] for t in tickets if (row := journal.get(db, t["id"])) and row["status"] == "done"]
    if stale:
        raise StaleJournal(stale)

    summary = Counter(reconcile(client, db, log_file))
    for ticket in tickets:
        summary[handle(client, db, decide, ticket, log_file)] += 1
    return dict(summary)


def reconcile(client: Helpdesk, db, log_file) -> list[str]:
    """For tickets left in_flight by an earlier run: GET them to learn what happened."""
    outcomes = []
    for row in journal.rows_with(db, "in_flight"):
        if is_handled(client.get_ticket(row["id"])):
            journal.set_status(db, row["id"], "done", "confirmed by GET after restart")
            _log(log_file, row, "recovered")
            outcomes.append("recovered")
        else:
            journal.set_status(db, row["id"], "decided")  # not saved: resend the stored decision
    return outcomes


def handle(client: Helpdesk, db, decide: Decider, ticket: dict, log_file) -> str:
    started = time.monotonic()
    row = journal.get(db, ticket["id"])
    if row is None:
        action, body = decide(ticket)
        journal.save_decision(db, ticket["id"], action, body)  # stored BEFORE posting
        row = journal.get(db, ticket["id"])
    if row["status"] == "anomaly":
        return _log(log_file, row, "skipped_anomaly", started=started)

    journal.set_status(db, row["id"], "in_flight")
    try:
        client.post_decision(row["id"], row["action"], row["payload"])
    except AlreadyHandled:
        journal.set_status(db, row["id"], "anomaly", "409 already_handled")
        return _log(log_file, row, "anomaly", error="409", started=started)
    except ApiError as exc:
        journal.set_status(db, row["id"], "anomaly", str(exc))
        return _log(log_file, row, "anomaly", error=str(exc.status), started=started)
    except (Unavailable, OutcomeUnknown) as exc:
        # Left in_flight on purpose: the next run GETs the ticket before resending.
        return _log(log_file, row, "pending", error=type(exc).__name__, started=started)
    journal.set_status(db, row["id"], "done")
    return _log(log_file, row, "done", started=started)


def reset(client: Helpdesk, db) -> None:
    """Reopen all practice tickets; clear the journal only if the helpdesk confirmed."""
    client.practice_reset()
    journal.clear(db)


def _log(log_file, row: dict, outcome: str, error: str | None = None, started=None) -> str:
    p = row["payload"]
    write_line(
        log_file,
        ticket_id=row["id"],
        outcome=outcome,
        action=row["action"],
        language=p.get("language"),
        category=p.get("category"),
        priority=p.get("priority"),
        confidence=p.get("confidence"),
        error=error,
        duration_ms=round((time.monotonic() - started) * 1000) if started else None,
    )
    return outcome
