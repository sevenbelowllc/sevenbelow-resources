# Remediation Plan Template (`15-remediation-plan.md`)

Prioritized fix order. Critical first, dependencies surfaced.

## Priority order

| Priority | Severity tier | Target SLO |
|---|---|---|
| P0 | Critical | Fix within 24-48 hours; halt-the-line |
| P1 | High | Fix within current sprint |
| P2 | Medium | Fix within next sprint |
| P3 | Low / Info | Backlog; bundle with related work |

## Fix sequence (Critical → Low)

### P0 (Critical)

1. **FINDING-NNN: [title]**
   - Smallest safe fix: [from finding template]
   - Blocking dependencies: [other findings or work that must land first]
   - Estimated effort: [hours]
   - Owner: [team / individual]
   - Tests required: [list]
   - Verification: [how to confirm fix lands; runtime smoke if authorized]
   - Rollback plan: [how to revert if fix breaks something]
2. **FINDING-NNN: ...**

### P1 (High)

[same shape]

### P2 (Medium)

[same shape]

### P3 (Low / Info)

[same shape; may be batched]

## Dependency graph

[Mermaid or list. Each finding's blocker.]

```
FINDING-001 (Critical, BOLA)          ─┐
                                       ├─ blocks → FINDING-008 (HIGH, SSE rate-limit) — same auth surface
FINDING-002 (Critical, role rebind)    ─┘
                                       
FINDING-003 (Critical, RLS bypass)    ─── blocks → FINDING-012 (MED, audit log gap) — needs fixed RLS first
```

## Cross-cutting changes

Some findings share a remediation. Bundle these:

- **Tenant context lint rule:** addresses FINDING-NNN, FINDING-NNN, FINDING-NNN. One ESLint plugin or runtime DB-wrapper assertion.
- **`safeExternalUrl(url, scope)` helper:** addresses FINDING-NNN, FINDING-NNN. Apply to webhook delivery, agent base URL, tool URL.
- **Layered rate limiter (Redis):** addresses FINDING-NNN, FINDING-NNN. Per-IP + per-user + per-tenant + per-operation.
- **HITL approval token:** addresses FINDING-NNN, FINDING-NNN. State-mutation tools require token bound to (tenant, thread, action).
- **CI gate restoration:** addresses FINDING-NNN, FINDING-NNN. Server-side gitleaks + trivy + tsc + jest as required checks.

## Required tests landing alongside fixes

Cross-reference `13-test-gap-report.md`. Every P0/P1 fix lands with at least one regression test from that report.

## Rollout sequence

1. Fix P0 critical items in isolation (small PRs, fast review).
2. Land cross-cutting infra (lint rule, helper, rate limiter, HITL token, CI gates).
3. Sweep P1 items that are now easier with cross-cutting infra in place.
4. Schedule P2/P3 sprint work.

## Risk register

| Risk | Mitigation |
|---|---|
| Fix breaks legitimate flow | Add regression test BEFORE deploying fix; staged rollout via flag |
| Infra change causes incident | Rollback plan documented per fix; canary on integration first |
| New finding emerges during fix | Re-run targeted phase against new code; add to register |
| Fix landed but not deployed | Tracking issue per fix tied to deploy SHA; verification at next release |

## Sign-off

- [ ] Every P0 has a fix landed + regression test green.
- [ ] Every P1 has a tracked ticket with target sprint.
- [ ] Every P2/P3 has a backlog ticket.
- [ ] Findings register updated with status (`Fixed in <SHA>` / `In progress` / `Backlog`).
- [ ] Verification artifacts captured (test runs, log evidence, runtime smoke if authorized).
