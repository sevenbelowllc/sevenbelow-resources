# CARL Domain: Security (OWASP)

**Authority:** `compliance-os-goldmaster-prds/00-product-foundation/security-standards-contract.md`
**Applies To:** All application code (compliance-core, compliance-ui)
**Standards:** OWASP Top 10 2021, OWASP ASVS v4.0.3, OWASP API Security Top 10 2023
**Updated:** 2026-02-15

---

## Rules

### Rule 0: NEVER Invent Security Parameters

All security values (rate limits, thresholds, header values, encryption settings) MUST cite OWASP, NIST, or CIS. If no standard covers the parameter, research industry practice from Cloudflare/AWS/GCP docs BEFORE proposing values.

**Cite the source for EVERY security parameter.**

**Anti-Pattern (BANNED):**
- "Set rate limit to 100 requests/minute" — NO SOURCE
- "Use CSP: default-src 'self'" — NO JUSTIFICATION

**Correct Pattern:**
- "Set rate limit to 100 req/min per IP (OWASP API4:2023 recommends 10-1000 based on endpoint sensitivity)"
- "Use CSP: default-src 'self' (OWASP ASVS V14.4.5 requires CSP on all responses)"

---

### Rule 1: Security Headers Required (OWASP ASVS V14)

All HTTP responses from application servers MUST include:

**Required Headers:**
- **Content-Security-Policy (CSP)** — OWASP ASVS V14.4.5
  - Minimum: `default-src 'self'`
  - For Next.js: Use nonce-based approach for inline scripts
- **Strict-Transport-Security (HSTS)** — OWASP ASVS V14.4.3
  - Minimum: `max-age=63072000` (2 years)
  - Include `includeSubDomains`
- **X-Content-Type-Options: nosniff** — OWASP ASVS V14.4.4
- **X-Frame-Options: DENY** — OWASP A04:2021 (Clickjacking)
  - Use `SAMEORIGIN` only if iframes are required
- **Referrer-Policy: strict-origin-when-cross-origin** — OWASP ASVS V14.4.7

**Implementation:**
- compliance-core: Use `helmet` middleware for Express
- compliance-ui: Configure in `next.config.js` headers section

**Verification:**
```bash
curl -I https://app.your-domain.com/health | grep -E '(Content-Security|Strict-Transport|X-Frame|X-Content-Type)'
```

---

### Rule 2: Rate Limiting Required on All Public APIs (OWASP API4:2023)

Every public API endpoint MUST have rate limiting. GraphQL endpoint requires both application-level (express-rate-limit) and edge-level (Cloudflare/Cloud Armor) rate limiting.

**OWASP API4:2023 — Unrestricted Resource Consumption**

**Application-Level Rate Limiting:**
- Use `express-rate-limit` on /graphql endpoint
- Recommended: 100 requests/15 minutes per IP for authenticated users
- Recommended: 10 requests/15 minutes per IP for unauthenticated endpoints
- Cite OWASP API Security Top 10 or industry benchmarks when setting limits

**Edge-Level Rate Limiting:**
- Cloud Armor rate limit rules
- Threshold: cite GCP Cloud Armor documentation or industry practice
- Must be in ENFORCE mode (preview = false) — CIS GCP 7.13

**GraphQL-Specific:**
- Query complexity limits (Apollo Server `maxRecursiveSelections`)
- Batch query limits
- Persistent query safelist (if implemented)

---

### Rule 3: No Version Exposure (OWASP A05:2021)

Health endpoints, error messages, and HTTP headers MUST NOT expose application version, framework version, or server software version in production (NODE_ENV=production).

**OWASP A05:2021 — Security Misconfiguration**

**Banned in Production:**
- `X-Powered-By: Express` header (helmet disables this)
- Version strings in error messages
- Framework names in user-facing errors
- Stack traces in API responses

**Allowed in Development:**
- Version in /health response body
- Stack traces in error responses
- Framework debug headers

**Implementation:**
- Express: `app.disable('x-powered-by')`
- Or use `helmet` which does this by default
- Error handlers: Check NODE_ENV before including stack traces

---

### Rule 4: All Public APIs Require Authentication (OWASP A07:2021)

No public-facing endpoint may operate without authentication unless explicitly documented as a public resource (e.g., health check, OpenID discovery).

**OWASP A07:2021 — Identification and Authentication Failures**

**GraphQL Endpoints:**
- MUST require valid Clerk JWT
- JWT verification MUST happen before resolver execution
- Unauthenticated requests return 401

**Public Endpoints (Explicitly Allowed):**
- `/health` — health check (no sensitive data)
- `/.well-known/jwks.json` — OpenID discovery (if implemented)

**Development Exception:**
- `x-user-id` header bypass is ONLY allowed when `NODE_ENV=development`
- Decision #106 — gated behind environment check

---

### Rule 5: GraphQL Security (OWASP A04:2021)

**OWASP A04:2021 — Insecure Design**

GraphQL endpoints require additional security controls beyond typical REST APIs.

**Required Controls:**

1. **Introspection Disabled in Production**
   - Apollo Server: `introspection: process.env.NODE_ENV !== 'production'`
   - Prevents schema enumeration attacks

2. **Query Depth/Complexity Limits**
   - Apollo Server: `validationRules: [depthLimit(10)]` or equivalent
   - Or use `maxRecursiveSelections` plugin
   - Prevents deeply nested query DoS

3. **CSRF Prevention**
   - Require custom header (`Apollo-Require-Preflight`) or content-type application/json
   - Prevent simple form POST attacks

4. **Batch Query Limits**
   - Limit number of operations in a single request
   - Prevent batch query DoS

**Recommended:**
- Persistent queries (safelist approach)
- Field-level cost analysis
- Query timeout limits

---

### Rule 6: Resolver-Level Authorization (OWASP A01:2021)

All GraphQL resolvers accessing multi-tenant data MUST enforce organization-scoped access control. Data queries MUST be filtered by the authenticated user's organizationId. **Deny by default.**

**OWASP A01:2021 — Broken Access Control**

**Pattern:**
```typescript
// BANNED — no authorization
const documents = await db.query('SELECT * FROM documents');

// CORRECT — org-scoped
const documents = await db.query(
  'SELECT * FROM documents WHERE organization_id = $1',
  [user.organizationId]
);
```

**Required for ALL resolvers that:**
- Query multi-tenant tables (documents, templates, workflows, users)
- Accept resource IDs as arguments
- Return lists of resources

**Exceptions:**
- Public health checks
- Admin endpoints (with explicit admin role check)

**Verification:**
- Every resolver accessing DB MUST have WHERE organization_id = $1
- Code review: search for SELECT without organization_id filter

---

### Rule 7: Audit Log Immutability (NIST CSF DE.CM)

Audit log tables MUST be append-only. PostgreSQL triggers MUST prevent UPDATE and DELETE operations on audit_logs.

**NIST CSF DE.CM — Continuous Monitoring**
**OWASP A08:2021 — Software and Data Integrity Failures**

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs table is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutability_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();

CREATE TRIGGER audit_log_immutability_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
```

**Verification:**
```sql
-- This should fail with "audit_logs table is append-only"
UPDATE audit_logs SET user_id = 'test' WHERE id = 1;
DELETE FROM audit_logs WHERE id = 1;
```

---

### Rule 8: Never Expose Endpoints Without Protection

All public-facing endpoints MUST be behind both Cloudflare (IP whitelisting) and Cloud Armor (WAF + default deny). Direct load balancer access MUST return 403.

**OWASP A05:2021 — Security Misconfiguration**
**CIS GCP 7.13 — WAF enforce mode**

**Required Layers:**

1. **Cloudflare** — IP whitelisting for known good IPs
   - Blocks non-Cloudflare traffic at edge
   - Provides DDoS protection

2. **Cloud Armor** — WAF + rate limiting
   - Priority 50: Allow Cloudflare IPs only
   - Priority 500: Explicit deny (required before rate limit rules)
   - Priority 1000: Rate limit rules
   - Default action: Deny (implicit)

3. **Application** — Authentication + authorization
   - Clerk JWT validation
   - Resolver-level org-scoping

**Verification:**
```bash
# Direct LB access should return 403
curl -I http://<LB_IP>/health

# Cloudflare access should return 200
curl -I https://app.your-domain.com/health
```

---

## Enforcement

This domain is automatically loaded at Claude session start via CARL system.

**Violations:**
- Any security parameter without citation → STOP execution
- Missing security headers in PR → REQUEST CHANGES
- Rate limiting missing on public endpoint → BLOCK merge
- Introspection enabled in production → BLOCK deployment

**Citation Format:**
```
# Setting rate limit to 100 req/15min per IP
# Source: OWASP API4:2023 recommends 10-1000 based on endpoint sensitivity
# Justification: /graphql is authenticated, 100 is conservative for normal usage
```

---

## Related Standards

| Standard | URL | Usage |
|----------|-----|-------|
| OWASP Top 10 2021 | https://owasp.org/Top10/ | Primary application security framework |
| OWASP ASVS v4.0.3 | https://owasp.org/www-project-application-security-verification-standard/ | Verification requirements (headers, session mgmt) |
| OWASP API Security Top 10 2023 | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ | GraphQL + REST API security |
| NIST CSF 2.0 | https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf | Organizational security framework |

---

**Version:** 1.0
**Status:** Active — enforced via CARL
**Last Updated:** 2026-02-15
