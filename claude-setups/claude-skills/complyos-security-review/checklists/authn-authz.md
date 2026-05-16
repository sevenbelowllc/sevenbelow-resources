# Authentication and Authorization Checklist

Cite the auth provider, the verification middleware, and the role-check function on every PASS.

## Authentication

### User auth (browser)

- [ ] Auth provider declared (Clerk / Auth0 / Cognito / custom). Cite version + SDK config.
- [ ] JWT signature verified server-side on every request. Cite the verification middleware line.
- [ ] JWT issuer pinned. Audience pinned to this service.
- [ ] JWT `exp` enforced. `iat` checked. `nbf` honored if present. Clock skew <= 30s.
- [ ] Token replay window bounded.
- [ ] Frontend middleware (e.g., Next.js `middleware.ts` for Clerk) is named correctly and ACTUALLY wired (verify build manifest, not just file presence).
- [ ] Public routes explicitly listed; default deny on unmapped paths.
- [ ] Token revocation path: logout terminates server-side session within SLO; role change forces re-auth.

### Service-to-service auth

- [ ] Internal services authenticated via OIDC ID tokens or mTLS, not shared bearer tokens.
- [ ] SA allowlist explicit. Cite the env var / settings field.
- [ ] Audience-locked tokens (caller mints token for THIS service, not a generic audience).
- [ ] Token verifier override / mock seam (if exists) gated on `env == 'local'` ONLY.

### Webhook auth

- [ ] Clerk webhook: svix signature verified.
- [ ] Stripe webhook: Stripe signature verified, raw body preserved.
- [ ] Pub/Sub webhook: OIDC token from Pub/Sub SA verified.
- [ ] GitHub / vendor webhooks: per-vendor signature verified.
- [ ] Replay protection: nonce or timestamp window.
- [ ] No webhook handler trusts payload-supplied tenant_id without DB cross-reference.

### Dev / test bypass paths

- [ ] All `x-test-token`, `x-user-id`, `DEV_AUTO_PROMOTE_*`, `set_identity_verifier`, etc. gated on `NODE_ENV === 'development'` (not `!== 'production'`).
- [ ] Startup assertion: bypass env vars must be unset in any non-development env.
- [ ] CI: integration tests use a separate test issuer / audience.

## Authorization

### Role / claim model

- [ ] Roles enumerated, documented, and immutable (no string concat into role).
- [ ] Role check helper centralized (one `requireRole(...)` / `assertAuth*(...)`).
- [ ] Cross-tenant roles (PLATFORM_ADMIN, SUPPORT, INTERNAL_AUDITOR) explicitly enumerated and audit-tagged.
- [ ] Caller cannot grant themselves a higher role (no self-promotion code path).

### Object-level (BOLA)

- [ ] Every fetch-by-id resolver / route checks ownership BEFORE returning.
- [ ] Resource fetch helpers (`getById`, `findOne`) take tenant context as a parameter and apply it.
- [ ] No "trust the join" — joins via tenant_id are correctness, not authz.

### Function-level (BFLA)

- [ ] Admin endpoints / mutations behind explicit role check, not just authed.
- [ ] Internal endpoints behind `verifyInternalIdentity` (OIDC SA allowlist).
- [ ] Admin actions logged with actor + target tenant + reason.

### Workflow state transitions

- [ ] Publish, approve, reject, sign, deactivate state changes authorized server-side; client-supplied `next_state` rejected.
- [ ] Segregation of duties: same actor cannot author + approve + publish (cite the SoD rule).
- [ ] HITL approval tokens bound to (tenant, target, action, expiry).
- [ ] State machine enforced server-side (cite the state-machine code or DB CHECK constraint).

### Sensitive flows

- [ ] Bulk export: per-actor daily cap + step-up MFA + audit + Sentry alert.
- [ ] Role grant: dual-approval for PLATFORM_ADMIN tier; no in-band single-actor promotion.
- [ ] Billing change: rate-limited + audited.
- [ ] Evidence delete: undo window + audit + alert + actor justification field.
- [ ] Support elevation: per-tenant grant + time-bound + MFA + audit + customer-visible.

### Tests required

- BOLA on every fetch-by-id resolver.
- BFLA on every admin / internal route.
- Role-elevation attempt by EMPLOYEE → ADMIN.
- Role-elevation attempt by ADMIN → PLATFORM_ADMIN.
- Workflow forge: client-supplied next_state on every state-machine endpoint.
- Webhook signature reject: tampered payload, wrong signature, expired timestamp.
- Dev-bypass path absent in non-dev env (assert env var unset OR env var set + assert reject).
