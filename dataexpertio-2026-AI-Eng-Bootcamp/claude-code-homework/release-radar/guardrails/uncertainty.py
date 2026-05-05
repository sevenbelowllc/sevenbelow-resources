"""Uncertainty statements guardrail."""

import re

from guardrails.base import Guardrail, GuardrailError

HEDGING_WORDS = re.compile(
    r"\b(?:might|possibly|perhaps|unclear|uncertain|maybe|could be|not sure|"
    r"hard to say|difficult to determine|cannot confirm)\b",
    re.IGNORECASE,
)

VALID_CONFIDENCE = {"high", "medium", "low"}


class UncertaintyGuardrail(Guardrail):
    name = "uncertainty"

    def check_output(self, data: dict, skill: str = "") -> dict:
        if data.get("status") == "insufficient_context":
            return data

        confidence = data.get("confidence")
        if confidence is None:
            raise GuardrailError(self.name, "Missing 'confidence' field in output.")

        if confidence not in VALID_CONFIDENCE:
            raise GuardrailError(
                self.name,
                f"Invalid confidence value '{confidence}'. Must be one of: {VALID_CONFIDENCE}",
            )

        # Check hedging language when confidence is high
        text_fields = [
            data.get("reasoning", ""),
            data.get("summary", ""),
            str(data.get("sections", "")),
            data.get("body", ""),
        ]
        combined_text = " ".join(text_fields)

        if confidence == "high" and HEDGING_WORDS.search(combined_text):
            raise GuardrailError(
                self.name,
                "Confidence is 'high' but output contains hedging language. "
                "Lower confidence or remove hedging.",
            )

        # Non-high confidence should have uncertainty flags
        uncertainty_flags = data.get("uncertainty_flags")
        if (
            confidence != "high"
            and isinstance(uncertainty_flags, list)
            and len(uncertainty_flags) == 0
        ):
            raise GuardrailError(
                self.name,
                f"Confidence is '{confidence}' but uncertainty_flags is empty. "
                "Add flags explaining the uncertainty.",
            )

        return data
