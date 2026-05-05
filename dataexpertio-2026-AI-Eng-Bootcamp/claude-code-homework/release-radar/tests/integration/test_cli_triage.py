"""Integration test for CLI triage command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_ISSUES = PROJECT_ROOT / "data" / "mock" / "issues.json"


@pytest.mark.integration
class TestCLITriage:
    def test_triage_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_triage_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_triage_results_have_structure(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        for item in data:
            assert "issue_id" in item
            assert "result" in item
