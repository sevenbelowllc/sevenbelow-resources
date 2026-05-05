"""Tests for schema validation guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.schema_validation import SchemaValidationGuardrail


class TestSchemaValidationGuardrail:
    def setup_method(self):
        self.guardrail = SchemaValidationGuardrail()

    def test_valid_triage_output_passes(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug", "frontend"],
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "affects Safari", "source": "issue body"}],
            "reasoning": "Multiple users report 500 errors on Safari.",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert result == output

    def test_missing_required_field_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
        }
        with pytest.raises(GuardrailError, match="priority"):
            self.guardrail.check_output(output, skill="triage-issue")

    def test_wrong_field_type_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": "bug",  # should be array
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
        }
        with pytest.raises(GuardrailError, match="labels"):
            self.guardrail.check_output(output, skill="triage-issue")

    def test_extra_fields_allowed(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug"],
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
            "extra_field": "should be fine",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert "extra_field" in result

    def test_insufficient_context_schema_valid(self):
        output = {
            "status": "insufficient_context",
            "missing": ["body", "reproduction steps"],
            "suggestion": "Please provide a detailed description.",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert result["status"] == "insufficient_context"

    def test_invalid_confidence_value_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug"],
            "recommended_owner": "frontend-team",
            "confidence": "very_high",  # invalid
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
        }
        with pytest.raises(GuardrailError, match="confidence"):
            self.guardrail.check_output(output, skill="triage-issue")
