"""Schema validation guardrail using jsonschema."""

import jsonschema

from guardrails.base import Guardrail, GuardrailError
from guardrails.schemas import SKILL_SCHEMAS


class SchemaValidationGuardrail(Guardrail):
    name = "schema_validation"

    def check_output(self, data: dict, skill: str = "") -> dict:
        schemas = SKILL_SCHEMAS.get(skill)
        if not schemas:
            return data

        errors = []
        best_error: str | None = None

        for i, schema in enumerate(schemas):
            try:
                jsonschema.validate(instance=data, schema=schema)
                return data
            except jsonschema.ValidationError as e:
                field_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else ""
                error_msg = f"{field_path}: {e.message}" if field_path else e.message
                errors.append(error_msg)
                # Prefer the error from the schema whose "status" enum matches
                status_values = schema.get("properties", {}).get("status", {}).get("enum", [])
                data_status = data.get("status")
                if data_status and data_status in status_values:
                    best_error = error_msg

        reported_error = best_error if best_error is not None else errors[0]
        raise GuardrailError(
            guardrail_name=self.name,
            message=f"Output does not match any valid schema for '{skill}': {reported_error}",
            details={"skill": skill, "errors": errors},
        )
