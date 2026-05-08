#!/usr/bin/env bash
# init-review.sh — bootstrap a security-review/ output skeleton from skill templates.
#
# Usage:
#   ./init-review.sh <output-root> [--with-ai]
#
#   <output-root>  target dir; will create <output-root>/security-review/
#   --with-ai      include 08-ai-rag-security-review.md (skip if no AI/RAG in scope)
#
# Reads from $SKILL_DIR (default: directory of this script's parent).
# Writes 14 or 15 stub artifacts pre-populated with header + scope reminder.
# Idempotent: refuses to overwrite existing files unless --force.

set -euo pipefail

OUT="${1:-}"
FORCE=0
WITH_AI=0
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --with-ai) WITH_AI=1 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ -z "$OUT" ]]; then
  echo "usage: init-review.sh <output-root> [--with-ai] [--force]" >&2
  exit 2
fi

SKILL_DIR="${SKILL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEMPLATES="$SKILL_DIR/templates"

if [[ ! -d "$TEMPLATES" ]]; then
  echo "templates dir not found at $TEMPLATES" >&2
  exit 1
fi

REVIEW_DIR="$OUT/security-review"
mkdir -p "$REVIEW_DIR"

ARTIFACTS=(
  "00-scope.md:scope-template.md:Scope and Constraints"
  "01-architecture-trust-boundaries.md::Architecture and Trust Boundaries"
  "02-threat-model.md:threat-model-template.md:Threat Model"
  "03-authentication-review.md::Authentication Review"
  "04-authorization-review.md::Authorization Review"
  "05-tenant-isolation-review.md::Tenant Isolation Review"
  "06-api-security-review.md::API Security Review"
  "07-data-evidence-security-review.md::Data, Document, and Evidence Security Review"
  "09-secrets-config-crypto-review.md::Secrets, Config, and Cryptography Review"
  "10-cicd-supply-chain-review.md::CI/CD and Supply Chain Review"
  "11-cloud-iac-review.md::Cloud and IaC Review"
  "12-logging-audit-monitoring-review.md::Logging, Audit, and Monitoring Review"
  "13-test-gap-report.md:test-plan-template.md:Test Gap Report"
  "14-findings-register.md:findings-register-template.md:Findings Register"
  "15-remediation-plan.md:remediation-plan-template.md:Remediation Plan"
)

if [[ "$WITH_AI" == "1" ]]; then
  ARTIFACTS=("${ARTIFACTS[@]:0:8}" "08-ai-rag-security-review.md::AI/RAG/Agent Security Review" "${ARTIFACTS[@]:8}")
fi

DATE="$(date +%Y-%m-%d)"
created=0
skipped=0

for entry in "${ARTIFACTS[@]}"; do
  IFS=':' read -r filename template title <<< "$entry"
  target="$REVIEW_DIR/$filename"

  if [[ -e "$target" && "$FORCE" != "1" ]]; then
    echo "skip (exists): $filename"
    skipped=$((skipped+1))
    continue
  fi

  {
    echo "# $title"
    echo
    echo "**Date:** $DATE"
    echo "**Skill:** complyos-security-review"
    echo "**Phase artifact**"
    echo
    echo "## Scope reminder"
    echo
    echo "[One paragraph describing what this phase covers. Reference 00-scope.md.]"
    echo
    echo "## Method"
    echo
    echo "[Which checklist applied. Which files inspected. Cite checklist path.]"
    echo
    echo "## Confirmed PASSes (with evidence)"
    echo
    echo "[Each PASS cites file:line + function/route/config. No PASS without evidence.]"
    echo
    echo "## Findings"
    echo
    echo "[One block per finding using templates/finding-template.md. Reject any finding missing required fields.]"
    echo
    echo "## Scope gaps surfaced"
    echo
    echo "[Each gap references an entry in 00-scope.md GAP-NNN.]"
    if [[ -n "$template" && -f "$TEMPLATES/$template" ]]; then
      echo
      echo "---"
      echo
      echo "<!-- Template reference: $template (copy structure as needed) -->"
    fi
  } > "$target"

  echo "created: $filename"
  created=$((created+1))
done

echo
echo "summary: $created created, $skipped skipped"
echo "output dir: $REVIEW_DIR"
