"""Integration test for CLI email command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_COMMITS = PROJECT_ROOT / "data" / "mock" / "commits.json"
MOCK_PRS = PROJECT_ROOT / "data" / "mock" / "pull_requests.json"


@pytest.mark.integration
class TestCLIEmail:
    def test_email_exits_zero(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "email",
                "--input",
                str(MOCK_COMMITS),
                "--prs",
                str(MOCK_PRS),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_email_outputs_valid_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "email",
                "--input",
                str(MOCK_COMMITS),
                "--prs",
                str(MOCK_PRS),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_email_results_have_structure(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "email",
                "--input",
                str(MOCK_COMMITS),
                "--prs",
                str(MOCK_PRS),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
        )
        data = json.loads(result.stdout)
        assert "result" in data
