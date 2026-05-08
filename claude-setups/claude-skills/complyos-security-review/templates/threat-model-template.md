# Threat Model Template (`02-threat-model.md`)

STRIDE-per-asset, focused on multi-tenant compliance product threats.

## Assets (rank by sensitivity)

| Asset | Sensitivity | Owner | Storage | Access pattern |
|---|---|---|---|---|
| Tenant evidence (uploaded docs) | Critical | Tenant | Object storage + DB pointers | Authenticated read; admin/support read with grant |
| Audit log | Critical | System | Append-only DB table | Read by tenant admin; cross-tenant read by PLATFORM_ADMIN with audit |
| Tenant configuration | High | Tenant | DB | Read/write by tenant admin |
| User PII | High | User | DB | Read by user; system access for support |
| Billing data | High | Tenant + Stripe | DB + Stripe | Read by tenant owner |
| Secrets / API keys | Critical | System | Secret Manager | Read at runtime via SA only |
| AI prompts/outputs | Medium-High | Tenant | LangFuse + DB | Read by tenant admin |
| RAG embeddings | Medium-High | Tenant | Vector DB | Read at retrieval time |
| Compliance framework canonicals | Low | System (shared) | DB Class P | Read by all tenants |

## Actors

| Actor | Trust level | Capabilities |
|---|---|---|
| Anonymous external | Untrusted | Browse public marketing pages |
| Authenticated tenant user (EMPLOYEE) | Low | Read/write tenant data within role |
| Tenant admin (OWNER/ADMIN) | Medium | All tenant ops, role mgmt within tenant |
| External tenant user (consultant) | Low | Multi-tenant memberships; explicit switch |
| PLATFORM_ADMIN (support) | High | Cross-tenant ops with grant + audit |
| System service account | High | Service-to-service calls within trust boundary |
| CI/CD pipeline | High | Build + deploy; no runtime data access |
| Third-party integration (Stripe, Clerk) | Medium | Bound webhook surface |
| Compromised tenant admin | Adversary (assume capable) | Full role within their tenant |
| Compromised support agent | Adversary (assume capable) | Cross-tenant if grant model is weak |
| Network attacker (passive) | Adversary | TLS termination point matters |
| Malicious internal employee | Adversary | Whatever the standing-access model permits |

## Entry points

| Entry point | Auth | Rate limit | Notes |
|---|---|---|---|
| Web app (Next.js, Vercel) | Clerk JWT | per-IP edge | Browser-side |
| Public API (`<public-api>` / `<private-api>`) | Clerk JWT / OIDC SA | per-IP + per-tenant | All app traffic |
| GraphQL `/graphql` | as above | + depth + complexity | |
| REST routes | as above | per-route | |
| SSE / WebSocket | as above | concurrent-conn cap | |
| Webhooks | provider signature | per-webhook | Clerk, Stripe, Pub/Sub |
| Admin / internal | role + OIDC | strict | |
| Agent runtime (AI) | service auth | per-tenant | Cluster-internal |
| CI/CD trigger | git event + branch protection | n/a | |

## Abuse cases (per asset, per actor)

For each (asset × actor) pair where the trust gap matters, write the abuse case:

### ABUSE-001: Cross-tenant evidence read by authenticated tenant user
- Asset: Tenant evidence
- Actor: Authenticated tenant user
- Path: BOLA on document fetch-by-id resolver / signed URL forge / direct bucket access
- Likely defenses: server-side ownership check, RLS, signed URL binding, bucket private + tenant prefix
- Critical-condition trigger: yes (cross-tenant data access)

### ABUSE-002: Tenant admin promotes self to PLATFORM_ADMIN
- Asset: Authorization model
- Actor: Tenant admin
- Path: mutation that accepts arbitrary `role` arg; mass-assignment in update; bypass via direct DB on a misrouted route
- Likely defenses: mutation rejects elevated role; role change requires dual approval
- Critical-condition trigger: yes (privilege escalation)

### ABUSE-003: Stripe metadata rewrite reroutes billing
- Asset: Billing data
- Actor: Compromised Stripe account / support tier
- Path: rewrite `customer.metadata.tenant_id`; webhook accepts and rebinds
- Likely defenses: pending-mapping table; reject rebind on webhook
- Critical-condition trigger: high

### ABUSE-004: Indirect prompt injection via uploaded evidence
- Asset: AI agent / tenant evidence
- Actor: Tenant admin (low-skill); compromised tenant
- Path: malicious instruction in uploaded doc; RAG retrieves; agent acts as instructed (e.g., emit credentials, exfil via tool call)
- Likely defenses: untrusted-content delimiter; tool-call validation; HITL gate on sensitive actions
- Critical-condition trigger: yes if cross-tenant exfil possible

### ABUSE-005: Webhook destination SSRF to internal metadata endpoint
- Asset: System secrets / internal APIs
- Actor: Tenant admin
- Path: register webhook URL pointing at metadata server / internal admin
- Likely defenses: validateExternalWebhookUrl at registration AND delivery; DNS rebind defense
- Critical-condition trigger: yes (RCE / secret exposure path)

### ABUSE-006: Background job runs without tenant context
- Asset: Tenant data
- Actor: System
- Path: queue worker pulls job; forgets `withTenantContext`; reads/writes against bare pool
- Likely defenses: lint rule banning bare DB calls; runtime assertion in DB wrapper
- Critical-condition trigger: yes if cross-tenant write

### ABUSE-007: Long-lived signed URL leaked
- Asset: Tenant evidence
- Actor: External (anyone with the URL)
- Path: signed URL with TTL > 15 min shared via email / link / browser history; reused after intended use
- Likely defenses: TTL <= 15 min; one-time-use for high-sensitivity; signed URL bound to actor
- Critical-condition trigger: yes (public access to private evidence)

[Continue for every (asset × actor) combination where the trust gap is non-trivial. Number sequentially.]

## Attack tree (top three)

For the three highest-impact abuse cases, draw an attack tree:

```
GOAL: cross-tenant evidence read
  AND
    1. Locate target tenant + object id
       OR
         a. Enumerate via predictable IDs
         b. Receive ID via collision / leak
         c. Guess from product knowledge
    2. Bypass authorization
       OR
         a. BOLA in fetch-by-id resolver
         b. Forge signed URL
         c. Compromise support tier with active grant
         d. Compromise SA with bucket read
    3. Retrieve content
       OR
         a. Through API
         b. Direct from bucket
         c. Via cached agent state
```

## Trust boundary diagram

[Inline ASCII or mermaid; reference detailed version in `01-architecture-trust-boundaries.md`.]

## Threats out of scope

- [Threat] — reason: [residual risk accepted by ops / handled by upstream layer / not realistic in this product]

## Findings flow

Every threat above either:

1. Is disproven by a citeable defense (cite in this artifact),
2. Produces a finding (file `14-findings-register.md` per template), or
3. Is BLOCKED on a scope gap (cite `00-scope.md` GAP-NNN).

Threats with NO disposition fail Phase 2.
