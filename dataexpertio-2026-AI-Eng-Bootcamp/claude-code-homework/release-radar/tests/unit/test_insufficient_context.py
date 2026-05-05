"""Tests for the InsufficientContextGuardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.insufficient_context import InsufficientContextGuardrail


@pytest.fixture
def guardrail():
    return InsufficientContextGuardrail()


# --- triage-issue ---


def test_issue_title_only_triggers(guardrail):
    """Issue with title only should trigger GuardrailError with 'body' in missing."""
    data = {"title": "Fix the login bug"}
    with pytest.raises(GuardrailError) as exc_info:
        guardrail.check_input(data, skill="triage-issue")
    err = exc_info.value
    assert err.details["status"] == "insufficient_context"
    assert "body" in err.details["missing"]


def test_issue_title_and_body_passes(guardrail):
    """Issue with title + body should pass through unchanged."""
    data = {"title": "Fix the login bug", "body": "Users cannot log in after the update."}
    result = guardrail.check_input(data, skill="triage-issue")
    assert result == data


# --- summarize-pr ---


def test_pr_no_diff_snippets_triggers(guardrail):
    """PR with no diff_snippets should trigger with 'diff_snippets' in missing."""
    data = {"title": "Add feature X"}
    with pytest.raises(GuardrailError) as exc_info:
        guardrail.check_input(data, skill="summarize-pr")
    err = exc_info.value
    assert err.details["status"] == "insufficient_context"
    assert "diff_snippets" in err.details["missing"]


def test_pr_all_fields_passes(guardrail):
    """PR with title + diff_snippets should pass through."""
    data = {"title": "Add feature X", "diff_snippets": ["- old line", "+ new line"]}
    result = guardrail.check_input(data, skill="summarize-pr")
    assert result == data


# --- digest-commits ---


def test_empty_commits_triggers(guardrail):
    """Empty commits list should trigger with 'commits' in missing."""
    data = {"commits": []}
    with pytest.raises(GuardrailError) as exc_info:
        guardrail.check_input(data, skill="digest-commits")
    err = exc_info.value
    assert err.details["status"] == "insufficient_context"
    assert "commits" in err.details["missing"]


def test_commits_with_data_passes(guardrail):
    """Non-empty commits list should pass through."""
    data = {"commits": [{"sha": "abc123", "message": "Initial commit"}]}
    result = guardrail.check_input(data, skill="digest-commits")
    assert result == data


# --- draft-email ---


def test_email_missing_digest_triggers(guardrail):
    """Email input missing digest should trigger with 'digest' in missing."""
    data = {"subject": "Weekly update"}
    with pytest.raises(GuardrailError) as exc_info:
        guardrail.check_input(data, skill="draft-email")
    err = exc_info.value
    assert err.details["status"] == "insufficient_context"
    assert "digest" in err.details["missing"]


# --- unknown skill ---


def test_unknown_skill_passes_through(guardrail):
    """Unknown skill should pass data through without error."""
    data = {"anything": "goes"}
    result = guardrail.check_input(data, skill="unknown-skill")
    assert result == data


# --- missing field precision ---


def test_missing_fields_lists_exactly_what_is_absent(guardrail):
    """When multiple fields are missing, details['missing'] lists each one."""
    data = {}  # missing both title and body for triage-issue
    with pytest.raises(GuardrailError) as exc_info:
        guardrail.check_input(data, skill="triage-issue")
    missing = exc_info.value.details["missing"]
    assert "title" in missing
    assert "body" in missing
    assert len(missing) == 2
