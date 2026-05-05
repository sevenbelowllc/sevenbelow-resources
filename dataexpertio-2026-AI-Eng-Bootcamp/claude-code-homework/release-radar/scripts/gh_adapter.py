"""GitHub data adapter — unified interface for mock and live data."""

import json
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data"


class GitHubAdapter:
    def __init__(self, token: str | None = None, mock: bool = False):
        self.token = token
        self.mock = mock
        self.mock_dir = DATA_DIR / "mock"
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _load_mock(self, filename: str) -> list[dict]:
        path = self.mock_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Mock data file not found: {path}")
        with open(path) as f:
            return json.load(f)

    def get_issues(self, repo: str, since: str | None = None) -> list[dict]:
        if self.mock:
            issues = self._load_mock("issues.json")
            if since:
                issues = [i for i in issues if i.get("created_at", "") >= since]
            return issues
        url = f"{self.base_url}/repos/{repo}/issues"
        params: dict[str, str | int] = {"state": "open", "per_page": 100}
        if since:
            params["since"] = since
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_issues(resp.json())

    def get_pull_requests(
        self, repo: str, state: str = "closed", since: str | None = None
    ) -> list[dict]:
        if self.mock:
            prs = self._load_mock("pull_requests.json")
            if since:
                prs = [p for p in prs if p.get("merged_at", "") >= since]
            return prs
        url = f"{self.base_url}/repos/{repo}/pulls"
        params: dict[str, str | int] = {
            "state": state,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
        }
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_prs(resp.json())

    def get_commits(self, repo: str, since: str | None = None) -> list[dict]:
        if self.mock:
            commits = self._load_mock("commits.json")
            if since:
                commits = [c for c in commits if c.get("date", "") >= since]
            return commits
        url = f"{self.base_url}/repos/{repo}/commits"
        params: dict[str, str | int] = {"per_page": 100}
        if since:
            params["since"] = since
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_commits(resp.json())

    def _normalize_issues(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": item["number"],
                "title": item["title"],
                "body": item.get("body"),
                "comments": [],
                "labels_existing": [label["name"] for label in item.get("labels", [])],
                "author": item["user"]["login"],
                "created_at": item["created_at"][:10],
            }
            for item in raw
            if "pull_request" not in item
        ]

    def _normalize_prs(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": item["number"],
                "title": item["title"],
                "description": item.get("body", ""),
                "diff_snippets": [],
                "files_changed": [],
                "additions": item.get("additions", 0),
                "deletions": item.get("deletions", 0),
                "author": item["user"]["login"],
                "merged_at": (item.get("merged_at") or "")[:10],
                "state": "merged" if item.get("merged_at") else item["state"],
            }
            for item in raw
        ]

    def _normalize_commits(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "sha": item["sha"][:7],
                "message": item["commit"]["message"].split("\n")[0],
                "author": item["commit"]["author"]["name"],
                "date": item["commit"]["author"]["date"][:10],
                "files": [],
            }
            for item in raw
        ]
