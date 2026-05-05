"""Shared test fixtures for Release Radar."""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def mock_issues():
    with open(DATA_DIR / "mock" / "issues.json") as f:
        return json.load(f)


@pytest.fixture
def mock_pull_requests():
    with open(DATA_DIR / "mock" / "pull_requests.json") as f:
        return json.load(f)


@pytest.fixture
def mock_commits():
    with open(DATA_DIR / "mock" / "commits.json") as f:
        return json.load(f)


@pytest.fixture
def valid_triage_input():
    return {
        "title": "Login fails on Safari",
        "body": "Users report 500 errors when logging in on Safari 17.",
        "comments": ["I can reproduce on macOS Sonoma."],
        "labels_existing": ["bug", "frontend", "backend"],
    }


@pytest.fixture
def valid_triage_output():
    return {
        "status": "ok",
        "severity": "high",
        "priority": "p0",
        "labels": ["bug", "frontend"],
        "recommended_owner": "frontend-team",
        "confidence": "high",
        "uncertainty_flags": [],
        "citations": [
            {"claim": "500 errors on Safari", "source": "issue body: 'Users report 500 errors'"}
        ],
        "reasoning": "Multiple users confirm 500 errors on Safari 17.",
    }


@pytest.fixture
def sparse_triage_input():
    return {"title": "Bug"}
