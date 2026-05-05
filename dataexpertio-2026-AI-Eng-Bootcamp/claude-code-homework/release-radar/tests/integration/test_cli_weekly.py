"""Integration test for CLI weekly command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"


@pytest.mark.integration
class TestCLIWeekly:
    def test_weekly_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--weekly"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_weekly_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--weekly"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_weekly_results_have_structure(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--weekly"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300,
        )
        data = json.loads(result.stdout)
        assert "triage" in data
        assert "pr_summaries" in data
        assert "digest" in data
        assert "email" in data
