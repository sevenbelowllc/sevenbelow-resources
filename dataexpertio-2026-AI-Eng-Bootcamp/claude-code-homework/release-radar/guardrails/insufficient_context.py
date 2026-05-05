"""Insufficient context fallback guardrail."""

from collections.abc import Callable
from typing import Any

from guardrails.base import Guardrail, GuardrailError

SKILL_REQUIREMENTS: dict[str, list[tuple[str, Callable[[Any], bool]]]] = {
    "triage-issue": [
        ("title", lambda v: isinstance(v, str) and len(v.strip()) > 0),
        ("body", lambda v: isinstance(v, str) and len(v.strip()) > 0),
    ],
    "summarize-pr": [
        ("title", lambda v: isinstance(v, str) and len(v.strip()) > 0),
        ("diff_snippets", lambda v: isinstance(v, list) and len(v) > 0),
    ],
    "digest-commits": [
        ("commits", lambda v: isinstance(v, list) and len(v) > 0),
    ],
    "draft-email": [
        ("digest", lambda v: isinstance(v, dict) and len(v) > 0),
    ],
}


class InsufficientContextGuardrail(Guardrail):
    name = "insufficient_context"

    def check_input(self, data: dict, skill: str = "") -> dict:
        requirements = SKILL_REQUIREMENTS.get(skill)
        if not requirements:
            return data

        missing = []
        for field_name, check_fn in requirements:
            value = data.get(field_name)
            if value is None or not check_fn(value):
                missing.append(field_name)

        if missing:
            raise GuardrailError(
                guardrail_name=self.name,
                message=f"Insufficient context for '{skill}'. Missing: {missing}",
                details={
                    "status": "insufficient_context",
                    "missing": missing,
                    "suggestion": f"Please provide: {', '.join(missing)}",
                },
            )

        return data
