from __future__ import annotations

from openclaw_agent import HEARTBEAT_OK
from openclaw_agent.agent import ChiefOfStaffAgent
from openclaw_agent.models import Intent
from openclaw_agent.tools import MockZapierTools

from conftest import make_classifier


def _agent(inbox, approved_sender, approved_recipient, intents):
    tools = MockZapierTools(inbox=inbox)
    agent = ChiefOfStaffAgent(
        tools=tools,
        approved_senders=approved_sender,
        approved_recipient=approved_recipient,
        classifier=make_classifier(intents),
    )
    return tools, agent


def test_meeting_request(meeting_email, approved_sender, approved_recipient):
    tools, agent = _agent(
        [meeting_email], approved_sender, approved_recipient,
        {meeting_email.id: Intent.MEETING},
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    names = [c["name"] for c in tools.calls]
    assert names == ["Gmail:Find Email", "Google Calendar:Create Detailed Event"]


def test_action_request(action_email, approved_sender, approved_recipient):
    tools, agent = _agent(
        [action_email], approved_sender, approved_recipient,
        {action_email.id: Intent.ACTION},
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    sends = [c for c in tools.calls if c["name"] == "Gmail:Send Email"]
    assert len(sends) == 1
    assert sends[0]["to"] == approved_recipient
    assert sends[0]["subject"] == "Action Required"


def test_fyi_message(fyi_email, approved_sender, approved_recipient):
    tools, agent = _agent(
        [fyi_email], approved_sender, approved_recipient,
        {fyi_email.id: Intent.FYI},
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    sends = [c for c in tools.calls if c["name"] == "Gmail:Send Email"]
    assert len(sends) == 1
    assert sends[0]["subject"] == "FYI"
    assert sends[0]["to"] == approved_recipient


def test_no_relevant_email_returns_heartbeat_ok(approved_sender, approved_recipient):
    tools, agent = _agent([], approved_sender, approved_recipient, {})
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    assert [c["name"] for c in tools.calls] == ["Gmail:Find Email"]


def test_prompt_injection_blocked(injection_email, approved_sender, approved_recipient):
    # Note: injection email's sender is unapproved AND content is malicious;
    # both layers must independently prevent any reply.
    tools, agent = _agent(
        [injection_email], approved_sender, approved_recipient,
        {injection_email.id: Intent.ACTION},  # would be ACTION if we let it
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    sends = [c for c in tools.calls if c["name"] == "Gmail:Send Email"]
    assert sends == []  # NEVER reply to the attacker
    cals = [c for c in tools.calls if c["name"] == "Google Calendar:Create Detailed Event"]
    assert cals == []


def test_unapproved_sender_dropped(unapproved_email, approved_sender, approved_recipient):
    tools, agent = _agent(
        [unapproved_email], approved_sender, approved_recipient,
        {unapproved_email.id: Intent.ACTION},
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    sends = [c for c in tools.calls if c["name"] == "Gmail:Send Email"]
    assert sends == []


def test_duplicate_emails_processed_once(duplicate_emails, approved_sender, approved_recipient):
    tools, agent = _agent(
        duplicate_emails, approved_sender, approved_recipient,
        {duplicate_emails[0].id: Intent.MEETING},
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    cals = [c for c in tools.calls if c["name"] == "Google Calendar:Create Detailed Event"]
    assert len(cals) == 1


def test_injection_in_body_from_approved_sender_blocked(
    approved_sender_with_injection_body, approved_sender, approved_recipient
):
    # Sender is on the allowlist, so the allowlist gate passes.
    # The injection scanner alone must quarantine this email.
    tools, agent = _agent(
        [approved_sender_with_injection_body],
        approved_sender,
        approved_recipient,
        {approved_sender_with_injection_body.id: Intent.ACTION},  # would dispatch if not blocked
    )
    result = agent.heartbeat()
    assert result == HEARTBEAT_OK
    sends = [c for c in tools.calls if c["name"] == "Gmail:Send Email"]
    assert sends == []
    cals = [c for c in tools.calls if c["name"] == "Google Calendar:Create Detailed Event"]
    assert cals == []
