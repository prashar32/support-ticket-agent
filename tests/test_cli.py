import pytest
from fake_helpdesk import FakeHelpdesk

from agent import cli, journal, runner
from agent.decide import stub_decide


@pytest.fixture
def handled(tmp_path, monkeypatch):
    """A fake helpdesk and journal after one full run."""
    monkeypatch.setattr(cli, "LOG_DIR", tmp_path / "logs")
    fake = FakeHelpdesk()
    db = journal.open_journal(tmp_path / "journal.db")
    runner.run(fake.client(), db, stub_decide, tmp_path / "run.jsonl")
    return fake, db


def test_reset_confirmed_reopens_and_clears_journal(handled):
    fake, db = handled
    assert cli.cmd_reset(fake.client(), db, ask=lambda _: "reset") == 0
    assert ("POST", "/practice/reset") in fake.requests
    assert journal.counts(db) == {}
    assert cli.cmd_run(fake.client(), db, stub_decide) == 0  # next run handles everything again
    assert len(fake.handled) == 30 and fake.statuses[409] == 0


def test_reset_aborted_makes_no_call(handled):
    fake, db = handled
    requests_before = len(fake.requests)
    assert cli.cmd_reset(fake.client(), db, ask=lambda _: "yes") == 1
    assert len(fake.requests) == requests_before
    assert journal.counts(db) == {"done": 30}


def test_reset_failure_keeps_journal(handled):
    fake, db = handled
    fake.fault("POST", "/practice/reset", *["503"] * 6)
    assert cli.cmd_reset(fake.client(), db, ask=lambda _: "reset") == 1
    assert journal.counts(db) == {"done": 30}
    assert len(fake.handled) == 30


def test_run_refuses_stale_journal(handled, capsys):
    fake, db = handled
    fake.handled.clear()
    assert cli.cmd_run(fake.client(), db, stub_decide) == 1
    assert "agent reset" in capsys.readouterr().out
    assert fake.statuses[409] == 0


def test_status_does_not_print_candidate(handled, capsys):
    fake, db = handled
    assert cli.cmd_status(fake.client(), db) == 0
    out = capsys.readouterr().out
    assert "Test Candidate" not in out and "candidate" not in out
    assert '"handled_tickets": 30' in out


def test_eval_needs_no_helpdesk(monkeypatch, tmp_path, capsys):
    from agent import evaluate

    def no_helpdesk():
        raise AssertionError("eval must not build a helpdesk client")

    calls = []
    monkeypatch.setattr(cli, "helpdesk_from_env", no_helpdesk)
    monkeypatch.setattr(
        evaluate, "run_eval", lambda *a: calls.append(a) or (tmp_path / "x.md", {"unsafe": 0})
    )
    assert cli.main(["eval", "--out", "baseline", "--repeat", "2"]) == 0
    assert calls[0][2:] == ("baseline", 2)
