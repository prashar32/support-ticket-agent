import pytest
from fake_helpdesk import FakeHelpdesk

from agent.helpdesk import AlreadyHandled, ApiError, OutcomeUnknown, Unavailable, is_handled

BODY = {"language": "nl", "category": "other", "priority": "P3", "reason": "r", "handoff_note": "n"}


def test_pagination_fetches_every_open_ticket():
    fake = FakeHelpdesk(n=25)
    tickets = fake.client().list_open_tickets()
    assert [t["id"] for t in tickets] == sorted(fake.tickets)
    assert fake.requests.count(("GET", "/tickets")) == 3


def test_client_never_exceeds_four_requests_per_second():
    fake = FakeHelpdesk(n=30)
    client = fake.client()
    for tid in fake.tickets:
        client.get_ticket(tid)
    assert fake.statuses[429] == 0
    assert fake.clock.t - 1000.0 >= (len(fake.requests) - 1) * 0.25


def test_503_is_retried_with_backoff():
    fake = FakeHelpdesk()
    fake.fault("GET", "/tickets", "503", "503")
    assert len(fake.client().list_open_tickets()) == 30
    assert 0.5 in fake.clock.sleeps and 1 in fake.clock.sleeps


def test_503_gives_up_after_retries():
    fake = FakeHelpdesk()
    fake.fault("GET", "/status", *["503"] * 6)
    with pytest.raises(Unavailable):
        fake.client().status()


def test_429_waits_retry_after():
    fake = FakeHelpdesk()
    fake.fault("GET", "/status", "429")
    fake.client().status()
    assert 2.0 in fake.clock.sleeps


def test_409_is_not_retried():
    fake = FakeHelpdesk()
    fake.handled["T001"] = {"action": "reply", "body": {}}
    with pytest.raises(AlreadyHandled):
        fake.client().post_decision("T001", "handoff", BODY)
    assert fake.posts("T001") == 1


def test_422_surfaces_problems():
    fake = FakeHelpdesk()
    with pytest.raises(ApiError) as err:
        fake.client().post_decision("T001", "reply", {"language": "nl"})
    assert err.value.status == 422
    assert "draft_reply is required for reply" in err.value.problems


def test_post_saved_then_timeout_is_checked_not_resent():
    fake = FakeHelpdesk()
    fake.fault("POST", "/tickets/T001/handoff", "timeout_after_save")
    fake.client().post_decision("T001", "handoff", BODY)
    assert fake.posts("T001") == 1
    assert ("GET", "/tickets/T001") in fake.requests
    assert fake.statuses[409] == 0


def test_post_lost_before_save_is_resent_after_check():
    fake = FakeHelpdesk()
    fake.fault("POST", "/tickets/T001/handoff", "timeout_before")
    fake.client().post_decision("T001", "handoff", BODY)
    assert fake.handled["T001"]["body"] == BODY
    assert fake.posts("T001") == 2  # one lost, one saved
    assert fake.statuses[409] == 0


def test_post_keeps_failing_raises_outcome_unknown():
    fake = FakeHelpdesk()
    fake.fault("POST", "/tickets/T001/handoff", *["timeout_before"] * 3)
    with pytest.raises(OutcomeUnknown):
        fake.client().post_decision("T001", "handoff", BODY)


def test_key_and_email_not_in_repr():
    client = FakeHelpdesk().client()
    assert "test-key" not in repr(client) and "example.com" not in repr(client)


def test_is_handled():
    assert not is_handled({"id": "T1", "handled": None})
    assert is_handled({"id": "T1", "handled": {"action": "reply"}})
    assert not is_handled({"id": "T1"})
