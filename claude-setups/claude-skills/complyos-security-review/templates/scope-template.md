# Scope Template (`00-scope.md`)

Phase 0 artifact. Captures every input and surfaces gaps. If any required input is missing, do NOT proceed to Phase 1.

## Review metadata

- **Date:** YYYY-MM-DD
- **Reviewer(s):** [name(s) / agent dispatch IDs]
- **Output root:** `docs/security-review/`
- **Triggering event:** [PR / release / incident / scheduled / customer questionnaire]
- **Companion / prior reports:** [paths]

## Required inputs

| # | Input | Provided? | Value |
|---|---|---|---|
| 1 | Repositories in scope | yes / no | [absolute paths] |
| 2 | Authority/spec index pointer | yes / no | [path] |
| 3 | Auth provider | yes / no | [Clerk / Auth0 / Cognito / custom] |
| 4 | API style | yes / no | [REST / GraphQL / both / gRPC] |
| 5 | Database engine + tenancy model | yes / no | [Postgres + RLS / schema-per-tenant / db-per-tenant / other] |
| 6 | Cloud provider + IaC tool | yes / no | [GCP + Terraform / AWS + CDK / etc.] |
| 7 | AI/RAG/agent presence | yes / no | [yes + stack / no] |
| 8 | Environments in scope | yes / no | [list each label, deployed yes/no, internet-reachable yes/no] |
| 9 | Runtime probing authorization | yes / no | [NONE / scoped to env X / explicit signature line below] |

## Optional inputs

- Compliance framework targets: [SOC 2 / GDPR / HIPAA / NIST CSF / ISO 27001 / PCI / none]
- Threat-actor profile: [external / malicious tenant admin / malicious internal / nation-state]
- Specific Jira/PR/branch this review gates: [refs]
- Known third-party integrations: [list]
- Prior audit reports to cross-reference: [paths]

## Scope inclusions

- Repos: [list]
- Code paths: [list directories / glob patterns]
- Environments: [list]
- Data classes in scope: [PII / customer evidence / billing / audit logs / system internal]

## Scope exclusions (explicit)

- [path/env] — reason
- [path/env] — reason

## Sensitive data inventory

| Data class | Examples | Storage | Encryption | Retention | In scope? |
|---|---|---|---|---|---|
| Customer PII | name, email, phone | Postgres | at rest + TLS | per policy | yes/no |
| Customer evidence | uploaded docs | object storage | at rest + TLS + signed-URL | per policy | yes/no |
| Audit logs | every action | Postgres | at rest + TLS | per policy | yes/no |
| Billing | Stripe customer ID, plan | Postgres + Stripe | tokenized | per policy | yes/no |
| Secrets | API keys, JWTs | Secret Manager | KMS | rotation cadence | yes/no |
| Tenant configuration | per-tenant settings | Postgres | at rest | per policy | yes/no |

## Trust boundaries

[Brief diagram or list. Detailed version goes in `01-architecture-trust-boundaries.md`.]

- Browser ↔ CDN/edge
- CDN ↔ public API
- Public API ↔ internal services
- Internal services ↔ DB
- Internal services ↔ AI runtime
- Internal services ↔ third-party integrations
- CI/CD runner ↔ deploy target

## Runtime probing authorization

If any phase requires runtime testing against a deployed environment, the user MUST sign below:

> I authorize controlled, non-destructive runtime testing of [env name] for the purpose of this security review. Tests must not modify data, rotate secrets, exceed cost caps, or affect other tenants. Authorized by: [name], date: YYYY-MM-DD.

If this section is empty, runtime testing is FORBIDDEN. All phases run static-only.

## Scope gaps

[Each gap blocks one or more findings. Reference these gap IDs from BLOCKED findings.]

### GAP-001: [short title]
- What is missing: [exact input or access]
- What it blocks: [phases / findings / checklist items]
- Resolution path: [how the user can resolve]

### GAP-002: ...

## Approval to proceed

- [ ] All required inputs provided OR all gaps documented above.
- [ ] User has reviewed the scope.
- [ ] Reviewer ready to proceed to Phase 1.
