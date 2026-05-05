#!/usr/bin/env python3
"""Pre-tool guardrail hook for Claude Code.

Reads tool input from stdin, runs pre-processing guardrails,
outputs modified data to stdout.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from guardrails.base import GuardrailError
from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    skill_map = {
        "triage-issue": "triage-issue",
        "summarize-pr": "summarize-pr",
        "digest-commits": "digest-commits",
        "draft-email": "draft-email",
    }
    skill = skill_map.get(tool_name, "")
    if not skill:
        return

    guardrails = [InsufficientContextGuardrail(), PIIRedactionGuardrail()]

    try:
        result = tool_input
        for g in guardrails:
            result = g.check_input(result, skill=skill)
        output = {"tool_input": result}
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
