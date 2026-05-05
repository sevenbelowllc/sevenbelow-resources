"""Integration test for CLI summarize command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_PRS = PROJECT_ROOT / "data" / "mock" / "pull_requests.json"


@pytest.mark.integration
class TestCLISummarize:
    def test_summarize_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "summarize", "--input", str(MOCK_PRS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_summarize_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "summarize", "--input", str(MOCK_PRS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_summarize_results_have_structure(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "summarize", "--input", str(MOCK_PRS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        for item in data:
            assert "pr_id" in item
            assert "result" in item
