import json

import pytest
from fake_helpdesk import Crash, FakeHelpdesk

from agent import journal, runner
from agent.decide import stub_decide


class CountingDecider:
    """Stub decider that records calls and stamps each decision with its call number."""

    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, ticket):
        self.calls.append(ticket["id"])
        action, body, meta = stub_decide(ticket)
        return action, {**body, "reason": f"decision #{len(self.calls)}"}, meta


@pytest.fixture
def setup(tmp_path):
    def make(**kwargs):
        fake = FakeHelpdesk(**kwargs)
        db = journal.open_journal(tmp_path / "journal.db")
        return fake, db, CountingDecider(), tmp_path / "run.jsonl"

    return make


def assert_one_answer_each(fake, decide):
    assert set(fake.handled) == set(fake.tickets)
    assert all(fake.posts(tid) >= 1 for tid in fake.tickets)
    assert sorted(decide.calls) == sorted(fake.tickets)  # model called once per ticket
    assert fake.statuses[409] == 0


def test_happy_path_lists_all_pages_before_first_post(setup):
    fake, db, decide, log = setup()
    summary = runner.run(fake.client(), db, decide, log)
    assert summary == {"done": 30}
    first_post = next(i for i, (m, _) in enumerate(fake.requests) if m == "POST")
    assert [r for r in fake.requests[:first_post] if r[1] == "/tickets"] == [("GET", "/tickets")] * 3
    assert ("GET", "/tickets") not in fake.requests[first_post:]
    assert_one_answer_each(fake, decide)
    assert journal.counts(db) == {"done": 30}
    assert len(log.read_text().splitlines()) == 30


def test_random_503s_still_one_answer_each(setup):
    fake, db, decide, log = setup(p503=0.2, seed=7)
    summary = runner.run(fake.client(), db, decide, log)
    if summary.get("pending"):  # retries used up: a second run finishes the job
        runner.run(fake.client(), db, decide, log)
    assert fake.statuses[503] > 0
    assert_one_answer_each(fake, decide)


def test_409_becomes_anomaly_without_retry(setup):
    fake, db, decide, log = setup()
    fake.fault("POST", "/tickets/T005/handoff", "already_handled")
    summary = runner.run(fake.client(), db, decide, log)
    assert summary == {"done": 29, "anomaly": 1}
    assert fake.posts("T005") == 1
    assert journal.get(db, "T005")["status"] == "anomaly"
    assert journal.get(db, "T005")["note"].startswith("409")


def test_422_becomes_anomaly_with_problems(setup):
    fake, db, _, log = setup()

    def bad_reply_for_t007(ticket):
        if ticket["id"] == "T007":
            return "reply", {"language": "nl", "category": "question", "priority": "P4", "reason": "x"}, {}
        return stub_decide(ticket)

    runner.run(fake.client(), db, bad_reply_for_t007, log)
    row = journal.get(db, "T007")
    assert row["status"] == "anomaly"
    assert "draft_reply is required for reply" in row["note"]


def test_saved_then_timeout_is_done_without_resend(setup):
    fake, db, decide, log = setup()
    fake.fault("POST", "/tickets/T003/handoff", "timeout_after_save")
    assert runner.run(fake.client(), db, decide, log) == {"done": 30}
    assert fake.posts("T003") == 1
    assert_one_answer_each(fake, decide)


def test_503s_used_up_on_post_is_finished_by_next_run(setup):
    fake, db, decide, log = setup()
    fake.fault("POST", "/tickets/T004/handoff", *["503"] * 6)
    assert runner.run(fake.client(), db, decide, log) == {"done": 29, "pending": 1}
    assert journal.get(db, "T004")["status"] == "in_flight"
    assert runner.run(fake.client(), db, decide, log) == {"done": 1}
    assert_one_answer_each(fake, decide)


def test_crash_between_decide_and_post(setup, monkeypatch):
    fake, db, decide, log = setup()
    real_set_status = journal.set_status

    def crash_on_t010(db_, tid, status, note=None):
        if tid == "T010" and status == "in_flight":
            raise Crash("died after the decision was stored")
        real_set_status(db_, tid, status, note)

    monkeypatch.setattr(journal, "set_status", crash_on_t010)
    with pytest.raises(Crash):
        runner.run(fake.client(), db, decide, log)
    stored = journal.get(db, "T010")
    assert stored["status"] == "decided"
    monkeypatch.undo()

    runner.run(fake.client(), db, decide, log)  # restart
    assert_one_answer_each(fake, decide)
    assert fake.sent["T010"] == stored["payload"]  # same stored decision was sent


def test_crash_during_post_before_it_was_saved(setup):
    fake, db, decide, log = setup()
    fake.fault("POST", "/tickets/T012/handoff", "crash_before")
    with pytest.raises(Crash):
        runner.run(fake.client(), db, decide, log)
    stored = journal.get(db, "T012")
    assert stored["status"] == "in_flight"

    runner.run(fake.client(), db, decide, log)  # restart: GET says not handled -> resend
    assert_one_answer_each(fake, decide)
    assert fake.sent["T012"] == stored["payload"]


def test_crash_between_post_and_journal_update(setup):
    fake, db, decide, log = setup()
    fake.fault("POST", "/tickets/T015/handoff", "crash_after_save")
    with pytest.raises(Crash):
        runner.run(fake.client(), db, decide, log)
    assert journal.get(db, "T015")["status"] == "in_flight"
    assert "T015" in fake.handled

    summary = runner.run(fake.client(), db, decide, log)  # restart: GET says handled -> done
    assert summary["recovered"] == 1
    assert fake.posts("T015") == 1
    assert journal.get(db, "T015")["status"] == "done"
    assert_one_answer_each(fake, decide)


def test_stale_journal_refuses_to_run(setup):
    fake, db, decide, log = setup()
    runner.run(fake.client(), db, decide, log)
    fake.handled.clear()  # helpdesk reset behind the journal's back
    posts_before = len([r for r in fake.requests if r[0] == "POST"])

    with pytest.raises(runner.StaleJournal) as err:
        runner.run(fake.client(), db, decide, log)
    assert len(err.value.ticket_ids) == 30
    assert len(decide.calls) == 30  # no new decisions
    assert len([r for r in fake.requests if r[0] == "POST"]) == posts_before


def test_log_has_no_ticket_text_or_secrets(setup):
    fake, db, decide, log = setup()
    runner.run(fake.client(), db, decide, log)
    text = log.read_text()
    for t in fake.tickets.values():
        assert t["body"] not in text and t["subject"] not in text
    for secret in ("NL91ABNA0417164300", "4111", "test-key", "me@example.com", "decision #"):
        assert secret not in text
    lines = [json.loads(line) for line in text.splitlines()]
    assert {line["ticket_id"] for line in lines} == set(fake.tickets)
