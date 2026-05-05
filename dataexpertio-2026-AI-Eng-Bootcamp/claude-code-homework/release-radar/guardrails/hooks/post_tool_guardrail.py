#!/usr/bin/env python3
"""Post-tool guardrail hook for Claude Code.

Reads tool output from stdin, runs post-processing guardrails,
outputs modified data to stdout.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from guardrails.base import GuardrailError
from guardrails.citation import CitationGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = data.get("tool_name", "")
    tool_output = data.get("tool_output", {})

    skill_map = {
        "triage-issue": "triage-issue",
        "summarize-pr": "summarize-pr",
        "digest-commits": "digest-commits",
        "draft-email": "draft-email",
    }
    skill = skill_map.get(tool_name, "")
    if not skill:
        return

    guardrails = [
        SchemaValidationGuardrail(),
        CitationGuardrail(),
        UncertaintyGuardrail(),
        PIIRedactionGuardrail(),
    ]

    try:
        result = tool_output
        for g in guardrails:
            result = g.check_output(result, skill=skill)
        output = {"tool_output": result}
        json.dump(output, sys.stdout)
    except GuardrailError as e:
        error_output = {
            "error": str(e),
            "details": e.details,
        }
        json.dump(error_output, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
