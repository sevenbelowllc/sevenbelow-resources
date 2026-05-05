"""Base class and exceptions for all guardrails."""


class GuardrailError(Exception):
    """Raised when a guardrail check fails."""

    def __init__(self, guardrail_name: str, message: str, details: dict | None = None):
        self.guardrail_name = guardrail_name
        self.message = message
        self.details = details or {}
        super().__init__(f"[{guardrail_name}] {message}")


class Guardrail:
    """Base class for all guardrails."""

    name: str = "base"

    def check_input(self, data: dict, skill: str = "") -> dict:
        return data

    def check_output(self, data: dict, skill: str = "") -> dict:
        return data
