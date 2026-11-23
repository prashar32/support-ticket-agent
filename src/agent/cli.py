"""Command line entry point: `uv run agent run | status | probe | reset`."""

import argparse
import json
from pathlib import Path

from agent import journal, runner
from agent.config import ConfigError, helpdesk_from_env
from agent.decide import stub_decide
from agent.helpdesk import Helpdesk, HelpdeskError
from agent.logs import log_path

JOURNAL = Path("state/journal.db")
LOG_DIR = Path("logs")
EXAMPLES = Path("evals/examples.json")
STATUS_FIELDS = ("mode", "open_tickets", "handled_tickets", "live_ends_at")  # not `candidate`


def status_line(client: Helpdesk) -> str:
    status = client.status()
    return json.dumps({k: status.get(k) for k in STATUS_FIELDS})


def cmd_run(client: Helpdesk, db) -> int:
    log_file = log_path(LOG_DIR)
    try:
        summary = runner.run(client, db, stub_decide, log_file)
    except runner.StaleJournal as exc:
        print(f"Refusing to run: {exc}: {', '.join(exc.ticket_ids)}")
        print("The helpdesk was reset without the journal. Use `uv run agent reset`.")
        return 1
    print(f"Run finished: {summary}")
    print(f"Log: {log_file}")
    return 0


def cmd_status(client: Helpdesk, db) -> int:
    print("Helpdesk:", status_line(client))
    print("Journal: ", journal.counts(db))
    return 0


def cmd_probe(client: Helpdesk, db) -> int:
    """Read-only look at the live helpdesk. GET requests only."""
    print("Status:", status_line(client))

    examples = client.examples()
    EXAMPLES.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLES.write_text(json.dumps(examples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    items = examples.get("examples", examples) if isinstance(examples, dict) else examples
    print(f"Examples: {len(items)} saved to {EXAMPLES}")

    page = client.ticket_page()
    print(f"First page: {len(page['tickets'])} tickets, next_cursor={page.get('next_cursor')}")
    print(f"Page keys: {sorted(page)}")
    for t in page["tickets"]:
        print(f"  {t['id']:<6} {t.get('customer_plan', '?'):<6} {t.get('subject', '')}")
    if page["tickets"]:
        one = client.get_ticket(page["tickets"][0]["id"])
        print(f"GET /tickets/{{id}} keys: {sorted(one)}")
    return 0


def cmd_reset(client: Helpdesk, db, ask=input) -> int:
    answer = ask("This reopens ALL practice tickets and clears the journal. Type 'reset' to go on: ")
    if answer.strip() != "reset":
        print("Aborted, nothing changed.")
        return 1
    try:
        runner.reset(client, db)
    except HelpdeskError as exc:
        print(f"Reset failed, journal kept: {type(exc).__name__}: {exc}")
        return 1
    print("Helpdesk reset and journal cleared.")
    return 0


COMMANDS = {"run": cmd_run, "status": cmd_status, "probe": cmd_probe, "reset": cmd_reset}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="handle all open tickets once")
    sub.add_parser("status", help="helpdesk status and journal counts")
    sub.add_parser("probe", help="read-only look at the live helpdesk; saves evals/examples.json")
    sub.add_parser("reset", help="reopen all practice tickets, then clear the journal")
    args = parser.parse_args(argv)

    try:
        client = helpdesk_from_env()
    except ConfigError as exc:
        print(exc)
        return 2
    db = journal.open_journal(JOURNAL)
    try:
        return COMMANDS[args.command](client, db)
    except HelpdeskError as exc:
        print(f"Helpdesk error: {type(exc).__name__}: {exc}")
        return 1
