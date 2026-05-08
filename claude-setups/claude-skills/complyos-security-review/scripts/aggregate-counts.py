#!/usr/bin/env python3
"""aggregate-counts.py — produce severity + category + status counts from a
findings register or a directory of phase artifacts.

Usage:
  aggregate-counts.py <file-or-dir>

Output: Markdown table block, ready to paste into 14-findings-register.md
"Aggregate counts" + "Findings by category" sections.

Reads `### FINDING-...` blocks; tallies Severity, Status, and Category fields.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


SEV_ORDER = ["Critical", "High", "Medium", "Low", "Info"]
STATUS_ORDER = ["CONFIRMED", "LIKELY", "STATIC-ONLY", "NEEDS-RUNTIME-TEST", "BLOCKED"]


def _field_regex(field: str) -> re.Pattern:
    """Match `- field: VALUE`, `- **field:** VALUE`, or `- **field**: VALUE`."""
    f = re.escape(field)
    return re.compile(
        rf"(?m)^\s*-\s*\*{{0,2}}\s*{f}\s*\*{{0,2}}\s*:\s*\*{{0,2}}\s*(.+?)\s*\*{{0,2}}\s*$"
    )


def _clean(value: str) -> str:
    return value.replace("**", "").strip().rstrip("|").strip()


def parse_findings(text: str) -> list[dict]:
    pattern = re.compile(r"(?m)^### (FINDING-[A-Za-z0-9_-]+):")
    matches = list(pattern.finditer(text))
    sev_re = _field_regex("Severity")
    status_re = _field_regex("Status")
    cat_re = _field_regex("Category")
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        sev = sev_re.search(body)
        status = status_re.search(body)
        cat = cat_re.search(body)
        out.append(
            {
                "id": m.group(1),
                "severity": (_clean(sev.group(1)).split()[0] if sev else "Unknown"),
                "status": (_clean(status.group(1)).split()[0] if status else "Unknown"),
                "category": (_clean(cat.group(1)) if cat else "Unknown"),
            }
        )
    return out


def collect(path: Path) -> list[dict]:
    if path.is_file():
        return parse_findings(path.read_text())
    findings = []
    for f in sorted(path.rglob("*.md")):
        findings.extend(parse_findings(f.read_text()))
    return findings


def render(findings: list[dict]) -> str:
    sev_counts = Counter(f["severity"] for f in findings)
    status_counts = Counter(f["status"] for f in findings)
    cat_counts = Counter(f["category"] for f in findings)

    lines = []
    lines.append("## Aggregate counts (auto-generated)")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---:|")
    for s in SEV_ORDER:
        lines.append(f"| {s} | {sev_counts.get(s, 0)} |")
    other_sev = sum(c for k, c in sev_counts.items() if k not in SEV_ORDER)
    if other_sev:
        lines.append(f"| Unknown/Other | {other_sev} |")
    lines.append(f"| **Total** | **{sum(sev_counts.values())}** |")
    lines.append("")

    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    for s in STATUS_ORDER:
        lines.append(f"| {s} | {status_counts.get(s, 0)} |")
    other_st = sum(c for k, c in status_counts.items() if k not in STATUS_ORDER)
    if other_st:
        lines.append(f"| Unknown/Other | {other_st} |")
    lines.append("")

    lines.append("## Findings by category (auto-generated)")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for cat, n in sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {cat} | {n} |")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: aggregate-counts.py <file-or-dir>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"path not found: {path}", file=sys.stderr)
        return 2

    findings = collect(path)
    if not findings:
        print("# no findings detected")
        return 0

    print(render(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
