# Roosterly support ticket agent

## How to run

```bash
uv sync
cp .env.example .env          # fill in HELPDESK_KEY and CANDIDATE_EMAIL
uv run agent probe            # read-only: status, examples -> evals/examples.json, first page of tickets
uv run agent run              # handle all open tickets once (safe to re-run after a crash)
uv run agent status           # helpdesk counts and journal counts
uv run agent reset            # asks for confirmation, reopens all practice tickets, clears the journal
uv run pytest -q              # offline tests against a fake helpdesk
```

State lives in state/journal.db (not committed); one log line per ticket goes to logs/run-<timestamp>.jsonl.
