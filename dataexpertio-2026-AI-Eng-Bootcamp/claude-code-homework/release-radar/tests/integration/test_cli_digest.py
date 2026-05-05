"""Integration test for CLI digest command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_COMMITS = PROJECT_ROOT / "data" / "mock" / "commits.json"


@pytest.mark.integration
class TestCLIDigest:
    def test_digest_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "digest", "--input", str(MOCK_COMMITS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_digest_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "digest", "--input", str(MOCK_COMMITS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_digest_results_have_structure(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "digest", "--input", str(MOCK_COMMITS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert "result" in data
