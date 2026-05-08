# Findings Register Template (`14-findings-register.md`)

Aggregate every finding produced during Phases 1-13. One row per finding in the table, full finding body below.

## Aggregate counts

| Phase | CRITICAL | HIGH | MEDIUM | LOW | INFO | Total |
|---|---:|---:|---:|---:|---:|---:|
| 1 Architecture | | | | | | |
| 2 Threat Model | | | | | | |
| 3 AuthN | | | | | | |
| 4 AuthZ | | | | | | |
| 5 Tenant Isolation | | | | | | |
| 6 API Security | | | | | | |
| 7 Data/Evidence | | | | | | |
| 8 AI/RAG | | | | | | |
| 9 Secrets/Config/Crypto | | | | | | |
| 10 CI/CD | | | | | | |
| 11 Cloud/IaC | | | | | | |
| 12 Logging/Audit | | | | | | |
| 13 Test Gaps | | | | | | |
| **Total** | | | | | | |

## Findings by category

| Category | Count |
|---|---:|
| Tenant Isolation | |
| AuthN | |
| AuthZ (BOLA + BFLA) | |
| Injection | |
| SSRF | |
| Resource Consumption | |
| Secrets/Crypto | |
| Logging/Audit | |
| CI/CD | |
| Cloud/IaC | |
| AI/RAG | |
| Misconfiguration | |
| Other | |

## Findings index

| ID | Severity | Status | Category | Title | Owner | Priority |
|---|---|---|---|---|---|---|
| FINDING-001 | | | | | | |
| FINDING-002 | | | | | | |
| ... | | | | | | |

## Full findings (one per `templates/finding-template.md` block)

### FINDING-001: ...
[full block per template]

### FINDING-002: ...
[full block per template]

...

## Cross-references

- Findings that overlap a prior audit at `[path/to/prior-report.md]`: list with prior-finding ID + delta (re-flag, severity change, scope change).
- Findings linked to open Jira tickets: list with ticket ID.
- Findings linked to in-flight PRs: list with PR URL + branch.

## Scope gaps surfaced during this review

- [Gap 1: what was missing, what was needed for CONFIRMED status, what BLOCKED findings cite this gap]
- [Gap 2: ...]

## Verification checklist (must all be YES before declaring complete)

- [ ] Every finding cites file/line evidence.
- [ ] Every PASS in the artifact files cites implementation evidence.
- [ ] Every BLOCKED finding references a specific scope-gap entry.
- [ ] Every Critical finding has a CONFIRMED or NEEDS-RUNTIME-TEST status; no Critical is LIKELY without explicit justification.
- [ ] Every finding has a smallest-safe-fix and a regression test recommendation.
- [ ] Findings register matches per-phase artifact totals.
