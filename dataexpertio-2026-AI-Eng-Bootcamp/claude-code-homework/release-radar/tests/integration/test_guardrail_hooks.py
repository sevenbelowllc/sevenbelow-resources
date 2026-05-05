"""Integration test for guardrail hook scripts."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PRE_HOOK = PROJECT_ROOT / "guardrails" / "hooks" / "pre_tool_guardrail.py"
POST_HOOK = PROJECT_ROOT / "guardrails" / "hooks" / "post_tool_guardrail.py"


class TestGuardrailHooks:
    def test_pre_hook_redacts_pii(self):
        input_data = {
            "tool_name": "triage-issue",
            "tool_input": {
                "title": "Bug report",
                "body": "Contact alice@example.com for details.",
            },
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "alice@example.com" not in json.dumps(output)

    def test_pre_hook_rejects_insufficient_context(self):
        input_data = {
            "tool_name": "triage-issue",
            "tool_input": {"title": "Bug"},
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert "error" in output

    def test_pre_hook_ignores_unknown_tool(self):
        input_data = {
            "tool_name": "unknown-tool",
            "tool_input": {"data": "test"},
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 0
