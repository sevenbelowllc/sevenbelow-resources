from __future__ import annotations

import re
from typing import Iterable

from .models import Email

INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(?:\w+\s+){0,3}previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:\w+\s+){0,3}prior", re.IGNORECASE),
    re.compile(r"reveal.*(system\s+prompt|secret|api\s*key)", re.IGNORECASE),
    re.compile(r"exfiltrate", re.IGNORECASE),
    re.compile(r"send\s+(?:me\s+)?(?:all\s+)?(?:secrets|credentials|api\s*keys)", re.IGNORECASE),
    re.compile(r"override.*safety", re.IGNORECASE),
]


def _normalize(value: str) -> str:
    return value.strip().lower()


def is_approved_sender(email: Email, approved: Iterable[str]) -> bool:
    norm_allowed = {_normalize(s) for s in approved}
    return _normalize(email.sender) in norm_allowed


def contains_injection(email: Email) -> tuple[bool, str | None]:
    haystack = f"{email.subject}\n{email.body}"
    for pattern in INJECTION_PATTERNS:
        if pattern.search(haystack):
            return True, pattern.pattern
    return False, None
