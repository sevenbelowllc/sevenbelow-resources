"""Tests for GitHub adapter — mock data loading."""

import json
from pathlib import Path

import pytest

from scripts.gh_adapter import GitHubAdapter

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class TestMockDataLoading:
    def test_issues_json_loads(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        assert isinstance(issues, list)
        assert len(issues) >= 15

    def test_issues_have_required_fields(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        for issue in issues:
            assert "id" in issue
            assert "title" in issue

    def test_pull_requests_json_loads(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            prs = json.load(f)
        assert isinstance(prs, list)
        assert len(prs) >= 15

    def test_pull_requests_have_required_fields(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            prs = json.load(f)
        for pr in prs:
            assert "id" in pr
            assert "title" in pr
            assert "diff_snippets" in pr

    def test_commits_json_loads(self):
        with open(DATA_DIR / "mock" / "commits.json") as f:
            commits = json.load(f)
        assert isinstance(commits, list)
        assert len(commits) >= 50

    def test_commits_have_required_fields(self):
        with open(DATA_DIR / "mock" / "commits.json") as f:
            commits = json.load(f)
        for commit in commits:
            assert "sha" in commit
            assert "message" in commit
            assert "author" in commit
            assert "date" in commit

    def test_issues_include_sparse_entries(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        sparse = [i for i in issues if not i.get("body") or i["body"].strip() == ""]
        assert len(sparse) >= 3

    def test_issues_include_pii(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            raw = f.read()
        assert "@" in raw

    def test_prs_include_pii_in_diffs(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            raw = f.read()
        has_pii = "@" in raw or "ghp_" in raw or "sk-" in raw
        assert has_pii


class TestGitHubAdapterMock:
    def setup_method(self):
        self.adapter = GitHubAdapter(mock=True)

    def test_get_issues_returns_list(self):
        issues = self.adapter.get_issues(repo="test/repo")
        assert isinstance(issues, list)
        assert len(issues) >= 15

    def test_get_pull_requests_returns_list(self):
        prs = self.adapter.get_pull_requests(repo="test/repo")
        assert isinstance(prs, list)
        assert len(prs) >= 15

    def test_get_commits_returns_list(self):
        commits = self.adapter.get_commits(repo="test/repo")
        assert isinstance(commits, list)
        assert len(commits) >= 50

    def test_get_commits_date_filter(self):
        commits = self.adapter.get_commits(repo="test/repo", since="2026-04-08")
        assert all(c["date"] >= "2026-04-08" for c in commits)

    def test_missing_mock_file_raises(self):
        adapter = GitHubAdapter(mock=True)
        adapter.mock_dir = adapter.mock_dir / "nonexistent"
        with pytest.raises(FileNotFoundError):
            adapter.get_issues(repo="test/repo")
