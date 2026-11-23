"""Command line entry point: `uv run agent run | status | probe | reset | review | eval`."""

import argparse
import json
from collections import Counter
from pathlib import Path

import anthropic

from agent import journal, runner
from agent.config import ConfigError, decider_from_env, helpdesk_from_env
from agent.helpdesk import Helpdesk, HelpdeskError
from agent.logs import log_path

JOURNAL = Path("state/journal.db")
LOG_DIR = Path("logs")
EXAMPLES = Path("evals/examples.json")
STATUS_FIELDS = ("mode", "open_tickets", "handled_tickets", "live_ends_at")  # not `candidate`


def status_line(client: Helpdesk) -> str:
    status = client.status()
    return json.dumps({k: status.get(k) for k in STATUS_FIELDS})


def cmd_run(client: Helpdesk, db, decide=None) -> int:
    log_file = log_path(LOG_DIR)
    try:
        summary = runner.run(client, db, decide or decider_from_env(), log_file)
    except runner.StaleJournal as exc:
        print(f"Refusing to run: {exc}: {', '.join(exc.ticket_ids)}")
        print("The helpdesk was reset without the journal. Use `uv run agent reset`.")
        return 1
    skipped = summary.pop("skipped", [])
    print(f"Run finished: {summary}")
    if skipped:
        print(f"{len(skipped)} tickets skipped because the model was unavailable: {', '.join(skipped)}.")
        print("They have no decision and were not answered. Run `uv run agent run` again to handle them.")
    print(f"Log: {log_file}")
    return 1 if skipped else 0


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


def review_lines(row: dict) -> list[str]:
    """One journal row in English: the decision, failed checks, and the text a reviewer needs."""
    p, m = row["payload"], row["meta"]
    head = [row["id"], row["status"], row["action"], p.get("language"), p.get("category"),
            p.get("priority"), p.get("confidence")]  # fmt: skip
    lines = ["  ".join(str(x) if x is not None else "-" for x in head)]
    if m.get("model_action") and m["model_action"] != row["action"]:
        lines.append(f"    escalated by code (model chose {m['model_action']})")
    lines.append(f"    checks: {', '.join(m.get('failed_checks') or []) or '-'}")
    if row["action"] == "reply":
        lines.append(f"    EN: {m.get('english_backtranslation') or '-'}")
    elif row["action"] == "handoff":
        lines.append(f"    note: {p.get('handoff_note') or '-'}")
    else:
        lines.append(f"    reason: {p.get('reason') or '-'}")
    if row.get("note"):
        lines.append(f"    journal: {row['note']}")
    return lines


def cmd_review(db) -> int:
    """Print every journal row for a human check. Local only: no helpdesk call, nothing logged."""
    rows = journal.all_rows(db)
    for row in rows:
        print("\n".join(review_lines(row)))
    actions = Counter(r["action"] for r in rows)
    escalated = sum(1 for r in rows if r["meta"].get("model_action") not in (None, r["action"]))
    not_done = sum(1 for r in rows if r["status"] != "done")
    print(f"\n{len(rows)} tickets: {dict(actions)}; escalated by code: {escalated}; not done: {not_done}")
    return 0


COMMANDS = {"run": cmd_run, "status": cmd_status, "probe": cmd_probe, "reset": cmd_reset}


def cmd_eval(name: str, repeat: int) -> int:
    """Run the decider on evals/examples.json. Calls the model API only, never the helpdesk."""
    from agent import evaluate  # the eval also needs the judge model; keep it out of normal runs

    md_path, summary = evaluate.run_eval(EXAMPLES, Path("evals/results"), name, repeat)
    print(json.dumps(summary, indent=2))
    print(f"Report: {md_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="handle all open tickets once")
    sub.add_parser("status", help="helpdesk status and journal counts")
    sub.add_parser("probe", help="read-only look at the live helpdesk; saves evals/examples.json")
    sub.add_parser("reset", help="reopen all practice tickets, then clear the journal")
    sub.add_parser("review", help="print every journal decision in English (local, no API calls)")
    ev = sub.add_parser("eval", help="run the decider on the labelled examples (model API only)")
    ev.add_argument("--out", default="latest", help="report name under evals/results/")
    ev.add_argument("--repeat", type=int, default=3, help="runs per example (default 3)")
    args = parser.parse_args(argv)

    try:
        if args.command == "eval":
            return cmd_eval(args.out, args.repeat)
        if args.command == "review":
            return cmd_review(journal.open_journal(JOURNAL))
        client = helpdesk_from_env()
        db = journal.open_journal(JOURNAL)
        return COMMANDS[args.command](client, db)
    except ConfigError as exc:
        print(exc)
        return 2
    except HelpdeskError as exc:
        print(f"Helpdesk error: {type(exc).__name__}: {exc}")
        return 1
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
        print(f"Model API refused the credentials ({type(exc).__name__}); check ANTHROPIC_API_KEY.")
        return 2
