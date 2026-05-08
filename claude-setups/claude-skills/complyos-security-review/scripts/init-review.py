#!/usr/bin/env python3
"""init-review.py — bootstrap a security-review/ output skeleton from skill templates.

Usage:
  init-review.py <output-root> [--with-ai] [--force]

  <output-root>  target dir; will create <output-root>/security-review/
  --with-ai      include 08-ai-rag-security-review.md (skip if no AI/RAG in scope)
  --force        overwrite existing files (default: skip)

Reads templates from the skill directory (parent of this script's parent).
Writes 14 (or 15 with --with-ai) stub artifacts pre-populated with header +
scope reminder + section scaffolding.

Exit codes:
  0 = success (or partial: some skipped, some created)
  2 = misuse / templates dir missing
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path


ARTIFACTS = [
    ("00-scope.md", "scope-template.md", "Scope and Constraints"),
    ("01-architecture-trust-boundaries.md", None, "Architecture and Trust Boundaries"),
    ("02-threat-model.md", "threat-model-template.md", "Threat Model"),
    ("03-authentication-review.md", None, "Authentication Review"),
    ("04-authorization-review.md", None, "Authorization Review"),
    ("05-tenant-isolation-review.md", None, "Tenant Isolation Review"),
    ("06-api-security-review.md", None, "API Security Review"),
    ("07-data-evidence-security-review.md", None, "Data, Document, and Evidence Security Review"),
    # 08 inserted conditionally
    ("09-secrets-config-crypto-review.md", None, "Secrets, Config, and Cryptography Review"),
    ("10-cicd-supply-chain-review.md", None, "CI/CD and Supply Chain Review"),
    ("11-cloud-iac-review.md", None, "Cloud and IaC Review"),
    ("12-logging-audit-monitoring-review.md", None, "Logging, Audit, and Monitoring Review"),
    ("13-test-gap-report.md", "test-plan-template.md", "Test Gap Report"),
    ("14-findings-register.md", "findings-register-template.md", "Findings Register"),
    ("15-remediation-plan.md", "remediation-plan-template.md", "Remediation Plan"),
]

AI_ARTIFACT = ("08-ai-rag-security-review.md", None, "AI/RAG/Agent Security Review")

STUB_BODY = """# {title}

**Date:** {date}
**Skill:** complyos-security-review
**Phase artifact**

## Scope reminder

[One paragraph describing what this phase covers. Reference 00-scope.md.]

## Method

[Which checklist applied. Which files inspected. Cite checklist path.]

## Confirmed PASSes (with evidence)

[Each PASS cites file:line + function/route/config. No PASS without evidence.]

## Findings

[One block per finding using templates/finding-template.md. Reject any finding missing required fields.]

## Scope gaps surfaced

[Each gap references an entry in 00-scope.md GAP-NNN.]
"""

TEMPLATE_REF = """
---

<!-- Template reference: {template} (copy structure as needed) -->
"""


def find_skill_dir(script_path: Path) -> Path:
    """Skill dir is the parent of the scripts/ dir that contains this script."""
    return script_path.resolve().parent.parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bootstrap security-review/ output skeleton.")
    p.add_argument("output_root", help="Target directory (security-review/ created inside).")
    p.add_argument("--with-ai", action="store_true", help="Include 08-ai-rag-security-review.md.")
    p.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_root = Path(args.output_root)
    skill_dir = find_skill_dir(Path(__file__))
    templates_dir = skill_dir / "templates"

    if not templates_dir.is_dir():
        print(f"templates dir not found at {templates_dir}", file=sys.stderr)
        return 2

    review_dir = out_root / "security-review"
    review_dir.mkdir(parents=True, exist_ok=True)

    artifacts = list(ARTIFACTS)
    if args.with_ai:
        artifacts.insert(8, AI_ARTIFACT)

    date = _dt.date.today().isoformat()
    created = 0
    skipped = 0

    for filename, template, title in artifacts:
        target = review_dir / filename

        if target.exists() and not args.force:
            print(f"skip (exists): {filename}")
            skipped += 1
            continue

        body = STUB_BODY.format(title=title, date=date)
        if template and (templates_dir / template).is_file():
            body += TEMPLATE_REF.format(template=template)

        target.write_text(body)
        print(f"created: {filename}")
        created += 1

    print()
    print(f"summary: {created} created, {skipped} skipped")
    print(f"output dir: {review_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
