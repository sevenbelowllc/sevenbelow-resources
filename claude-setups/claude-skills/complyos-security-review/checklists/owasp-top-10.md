# OWASP Top 10:2021 Checklist

For each item: produce a CONFIRMED PASS with evidence, a finding (any status), or a SCOPE-GAP entry. Generic checklist output is rejected.

## A01:2021 — Broken Access Control

- [ ] Server-side authorization on every state-changing endpoint. Cite middleware/resolver guard line.
- [ ] Object-level authorization on every resource fetch by id. Cite the ownership check (tenant_id match, owner check, role check).
- [ ] Function-level authorization on every admin/elevated endpoint. Cite role check.
- [ ] Workflow state transitions (publish/approve/reject/sign) authorized server-side. Reject any "trust client-supplied next_state".
- [ ] Force-browse paths (incremented IDs, predictable URLs, signed URLs) protected.
- [ ] CORS not used as access control.
- [ ] Default deny on unmapped routes.

## A02:2021 — Cryptographic Failures

- [ ] TLS termination point identified. Cite ingress / Cloud LB / Cloudflare config.
- [ ] HSTS enabled with `includeSubDomains` and `preload`.
- [ ] Cookies on auth endpoints set `Secure`, `HttpOnly`, `SameSite=Strict|Lax` per design.
- [ ] Passwords hashed with Argon2id / bcrypt cost-factor >= 12 (or auth-provider-managed; cite which).
- [ ] At-rest encryption on DB + object storage + secrets store. Cite the GCP/AWS config or TF resource.
- [ ] Secrets never in repo, never in `NEXT_PUBLIC_*` / public env vars.
- [ ] Sensitive PII columns encrypted or tokenized where required by data classification.

## A03:2021 — Injection

- [ ] All SQL parameterized (asyncpg `$1..$N`, pg `$1`, knex bindings, ORM parameter API). Grep for string-interpolation in SQL.
- [ ] No raw SQL execution from user input outside migration tooling.
- [ ] GraphQL resolvers do not concatenate variables into raw queries.
- [ ] OS command execution avoided; if present, cite use of `execFile` with arg array (not shell concatenation).
- [ ] HTML rendering goes through a sanitizer (DOMPurify or framework-managed escaping).
- [ ] LDAP, NoSQL, XPath, template, header, log injection — checked per the codebase shape.

## A04:2021 — Insecure Design

- [ ] Threat model exists or is being produced (`02-threat-model.md`).
- [ ] Trust boundaries documented (browser <-> edge <-> API <-> DB <-> AI service <-> third party).
- [ ] Rate limits per-user / per-tenant / per-IP layered.
- [ ] Sensitive flows (signup, role grant, billing change, evidence delete, support elevation) have anti-abuse controls.
- [ ] Idempotency keys on retry-prone flows (payment, agent run, webhook process).
- [ ] Data classification documented; flows respect classification.

## A05:2021 — Security Misconfiguration

- [ ] No verbose error messages or stack traces returned in nonprod-public or prod responses.
- [ ] No default credentials. Cite startup assertions for required secrets.
- [ ] No introspection / debug endpoints / Swagger / dev portal exposed in any internet-reachable env.
- [ ] CSP, X-Frame-Options (or CSP `frame-ancestors`), X-Content-Type-Options, Referrer-Policy, Permissions-Policy set.
- [ ] CORS allowlist explicit; no wildcards with `Allow-Credentials: true`.
- [ ] Container images run as non-root + readOnlyRootFilesystem + drop ALL capabilities.

## A06:2021 — Vulnerable and Outdated Components

- [ ] Lockfiles committed (`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` / `poetry.lock` / `requirements.lock`).
- [ ] Server-side dependency scan in CI (`npm audit`, `pip-audit`, `osv-scanner`, Snyk, GitHub Advanced Security).
- [ ] Image scanning in CI (Trivy, Grype) with CRITICAL=fail.
- [ ] Renovate / Dependabot configured with PR reviewer rules.
- [ ] Pinned versions on high-risk deps (auth, crypto, parser).
- [ ] No `latest` tag in deployed image references.

## A07:2021 — Identification and Authentication Failures

- [ ] Auth provider integration validates JWT signature, issuer, audience, exp, iat, nbf, clock skew.
- [ ] Login rate limiting + lockout policy.
- [ ] MFA available for admin/elevated roles; required for support elevation.
- [ ] Session/token revocation pathway works (logout, role change, suspicious activity).
- [ ] Service-to-service auth uses signed tokens (OIDC / mTLS); no shared bearer tokens reused across services.
- [ ] Email change / password reset flows verify ownership of new identifier.

## A08:2021 — Software and Data Integrity Failures

- [ ] CI/CD pipeline gated by branch protection and required server-side checks.
- [ ] Container image build provenance recorded (SLSA level documented or in roadmap).
- [ ] Webhook signatures verified (Clerk svix, Stripe, GitHub, Pub/Sub OIDC).
- [ ] Deserialization paths use safe formats (JSON with schema validation; no unsafe Python binary-serialization modules; no unsafe YAML loaders; no Java native serialization on untrusted input).
- [ ] Auto-update mechanisms (if any) verify signatures.

## A09:2021 — Security Logging and Monitoring Failures

- [ ] Auth failures logged with rate-limited correlation.
- [ ] Privilege escalation events logged (role change, support elevation).
- [ ] Tenant-isolation violation attempts logged + alerted.
- [ ] Workflow transitions (publish/approve/sign) recorded in immutable audit log.
- [ ] Evidence access (download, share, delete) logged.
- [ ] Logs scrub PII / tokens / secrets before forwarding to Sentry / LangFuse / external store.
- [ ] Alert rules exist for: auth-failure spikes, BOLA attempts, secret-exposure, RLS denial spikes, agent-cost spikes.

## A10:2021 — Server-Side Request Forgery (SSRF)

- [ ] No outbound HTTP from request handler with user-controlled URL without scheme + host validation.
- [ ] Webhook destination URLs validated against private/internal address space at registration AND delivery (DNS-rebind defense).
- [ ] Image/document fetch by URL (if any) gated by allowlist or proxy.
- [ ] Internal service URLs (agent base URL, db proxy, internal admin) validated `*.svc.cluster.local` or RFC1918 only.
- [ ] LLM tool calls that fetch URLs gated by allowlist + outbound proxy with private-IP block.

## Required regression tests

Each checklist item above must be backed by a regression test from `templates/test-plan-template.md`. Map per OWASP category:

- A01 Broken Access Control → categories 5 (BOLA), 6 (BFLA), 12 (workflow forgery)
- A02 Cryptographic Failures → review-time only (verify TLS/HSTS via deploy probe)
- A03 Injection → SQL parameterization unit tests; XSS sanitization tests
- A04 Insecure Design → category 13 (rate/resource abuse), 11 (signed URL expiry)
- A05 Security Misconfiguration → CI gate verifying introspection/dev-portal disabled in deployed envs
- A06 Vulnerable Components → CI dep scan + image scan must fail on CRITICAL
- A07 AuthN Failures → categories 4 (tenant ID spoofing), 7-8 (support elevation expiry/audit)
- A08 Software Integrity → category 17 (webhook signature validation)
- A09 Logging Failures → category 21 (security event audit logging)
- A10 SSRF → URL-validator unit tests covering RFC1918 / loopback / metadata IPs / DNS rebind
