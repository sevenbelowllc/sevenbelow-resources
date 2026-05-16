# Data, Document, and Evidence Storage Security Checklist

Compliance evidence is the highest-sensitivity data class. Cite bucket config, signed-URL generator, scan worker, retention policy.

## Object storage configuration

- [ ] Bucket private; uniform bucket-level access enabled (no per-object ACL drift).
- [ ] Public access prevention enforced at the org / bucket level. Cite TF resource.
- [ ] Bucket layout: tenant prefix mandatory (`{bucket}/{tenant_id}/...`).
- [ ] Cross-region replication / backup policy documented; access audited.
- [ ] Versioning enabled for compliance evidence (immutable retention support).
- [ ] At-rest encryption: customer-managed key (CMEK) for tenant evidence where data classification requires.

## Upload path

- [ ] Upload endpoint authenticates AND tenant-scopes the destination prefix.
- [ ] Filename sanitized (no `..`, no absolute paths, no embedded `/`).
- [ ] Content-Type validated against allow-list; magic-byte sniff to defeat extension spoofing.
- [ ] Max upload size enforced server-side.
- [ ] Per-actor upload rate limit.
- [ ] Direct upload via signed URL: signed URL bound to (tenant, actor, content_type, size, expiry).
- [ ] Malware scan on every upload before file becomes accessible. Cite scan service + result-handling webhook.

## Download path

- [ ] Download endpoint authenticates AND verifies tenant ownership of the requested object.
- [ ] No object-id-from-path direct GET without authz.
- [ ] `Content-Disposition: attachment` set; `Content-Type` validated; `X-Content-Type-Options: nosniff` set.
- [ ] Download events audit-logged (actor, tenant, object id, timestamp).
- [ ] Per-actor download rate limit on sensitive evidence.

## Signed URLs

- [ ] TTL <= 15 min for sensitive evidence by default.
- [ ] Signed URL bound to: tenant_id, actor_id, object_id, http_method, content_type, expiry.
- [ ] Signed URLs do NOT use bucket-level service account creds; use per-request impersonation or HMAC.
- [ ] Signed URL revocation path documented (key rotation, grant revoke).
- [ ] One-time-use signed URLs for high-sensitivity downloads (audit reports, raw evidence).
- [ ] Signed URL generation rate-limited per actor + audit-logged.

## Malware / DLP scanning

- [ ] Anti-malware scan service wired (cite ClamAV / Cloud DLP / Lacework / etc.).
- [ ] Quarantine state for in-flight scan. Object NOT served until scan returns CLEAN.
- [ ] INFECTED state triggers alert + audit + customer notification per policy.
- [ ] DLP / sensitive-content scan per data classification policy (PII detection, secrets in evidence).

## Retention and deletion

- [ ] Per-tenant retention policy documented + enforced.
- [ ] Soft-delete with grace period for accidental delete recovery.
- [ ] Hard-delete at retention end; deletion audit-logged.
- [ ] Right-to-erasure (GDPR) path documented + tested.
- [ ] Tenant offboarding: full data export + deletion procedure documented + tested.

## Encryption

- [ ] TLS in transit on every leg.
- [ ] At-rest encryption on bucket + DB + secrets.
- [ ] Sensitive PII columns: column-level encryption or tokenization where required.
- [ ] Key management documented: KMS provider, rotation cadence, custodianship.

## Authorization on document operations

- [ ] Read: authenticated + tenant + role check (some docs admin-only).
- [ ] Create: authenticated + tenant + role check.
- [ ] Update: as create + version bump + author audit.
- [ ] Delete: as update + reason field + audit + alert.
- [ ] Share: signed URL + tenant scope + expiry + audit.
- [ ] Sign / approve: HITL token + segregation of duties + audit.

## Tests required

- Cross-tenant download attempt.
- Cross-tenant upload attempt.
- Signed URL from tenant A consumed by tenant B.
- Signed URL replay after expiry.
- Filename traversal in upload.
- Content-type spoof in upload.
- Direct bucket public access attempt (verify denied).
- Malware-positive upload reaches user (verify quarantine).
- Evidence delete without justification (verify rejected).
- Right-to-erasure end-to-end run on a fixture tenant.
