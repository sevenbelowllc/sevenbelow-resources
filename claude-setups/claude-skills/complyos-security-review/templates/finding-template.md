# Finding Template

Every finding MUST use this exact format. Reject findings missing any field. Replace `[brackets]` with concrete values.

```
### FINDING-[NNN]: [short imperative title — what is wrong]

- Severity: [Critical | High | Medium | Low | Info]
- Status: [CONFIRMED | LIKELY | STATIC-ONLY | NEEDS-RUNTIME-TEST | BLOCKED]
- Category: [Tenant Isolation | AuthN | AuthZ | BOLA | BFLA | Injection | SSRF | Secrets | Crypto | Logging | CI/CD | Cloud/IaC | AI/RAG | Resource Consumption | Misconfiguration | Other]
- OWASP Mapping: [A01..A10 | API1..API10 | LLM01..LLM10 | ASVS Vx.y.z]
- CWE Mapping: [CWE-NNN — name]
- Affected Component: [service/repo/module]
- Affected Tenant/Data Boundary: [which tenancy boundary breaks; "N/A" only if truly cross-cutting]
- Evidence:
  - File: [absolute or repo-relative path:line]
  - Function/Class: [name]
  - Route/API: [HTTP method + path or GraphQL operation name]
  - Config: [k8s manifest / TF resource / env var ref]
  - Test: [test file path + test name; "MISSING" if no test exists]
- What was observed: [1-3 sentences citing the code]
- Why this is vulnerable: [1-3 sentences on the security property violated]
- Attack path:
  1. [step 1]
  2. [step 2]
  3. [outcome]
- Business impact: [data exposure / SLO breach / compliance breach / financial / reputational]
- Tenant/data impact: [scope of affected tenants/users/records]
- Reproduction steps:
  - Static: [grep / read file:line / inspect config block]
  - Runtime (recommended controlled test, NOT to run unless authorized): [curl/script with parameters; mark NEEDS-RUNTIME-TEST]
- Smallest safe fix: [the narrowest code change that removes the defect; cite the file/function]
- Tests required:
  - [unit/integration/e2e/security test that catches regression]
  - [optional second test for defense-in-depth]
- Regression risk: [low / medium / high — what else could the fix break]
- Suggested owner: [team or repo CODEOWNER]
- Priority: [P0 / P1 / P2 / P3 — orthogonal to severity; reflects fix sequencing]
- Blocking questions: [any unresolved ambiguity that prevents CONFIRMED status]
```

## Status decision rules

- **CONFIRMED** — Static evidence proves the defect exists today. Cite line numbers that satisfy the "What was observed" claim. No runtime check required.
- **LIKELY** — Strong static signal but at least one premise unverified. Name the unverified premise in `Blocking questions`. Fix may proceed; verification should be added.
- **STATIC-ONLY** — Defect class is present in static analysis; runtime impact depends on data/config not in scope (e.g., depends on whether a feature flag is on in prod). State the dependency.
- **NEEDS-RUNTIME-TEST** — Cannot be confirmed without controlled runtime test. Recipe required in `13-test-gap-report.md`. Do not execute without scope-doc authorization.
- **BLOCKED** — Required scope/access missing. Cite the specific scope-gap entry in `00-scope.md`.

## Severity decision rules (quick reference; full model in `SKILL.md`)

- **Critical** — Cross-tenant data access; auth bypass; privilege escalation; RCE; exposed prod secret; AI/RAG tenant leakage; forged publish/approval; destructive op without authz.
- **High** — BOLA / BFLA; unsafe upload/download; SQL/NoSQL/GraphQL injection; weak webhook validation; overbroad cloud IAM with sensitive-data path.
- **Medium** — Missing rate limits; missing audit event; sensitive error leakage; broad CORS; weak headers with plausible exploit; dep CVE without confirmed exploit; misconfigured nonprod with sensitive data.
- **Low** — Hardening gap with low exploitability; documentation mismatch; missing non-critical header; non-sensitive info disclosure; minor test gap.
- **Info** — Defense-in-depth opportunity with no current exploit path.

## Anti-patterns (reject these findings)

- No file:line evidence.
- "It looks like X might be wrong."
- "Framework should handle this."
- Bundles 3+ defects in one finding.
- Recommends rewrite when targeted change suffices.
- No test recommendation.
- No attack path.
- No smallest-safe-fix.
