"""TDD tests for the uncertainty guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.uncertainty import UncertaintyGuardrail


@pytest.fixture
def guardrail():
    return UncertaintyGuardrail()


# Test 1: High confidence with no hedging passes
def test_high_confidence_no_hedging_passes(guardrail):
    data = {
        "confidence": "high",
        "reasoning": "The release notes clearly state version 2.0 is out.",
        "summary": "Version 2.0 released with breaking changes.",
    }
    result = guardrail.check_output(data)
    assert result == data


# Test 2: High confidence with hedging language raises GuardrailError matching "hedging"
def test_high_confidence_with_hedging_raises(guardrail):
    data = {
        "confidence": "high",
        "reasoning": "This might be a breaking change, but I'm not sure.",
        "summary": "Version 2.0 possibly released.",
    }
    with pytest.raises(GuardrailError, match="hedging"):
        guardrail.check_output(data)


# Test 3: Low confidence with empty uncertainty_flags raises GuardrailError matching
# "uncertainty_flags"
def test_low_confidence_empty_flags_raises(guardrail):
    data = {
        "confidence": "low",
        "reasoning": "There are conflicting signals in the data.",
        "uncertainty_flags": [],
    }
    with pytest.raises(GuardrailError, match="uncertainty_flags"):
        guardrail.check_output(data)


# Test 4: Medium confidence with flags passes
def test_medium_confidence_with_flags_passes(guardrail):
    data = {
        "confidence": "medium",
        "reasoning": "Some information is available but incomplete.",
        "uncertainty_flags": ["incomplete_changelog", "no_release_date"],
    }
    result = guardrail.check_output(data)
    assert result == data


# Test 5: Invalid confidence value raises GuardrailError matching "confidence"
def test_invalid_confidence_raises(guardrail):
    data = {
        "confidence": "very_high",
        "reasoning": "Everything looks good.",
    }
    with pytest.raises(GuardrailError, match="confidence"):
        guardrail.check_output(data)


# Test 6: Missing confidence field raises GuardrailError matching "confidence"
def test_missing_confidence_raises(guardrail):
    data = {
        "reasoning": "No confidence level provided.",
        "summary": "Something happened.",
    }
    with pytest.raises(GuardrailError, match="confidence"):
        guardrail.check_output(data)


# Test 7: Insufficient context status is skipped (passes through)
def test_insufficient_context_skipped(guardrail):
    data = {
        "status": "insufficient_context",
        "reasoning": "Not enough data to analyze.",
    }
    result = guardrail.check_output(data)
    assert result == data
