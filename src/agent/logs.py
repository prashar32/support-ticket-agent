"""One JSON line per ticket. Only whitelisted fields, and none of them is free text (flags and
failed_checks are fixed names), so no ticket body, subject, reply, note, email, key or payment
detail can reach a log."""

import json
from datetime import UTC, datetime
from pathlib import Path

FIELDS = (
    "ts", "ticket_id", "outcome", "action", "language", "category", "priority", "confidence",
    "flags", "failed_checks", "model", "input_tokens", "output_tokens", "cost_usd",
    "error", "duration_ms",
)  # fmt: skip


def log_path(log_dir: str | Path = "logs") -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(log_dir) / f"run-{stamp}.jsonl"


def write_line(path: str | Path, **fields) -> dict:
    unknown = set(fields) - set(FIELDS)
    if unknown:
        raise ValueError(f"not allowed in logs: {sorted(unknown)}")
    record = {"ts": datetime.now(UTC).isoformat(timespec="seconds"), **fields}
    record = {k: record[k] for k in FIELDS if record.get(k) is not None}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
