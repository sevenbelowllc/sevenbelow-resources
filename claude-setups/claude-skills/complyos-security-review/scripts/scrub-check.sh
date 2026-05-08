#!/usr/bin/env bash
# scrub-check.sh — verify a security-review/ output dir does not contain secrets,
# tokens, customer names, or other publish-blocking content before sharing.
#
# Usage:
#   ./scrub-check.sh <review-dir> [--config <path>]
#
# Default deny-pattern set covers:
#   - JWT-shaped strings (eyJ...)
#   - common secret prefixes (sk_, pk_, ghp_, ghs_, gho_, AKIA, ASIA, AIza, xoxb-, xoxa-)
#   - private-key markers (BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY, etc.)
#   - .pem / .key file references
#   - PLACEHOLDER_ literals are PERMITTED (per workspace convention DEC-055)
#
# Customer / hostname / Jira-key denial is operator-supplied via --config FILE
# (one regex per line). Keeps this script generic.
#
# Exit codes:
#   0 = clean
#   1 = matches found (review report not safe to publish)
#   2 = misuse

set -euo pipefail

DIR="${1:-}"
CONFIG=""
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$DIR" || ! -d "$DIR" ]]; then
  echo "usage: scrub-check.sh <review-dir> [--config <path>]" >&2
  exit 2
fi

# Default deny patterns (extended regex, multi-line OR via -E "(a|b|c)").
# IMPORTANT: PLACEHOLDER_* literals are allowed by convention; do not include them here.
DEFAULT_PATTERNS='eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|sk_(live|test)_[A-Za-z0-9]{16,}|pk_(live|test)_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{20,}|xox[abps]-[A-Za-z0-9-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'

matches_found=0
log_match() {
  matches_found=1
  echo "$1"
}

echo "== scrub-check on $DIR =="

# Default secret patterns
echo "-- default secret patterns --"
hits=$(grep -rEn -- "$DEFAULT_PATTERNS" "$DIR" 2>/dev/null || true)
if [[ -n "$hits" ]]; then
  echo "$hits"
  log_match "FAIL: default secret pattern hit"
fi

# Operator-supplied custom patterns
if [[ -n "$CONFIG" && -f "$CONFIG" ]]; then
  echo "-- custom patterns from $CONFIG --"
  while IFS= read -r pat; do
    [[ -z "$pat" || "$pat" =~ ^# ]] && continue
    hits=$(grep -rEn -- "$pat" "$DIR" 2>/dev/null || true)
    if [[ -n "$hits" ]]; then
      echo "$hits"
      log_match "FAIL: custom pattern hit -- $pat"
    fi
  done < "$CONFIG"
elif [[ -n "$CONFIG" ]]; then
  echo "config not found: $CONFIG" >&2
  exit 2
fi

# Common file-extension references that should not appear in published report
echo "-- private-key file references --"
hits=$(grep -rEn -- '\.(pem|key|p12|pfx|jks)\b' "$DIR" 2>/dev/null || true)
if [[ -n "$hits" ]]; then
  echo "$hits"
  log_match "FAIL: private-key file reference"
fi

if [[ "$matches_found" -eq 0 ]]; then
  echo
  echo "PASS: no patterns matched. Review safe to share at this layer."
  echo "Note: this script does not detect customer names, hostnames, or PII —"
  echo "supply --config with operator-curated patterns for that coverage."
  exit 0
fi

echo
echo "FAIL: $DIR contains content matching deny patterns. Do not publish."
exit 1
