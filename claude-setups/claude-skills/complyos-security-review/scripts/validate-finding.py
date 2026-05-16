#!/usr/bin/env python3
"""validate-finding.py — lint a finding block against templates/finding-template.md.

Usage:
  validate-finding.py <path-to-md-file>
  validate-finding.py --stdin            # read from stdin

Exits non-zero on any finding that fails.
Reports missing required fields, invalid severity, invalid status, missing
evidence, missing attack path, missing fix recommendation.

A finding block starts at "### FINDING-" and ends at the next "### FINDING-" or
end of file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "Severity",
    "Status",
    "Category",
    "OWASP Mapping",
    "CWE Mapping",
    "Affected Component",
    "Affected Tenant/Data Boundary",
    "Evidence",
    "What was observed",
    "Why this is vulnerable",
    "Attack path",
    "Business impact",
    "Tenant/data impact",
    "Reproduction steps",
    "Smallest safe fix",
    "Tests required",
    "Regression risk",
    "Suggested owner",
    "Priority",
]

VALID_SEVERITIES = {"Critical", "High", "Medium", "Low", "Info"}
VALID_STATUSES = {"CONFIRMED", "LIKELY", "STATIC-ONLY", "NEEDS-RUNTIME-TEST", "BLOCKED"}

EVIDENCE_SUBFIELDS_AT_LEAST_ONE_OF = ["File:", "Function/Class:", "Route/API:", "Config:", "Test:"]

INVALID_EVIDENCE_PHRASES = [
    "looks okay",
    "appears secure",
    "probably handled",
    "framework should handle this",
    "no obvious issue",
    "assumed safe",
    "not reviewed but likely fine",
]


def split_findings(text: str) -> list[tuple[str, str]]:
    """Return list of (finding_id_or_index, body)."""
    pattern = re.compile(r"(?m)^### (FINDING-[A-Za-z0-9_-]+):", re.MULTILINE)
    matches = list(pattern.finditer(text))
    findings = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        findings.append((m.group(1), text[start:end]))
    return findings


def _field_regex(field: str) -> re.Pattern:
    """Match a finding line for `field`, tolerating optional markdown-bold styles:
       `- field: VALUE`, `- **field:** VALUE`, `- **field**: VALUE`.
       Capture group 1 = VALUE (with surrounding asterisks/whitespace stripped).
    """
    f = re.escape(field)
    return re.compile(
        rf"(?m)^\s*-\s*\*{{0,2}}\s*{f}\s*\*{{0,2}}\s*:\s*\*{{0,2}}\s*(.+?)\s*\*{{0,2}}\s*$"
    )


def _first_token(value: str) -> str:
    """Extract leading token from a field value, stripping leftover markdown."""
    return value.replace("**", "").strip().split()[0] if value.strip() else ""


def lint_finding(fid: str, body: str) -> list[str]:
    errors = []
    lower_body = body.lower()

    for field in REQUIRED_FIELDS:
        if not _field_regex(field).search(body):
            errors.append(f"missing required field: {field}")

    sev_match = _field_regex("Severity").search(body)
    if sev_match:
        sev = _first_token(sev_match.group(1))
        if sev and sev not in VALID_SEVERITIES:
            errors.append(f"invalid severity: {sev!r} (must be one of {sorted(VALID_SEVERITIES)})")

    status_match = _field_regex("Status").search(body)
    if status_match:
        st = _first_token(status_match.group(1))
        if st and st not in VALID_STATUSES:
            errors.append(f"invalid status: {st!r} (must be one of {sorted(VALID_STATUSES)})")

    if not any(sub in body for sub in EVIDENCE_SUBFIELDS_AT_LEAST_ONE_OF):
        errors.append("Evidence section missing — needs at least one of File:/Function/Class:/Route/API:/Config:/Test:")

    file_lines = re.findall(r"(?m)^\s*-?\s*File:\s*([^\n]+)", body)
    if file_lines:
        ok = any(re.search(r":\d+", line) for line in file_lines)
        if not ok:
            errors.append("File: evidence present but missing line number (expected `path:LINE`)")

    for phrase in INVALID_EVIDENCE_PHRASES:
        if phrase in lower_body:
            errors.append(f'invalid evidence phrase present: "{phrase}"')

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate-finding.py <file.md> | --stdin", file=sys.stderr)
        return 2

    if sys.argv[1] == "--stdin":
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"file not found: {path}", file=sys.stderr)
            return 2
        text = path.read_text()
        source = str(path)

    findings = split_findings(text)
    if not findings:
        print(f"{source}: no findings detected (looking for '### FINDING-' headers)")
        return 0

    total_errors = 0
    for fid, body in findings:
        errs = lint_finding(fid, body)
        if errs:
            total_errors += len(errs)
            print(f"\n{source}: {fid}")
            for e in errs:
                print(f"  - {e}")

    print(f"\nchecked {len(findings)} finding(s); {total_errors} error(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
