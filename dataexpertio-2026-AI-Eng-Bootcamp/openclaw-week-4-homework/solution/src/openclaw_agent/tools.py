from __future__ import annotations

from typing import List

from langsmith import traceable

from .models import Email


class MockZapierTools:
    """Deterministic stand-in for the Zapier MCP tools used in week 4."""

    def __init__(self, inbox: List[Email]) -> None:
        self.inbox = inbox
        self.tool_call_count = 0
        self.estimated_tokens = 0
        self.calls: list[dict] = []

    def _log_tool(self, name: str, payload: str, args: dict) -> None:
        if "name" in args:
            raise ValueError("tool args must not include reserved key 'name'")
        self.tool_call_count += 1
        self.estimated_tokens += len(payload.split()) + 20
        self.calls.append({"name": name, **args})
        print(f"[TOOL] {name}: {payload}")

    @traceable(name="Gmail:Find Email")
    def find_email(self, query: str, limit: int = 50) -> List[Email]:
        self._log_tool(
            "Gmail:Find Email",
            f"query={query!r}, limit={limit}",
            {"query": query, "limit": limit},
        )
        seen: dict[str, Email] = {}
        for e in self.inbox:
            seen.setdefault(e.id, e)
        return list(seen.values())[:limit]

    @traceable(name="Google Calendar:Create Detailed Event")
    def create_calendar_event(
        self, title: str, start: str, end: str, attendee: str
    ) -> None:
        self._log_tool(
            "Google Calendar:Create Detailed Event",
            f"title={title!r}, start={start}, end={end}, attendee={attendee}",
            {"title": title, "start": start, "end": end, "attendee": attendee},
        )

    @traceable(name="Gmail:Send Email")
    def send_email(self, to: str, subject: str, body: str) -> None:
        self._log_tool(
            "Gmail:Send Email",
            f"to={to}, subject={subject!r}, body_len={len(body)}",
            {"to": to, "subject": subject, "body_len": len(body)},
        )
