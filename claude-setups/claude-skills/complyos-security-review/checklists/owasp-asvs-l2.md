# OWASP ASVS Level 2 Checklist (excerpted, evidence-required)

Level 2 = applications handling sensitive data (compliance/audit/customer evidence). Cite implementation evidence per item.

## V2 — Authentication

- [ ] V2.1.1 Password length >= 12 (or auth-provider-managed; cite Clerk/Auth0/Cognito policy).
- [ ] V2.1.5 Disallow top-N common passwords + breached-password check.
- [ ] V2.2.1 Anti-automation on auth endpoints (rate limit + lockout). Cite middleware.
- [ ] V2.5.6 Token recovery flow does not bypass MFA.
- [ ] V2.6.1 OTP/TOTP secrets stored encrypted; TOTP windows validated.
- [ ] V2.7.1 OOB second factor delivered via verified channel only.
- [ ] V2.8.1 Single-use tokens for password reset / email change.
- [ ] V2.10.1 Service accounts use signed tokens (no shared bearer reuse).

## V3 — Session Management

- [ ] V3.2.1 New session id on login.
- [ ] V3.2.2 Session id not in URL/log/error.
- [ ] V3.3.1 Logout terminates session server-side.
- [ ] V3.3.4 Concurrent session policy defined and enforced (or accepted in scope doc).
- [ ] V3.4.1 Cookies: `Secure`, `HttpOnly`, `SameSite`. Cite cookie set.
- [ ] V3.5.1 Token revocation on role change / privilege change.

## V4 — Access Control

- [ ] V4.1.1 Trusted enforcement points server-side; no client-side authz claims trusted.
- [ ] V4.1.2 Default deny.
- [ ] V4.1.3 Principle of least privilege.
- [ ] V4.2.1 Object-level authz on every resource fetch.
- [ ] V4.2.2 Sensitive resources protected against direct-object-reference attacks (BOLA).
- [ ] V4.3.1 Admin endpoints require additional authz layer (role + MFA + audit).
- [ ] V4.3.2 Admin actions tagged in audit log with actor, target tenant, timestamp.

## V5 — Validation, Sanitization, Encoding

- [ ] V5.1.1 Input validation server-side via schema (Pydantic, Zod, GraphQL types).
- [ ] V5.1.4 Validate URL/email/UUID with explicit type, not regex-only.
- [ ] V5.2.4 SSRF defense at every outbound URL construction site.
- [ ] V5.3.1 Output encoding context-appropriate (HTML, JS, URL, SQL).
- [ ] V5.3.4 SQL parameter binding; no string concat.
- [ ] V5.5.2 Deserialize only safe formats with schema.

## V6 — Stored Cryptography

- [ ] V6.1.1 Sensitive data classified.
- [ ] V6.2.1 Encryption at rest for sensitive data (DB, storage, secrets).
- [ ] V6.2.2 Modern AEAD ciphers (AES-GCM, ChaCha20-Poly1305).
- [ ] V6.4.1 Key management documented (KMS, key rotation cadence, custodianship).

## V7 — Error Handling and Logging

- [ ] V7.1.1 No stack traces or internal IDs returned in error responses.
- [ ] V7.1.2 Errors logged server-side with correlation id.
- [ ] V7.3.1 Sensitive data scrubbed from logs (tokens, passwords, PII).
- [ ] V7.4.1 Security events logged (auth fail, privilege escalation, RLS deny, admin action).

## V8 — Data Protection

- [ ] V8.1.1 Sensitive data not cached on client.
- [ ] V8.1.4 Sensitive data not stored in browser history / autocomplete.
- [ ] V8.2.2 Backups encrypted; access audited.
- [ ] V8.3.4 Right-to-erasure implemented per data classification + GDPR scope.

## V9 — Communications

- [ ] V9.1.1 TLS 1.2+ everywhere. No HTTP fallback.
- [ ] V9.1.2 HSTS with preload.
- [ ] V9.2.1 Certificate validation enforced on outbound calls (no `verify=False`).

## V10 — Malicious Code

- [ ] V10.3.1 Lockfiles + SCA in CI.
- [ ] V10.3.2 Subresource Integrity (SRI) on third-party scripts where feasible.

## V11 — Business Logic

- [ ] V11.1.1 Anti-automation on sensitive flows (signup, role grant, evidence delete, support elevation, agent run).
- [ ] V11.1.4 Idempotency on retry-prone state transitions.

## V12 — Files and Resources

- [ ] V12.1.1 Upload size + type + content-sniff validation.
- [ ] V12.3.1 Filenames sanitized; no traversal.
- [ ] V12.4.1 Files served with correct `Content-Type` + `Content-Disposition: attachment` for downloads.
- [ ] V12.5.1 Files scanned for malware before serve (cite scan service).
- [ ] V12.6.1 Signed-URL TTL <= 15 min for sensitive artifacts.

## V13 — API & Web Service

- [ ] V13.1.1 Schema validation on all API requests.
- [ ] V13.1.4 Rate limiting per endpoint + per principal.
- [ ] V13.2.1 RESTful methods used correctly (GET pure-read, no state change).
- [ ] V13.3.1 GraphQL depth + complexity + alias-count limits.
- [ ] V13.4.1 No mass-assignment (block server-controlled fields like `role`, `tenantId`, `createdAt`).

## V14 — Configuration

- [ ] V14.1.1 Build pipeline reproducible.
- [ ] V14.2.1 Container provenance recorded.
- [ ] V14.3.1 Security headers set per A05.
- [ ] V14.4.1 No debug interfaces in deployed envs.
- [ ] V14.5.1 Cross-env separation (no prod secrets in nonprod, no nonprod data in prod).
