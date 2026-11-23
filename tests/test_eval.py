"""The eval with a scripted decider and judge: scoring, repeats, labels never leak."""

import json

import anthropic
import httpx

from agent import evaluate


def example(ex_id, body, language, category, priority, action, reason):
    label = {
        "language": language,
        "category": category,
        "priority": priority,
        "action": action,
        "reason": reason,
    }
    return {"id": ex_id, "subject": "s", "body": body, "label": label}


EXAMPLES = [
    example("E1", "Hoe ruil ik een dienst?", "nl", "question", "P4", "reply", "F03."),
    example("E2", "Ik wil mijn geld terug.", "nl", "billing", "P2", "handoff", "Refund."),
    example("E3", "Verdubbel je geld.", "nl", "other", "P4", "close", "Spam."),
]


class ScriptedDecider:
    """Returns the scripted action per example id; can change per call to simulate run-to-run noise."""

    def __init__(self, script):
        self.script, self.seen, self.count = script, [], {}

    def __call__(self, ticket):
        self.seen.append(ticket)
        i = self.count[ticket["id"]] = self.count.get(ticket["id"], 0) + 1
        action = self.script[ticket["id"]][(i - 1) % len(self.script[ticket["id"]])]
        body = {"language": "nl", "category": "question", "priority": "P4", "reason": "r", "confidence": 0.9}
        if action == "reply":
            body["draft_reply"] = "Hoi! ..."
        meta = {"model_action": action, "failed_checks": [], "flags": [], "faq_ids": ["F03"],
                "english_backtranslation": "Hi! ...", "model": "fake", "input_tokens": 1000,
                "output_tokens": 200, "cost_usd": 0.0002}  # fmt: skip
        return action, body, meta


class FakeJudge:
    def __init__(self, verdict=True):
        self.verdict, self.seen = verdict, []

    def __call__(self, ticket, cited, backtranslation):
        self.seen.append((ticket, cited, backtranslation))
        v = self.verdict
        return {"judged": True, "answers_question": v, "faq_only": True, "polite_complete": True,
                "comment": "ok", "cost_usd": 0.001}  # fmt: skip


def run(tmp_path, script, repeat=3, judge=None):
    path = tmp_path / "examples.json"
    path.write_text(json.dumps({"examples": EXAMPLES}), encoding="utf-8")
    decider, judge = ScriptedDecider(script), judge or FakeJudge()
    md, summary = evaluate.run_eval(path, tmp_path / "results", "t", repeat, decide=decider, judge=judge)
    return md, summary, decider, judge


def test_labels_never_reach_decider_or_judge(tmp_path):
    _, _, decider, judge = run(tmp_path, {"E1": ["reply"], "E2": ["reply"], "E3": ["close"]})
    assert decider.seen and all("label" not in t for t in decider.seen)
    for ticket, cited, back in judge.seen:
        text = json.dumps([ticket, cited, back])
        assert "label" not in ticket and "Refund." not in text and "F03." not in text
    assert "Swapping shifts" in judge.seen[0][1]  # judge gets the cited FAQ text


def test_unsafe_and_wrong_close_counted_per_run(tmp_path):
    script = {"E1": ["reply"], "E2": ["reply", "handoff", "handoff"], "E3": ["close", "reply", "close"]}
    _, s, _, _ = run(tmp_path, script)
    assert s["unsafe"]["per_run"] == [1, 1, 0] and s["unsafe"]["mean"] == 0.667
    assert s["unsafe"]["max"] == 1 and s["wrong_close"]["per_run"] == [0, 0, 0]
    assert s["accuracy"]["action"]["per_run"] == [0.67, 0.67, 1.0]


def test_wrong_close(tmp_path):
    _, s, _, _ = run(tmp_path, {"E1": ["close"], "E2": ["handoff"], "E3": ["close"]}, repeat=1)
    assert s["wrong_close"]["per_run"] == [1]


def test_per_example_k_of_n_and_judge_only_on_final_replies(tmp_path):
    script = {"E1": ["reply", "handoff", "reply"], "E2": ["handoff"], "E3": ["close"]}
    md, s, decider, judge = run(tmp_path, script, judge=FakeJudge(verdict=False))
    assert len(decider.seen) == 9 and len(judge.seen) == 2
    assert s["reply_quality"]["judged"] == 2 and s["reply_quality"]["mean_all_yes"] == 0.0
    text = md.read_text()
    assert "| E1 | reply/question/P4/nl | 2/3 |" in text
    assert "Label reason: F03." in text and "Back-translation: Hi! ..." in text
    report = json.loads((tmp_path / "results" / "t.json").read_text())
    assert len(report["runs"]) == 3 and report["labels"]["E2"]["action"] == "handoff"


def test_cost_per_100_tickets(tmp_path):
    _, s, _, _ = run(tmp_path, {"E1": ["handoff"], "E2": ["handoff"], "E3": ["close"]}, repeat=2)
    assert s["agent_tokens"] == {"input": 6000, "output": 1200}
    assert s["agent_cost_per_100_tickets_usd"] == 0.02


class FailingClient:
    def __init__(self):
        self.beta = self
        self.messages = self

    def parse(self, **kwargs):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.test"))


def test_failed_judge_call_is_not_judged_not_a_pass():
    judge = evaluate.make_judge(model="claude-sonnet-5-5", client=FailingClient())
    v = judge({"subject": "s", "body": "b"}, "faq", "reply")
    assert v == {"judged": False, "error": "APIConnectionError", "cost_usd": 0.0}
