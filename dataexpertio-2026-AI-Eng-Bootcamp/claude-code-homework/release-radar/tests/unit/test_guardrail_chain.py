"""Tests for guardrail chain execution."""

import pytest

from guardrails.base import GuardrailError
from guardrails.chain import GuardrailChain
from guardrails.citation import CitationGuardrail
from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail


class TestGuardrailChain:
    def setup_method(self):
        self.chain = GuardrailChain(
            pre_guardrails=[
                InsufficientContextGuardrail(),
                PIIRedactionGuardrail(),
            ],
            post_guardrails=[
                SchemaValidationGuardrail(),
                CitationGuardrail(),
                UncertaintyGuardrail(),
                PIIRedactionGuardrail(),
            ],
        )

    def test_pre_guardrails_execute_in_order(self, valid_triage_input):
        valid_triage_input["body"] = "alice@example.com reports 500 errors"
        result = self.chain.run_pre(valid_triage_input, skill="triage-issue")
        assert "alice@example.com" not in result["body"]
        assert "[REDACTED-EMAIL]" in result["body"]

    def test_pre_guardrail_short_circuits_on_failure(self, sparse_triage_input):
        with pytest.raises(GuardrailError, match="insufficient_context"):
            self.chain.run_pre(sparse_triage_input, skill="triage-issue")

    def test_post_guardrails_execute_in_order(self, valid_triage_output):
        result = self.chain.run_post(valid_triage_output, skill="triage-issue")
        assert result["status"] == "ok"

    def test_post_guardrail_fails_on_invalid_schema(self):
        bad_output = {"status": "ok", "severity": "high"}
        with pytest.raises(GuardrailError, match="schema_validation"):
            self.chain.run_post(bad_output, skill="triage-issue")

    def test_post_guardrail_fails_on_empty_citations(self, valid_triage_output):
        valid_triage_output["citations"] = []
        with pytest.raises(GuardrailError, match="citation"):
            self.chain.run_post(valid_triage_output, skill="triage-issue")

    def test_post_guardrail_redacts_pii_in_output(self, valid_triage_output):
        valid_triage_output["reasoning"] = "User alice@example.com confirmed the bug."
        result = self.chain.run_post(valid_triage_output, skill="triage-issue")
        assert "alice@example.com" not in result["reasoning"]
        assert "[REDACTED-EMAIL]" in result["reasoning"]
