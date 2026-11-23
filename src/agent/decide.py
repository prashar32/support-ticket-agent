"""Decide what to do with one ticket: one model call, then code rules (rules.py).

A decider returns (action, body, meta):
- action: reply / handoff / close
- body:   the JSON sent to POST /tickets/{id}/{action} (API fields only)
- meta:   what we keep locally (journal, logs, eval): flags, failed checks, tokens, cost, ...

The model gets no tools and never posts. The ticket goes in as JSON inside <ticket_data> markers.
"""

import json
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

from agent import rules

ROOT = Path(__file__).resolve().parents[2]
FAQ_PATH = ROOT / "data" / "faq.md"
PROMPT_PATH = Path(__file__).with_name("prompt.md")
DEFAULT_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 8000

# USD per million tokens (input, output), from platform.claude.com/docs/en/about-claude/pricing,
# checked 2026-11-24. Haiku 5.5 price is for prompts up to 100K tokens (ours are ~3K).
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}

Flag = Literal[
    "refund", "cancellation_or_contract", "personal_data", "security", "legal_threat",
    "churn_threat", "payment_details", "spam", "empty", "multiple_requests",
]  # fmt: skip


class Part(BaseModel):
    topic_en: str
    faq_id: str | None


class ModelDecision(BaseModel):
    language: Literal["nl", "en", "de"]
    flags: list[Flag]
    parts: list[Part]
    category: Literal["bug", "billing", "feature_request", "question", "other"]
    priority: Literal["P1", "P2", "P3", "P4"]
    action: Literal["reply", "handoff", "close"]
    confidence: float
    reason: str
    faq_ids: list[str]
    draft_reply: str
    english_backtranslation: str
    handoff_note: str


class ModelUnavailable(Exception):
    """The model API could not be reached (after the SDK's retries). Nothing was decided."""


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


def system_prompt(faq_text: str) -> str:
    return PROMPT_PATH.read_text(encoding="utf-8") + faq_text


def ticket_message(ticket: dict) -> str:
    """Only these fields reach the model: never the id, and never a label."""
    data = {k: ticket.get(k, "") for k in ("channel", "customer_plan", "subject", "body")}
    # "<" is escaped so the ticket text can never close the data block.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return f"Decide on this ticket.\n<ticket_data>\n{payload}\n</ticket_data>"


def claude_call(system: str, user: str, model: str = DEFAULT_MODEL, effort: str | None = None,
                client: anthropic.Anthropic | None = None) -> tuple[dict | None, dict]:  # fmt: skip
    """One structured-output call. Returns (decision or None if unusable, usage)."""
    client = client or anthropic.Anthropic()
    extra = {"output_config": {"effort": effort}} if effort else {}
    try:
        resp = client.messages.parse(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=ModelDecision,
            **extra,
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
        raise  # configuration problem: stop the run
    except anthropic.APIError as exc:  # connection, timeout, 429, 5xx, ... after SDK retries
        raise ModelUnavailable(type(exc).__name__) from exc
    except ValueError:  # includes pydantic's ValidationError and JSON decode errors
        return None, {"model": model, "stop_reason": "unparseable"}
    usage = {
        "model": model,
        "stop_reason": resp.stop_reason,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cost_usd": cost_usd(model, resp.usage.input_tokens, resp.usage.output_tokens),
    }
    parsed = resp.parsed_output if resp.stop_reason == "end_turn" else None
    return (parsed.model_dump() if parsed else None), usage


def unusable_output(ticket: dict, stop_reason: str | None) -> dict:
    """Safe stand-in when the model gave no usable decision: a human reads the ticket."""
    return {
        "language": rules.detect_language(rules.ticket_text(ticket)) or "nl",
        "flags": [], "parts": [], "category": "other", "priority": "P3", "action": "handoff",
        "confidence": 0.0, "faq_ids": [], "draft_reply": "", "english_backtranslation": "",
        "reason": f"No usable model output ({stop_reason}); sent to a human.",
        "handoff_note": "Automated triage could not read this ticket. Please read it in full.",
    }  # fmt: skip


def make_decider(call_model, faq_text: str | None = None):
    """call_model(system, user) -> (decision dict or None, usage dict). Tests pass a scripted fake."""
    faq_text = faq_text or FAQ_PATH.read_text(encoding="utf-8")
    system = system_prompt(faq_text)
    faq = rules.parse_faq(faq_text)

    def decide(ticket: dict) -> tuple[str, dict, dict]:
        data, usage = call_model(system, ticket_message(ticket))
        unusable = data is None
        if unusable:
            data = unusable_output(ticket, usage.get("stop_reason"))
        action, body, failed = rules.apply(ticket, data, faq)
        if unusable:
            failed = ["model_output", *failed]
        meta = {
            "model_action": None if unusable else data["action"],
            "flags": data["flags"],
            "failed_checks": failed,
            "faq_ids": data["faq_ids"],
            "english_backtranslation": rules.redact(data["english_backtranslation"]),
            "model": usage.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cost_usd": usage.get("cost_usd"),
        }
        return action, body, meta

    return decide


def claude_decider(model: str = DEFAULT_MODEL, effort: str | None = None):
    client = anthropic.Anthropic()
    return make_decider(lambda system, user: claude_call(system, user, model, effort, client))


def stub_decide(ticket: dict) -> tuple[str, dict, dict]:
    """No-model decider for plumbing tests: always hand off with a fixed note."""
    return (
        "handoff",
        {
            "language": "nl",
            "category": "other",
            "priority": "P3",
            "reason": "Stub decider, no model.",
            "handoff_note": "Automated triage not enabled; please review this ticket.",
            "confidence": 0.0,
        },
        {},
    )
