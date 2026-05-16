# Tenant Isolation Checklist (first-class domain)

Multi-tenant SaaS isolation failures are Critical by default. Cite the chokepoint code on every PASS.

## Tenant ID derivation

- [ ] Server-side derivation only. Cite the code that derives tenant_id from the verified principal (Clerk JWT claim, OIDC SA token, signed tenant claim).
- [ ] Backend NEVER trusts `tenant_id` from request body, query string, path param, header, or unsigned cookie.
- [ ] Where `tenant_id` IS in the path (e.g., `/api/tenants/:tenantId/...`), middleware cross-checks against principal-derived tenant before the resolver runs.
- [ ] Multi-tenant users (consultants, support agents, PLATFORM_ADMIN) explicitly switch tenant via authenticated mutation, not header.

## Tenant context propagation

- [ ] AsyncLocalStorage / context-var pattern set at request entry, cleared at exit.
- [ ] Every DB checkout reads from ALS and `SET LOCAL app.current_tenant_id = $1` (or equivalent GUC).
- [ ] Background jobs / queue workers explicitly enter `withTenantContext(jobTenantId)` before any DB call.
- [ ] Webhook handlers derive tenant from the signed payload + cross-reference DB binding (no implicit propagation).
- [ ] Async fire-and-forget paths (Promises, asyncio tasks) carry tenant context across the boundary.

## Row Level Security (RLS)

- [ ] Every Class T (tenant-scoped) table has `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` AND `... FORCE ROW LEVEL SECURITY`.
- [ ] Every Class T table has at least one RLS policy that uses `current_setting('app.current_tenant_id')::uuid`.
- [ ] Application DB role does NOT have BYPASSRLS.
- [ ] Migration role with BYPASSRLS used only by migration runner / seed runner / db-bootstrap, not request path.
- [ ] System tenant for shared/global rows (if any) uses an explicit reserved UUID and is documented.
- [ ] Composite PK with tenant_id leading column on every Class T table (defense-in-depth + index alignment).
- [ ] Secondary indexes lead with tenant_id where the query path filters by it.

## RLS bypass paths (audit each)

- [ ] Background jobs (BullMQ, Cron, Cloud Scheduler, Pub/Sub workers): cite tenant context entry.
- [ ] Migrations: cite which run as `compliance_migrator` (BYPASSRLS) and confirm migrations cannot be invoked from request path.
- [ ] Seed scripts: same.
- [ ] Service / system roles (Stripe webhook handler, email worker, malware scan webhook): cite explicit tenant binding before write.
- [ ] Admin tooling: cite per-tenant grant + audit log.
- [ ] Test fixtures: confirm they cannot run against deployed DB.

## Cross-tenant data references

- [ ] No table has a tenant-scoped FK to a row in a different tenant (CHECK constraint or app-level enforcement).
- [ ] Shared dictionary tables (frameworks, criteria templates, threat intel) are Class P (no tenant_id) and explicitly documented.
- [ ] Cross-tenant aggregations (multi-org dashboard, portfolio views) execute per-tenant query inside `withTenantContext(tenantId)` loop, not bare-pool fan-out.

## Object-level authorization (BOLA)

- [ ] Every resolver / route that fetches by id verifies tenant ownership BEFORE returning. RLS is defense-in-depth, not the only check.
- [ ] DataLoader instances are per-request, tenant-scoped, never module-global.
- [ ] GraphQL field resolvers do not return objects of a different tenant via association traversal (`tenant.users.tenant.users`).
- [ ] Workflow tokens (approval link, signed URL, share link) bound to tenant + verified at consumption.

## Function-level authorization (BFLA)

- [ ] Every admin / support / system mutation behind explicit role check (not just `isAuthenticated`).
- [ ] Cross-tenant admin actions (PLATFORM_ADMIN bulk-export, role grant) require: per-tenant grant + MFA step-up + audit log + Sentry alert.
- [ ] Role enums do not allow self-promotion: caller cannot grant themselves a higher role.

## Support / admin elevation

- [ ] Support access requires explicit per-tenant grant (not standing access).
- [ ] Grants time-bound (default <= 4 hours, configurable per policy).
- [ ] Grants logged in immutable audit log with: actor, target tenant, justification, expiry.
- [ ] Grant expiry enforced server-side; no client-side TTL trust.
- [ ] MFA step-up required at grant creation AND at each elevated action.
- [ ] Customer-visible audit of when their tenant was accessed by support.

## Tenant-scoped object storage

- [ ] Bucket layout enforces tenant prefix: `{bucket}/{tenant_id}/...`.
- [ ] Read/write authorization layer checks `tenant_id` from path against authenticated tenant.
- [ ] Cross-tenant object reference (signed URL for tenant A given to tenant B) blocked.
- [ ] Bucket is private; no public ACL on tenant evidence.

## Signed URLs

- [ ] TTL <= 15 minutes for sensitive evidence by default.
- [ ] Signed URL bound to tenant + actor + object id (not just object path).
- [ ] One-time-use signed URLs for high-sensitivity downloads (audit reports, raw evidence).
- [ ] Signed URL generation logged + rate-limited per actor.

## AI/RAG tenant isolation

- [ ] Vector DB queries scoped: `WHERE tenant_id = current_setting('app.current_tenant_id')::uuid` OR collection-per-tenant.
- [ ] Embedding ingest tenant-bound at write time (never global "all-tenant" corpus).
- [ ] Agent state checkpoints (LangGraph thread state) tenant-bound; thread_id lookup verifies (thread_id, tenant_id) before resume.
- [ ] Agent tool calls inherit tenant context; tools that hit DB go through `withTenantContext`.
- [ ] Agent runtime cross-checks caller-asserted tenant against signed tenant claim, not just `x-tenant-id` header.

## Tests required (cross-ref `13-test-gap-report.md`)

- Cross-tenant read attempt against every Class T table.
- Cross-tenant write / update / delete attempt against every Class T table.
- Cross-tenant search / list attempt with tenant_id of another tenant.
- Tenant-id spoofing in JWT claim / header / body / path.
- BOLA on every fetch-by-id resolver.
- Background job runs in wrong tenant context.
- Webhook from tenant A binding to tenant B's resource.
- Signed URL from tenant A consumed by tenant B.
- Agent thread_id from tenant A resumed by tenant B.
- RAG query from tenant A returns tenant B's chunks.
- Support elevation expiry enforcement.
- Support elevation audit log presence.
