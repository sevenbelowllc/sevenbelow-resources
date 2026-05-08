# Example Usage Prompt

Paste this into Claude Code (or your harness) to invoke the skill against this workspace.

---

```
/complyos-security-review

Scope:
- Repos: <agent-service>, <api-service>, <ui-service>
- Authority pointer: docs/specs/INDEX.md
- Auth provider: Clerk (frontend SDK + backend JWT verify)
- API style: GraphQL (Apollo Server 5) + REST (Express 5) on <api-service>; FastAPI on <agent-service>
- Database: Postgres 16 + RLS on Class T tables; three-role model (compliance_migrator / compliance_app / compliance_readonly)
- Cloud + IaC: GCP + Terraform (<iac-root> + <iac-metadata>)
- AI/RAG: yes — LangGraph + LangChain + Claude/OpenAI + pgvector
- Environments in scope: local + integration (nonprod backend at <api-domain>; UI at <ui-domain>)
- Runtime probing authorization: NONE — static-only
- Output root: docs/security-review/
- Compliance frameworks targeted: SOC 2 + GDPR + NIST CSF 2.0 (capstone scope)
- Threat-actor profile: external + malicious tenant admin + compromised support tier
- Prior reports to cross-reference:
  - docs/security-review/prior-report.md
  - docs/security-review/prior-api-report.md

Run all phases. Skip Phase 8 only if AI/RAG turns out to be entirely scaffolded-but-not-wired. Surface any scope gaps in 00-scope.md before proceeding to Phase 1.

Hard rules (reaffirm):
- No secret values printed or read.
- No runtime calls against deployed env.
- Every finding cites file:line evidence.
- Every PASS cites implementation evidence.
- Tenant-isolation breaches default to Critical.
- Stub endpoints mounted in deployable image without feature gate are findings, not PASSes.
```

---

## What the skill will produce

A `security-review/` directory with 15 artifacts (or 14 if AI/RAG is genuinely absent), a `14-findings-register.md` aggregating every finding, a `15-remediation-plan.md` with prioritized fix order, and a `13-test-gap-report.md` listing every required regression test category with at least one concrete recommendation each.

## Common follow-ups

- "Re-run Phase 5 against the latest integration branch."
- "Verify FINDING-NNN against <api-service>@<SHA>."
- "Generate the smallest-safe-fix PR for FINDING-NNN."
- "Cross-reference findings against Jira JIRA-NNN epic."

## Related skills

- `compliance-os-api-standard` — fires on resolver/SDL/REST changes.
- `hard-isolation-migration-checklist` — fires on Class T migration.
- `owasp-security` — general OWASP reference.
- `precheck` — architecture-grounding gate before infra/skill design.
