import pytest

from agent import rules
from agent.decide import FAQ_PATH

FAQ = rules.parse_faq(FAQ_PATH.read_text(encoding="utf-8"))


def decision(**over):
    base = {
        "language": "nl", "flags": [], "parts": [{"topic_en": "swap shifts", "faq_id": "F03"}],
        "category": "question", "priority": "P4", "action": "reply", "confidence": 0.9,
        "reason": "How-to answered by the FAQ.", "faq_ids": ["F03"],
        "draft_reply": "Hoi! Je kunt een dienst ruilen in de app: open de dienst en tik op 'Ruil aanbieden'. "
        "De manager keurt het goed onder Rooster \u2192 Verzoeken. "
        "Met vriendelijke groet, het Roosterly team",
        "english_backtranslation": "Hi! ...", "handoff_note": "Customer asks how to swap shifts.",
    }  # fmt: skip
    return {**base, **over}


def ticket(body="Hoe ruil ik een dienst met een collega?", subject="Dienst ruilen"):
    return {"id": "X1", "subject": subject, "body": body}


def test_clean_reply_passes():
    action, body, failed = rules.apply(ticket(), decision(), FAQ)
    assert (action, failed) == ("reply", [])
    assert set(body) == {"language", "category", "priority", "confidence", "reason", "draft_reply"}


@pytest.mark.parametrize("flag", rules.ALWAYS_HUMAN)
def test_always_human_flag_hands_off(flag):
    action, body, failed = rules.apply(ticket(), decision(flags=[flag]), FAQ)
    assert action == "handoff" and "human_flag" in failed
    assert body["handoff_note"].startswith("Auto-escalated (model chose reply).")
    assert "draft_reply" not in body


@pytest.mark.parametrize(
    "text, topic",
    [
        ("Kunnen jullie het bedrag terugbetalen?", "refund"),
        ("Ik wil mijn abonnement opzeggen.", "cancellation_or_contract"),
        ("Ich m\u00f6chte k\u00fcndigen.", "cancellation_or_contract"),
        ("Graag inzage in mijn gegevens volgens de AVG.", "personal_data"),
        ("Ons account is gehackt!", "security"),
        ("Mijn advocaat neemt contact op.", "legal_threat"),
        ("We overwegen over te stappen naar een concurrent.", "churn_threat"),
        ("I want a refund for March.", "refund"),
        ("Bitte R\u00fcckerstattung f\u00fcr Mai.", "refund"),
    ],
)
def test_keyword_backstop_hands_off_even_if_model_misses_it(text, topic):
    assert topic in rules.keyword_topics(text)
    action, _, failed = rules.apply(ticket(text), decision(), FAQ)
    assert action == "handoff" and "human_keyword" in failed


@pytest.mark.parametrize(
    "text",
    [
        "Hoe voeg ik een medewerker toe met 32 contracturen?",  # F02, not a contract change
        "Kan ik een dienst annuleren in het rooster?",  # cancelling a shift is a how-to
        "Hoe wissel ik van taal in de app?",
    ],
)
def test_keywords_do_not_fire_on_faq_questions(text):
    assert rules.keyword_topics(text) == []


def test_luhn_and_iban():
    assert rules.luhn_ok("4111111111111111") and not rules.luhn_ok("4111111111111112")
    assert rules.has_payment_details("kaart 4111-1111-1111-1111")
    assert rules.has_payment_details("IBAN NL91ABNA0417164300")
    assert not rules.has_payment_details("bel 06 1234 5678, factuur 2026-0042, 25 medewerkers")
    assert not rules.has_payment_details("nummer 4111 1111 1111 1112")  # fails Luhn


def test_payment_details_in_ticket_hand_off_and_are_never_echoed():
    t = ticket("Hoe ruil ik een dienst? Mijn IBAN is NL91 ABNA 0417 1643 00, kaart 4111 1111 1111 1111.")
    d = decision(
        draft_reply="Hoi, uw IBAN NL91 ABNA 0417 1643 00 is genoteerd.",
        reason="Card 4111 1111 1111 1111 seen.",
        handoff_note="IBAN NL91ABNA0417164300 and card 4111111111111111 in ticket.",
    )
    action, body, failed = rules.apply(t, d, FAQ)
    assert action == "handoff" and "payment_details" in failed
    out = str(body)
    for secret in ("0417", "4111"):
        assert secret not in out
    assert "[redacted]" in body["handoff_note"] and "not repeated" in body["handoff_note"]


def test_reply_language_must_match_ticket():
    d = decision(draft_reply="Hi! You can swap a shift in the app: open it and tap 'Ruil aanbieden'. Thanks!")
    action, _, failed = rules.apply(ticket(), d, FAQ)
    assert action == "handoff" and "draft_language" in failed


def test_model_language_field_checked_against_detected_ticket_language():
    _, _, failed = rules.apply(ticket(), decision(language="en"), FAQ)
    assert "ticket_language" in failed


@pytest.mark.parametrize("ids", [[], ["F99"], ["F03", "F42"]])
def test_cited_faq_ids_must_exist(ids):
    action, _, failed = rules.apply(ticket(), decision(faq_ids=ids), FAQ)
    assert action == "handoff" and "faq_ids" in failed


def test_unanswered_part_hands_off():
    parts = [{"topic_en": "swap shifts", "faq_id": "F03"}, {"topic_en": "custom report", "faq_id": None}]
    action, _, failed = rules.apply(ticket(), decision(parts=parts), FAQ)
    assert action == "handoff" and "unanswered_part" in failed


def test_price_times_ticket_number_is_grounded():
    t = ticket("Wat kost Plus voor 25 medewerkers?", "Prijs Plus")
    d = decision(
        faq_ids=["F05"],
        parts=[{"topic_en": "price", "faq_id": "F05"}],
        draft_reply="Hoi! Plus kost \u20ac6 per actieve medewerker per maand. Voor 25 medewerkers is dat "
        "\u20ac150 per maand, excl. btw. Met vriendelijke groet, het Roosterly team",
    )
    assert rules.apply(t, d, FAQ)[2] == []


@pytest.mark.parametrize(
    "extra, check",
    [
        ("Kijk op help.roosterly.nl voor meer.", "url"),
        ("Mail ons op support@roosterly.nl.", "url"),
        ("Ga naar Instellingen \u2192 Diensten om het aan te zetten.", "menu_path"),
        ("Je krijgt 20% korting op het Plus abonnement.", "number"),
        ("We reageren binnen 24 uur op je verzoek.", "number"),
    ],
)
def test_invented_facts_fail_grounding(extra, check):
    d = decision()
    d["draft_reply"] = d["draft_reply"] + " " + extra
    action, _, failed = rules.apply(ticket(), d, FAQ)
    assert action == "handoff" and check in failed


def test_empty_draft_hands_off():
    assert rules.apply(ticket(), decision(draft_reply="  "), FAQ)[2] == ["empty_draft"]


def test_low_confidence_hands_off_reply_and_close():
    assert "low_confidence" in rules.apply(ticket(), decision(confidence=0.5), FAQ)[2]
    close = decision(action="close", flags=["spam"], confidence=0.5, draft_reply="")
    assert rules.apply(ticket("Koop nu crypto"), close, FAQ)[0] == "handoff"


def test_multiple_requests_with_human_part_hands_off():
    parts = [{"topic_en": "swap", "faq_id": "F03"}, {"topic_en": "custom export", "faq_id": None}]
    d = decision(action="handoff", flags=["multiple_requests"], parts=parts, draft_reply="")
    assert "multiple_requests" in rules.apply(ticket(), d, FAQ)[2]


def test_close_needs_spam_or_empty_flag():
    d = decision(action="close", flags=[], draft_reply="")
    action, body, failed = rules.apply(ticket(), d, FAQ)
    assert action == "handoff" and failed == ["close_not_spam"] and body["handoff_note"]
    spam = decision(action="close", flags=["spam"], draft_reply="")
    action, body, _ = rules.apply(ticket("Verdubbel je geld"), spam, FAQ)
    assert action == "close" and set(body) == {"language", "category", "priority", "confidence", "reason"}


def test_rules_never_turn_handoff_into_reply():
    d = decision(action="handoff")
    assert rules.apply(ticket(), d, FAQ)[0] == "handoff"


def test_handoff_note_is_capped():
    d = decision(flags=["refund"], handoff_note="word " * 300)
    note = rules.apply(ticket(), d, FAQ)[1]["handoff_note"]
    assert len(note) <= rules.NOTE_LIMIT and note.endswith("...")


@pytest.mark.parametrize(
    "text, lang",
    [
        ("Hoe voeg ik een nieuwe medewerker toe aan ons rooster?", "nl"),
        ("How do I add a new employee to the rota?", "en"),
        ("Wie kann ich einen neuen Mitarbeiter hinzuf\u00fcgen?", "de"),
        ("Onderhoud?", None),
    ],
)
def test_detect_language(text, lang):
    assert rules.detect_language(text) == lang


@pytest.mark.parametrize(
    "flag, model_priority, expected",
    [
        ("security", "P3", "P1"),
        ("legal_threat", "P4", "P1"),
        ("refund", "P4", "P2"),
        ("cancellation_or_contract", "P3", "P2"),
        ("churn_threat", "P4", "P2"),
        ("personal_data", "P3", "P2"),
        ("payment_details", "P4", "P2"),
        ("refund", "P1", "P1"),  # a floor never lowers
        ("personal_data", "P2", "P2"),
        ("multiple_requests", "P4", "P4"),  # not a floor topic
    ],
)
def test_priority_floor_from_model_flag(flag, model_priority, expected):
    _, body, _ = rules.apply(ticket(), decision(flags=[flag], priority=model_priority), FAQ)
    assert body["priority"] == expected
    raised = f"Priority raised from {model_priority} to {expected} by code."
    assert (raised in body["reason"]) == (expected != model_priority)


def test_priority_floor_from_keyword_and_payment_details_in_ticket():
    _, body, _ = rules.apply(ticket("Ons account is gehackt!"), decision(priority="P4"), FAQ)
    assert body["priority"] == "P1"  # keyword backstop, model gave no flag
    _, body, _ = rules.apply(ticket("Mijn IBAN is NL91ABNA0417164300"), decision(priority="P4"), FAQ)
    assert body["priority"] == "P2" and "0417164300" not in body["reason"]


def test_highest_floor_wins():
    d = decision(flags=["refund", "legal_threat"], priority="P4")
    assert rules.apply(ticket(), d, FAQ)[1]["priority"] == "P1"


def test_no_floor_topic_keeps_model_priority():
    assert rules.apply(ticket(), decision(priority="P4"), FAQ)[1]["priority"] == "P4"


def test_escalated_reply_note_carries_the_draft_not_the_model_note():
    d = decision(
        draft_reply="Hoi! Kijk op https://example.com voor de uitleg. Groet, het Roosterly team",
        english_backtranslation="Hi! See https://example.com for the explanation.",
        handoff_note="No action needed.",
    )
    action, body, failed = rules.apply(ticket(), d, FAQ)
    assert action == "handoff" and failed == ["url"]
    note = body["handoff_note"]
    assert note.startswith("Auto-escalated: reply contains a URL not in the cited FAQ.")
    assert "Draft reply (EN): Hi! See https://example.com" in note
    assert note.endswith("Check the flagged part and send if correct.")
    assert "No action needed" not in note


def test_escalated_reply_with_human_topic_keeps_the_human_note():
    d = decision(flags=["refund"], handoff_note="Customer wants money back for March.")
    note = rules.apply(ticket(), d, FAQ)[1]["handoff_note"]
    assert "send if correct" not in note and "Draft reply" not in note
    assert note.endswith("Customer wants money back for March.")


def test_escalated_reply_note_never_repeats_payment_details():
    d = decision(confidence=0.5, english_backtranslation="Your card 4111 1111 1111 1111 is fine.")
    note = rules.apply(ticket(), d, FAQ)[1]["handoff_note"]
    assert "Draft reply (EN)" in note and "4111" not in note
