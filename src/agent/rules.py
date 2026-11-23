"""Client rules enforced in code, after the model. Each rule can only make a decision safer:
it can turn reply or close into handoff, never the other way round.

apply(ticket, decision, faq) -> (action, body, failed_checks)

0. Payment details are redacted from every outgoing text, whatever the action.
1. Always-human topics (model flag, or a keyword backstop in nl/en/de) -> handoff.
2. A card number (Luhn) or IBAN in the ticket -> handoff.
3. A reply must pass checks: language, cited FAQ ids, grounding of URLs, menu paths and numbers.
4. Confidence below 0.7 -> handoff.
5. Several requests where any part needs a human -> handoff.
6. Close without a spam or empty flag -> handoff.
7. Priority floors from the brief's definitions: security or legal risk -> at least P1; money, the
   contract or personal data -> at least P2. Floors only raise the priority, never lower it.
"""

import re
import unicodedata

MIN_CONFIDENCE = 0.7
NOTE_LIMIT = 1000  # room for a draft back-translation in an escalated reply
ALWAYS_HUMAN = ("refund", "cancellation_or_contract", "personal_data", "security", "legal_threat",
                "churn_threat")  # fmt: skip

# Lowest allowed priority per topic (P1 is highest). P1: "a security or legal risk". P2: "money or
# the contract is involved"; personal data requests are treated the same way.
PRIORITY_FLOORS = {"security": "P1", "legal_threat": "P1", "refund": "P2", "cancellation_or_contract": "P2",
                   "churn_threat": "P2", "personal_data": "P2", "payment_details": "P2"}  # fmt: skip

# Keyword backstop. Matched on lowercased text with accents removed (so "beeindig" matches
# "beeindigen" written with a diaeresis). Stems are chosen to avoid FAQ topics: no bare "contract"
# (F02 mentions contract hours), no "annuleren" (cancelling a shift is a how-to).
KEYWORDS = {
    "refund": r"terugbetal|terugstort|geld terug|restitutie|refund|money back|chargeback|charged twice"
    r"|dubbel (betaald|afgeschreven)|onterecht afgeschreven|ruckerstatt|geld zuruck|doppelt abgebucht",
    "cancellation_or_contract": r"opzeg|beeindig|cancel (my|our|the) (account|subscription|contract)"
    r"|cancellation|terminate|kundig|downgrad",
    "personal_data": r"\bavg\b|gdpr|dsgvo|inzage|persoonsgegevens|gegevens (verwijderen|wissen)"
    r"|personal data|right to be forgotten|personenbezogen|datenauskunft",
    "security": r"gehackt|hacked|datalek|data ?breach|data leak|phishing|onbevoegd|unauthori[sz]ed"
    r"|verdachte (login|inlog)|suspicious login|gestolen|gestohlen|verdachtig",
    "legal_threat": r"advocaat|rechtszaak|juridische stappen|ingebrekestelling|aansprakelijk|lawyer"
    r"|attorney|legal action|lawsuit|\bsue\b|anwalt|\bklage\b",
    "churn_threat": r"overstap|concurrent|andere aanbieder|ander pakket|competitor"
    r"|switch(ing)? to (another|a different)|anbieter wechseln|zur konkurrenz",
}

ARROWS = ("\u2192", "->", "\u00bb", " > ")  # the FAQ writes menu paths with a right arrow
STOPWORDS = {
    "nl": "de het een en ik je jij u uw ons onze niet wat hoe waar wanneer voor met op van naar bij kan"
    " kunt kunnen graag hoi hallo bedankt dank alvast mijn dat deze er nog ook maar als dan om te zijn"
    " wordt worden hebben heb heeft jullie onder",
    "en": "the a an and i you your our not what how where when for with on of to at can could please"
    " hi hello thanks thank my that this there also but if or it be have has do does are under",
    "de": "der das ein eine einen und ich ihr wir unser nicht wie wo wann fur mit auf von zu bei kann"
    " konnen bitte danke mein dass diese es auch aber wenn oder haben ist sind wird unter sie",
}

# --- text helpers -------------------------------------------------------------


def fold(text: str) -> str:
    """Lowercase and strip accents: 'Rueckerstattung' with an umlaut -> 'ruckerstattung'."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def ticket_text(ticket: dict) -> str:
    return f"{ticket.get('subject', '')}\n{ticket.get('body', '')}"


def parse_faq(faq_text: str) -> dict[str, str]:
    """{'F01': 'entry text', ...} from the '## F01 ...' headings; the rules section is not an entry."""
    entries = {}
    for block in re.split(r"^## ", faq_text, flags=re.M)[1:]:
        m = re.match(r"(F\d{2})\b", block)
        if m:
            entries[m.group(1)] = block.split("\n---")[0].strip()
    return entries


# --- payment details (rule 0 and 2) ------------------------------------------

IBAN = re.compile(r"\b[A-Z]{2}\d{2} ?(?:[A-Z0-9]{4} ?){2,7}[A-Z0-9]{1,4}\b", re.I)
CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def _is_card(match: re.Match) -> bool:
    digits = re.sub(r"\D", "", match.group())
    return 13 <= len(digits) <= 19 and luhn_ok(digits)


def has_payment_details(text: str) -> bool:
    return bool(IBAN.search(text)) or any(_is_card(m) for m in CARD.finditer(text))


def redact(text: str) -> str:
    text = IBAN.sub("[redacted]", text)
    return CARD.sub(lambda m: "[redacted]" if _is_card(m) else m.group(), text)


# --- language (rule 3) ---------------------------------------------------------

_WORDS = {lang: set(fold(words).split()) for lang, words in STOPWORDS.items()}
_SHARED = {w for lang in _WORDS for w in _WORDS[lang] if sum(w in s for s in _WORDS.values()) > 1}
_WORDS = {lang: words - _SHARED for lang, words in _WORDS.items()}


def detect_language(text: str) -> str | None:
    """nl / en / de by counting stopwords, or None if too few or tied."""
    tokens = re.findall(r"[a-z]+", fold(text))
    scores = sorted(((sum(t in words for t in tokens), lang) for lang, words in _WORDS.items()), reverse=True)
    (best, lang), (second, _) = scores[0], scores[1]
    return lang if best >= 2 and best > second else None


# --- grounding (rule 3) --------------------------------------------------------

URL = re.compile(r"\b(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[\w./-]*)?", re.I)
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def urls(text: str) -> set[str]:
    return {re.sub(r"^https?://", "", u.lower()).rstrip("./") for u in URL.findall(text)}


def numbers(text: str) -> set[float]:
    return {float(n.replace(",", ".")) for n in NUMBER.findall(URL.sub(" ", text))}


def menu_steps(text: str) -> set[tuple[str, str]]:
    """Each arrow in a menu path as (word before, word after), lowercased: ('team', 'medewerker')."""
    for arrow in ARROWS[1:]:
        text = text.replace(arrow, ARROWS[0])
    steps = set()
    parts = text.split(ARROWS[0])
    for left, right in zip(parts, parts[1:], strict=False):
        before, after = left.split()[-1:], right.split()[:1]
        if before and after:
            steps.add((_word(before[0]), _word(after[0])))
    return steps


def _word(w: str) -> str:
    return re.sub(r"^\W+|\W+$", "", w).lower()


def grounding_failures(draft: str, cited: str, ticket: str) -> list[str]:
    failed = []
    if not urls(draft) <= urls(cited):
        failed.append("url")
    if not menu_steps(draft) <= menu_steps(cited):
        failed.append("menu_path")
    faq_nums, ticket_nums = numbers(cited), numbers(ticket)
    allowed = faq_nums | ticket_nums | {round(f * t, 2) for f in faq_nums for t in ticket_nums}
    if not {round(n, 2) for n in numbers(draft)} <= allowed:
        failed.append("number")
    return failed


# --- the rules -----------------------------------------------------------------

EXPLAIN = {
    "human_flag": "always-human topic flagged by the model",
    "human_keyword": "always-human keyword in the ticket",
    "payment_details": "payment details present in the ticket (not repeated here)",
    "empty_draft": "reply had no text",
    "draft_language": "reply language does not match the ticket",
    "ticket_language": "detected ticket language differs from the model's",
    "faq_ids": "reply cites no or unknown FAQ entries",
    "unanswered_part": "part of the ticket is not answered by the FAQ",
    "url": "reply contains a URL not in the cited FAQ",
    "menu_path": "reply contains a menu path not in the cited FAQ",
    "number": "reply contains a number not in the cited FAQ or ticket",
    "low_confidence": "model confidence below 0.7",
    "multiple_requests": "several requests and at least one needs a human",
    "close_not_spam": "close without a spam or empty flag",
}


# Checks about the quality of a reply. If only these fail, a human can fix and send the draft.
# Human topics and payment details are not in this set: those tickets never get "send if correct".
REPLY_CHECKS = {"empty_draft", "draft_language", "ticket_language", "faq_ids", "unanswered_part", "url",
                "menu_path", "number", "low_confidence", "multiple_requests"}  # fmt: skip


def keyword_topics(text: str) -> list[str]:
    folded = fold(text)
    return [topic for topic, pattern in KEYWORDS.items() if re.search(pattern, folded)]


def reply_failures(ticket: dict, d: dict, faq: dict[str, str]) -> list[str]:
    draft, text = d["draft_reply"], ticket_text(ticket)
    if not draft.strip():
        return ["empty_draft"]
    failed = []
    ticket_lang = detect_language(text)
    if ticket_lang and ticket_lang != d["language"]:
        failed.append("ticket_language")
    if detect_language(draft) != (ticket_lang or d["language"]):
        failed.append("draft_language")
    if not d["faq_ids"] or any(f not in faq for f in d["faq_ids"]):
        failed.append("faq_ids")
    if any(not p.get("faq_id") or p["faq_id"] not in faq for p in d["parts"]):
        failed.append("unanswered_part")
    cited = "\n".join(faq[f] for f in d["faq_ids"] if f in faq)
    return failed + grounding_failures(draft, cited, text)


def priority_floor(priority: str, topics: list[str]) -> str:
    """The most urgent of the model's priority and the floors of the topics ("P1" < "P2")."""
    return min([priority, *(PRIORITY_FLOORS[t] for t in topics if t in PRIORITY_FLOORS)])


def apply(ticket: dict, d: dict, faq: dict[str, str]) -> tuple[str, dict, list[str]]:
    text, flags, action = ticket_text(ticket), set(d["flags"]), d["action"]
    keywords = keyword_topics(text)
    topics = sorted(flags & set(ALWAYS_HUMAN)) + [t for t in keywords if t not in flags]
    failed = []
    if flags & set(ALWAYS_HUMAN):
        failed.append("human_flag")
    if keywords:
        failed.append("human_keyword")
    payment = "payment_details" in flags or has_payment_details(text)
    if payment:
        failed.append("payment_details")
    if action == "reply":
        failed += reply_failures(ticket, d, faq)
    if action in ("reply", "close") and d["confidence"] < MIN_CONFIDENCE:
        failed.append("low_confidence")
    if "multiple_requests" in flags and (topics or any(not p.get("faq_id") for p in d["parts"])):
        failed.append("multiple_requests")
    if action == "close" and not flags & {"spam", "empty"}:
        failed.append("close_not_spam")

    body = {k: d[k] for k in ("language", "category", "priority")}
    body["confidence"] = round(min(max(float(d["confidence"]), 0.0), 1.0), 2)
    body["reason"] = redact(d["reason"])
    floor_topics = topics + (["payment_details"] if payment else [])
    floored = priority_floor(d["priority"], floor_topics)
    if floored != d["priority"]:
        body["priority"] = floored
        body["reason"] += f" Priority raised from {d['priority']} to {floored} by code."
    escalated_from = action if failed and action != "handoff" else None
    if escalated_from:
        action = "handoff"
        body["reason"] += f" Escalated by code: {', '.join(failed)}."
    if action == "reply":
        body["draft_reply"] = redact(d["draft_reply"])
    elif action == "handoff":
        body["handoff_note"] = handoff_note(d, failed, topics, escalated_from)
    return action, body, failed


def handoff_note(d: dict, failed: list[str], topics: list[str], escalated_from: str | None) -> str:
    backtranslation = d["english_backtranslation"].strip()
    if escalated_from == "reply" and set(failed) <= REPLY_CHECKS and backtranslation:
        # Only reply-quality checks failed: give the agent the draft to check, not the model's note
        # (which was written for a reply and may say "no action needed").
        why = "; ".join(EXPLAIN[f] for f in failed)
        note = (f"Auto-escalated: {why}. Draft reply (EN): {backtranslation}"
                " Check the flagged part and send if correct.")  # fmt: skip
    else:
        lines = []
        if escalated_from:
            lines.append(f"Auto-escalated (model chose {escalated_from}).")
        if failed:
            why = "; ".join(EXPLAIN[f] for f in failed)
            lines.append(f"Checks: {why}." + (f" Topics: {', '.join(topics)}." if topics else ""))
        lines.append(d["handoff_note"].strip())
        note = " ".join(lines)
    note = redact(note)
    return note if len(note) <= NOTE_LIMIT else note[: NOTE_LIMIT - 3].rstrip() + "..."
