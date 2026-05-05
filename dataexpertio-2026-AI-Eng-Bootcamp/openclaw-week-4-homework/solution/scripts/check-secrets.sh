#!/usr/bin/env bash
# Pre-commit secret guard. Fails if a real-looking key appears
# in a tracked file other than .env.example.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Files staged for commit
FILES=$(git diff --cached --name-only --diff-filter=ACM \
  | grep -v -E '(^|/)\.env\.example$' || true)

if [[ -z "$FILES" ]]; then exit 0; fi

HITS=$(printf '%s\n' "$FILES" | tr '\n' '\0' \
  | xargs -0 grep -lE '(sk-de-[A-Za-z0-9]{8,}|lsv2_pt_[A-Za-z0-9]{8,})' 2>/dev/null || true)

if [[ -n "$HITS" ]]; then
  echo "ERROR: real-looking secret detected in:"
  printf '  %s\n' $HITS
  exit 1
fi
exit 0
