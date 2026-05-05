"""Tests for the citation guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.citation import CitationGuardrail


@pytest.fixture
def guardrail():
    return CitationGuardrail()


# Test 1: Valid citations with claim+source passes
def test_valid_citations_pass(guardrail):
    data = {
        "summary": "Some release notes.",
        "citations": [
            {
                "claim": "Feature X was added.",
                "source": "https://github.com/org/repo/commit/abc123",
            },
        ],
    }
    result = guardrail.check_output(data)
    assert result is data


# Test 2: Empty citations array raises GuardrailError matching "citations"
def test_empty_citations_raises(guardrail):
    data = {"citations": []}
    with pytest.raises(GuardrailError, match="citations"):
        guardrail.check_output(data)


# Test 3: Missing citations field raises GuardrailError matching "citations"
def test_missing_citations_field_raises(guardrail):
    data = {"summary": "No citations here."}
    with pytest.raises(GuardrailError, match="citations"):
        guardrail.check_output(data)


# Test 4: Citation missing claim field raises GuardrailError matching "claim"
def test_citation_missing_claim_raises(guardrail):
    data = {
        "citations": [
            {"source": "https://github.com/org/repo/commit/abc123"},
        ]
    }
    with pytest.raises(GuardrailError, match="claim"):
        guardrail.check_output(data)


# Test 5: Citation missing source field raises GuardrailError matching "source"
def test_citation_missing_source_raises(guardrail):
    data = {
        "citations": [
            {"claim": "Feature X was added."},
        ]
    }
    with pytest.raises(GuardrailError, match="source"):
        guardrail.check_output(data)


# Test 6: Insufficient context status is skipped (passes through)
def test_insufficient_context_skipped(guardrail):
    data = {"status": "insufficient_context"}
    result = guardrail.check_output(data)
    assert result is data


# Test 7: Commit SHA citation is valid
def test_commit_sha_citation_valid(guardrail):
    data = {
        "citations": [
            {
                "claim": "Fixed memory leak in parser.",
                "source": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            }
        ]
    }
    result = guardrail.check_output(data)
    assert result is data
