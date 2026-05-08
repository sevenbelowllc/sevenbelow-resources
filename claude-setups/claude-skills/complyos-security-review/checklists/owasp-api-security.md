# OWASP API Security Top 10:2023 Checklist

For each item: produce CONFIRMED PASS with evidence, a finding, or SCOPE-GAP. For multi-tenant compliance platforms, BOLA + BFLA + Resource-Consumption + Unsafe-Consumption are the highest-yield categories.

## API1:2023 — Broken Object Level Authorization (BOLA)

- [ ] Every resource fetch by id (REST path param or GraphQL `id` arg) verifies caller has access to that specific object. Cite the ownership check.
- [ ] No reliance on RLS alone for object-level authz; RLS is defense-in-depth.
- [ ] DataLoader / batching layers do not leak across tenants (cite per-request loader instantiation tied to tenant context).
- [ ] Predictable IDs (sequential, low-entropy) compensated with explicit ownership check at resolver.
- [ ] Workflow-state-keyed lookups (`getApprovalByToken`, `getEvidenceBySignedUrl`) verify tenant binding on the token AND on the underlying object.

## API2:2023 — Broken Authentication

- [ ] JWT signature, issuer, audience, exp, iat, nbf, clock skew all verified.
- [ ] Service-to-service auth uses short-lived signed tokens (OIDC ID tokens, mTLS).
- [ ] Webhook auth: provider signature verified server-side (Clerk svix, Stripe sig, Pub/Sub OIDC).
- [ ] No "x-test-token" / "x-user-id" / dev-bypass paths reachable in deployed envs (gate strictly on `NODE_ENV === 'development'`, not `!== 'production'`).
- [ ] Session/token revocation propagates within SLO (e.g., 5 min on role change).

## API3:2023 — Broken Object Property Level Authorization

- [ ] GraphQL field-level authz: sensitive properties (`user.email`, `tenant.stripe_customer_id`, `auditLog.actorIp`, `auditLog.userAgent`) restricted per role.
- [ ] Mass-assignment blocked on every mutation: server-controlled fields (`role`, `tenantId`, `clerkId`, `createdAt`, `updatedAt`, `auditChain`) cannot be set via input type.
- [ ] REST PATCH/PUT bodies validated against allow-list schema; extra fields rejected, not silently dropped.

## API4:2023 — Unrestricted Resource Consumption

- [ ] Per-endpoint rate limit. Cite middleware.
- [ ] Per-tenant rate limit (separate from per-IP).
- [ ] Per-user rate limit on sensitive flows.
- [ ] GraphQL depth limit AND query complexity / cost limit. Cite plugin config.
- [ ] Pagination: max `first`/`limit` enforced; reject above cap, do not silently slice.
- [ ] DataLoader batch size capped.
- [ ] SSE/WebSocket per-tenant concurrent-connection cap.
- [ ] Body-size cap per route (especially file upload, agent input, webhook bodies).
- [ ] LLM cost caps: per-tenant daily/hourly budget enforced at request entry, not just observed in trace.
- [ ] Agent loop max-iteration / max-token / wall-clock caps.
- [ ] Idempotency-Key support on retry-prone expensive endpoints.

## API5:2023 — Broken Function Level Authorization

- [ ] Every admin-tier endpoint behind explicit role check (not just "authed").
- [ ] Internal endpoints behind `verifyInternalIdentity` (OIDC SA allowlist).
- [ ] Role enums do not allow self-promotion (caller cannot grant themselves a higher role).
- [ ] Cross-tenant admin actions logged with actor + target tenant + justification.

## API6:2023 — Unrestricted Access to Sensitive Business Flows

- [ ] Bulk-action mutations (bulk invite, bulk export, bulk publish, bulk delete) throttled + audited + step-up-auth-gated.
- [ ] Tenant-creation endpoint protected against rapid-fire automation.
- [ ] Stripe checkout flow binds (Clerk session, Stripe customer, tenant_id) at intent-creation time; webhook rejects rebind.
- [ ] Password-reset / email-change / role-change rate-limited per actor + target.
- [ ] Support elevation requires: explicit per-tenant grant + time-bound expiration + MFA + audit log.

## API7:2023 — Server-Side Request Forgery (SSRF)

- [ ] Every outbound HTTP from server code with caller-controlled URL gated by `validateExternalUrl(url, scope)`.
- [ ] Webhook destination URLs validated at registration AND delivery (DNS rebind defense: re-resolve at delivery, reject if private).
- [ ] Internal service URLs (agent base URL, internal admin) validated `*.svc.cluster.local` or RFC1918.
- [ ] LLM agent tool inputs that contain URLs validated against allowlist.
- [ ] Outbound proxy enforces private-IP block at network layer.

## API8:2023 — Security Misconfiguration

- [ ] Apollo introspection disabled in any internet-reachable env.
- [ ] Swagger / `/dev-portal` / `/schema` / `/docs` not exposed in deployed envs.
- [ ] Sentry-example / debug endpoints removed.
- [ ] Error responses do not leak stack traces or internal codes.
- [ ] CORS allowlist explicit; no wildcard with `Allow-Credentials: true`.
- [ ] Security headers per A05.
- [ ] Container `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, drop ALL caps.
- [ ] No `:latest` tag in deployed image refs.

## API9:2023 — Improper Inventory Management

- [ ] Stub endpoints not mounted in deployable image without feature gate (fail with 501).
- [ ] Old/v1 API versions sunset with documented EOL.
- [ ] OpenAPI / GraphQL schema documents private/internal endpoints separately (or not at all).
- [ ] Internal admin routes mounted under distinct path prefix and gated.

## API10:2023 — Unsafe Consumption of APIs

- [ ] All third-party API responses validated against expected schema.
- [ ] Trust boundary on Stripe metadata enforced (no rebind on tenant_id).
- [ ] Trust boundary on Clerk webhook payloads enforced (signature verify + email_verified check before rebind).
- [ ] Trust boundary on LLM responses: prompt injection from RAG / tool output sanitized; tool-call output validated before state mutation.
- [ ] Outbound TLS verification ON; no `verify=False`.
- [ ] Timeout + retry budgets per third-party API.
- [ ] Cert pinning where supply-chain risk warrants.
