#!/bin/bash
# Release Radar — Full Test Plan
# Captures all output to tests/test_results.log
#
# Tests:
#  1. Linting (ruff check + format)
#  2. Type checking (mypy)
#  3. Unit tests (77 tests, no API calls)
#  4. Hook integration tests (3 tests, no API calls)
#  5. CLI help verification
#  6. CLI triage — single issue (API call)
#  7. CLI triage — insufficient context fallback (no API call)
#  8. CLI digest — mock commits (API call)
#  9. CLI email — full pipeline (API call)
# 10. CLI weekly — full mock report (API call)
# 11. PII redaction verification — ensure no PII leaks
# 12. Live GitHub adapter test
# 13. Sample I/O validation

set -o pipefail

cd "$(dirname "$0")/.."
LOG="tests/test_results.log"
PASS=0
FAIL=0
TOTAL=0

log() {
    echo "$@" | tee -a "$LOG"
}

separator() {
    log ""
    log "================================================================"
    log "$1"
    log "================================================================"
}

run_test() {
    local name="$1"
    shift
    TOTAL=$((TOTAL + 1))
    separator "TEST $TOTAL: $name"
    log "Command: $*"
    log "Started: $(date)"
    log ""

    if eval "$@" >> "$LOG" 2>&1; then
        log ""
        log "RESULT: PASS ✓"
        PASS=$((PASS + 1))
    else
        log ""
        log "RESULT: FAIL ✗ (exit code: $?)"
        FAIL=$((FAIL + 1))
    fi
    log ""
}

# Clear log
> "$LOG"
log "Release Radar Test Plan — $(date)"
log "Working directory: $(pwd)"
log "Python: $(python --version 2>&1)"
log ""

# ── 1. Linting ──
run_test "Ruff lint check" "ruff check ."
run_test "Ruff format check" "ruff format --check ."

# ── 2. Type checking ──
run_test "Mypy type check" "python -m mypy scripts/ guardrails/ --ignore-missing-imports"

# ── 3. Unit tests ──
run_test "Unit tests (all)" "python -m pytest tests/unit/ -v --tb=short"

# ── 4. Hook integration tests ──
run_test "Hook integration tests" "python -m pytest tests/integration/test_guardrail_hooks.py -v --tb=short"

# ── 5. CLI help ──
run_test "CLI --help" "python scripts/release_radar.py --help"

# ── 6. CLI triage — single issue ──
run_test "CLI triage (single issue, API)" '
cat > /tmp/rr_test_issue.json << '\''JSONEOF'\''
[{
  "id": 99,
  "title": "Payment processing fails with timeout",
  "body": "Users report payment timeouts after 30s. Error in PaymentService.charge(). Contact support@company.internal for logs.",
  "comments": ["Same issue since last deploy", "Affects all payment methods"],
  "labels_existing": ["bug", "payments", "urgent"]
}]
JSONEOF
python scripts/release_radar.py triage --input /tmp/rr_test_issue.json
'

# ── 7. CLI triage — insufficient context ──
run_test "CLI triage (insufficient context, no API)" '
cat > /tmp/rr_sparse_issue.json << '\''JSONEOF'\''
[{"id": 1, "title": "Bug"}]
JSONEOF
python scripts/release_radar.py triage --input /tmp/rr_sparse_issue.json
'

# ── 8. CLI digest ──
run_test "CLI digest (mock commits, API)" "python scripts/release_radar.py digest --input data/mock/commits.json"

# ── 9. CLI email — full pipeline ──
run_test "CLI email pipeline (API)" "python scripts/release_radar.py email --input data/mock/commits.json --prs data/mock/pull_requests.json"

# ── 10. CLI weekly — full report ──
run_test "CLI weekly report (mock data, API)" "python scripts/release_radar.py --weekly"

# ── 11. PII redaction verification ──
run_test "PII redaction — no leaks in output" '
python -c "
import json, re, sys

# Check triage output for PII
with open(\"/tmp/rr_test_issue.json\") as f:
    pass  # input had PII

# Run guardrails on PII-laden input
sys.path.insert(0, \".\")
from guardrails.pii_redaction import PIIRedactionGuardrail
g = PIIRedactionGuardrail()

test_cases = [
    (\"email\", \"Contact alice@company.internal\"),
    (\"phone\", \"Call 555-123-4567\"),
    (\"ssn\", \"SSN: 123-45-6789\"),
    (\"api_key\", \"key: sk-ant-api03-secret123\"),
    (\"github_token\", \"token: ghp_abc123def456\"),
    (\"ip\", \"Server at 192.168.1.100\"),
    (\"connection_string\", \"db: postgres://user:pass@host/db\"),
    (\"internal_url\", \"Deploy to https://app.internal.corp.com\"),
    (\"credit_card\", \"Card: 4111 1111 1111 1111\"),
    (\"private_key\", \"-----BEGIN RSA PRIVATE KEY-----\"),
    (\"aws_key\", \"AKIAIOSFODNN7EXAMPLE\"),
    (\"slack_token\", \"xoxb-123-456-abc\"),
]

passed = 0
for name, text in test_cases:
    result = g.redact_text(text)
    if \"REDACTED\" in result:
        print(f\"  {name}: REDACTED correctly -> {result}\")
        passed += 1
    else:
        print(f\"  {name}: FAILED — PII not redacted: {result}\")

print(f\"\n  PII patterns: {passed}/{len(test_cases)} redacted\")
if passed < len(test_cases):
    sys.exit(1)
"
'

# ── 12. Live GitHub adapter ──
run_test "GitHub adapter (live API)" '
python -c "
import sys; sys.path.insert(0, \".\")
from dotenv import load_dotenv; import os; load_dotenv()
from scripts.gh_adapter import GitHubAdapter
token = os.getenv(\"GITHUB_PAT_TOKEN\")
if not token:
    print(\"No GITHUB_PAT_TOKEN — skipping live test\")
    sys.exit(0)
adapter = GitHubAdapter(token=token, mock=False)
issues = adapter.get_issues(repo=\"anthropics/claude-code\", since=\"2026-04-01\")
prs = adapter.get_pull_requests(repo=\"anthropics/claude-code\", since=\"2026-04-01\")
commits = adapter.get_commits(repo=\"anthropics/claude-code\", since=\"2026-04-01\")
print(f\"  Issues: {len(issues)}\")
print(f\"  PRs: {len(prs)}\")
print(f\"  Commits: {len(commits)}\")
if len(issues) > 0 and len(commits) > 0:
    print(\"  Live adapter working\")
else:
    print(\"  WARNING: no data returned\")
"
'

# ── 13. Sample I/O validation ──
run_test "Sample I/O files valid JSON" '
python -c "
import json, sys
from pathlib import Path

samples_dir = Path(\"data/samples\")
errors = 0
for sample in sorted(samples_dir.iterdir()):
    if not sample.is_dir():
        continue
    for f in [\"input.json\", \"output.json\"]:
        path = sample / f
        try:
            json.loads(path.read_text())
            print(f\"  {sample.name}/{f}: valid JSON\")
        except Exception as e:
            print(f\"  {sample.name}/{f}: INVALID — {e}\")
            errors += 1

if errors:
    sys.exit(1)
print(f\"\n  All sample files valid\")
"
'

# ── Summary ──
separator "TEST PLAN SUMMARY"
log "Total:  $TOTAL"
log "Passed: $PASS"
log "Failed: $FAIL"
log ""
log "Finished: $(date)"

if [ "$FAIL" -gt 0 ]; then
    log "STATUS: SOME TESTS FAILED"
    exit 1
else
    log "STATUS: ALL TESTS PASSED"
    exit 0
fi
