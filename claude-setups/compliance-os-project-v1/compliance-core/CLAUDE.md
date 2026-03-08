# Claude Operating Contract — compliance-core

## Repo Role

This is an **EXECUTION ONLY** repository. It contains the [YOUR PRODUCT NAME] backend API. You write application code here — services, resolvers, migrations, tests. Nothing else.

---

## Repo Roles (LOCKED)

| Repository | Role |
|------------|------|
| `compliance-os-goldmaster-prds` | AUTHORITY — normative docs, contracts, guard scripts |
| `[ORCHESTRATOR-REPO]` | ORCHESTRATION — .planning/, handoffs, runbooks, decisions |
| **`compliance-core`** | **EXECUTION — backend code lives here** |
| `compliance-ui` | EXECUTION — frontend code |
| `compliance-tpis` | EXECUTION — third-party integration microservice |
| `[TERRAFORM-MODULES]-*` | INFRA — Terraform modules |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | >=20.0.0 |
| Language | TypeScript | 5.9 (ES2022 modules, strict mode) |
| HTTP | Express | 5.x |
| API | Apollo Server (GraphQL) | 5.x |
| Database | PostgreSQL | via `pg` 8.x |
| ORM | TypeORM | 0.3.x (entities + raw SQL migrations) |
| Auth | Clerk | @clerk/backend 2.x |
| Payments | Stripe | 17.x |
| WebSocket | Socket.io | 4.x |
| Push | OneSignal | @onesignal/node-onesignal 5.x |
| Feature Flags | Harness | @harnessio/ff-nodejs-server-sdk 1.x |
| Jobs | node-cron | 4.x |
| Storage | AWS S3 SDK | @aws-sdk/client-s3 3.x |
| Monitoring | Sentry | @sentry/nestjs 10.x |
| Testing | Jest + ts-jest | 30.x / 29.x |
| E2E Testing | Playwright | 1.40 |

---

## Project Structure

```
src/
  config/           # App configuration
  db/
    entities/       # TypeORM entities
    migrations/     # Raw SQL migration files (numbered: 001_xxx.sql)
    seeds/          # Database seed data
  graphql/          # GraphQL schema definitions
  initializers/     # Auto-discovered *.initializer.ts startup tasks
  jobs/             # Cron jobs and scheduled tasks
  middleware/       # Express middleware (auth, logging)
  processors/       # Event processors (digest, deletion, snapshots)
  resolvers/        # GraphQL resolvers (per domain)
  runners/          # CLI runner framework (Commander.js)
    commands/       # Domain CLI commands
  services/         # Business logic (~34 domain services)
  types/            # Shared TypeScript types
  utils/            # Utility functions
  webhooks/         # Webhook handlers (Clerk, Stripe)
```

---

## Path Alias

```typescript
import { something } from '@/services/SomeService';
// resolves to src/services/SomeService
```

---

## Key Patterns (ENFORCED)

### Backend-First State Machines
- ALL state transitions are enforced server-side
- Frontend receives `allowedTransitions[]` — it NEVER computes them
- Segregation of Duties (Author ≠ Approver) validated per instance

### Raw SQL Migrations
- Migrations are numbered SQL files in `src/db/migrations/`
- Pattern: `NNN_descriptive_name.sql`
- Prisma was removed (Phase 11). Use `pg` for queries, TypeORM for entities.

### Runners Pattern
- CLI commands use Commander.js with lifecycle wrapper (`createRunner`)
- Domain runners are thin CLI wrappers — no business logic in CLI layer
- Initializers are auto-discovered `*.initializer.ts` files

### Cloud SQL & Secrets
<!-- Full rules in CARL domains: SECRETS, INFRASTRUCTURE. Summaries here. -->
- **Cloud SQL:** Node.js Connector + Workload Identity — `[ORCHESTRATOR-REPO]/decisions/CLOUD_SQL_CONNECTIVITY.md`
- **Secrets:** ESO delivers env vars, CSI BANNED — `[ORCHESTRATOR-REPO]/decisions/SECRETS_ESO_NOT_CSI.md`
- Application code reads `process.env`, NOT filesystem paths

### Audit Logging
- Synchronous PostgreSQL inserts (not queued)
- Immutable via database trigger
- SHA-256 hash chain for tamper detection

<!-- Domain separation rules are in CARL GOVERNANCE domain -->

---

## Authority References

When implementing features, these documents in `compliance-os-goldmaster-prds` are authoritative:

| Document | Path (relative to goldmaster-prds) |
|----------|-----|
| State Registry | `03-governance/state-registry.md` |
| API Schema | `01-system-architecture/api-schema-specification.md` |
| Approvals State Machine | `01-system-architecture/approvals-state-machine-specification.md` |
| Auth Integration | `07-security-privacy/auth-integration-specification.md` |
| Audit Logging | `08-observability/audit-logging-specification.md` |
| Evidence Lifecycle | `01-system-architecture/evidence-lifecycle-specification.md` |
| Cross-Domain Contracts | `04-cross-domain-contracts/cross-domain-governance-contracts-index.md` |

**If your code contradicts these specifications, your code is wrong.**

---

## What You MUST NOT Do

- Write planning documents, roadmaps, or GSD state (belongs in orchestrator)
- Modify or create authority documents (belongs in goldmaster-prds)
- Write frontend code (belongs in compliance-ui)
- Write infrastructure code (belongs in terraform repos)
- Invent lifecycle states not defined in `state-registry.md`
- Use frontend state machines — backend is authoritative
- Use Prisma (deleted in Phase 11)
- Hardcode user IDs, org IDs, or credentials
- Write real secret values into ANY file (code, .env.example, docs). Use `REPLACE_ME` placeholders and `process.env.*` in code. All secrets live in GCP Secret Manager ONLY.

---

## Implementation Instructions

Implementation plans and handoff context come from:
```
[ORCHESTRATOR-REPO]/handoffs/core/
```

If no handoff exists for your current task, ask the user for context or reference the orchestrator's `.planning/` state.

---

## Development

```bash
npm run dev          # Start dev server (tsx watch)
npm run build        # TypeScript compilation
npm run db:migrate   # Run database migrations
npm run db:seed      # Seed database
npm test             # Run Jest tests
npm run test:e2e     # Run Playwright E2E tests
```

**Server:** http://localhost:4000
**GraphQL Playground:** http://localhost:4000/graphql
**Frontend expects:** CORS from http://localhost:3000

---

## Security Standards Adherence (NON-NEGOTIABLE)

Authority: `compliance-os-goldmaster-prds/00-product-foundation/security-standards-contract.md`
CARL domains: `security`, `cis-benchmarks`

- NEVER invent security parameters. All values MUST cite OWASP/NIST/CIS.
- Security headers (CSP, HSTS, X-Frame-Options) MUST be present on all responses (helmet).
- Rate limiting MUST be configured on /graphql endpoint (express-rate-limit).
- GraphQL introspection MUST be disabled in production.
- GraphQL query complexity MUST be limited (maxRecursiveSelections).
- All resolvers accessing multi-tenant data MUST enforce org-scoping.
- All NEW resolvers MUST use `assertAuthAndOrg()` or `assertAuth()` from `src/graphql/auth/resolver-auth.ts` — inline auth checks are BANNED for new code. Existing resolvers may still use inline patterns but will be migrated over time.
- **Auditor permissions (Decision 167):** Both `EXTERNAL_AUDITOR` and `INTERNAL_AUDITOR` have identical permissions: CAN post comments and create/respond to evidence requests. CANNOT create/edit/approve/delete Controlled Documents (read-only). Resolvers for comments and evidence requests MUST allow both auditor roles. Document mutation resolvers MUST reject both auditor roles.
- Health endpoint MUST NOT expose version info in production.
- Audit logs MUST be append-only (PostgreSQL trigger enforced).
- Container images MUST be pinned to SHA256 digests in Dockerfile.

---

*This contract is loaded automatically by Claude Code. Follow it exactly.*
