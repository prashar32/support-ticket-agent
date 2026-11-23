"""SQLite journal: one row per ticket, so a re-run never sends a second answer.

Status flow:  decided -> in_flight -> done
                                   -> anomaly   (409, or a request the server rejected)
The decision is stored BEFORE it is posted, and a stored decision is never regenerated.
"""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

STATUSES = ("decided", "in_flight", "done", "anomaly")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id         TEXT PRIMARY KEY,
    status     TEXT NOT NULL,
    action     TEXT NOT NULL,
    payload    TEXT NOT NULL,
    note       TEXT,
    updated_at TEXT NOT NULL
)
"""


def open_journal(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, isolation_level=None)  # autocommit: every write is durable at once
    db.row_factory = sqlite3.Row
    db.execute(SCHEMA)
    return db


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    return {**dict(r), "payload": json.loads(r["payload"])}


def get(db: sqlite3.Connection, ticket_id: str) -> dict | None:
    return _row(db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


def save_decision(db: sqlite3.Connection, ticket_id: str, action: str, payload: dict) -> None:
    """Insert a new decision. Fails if the ticket already has one: decisions are never replaced."""
    db.execute(
        "INSERT INTO tickets (id, status, action, payload, updated_at) VALUES (?, 'decided', ?, ?, ?)",
        (ticket_id, action, json.dumps(payload, ensure_ascii=False), _now()),
    )


def set_status(db: sqlite3.Connection, ticket_id: str, status: str, note: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    db.execute(
        "UPDATE tickets SET status = ?, note = ?, updated_at = ? WHERE id = ?",
        (status, note, _now(), ticket_id),
    )


def rows_with(db: sqlite3.Connection, status: str) -> list[dict]:
    rows = db.execute("SELECT * FROM tickets WHERE status = ? ORDER BY id", (status,))
    return [_row(r) for r in rows]


def counts(db: sqlite3.Connection) -> dict[str, int]:
    return dict(db.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall())


def clear(db: sqlite3.Connection) -> None:
    db.execute("DELETE FROM tickets")
