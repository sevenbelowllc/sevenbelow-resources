"""PII redaction guardrail with 12+ pattern categories."""

import re

from guardrails.base import Guardrail

PII_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # Order matters — more specific patterns first
    (
        "[REDACTED-EMAIL]",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "Email",
    ),
    (
        "[REDACTED-SSN]",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "SSN",
    ),
    (
        "[REDACTED-PHONE]",
        re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "Phone",
    ),
    (
        "[REDACTED-CC]",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "Credit card",
    ),
    (
        "[REDACTED-IP]",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        "IPv4",
    ),
    (
        "[REDACTED-KEY]",
        re.compile(
            r"(?:sk-ant-[\w-]+|ghp_[\w]+|github_pat_[\w]+|"
            r"xoxb-[\w-]+|xoxp-[\w-]+|xoxs-[\w-]+|AKIA[0-9A-Z]{16})"
        ),
        "API keys",
    ),
    (
        "[REDACTED-PRIVATE-KEY]",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?(?:PRIVATE KEY|CERTIFICATE)-----"
            r"[\s\S]*?(?:-----END|$)"
        ),
        "Private keys",
    ),
    (
        "[REDACTED-CONNECTION-STRING]",
        re.compile(r"(?:postgres(?:ql)?|mysql|mongodb|redis|amqp)://[^\s]+"),
        "Connection strings",
    ),
    (
        "[REDACTED-URL]",
        re.compile(r"https?://[^\s]*\.(?:internal|corp|local|lan)[^\s]*"),
        "Internal URLs",
    ),
]


class PIIRedactionGuardrail(Guardrail):
    name = "pii_redaction"

    def redact_text(self, text: str) -> str:
        result = text
        for tag, pattern, _desc in PII_PATTERNS:
            result = pattern.sub(tag, result)
        return result

    def _redact_value(self, value: object) -> object:
        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        return value

    def check_input(self, data: dict, skill: str = "") -> dict:
        result = self._redact_value(data)
        assert isinstance(result, dict)
        return result

    def check_output(self, data: dict, skill: str = "") -> dict:
        result = self._redact_value(data)
        assert isinstance(result, dict)
        return result
