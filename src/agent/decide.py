"""Decide what to do with one ticket.

Session 1 stub: always hand off with a fixed note, so the plumbing can be tested
without a model. The model-based decider replaces this function.
A decider returns (action, body): action is reply / handoff / close, and body is
the JSON sent to POST /tickets/{id}/{action}.
"""


def stub_decide(ticket: dict) -> tuple[str, dict]:
    return "handoff", {
        "language": "nl",
        "category": "other",
        "priority": "P3",
        "reason": "Stub decider, no model yet.",
        "handoff_note": "Automated triage not enabled yet; please review this ticket.",
        "confidence": 0.0,
    }
