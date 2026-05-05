from datetime import datetime

from openclaw_agent.models import Email
from openclaw_agent.tools import MockZapierTools


def _email(eid: str, sender: str = "x@y.com") -> Email:
    return Email(
        id=eid,
        sender=sender,
        subject="s",
        body="b",
        unread=True,
        received_at=datetime.now(),
    )


def test_find_email_returns_inbox_and_counts_one_call():
    inbox = [_email("e1"), _email("e2")]
    tools = MockZapierTools(inbox=inbox)

    result = tools.find_email("unread last 24h", limit=100)

    assert {e.id for e in result} == {"e1", "e2"}
    assert tools.tool_call_count == 1


def test_send_email_increments_counter():
    tools = MockZapierTools(inbox=[])
    tools.send_email(to="a@b.com", subject="hi", body="x")
    assert tools.tool_call_count == 1


def test_create_calendar_event_increments_counter():
    tools = MockZapierTools(inbox=[])
    tools.create_calendar_event(
        title="m", start="2026-04-28T14:00", end="2026-04-28T14:30",
        attendee="a@b.com",
    )
    assert tools.tool_call_count == 1


def test_find_email_dedupes_inbox_by_id():
    dup = _email("e1")
    inbox = [dup, dup, _email("e2")]
    tools = MockZapierTools(inbox=inbox)
    result = tools.find_email("unread", limit=100)
    assert sorted(e.id for e in result) == ["e1", "e2"]


def test_calls_log_records_name_and_args_for_each_tool():
    tools = MockZapierTools(inbox=[_email("e1")])
    tools.find_email("unread", limit=10)
    tools.send_email(to="owner@example.com", subject="hi", body="hello world")
    tools.create_calendar_event(
        title="m", start="t1", end="t2", attendee="owner@example.com"
    )

    assert [c["name"] for c in tools.calls] == [
        "Gmail:Find Email",
        "Gmail:Send Email",
        "Google Calendar:Create Detailed Event",
    ]


def test_send_email_calls_log_records_body_len_not_body():
    tools = MockZapierTools(inbox=[])
    tools.send_email(to="owner@example.com", subject="hi", body="secret content")
    entry = tools.calls[0]
    assert entry["body_len"] == len("secret content")
    assert "body" not in entry  # privacy: body content must not be logged


def test_estimated_tokens_increases_with_tool_calls():
    tools = MockZapierTools(inbox=[])
    assert tools.estimated_tokens == 0
    tools.send_email(to="x@y.com", subject="hi", body="z")
    assert tools.estimated_tokens > 0
