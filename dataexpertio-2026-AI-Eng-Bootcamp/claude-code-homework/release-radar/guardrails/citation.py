"""Citation to source guardrail."""

from guardrails.base import Guardrail, GuardrailError


class CitationGuardrail(Guardrail):
    name = "citation"

    def check_output(self, data: dict, skill: str = "", input_data: dict | None = None) -> dict:
        if data.get("status") == "insufficient_context":
            return data

        citations = data.get("citations")
        if citations is None:
            raise GuardrailError(self.name, "Missing 'citations' field in output.")

        if not isinstance(citations, list) or len(citations) == 0:
            raise GuardrailError(self.name, "Output 'citations' must be a non-empty list.")

        for i, citation in enumerate(citations):
            if not isinstance(citation, dict):
                raise GuardrailError(self.name, f"Citation {i} is not an object.")
            if "claim" not in citation:
                raise GuardrailError(self.name, f"Citation {i} missing 'claim' field.")
            if "source" not in citation:
                raise GuardrailError(self.name, f"Citation {i} missing 'source' field.")

        return data
