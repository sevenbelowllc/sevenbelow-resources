"""Guardrail chain for ordered pre/post processing."""

from guardrails.base import Guardrail


class GuardrailChain:
    def __init__(
        self,
        pre_guardrails: list[Guardrail] | None = None,
        post_guardrails: list[Guardrail] | None = None,
    ):
        self.pre_guardrails = pre_guardrails or []
        self.post_guardrails = post_guardrails or []

    def run_pre(self, data: dict, skill: str = "") -> dict:
        result = data
        for guardrail in self.pre_guardrails:
            result = guardrail.check_input(result, skill=skill)
        return result

    def run_post(self, data: dict, skill: str = "", input_data: dict | None = None) -> dict:
        result = data
        for guardrail in self.post_guardrails:
            # CitationGuardrail has an extra input_data param
            try:
                result = guardrail.check_output(result, skill=skill, input_data=input_data)  # type: ignore[call-arg]
            except TypeError:
                result = guardrail.check_output(result, skill=skill)
        return result
