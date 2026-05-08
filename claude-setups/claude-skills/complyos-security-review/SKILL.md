---
name: complyos-security-review
description: Deep, evidence-backed security review of a multi-tenant SaaS compliance platform. Covers OWASP Top 10, ASVS L2, OWASP API Top 10, OWASP LLM Top 10, tenant isolation, RLS, evidence/document storage, support elevation, AI/RAG, CI/CD, cloud/IaC. Use when the user asks for a security review, audit, threat model, or pre-release security verification. Triggers on `/complyos-security-review`, "security review", "security audit", "threat model", "tenant isolation review", "RLS review", "API security review", "AI security review".
---

# complyos-security-review

## Purpose

Perform a deep, evidence-backed security review of a multi-tenant SaaS compliance platform. Produce a structured findings register and remediation plan with file/route/config evidence on every claim. Reject generic checklist output. Reject unevidenced PASS verdicts. Separate static-only findings from runtime-test-required findings. Treat tenant-isolation breaches as Critical by default.

## When to use

- User asks for a security review, security audit, threat model, vulnerability assessment, pre-release security pass, OWASP review, ASVS review, API security review, tenant isolation review, RLS review, or AI/RAG security review.
- Before merging a major refactor that touches auth, tenancy, RLS, evidence storage, AI agents, webhooks, or admin paths.
- Before a customer security questionnaire or capstone/grant submission requiring documented review.
- After a security incident, to verify scope and detect related defects.

## When NOT to use

- General code review (use a code-review skill instead).
- Lint, typecheck, or test-failure debugging.
- Performance analysis.
- Refactor planning without security context.
- Marketing/sales/compliance-narrative writing.

## Required inputs (refuse if missing)

1. Repository roots in scope (absolute paths or workspace map).
2. Authoritative spec / authority index pointer (e.g., `library-reading-room/specs/INDEX.md` if present).
3. Auth provider name (e.g., Clerk, Auth0, Cognito, custom).
4. API style (REST, GraphQL, both, gRPC).
5. Database engine + tenancy model (RLS-enforced shared DB, schema-per-tenant, db-per-tenant).
6. Cloud provider + IaC tool (e.g., GCP + Terraform).
7. Whether AI/RAG/agent code paths exist in scope.
8. Environment(s) under review (label clearly: `local`, `integration`, `nonprod`, `prod`). State which are deployed and reachable.
9. Explicit authorization for any runtime probing (default: NONE — static-only).

If any required input is missing: STOP. Emit `00-scope.md` with a Scope Gap section and ask the user to fill it. Do not proceed to Phase 1 with placeholder assumptions.

## Optional inputs

- Prior audit reports to cross-reference.
- Known third-party integrations (Stripe, OpenAI, Anthropic, Snyk, Sentry, etc.).
- Compliance framework targets (SOC 2, GDPR, HIPAA, NIST CSF, ISO 27001) — affects severity weighting on audit/log/retention findings.
- Threat-actor profile (script kiddie, malicious tenant admin, malicious internal employee, nation-state) — affects realism of attack paths.
- Specific Jira/PR/branch the review is gating.

## Operating rules (HARD)

1. **No guessing.** If evidence is absent, say so. Do not infer a control exists from naming or comments.
2. **No generic checklist output.** Every checklist line must produce either a CONFIRMED PASS with evidence, a finding (any status), or a SCOPE-GAP entry.
3. **No finding without evidence.** Cite file path + line number + function/route/config block.
4. **No PASS without implementation evidence.** Comments, READMEs, and CLAUDE.md claims are NOT evidence; corresponding code/test/migration IS evidence.
5. **Separate finding statuses:** CONFIRMED, LIKELY, STATIC-ONLY, NEEDS-RUNTIME-TEST, BLOCKED.
6. **Separate scopes:** application findings vs infrastructure findings; actual vulnerability vs missing evidence; design risk vs implementation bug.
7. **No production runtime tests** unless explicitly authorized in the scope doc.
8. **No destructive tests.** No data-modifying, lock-acquiring, or cost-incurring runtime calls.
9. **No secret rotation, printing, exfiltration, or fake production secret generation.** Reference Bitwarden/Secret Manager IDs by name only.
10. **Do not weaken security controls** to make a test pass or to confirm a finding. Reproduce defensively (read-only repro steps + recommended controlled test).
11. **Do not mark phases done without artifact written.** A phase is complete when its artifact file exists, has evidence per finding, and the user has not asked for more depth.
12. **If a result depends on runtime behavior not visible in code:** mark NEEDS-RUNTIME-TEST and write a controlled test recipe in `13-test-gap-report.md`. Do not run it without explicit authorization.

## Safety rules

- Reading code: always allowed.
- Reading deployed config: only if scope authorizes.
- Reading secret values from any vault, env, or file: NEVER. Reference by ID/name only. (Per `~/.claude/CLAUDE.md` §8 Secret Handling.)
- Reading `~/.zshrc`, `.envrc`, `.env`, `*credentials*.json`: BLOCKED.
- Outbound HTTP calls during review: only to public docs / vendor advisory / CVE feed; never to the target's deployed environment without authorization.
- Test execution: only on local/CI; never against deployed environments without scope-doc authorization signature line.

## Critical failure conditions

The following must be treated as **Critical** unless clearly disproven by implementation evidence (cite the disproof code):

- Cross-tenant data access path (read OR write OR list).
- Tenant-owned data accessed without tenant scoping.
- Backend trusting `tenant_id` from request body, query string, path param, header, or any client-controlled JWT claim that is not signature-bound to that tenant.
- Missing RLS where the tenancy model requires it.
- RLS bypass through background jobs, migrations, seeds, service roles, or webhooks.
- Support/admin tooling without explicit per-tenant grant.
- Support/admin tooling without time-bound expiration.
- Support/admin tooling without audit logging.
- AI/RAG retrieval crossing tenant boundaries.
- Evidence/document download without tenant authorization.
- Public object storage exposure of private evidence.
- Long-lived signed URLs (>15 min default) for sensitive artifacts.
- Forged approval/publish/workflow transitions from the client.
- Auth bypass.
- Privilege escalation.
- Exposed production secret.
- Remote code execution.
- SQL/NoSQL/GraphQL injection with sensitive-data impact.
- Destructive operation without server-side authorization.

## Review phases

| Phase | Title | Output artifact |
|---|---|---|
| 0 | Scope and Constraints | `security-review/00-scope.md` |
| 1 | Architecture and Trust Boundaries | `01-architecture-trust-boundaries.md` |
| 2 | Threat Model | `02-threat-model.md` |
| 3 | Authentication Review | `03-authentication-review.md` |
| 4 | Authorization Review | `04-authorization-review.md` |
| 5 | Tenant Isolation Review | `05-tenant-isolation-review.md` |
| 6 | API Security Review | `06-api-security-review.md` |
| 7 | Data, Document, and Evidence Security Review | `07-data-evidence-security-review.md` |
| 8 | AI/RAG/Agent Security Review | `08-ai-rag-security-review.md` |
| 9 | Secrets, Config, and Cryptography Review | `09-secrets-config-crypto-review.md` |
| 10 | CI/CD and Supply Chain Review | `10-cicd-supply-chain-review.md` |
| 11 | Cloud/IaC Review | `11-cloud-iac-review.md` |
| 12 | Logging, Audit, and Monitoring Review | `12-logging-audit-monitoring-review.md` |
| 13 | Test Gap Review | `13-test-gap-report.md` |
| 14 | Findings Register and Remediation Plan | `14-findings-register.md` + `15-remediation-plan.md` |

Run sequentially. Phase 8 is conditional on AI/RAG presence (declared in Phase 0). Each phase loads its corresponding `checklists/*.md`.

## Evidence requirements

Valid evidence:

- File path + line number (`src/middleware/auth.ts:396`).
- Function/class name (`function findOrCreateUser(...)`).
- Route/API name (`POST /api/agent/stream`).
- Resolver / controller / service module.
- Middleware registration line in app bootstrap.
- Database migration file + line.
- RLS policy SQL.
- Terraform resource block (file + resource type + name).
- CI/CD pipeline file + step name.
- Test file + test case name.
- Configuration file (typed env, k8s manifest, secret reference by ID).
- Runtime command output, ONLY if the command was authorized + non-destructive.

Invalid evidence (reject):

- "Looks okay."
- "Appears secure."
- "Probably handled."
- "Framework should handle this."
- "No obvious issue."
- "Assumed safe."
- "Not reviewed but likely fine."
- "Documented in the spec." (Spec is intent, not evidence; cite the implementation that fulfills the spec.)

## Severity model

**Critical:**
- Cross-tenant data access.
- Auth bypass.
- Privilege escalation to admin/support/system role.
- RCE.
- Exposed production secret.
- Public access to private tenant evidence/customer data.
- AI/RAG tenant leakage.
- Forged publish/approval transition with compliance impact.
- Destructive operation without server-side authorization.

**High:**
- Broken object-level authorization (BOLA).
- Broken function-level authorization (BFLA).
- Unsafe file upload/download path.
- Missing server-side authorization on privileged APIs.
- SQL/NoSQL/GraphQL injection path.
- Weak webhook/service token validation.
- Overbroad cloud IAM with plausible sensitive-data path.

**Medium:**
- Missing rate limits.
- Missing audit event for sensitive action.
- Sensitive error leakage.
- Overly broad CORS.
- Weak security headers with plausible exploit path.
- Dependency vulnerability without confirmed exploit path.
- Misconfigured non-production environment with sensitive data.

**Low:**
- Hardening gap with low exploitability.
- Documentation mismatch.
- Missing non-critical header.
- Non-sensitive information disclosure.
- Minor test gap.

**Info:**
- Defense-in-depth opportunity with no current exploit path.
- Style/convention notes that affect future review surface.

## Finding status model

| Status | Meaning |
|---|---|
| CONFIRMED | Static evidence proves the defect exists today (cite line numbers). |
| LIKELY | Strong static signal but at least one premise unverified (state which). |
| STATIC-ONLY | Defect class is present in static analysis; runtime impact depends on data/config not in scope. |
| NEEDS-RUNTIME-TEST | Cannot be confirmed without controlled runtime test. Recipe required in `13-test-gap-report.md`. |
| BLOCKED | Required scope/access missing. Cite the scope-gap entry that blocks this. |

## Required output artifacts

The review writes to `security-review/` (relative to the user's chosen output root, default `library-reading-room/research/security-review-<YYYY-MM-DD>/`):

```
security-review/
  00-scope.md
  01-architecture-trust-boundaries.md
  02-threat-model.md
  03-authentication-review.md
  04-authorization-review.md
  05-tenant-isolation-review.md
  06-api-security-review.md
  07-data-evidence-security-review.md
  08-ai-rag-security-review.md           (skip if no AI/RAG declared)
  09-secrets-config-crypto-review.md
  10-cicd-supply-chain-review.md
  11-cloud-iac-review.md
  12-logging-audit-monitoring-review.md
  13-test-gap-report.md
  14-findings-register.md
  15-remediation-plan.md
```

Each phase artifact must contain:

1. Scope reminder (one paragraph).
2. Method (which checklist, which files inspected).
3. Confirmed PASSes with evidence.
4. Findings (one per `templates/finding-template.md` block).
5. Scope gaps surfaced during this phase.

## Review completion criteria

Review is complete when ALL of:

1. All 15 (or 14, no AI) artifact files written.
2. Every finding cites file/route/config evidence.
3. Every PASS cites implementation evidence.
4. `14-findings-register.md` lists every finding with status, severity, OWASP/CWE mapping, owner, priority.
5. `15-remediation-plan.md` orders findings by Critical → Low and cites blocking dependencies.
6. `13-test-gap-report.md` lists every required test category with at least one concrete missing-test recommendation each.
7. Scope gaps (if any) appear in `00-scope.md` and are referenced by every BLOCKED finding.

## Failure / blocked criteria

Halt and report (do not paper over):

- Required scope input missing → emit `00-scope.md` Scope Gap section, stop.
- Repository inaccessible → BLOCKED finding citing the missing path.
- Auth provider not declared → cannot run Phase 3 → BLOCKED.
- Tenancy model not declared → cannot run Phase 5 → BLOCKED.
- AI/RAG presence not declared → ask once; if unanswered, default to YES (run Phase 8) and note assumption.

## Anti-patterns (never do these)

- Producing a generic OWASP Top 10 checklist with no per-item evidence.
- Marking everything PASS because the framework "is secure by default."
- Reporting a finding without a reproducible attack path.
- Reporting a finding without a smallest-safe-fix recommendation.
- Reporting a finding without naming the test that would catch its regression.
- Treating spec/CLAUDE.md text as implementation evidence.
- Bundling 5 different defects into one finding.
- Using vague severity language ("medium-high", "could be high").
- Recommending a rewrite when a small targeted change would fix the defect.
- Suppressing findings because "the team already knows about it" — record it anyway with cross-ref.
- Running a runtime test against a deployed environment without explicit scope-doc authorization line.

## Example invocation

```
/compliance-os-security-review
  scope: agent-core compliance-core compliance-ui
  authority: library-reading-room/specs/INDEX.md
  auth_provider: Clerk
  api: REST + GraphQL (Apollo Server 5)
  db: Postgres 16 + RLS
  cloud: GCP + Terraform
  ai_rag: yes (LangGraph + LangChain + pgvector)
  envs_in_scope: local, integration (nonprod backend at int-api.sevenbelow.com)
  runtime_authz: NONE (static-only)
  output: library-reading-room/research/security-review-2026-05-08/
```

## Helper scripts

The skill ships four optional helpers under `scripts/`. Use them to enforce operating rules deterministically:

- `scripts/init-review.sh <out>` — bootstrap the 14-15 artifact stubs from templates (idempotent).
- `scripts/validate-finding.py <file>` — lint finding blocks against `templates/finding-template.md`. Exits 1 on missing fields, invalid severity/status, missing line-number evidence, or banned phrases.
- `scripts/aggregate-counts.py <file-or-dir>` — emit Markdown tables for `14-findings-register.md` aggregate counts.
- `scripts/scrub-check.sh <review-dir>` — detect JWT/API-key/private-key patterns before publishing the report.

These are pre-completion gates. The skill's review is not complete until `validate-finding.py` exits 0 against `14-findings-register.md` and `scrub-check.sh` exits 0 against the review dir.

## Validation rubric (skill self-check before completion)

| # | Question | Pass criterion |
|---|---|---|
| 1 | Did Phase 0 capture every required input or surface gaps? | `00-scope.md` exists; missing inputs listed under Scope Gaps. |
| 2 | Does every finding cite file + line evidence? | Grep for `Evidence:` blocks; each must include `File:` and `Function/Route/Config:`. |
| 3 | Does every PASS cite implementation? | No `PASS` without an adjacent `Evidence:` block. |
| 4 | Are statuses separated? | Each finding has CONFIRMED / LIKELY / STATIC-ONLY / NEEDS-RUNTIME-TEST / BLOCKED. |
| 5 | Is tenant isolation a first-class domain? | `05-tenant-isolation-review.md` exists with at least: tenant_id derivation, RLS, ALS/GUC propagation, jobs, webhooks, signed URLs. |
| 6 | Is AI/RAG covered (when applicable)? | `08-ai-rag-security-review.md` covers prompt injection, tenant-scoped retrieval, tool authz, output handling, cost cap. |
| 7 | Is CI/CD + supply chain covered? | `10-cicd-supply-chain-review.md` covers lockfiles, SCA, secret scan, branch protection, build provenance. |
| 8 | Is Cloud/IaC covered? | `11-cloud-iac-review.md` cites IAM, SAs, buckets, network, secret refs, env separation. |
| 9 | Is the Test Gap report present and concrete? | `13-test-gap-report.md` lists every required test category with at least one concrete recommendation. |
| 10 | Is the remediation plan prioritized + dependency-aware? | `15-remediation-plan.md` orders Critical → Low; lists blocking dependencies. |
| 11 | Are Critical conditions disproven by code, not by absence-of-evidence? | Every Critical-class checkpoint has either a finding OR an explicit code citation that disproves it. |
| 12 | Are scope gaps explicit? | `00-scope.md` Scope Gaps section + every BLOCKED finding cites a gap entry. |

If any rubric answer is NO, do not declare review complete. Fix and re-emit affected artifact(s).
