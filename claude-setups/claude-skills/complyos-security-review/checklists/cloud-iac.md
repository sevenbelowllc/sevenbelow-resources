# Cloud and Infrastructure-as-Code Checklist

Cite TF resource block (file + type + name) on every PASS. Cloud provider neutral but oriented toward GCP + Terraform.

## IAM and service accounts

- [ ] Per-service SA (not default compute SA).
- [ ] Workload Identity binds k8s SA to GCP SA (no key file mounts).
- [ ] Roles narrowest necessary (no `roles/owner`, no `roles/editor` on prod project).
- [ ] No SA key files committed; SA keys disabled at org policy level.
- [ ] Cross-project access uses explicit IAM binding, not wildcard.
- [ ] Break-glass / human admin access via IAP-tunnel + audit, not standing SSH.

## Project / environment separation

- [ ] Distinct projects per environment (`-prod`, `-nonprod`, `-shared`).
- [ ] No shared secrets across env-projects.
- [ ] No prod resources referenced from nonprod TF state.
- [ ] TF state stored in encrypted backend (GCS bucket with object versioning + access audit).
- [ ] TF state bucket access restricted to TF-runner SA + ops break-glass.

## Network exposure

- [ ] Public-facing services list explicit. Cite each Cloud LB / Ingress / API Gateway resource.
- [ ] Internal services use ClusterIP / private LB; no accidental public exposure.
- [ ] DB instances private IP only; no public IP enabled. Cite `private_ip_google_access`.
- [ ] Cloud SQL: authorized networks empty in deployed env; access via Cloud SQL Auth Proxy / private IP.
- [ ] WAF / Cloud Armor on public endpoints. Cite policy rules.
- [ ] CDN / Cloudflare in front of public app: enforce origin auth (not just header presence).

## Storage

- [ ] Object storage: public access prevention enforced.
- [ ] Object storage: uniform bucket-level access enabled.
- [ ] Object storage: tenant-prefix layout enforced (per data-evidence checklist).
- [ ] Object storage: versioning + retention for compliance evidence.
- [ ] Cross-region replication / backup policy documented.

## Database

- [ ] DB encryption at rest with CMEK where data classification requires.
- [ ] DB roles separated: app role (no BYPASSRLS), migration role (BYPASSRLS, deploy-time only), readonly role (analytics).
- [ ] DB password / IAM authentication. No shared password across services.
- [ ] DB backups encrypted; restore path tested.
- [ ] PITR / point-in-time recovery enabled.

## Secret Manager

- [ ] Secrets in Secret Manager; no plaintext in TF, env files, or k8s manifests.
- [ ] Secret refs by ID; values mounted at runtime via External Secrets Operator (ESO) or CSI driver.
- [ ] Secret rotation cadence documented per secret class.
- [ ] Audit log on secret access (cite Cloud Audit Logs config).
- [ ] Per-tenant secrets (provider keys, customer-supplied) tenant-scoped at access layer.

## Logging and monitoring

- [ ] Cloud Audit Logs enabled (Admin Activity, Data Access where data classification warrants).
- [ ] Logs exported to a separate logging project (immutable).
- [ ] Sensitive log fields redacted (cite log-router config).
- [ ] Alert rules: IAM change, SA key creation, public-bucket toggle, prod project access by unexpected principal.
- [ ] Sentry / external observability scrub PII at transport.

## IaC pipeline

- [ ] TF plan reviewed before apply (no auto-apply on prod).
- [ ] TF apply requires distinct SA from TF plan SA on prod.
- [ ] Drift detection runs (Atlantis, Terraform Cloud, scheduled `terraform plan`).
- [ ] Critical resources (KMS keys, IAM bindings) require multi-approver review (cite branch-protection or PR ruleset).
- [ ] No `terraform import` of secrets; secrets stay in Secret Manager.

## Org-level guardrails

- [ ] Org policies: disable SA key creation, restrict public IP on Cloud SQL, restrict allowed locations.
- [ ] VPC-SC perimeter on prod data resources where data classification warrants.
- [ ] Hierarchical firewall policies prevent ad-hoc rules.

## Tests required

- Public-bucket creation attempt (verify org-policy denies).
- SA key creation attempt (verify org-policy denies).
- Cross-project access attempt with nonprod SA (verify denied on prod).
- TF apply with build-time SA (verify denied on prod).
- DB connection from public IP (verify denied).
- Secret read by unauthorized SA (verify denied + audit-logged).
