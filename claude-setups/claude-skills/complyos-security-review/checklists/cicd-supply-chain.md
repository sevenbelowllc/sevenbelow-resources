# CI/CD and Supply Chain Security Checklist

Cite the pipeline file, branch protection setting, and secret-store reference on every PASS.

## Pipeline gates

- [ ] CI/CD pipeline file in scope (Buildkite `.buildkite/pipeline.yml`, GitHub Actions, Cloud Build).
- [ ] Server-side gates run on every PR / push to protected branches:
  - [ ] Lint
  - [ ] Typecheck
  - [ ] Unit tests
  - [ ] Integration tests (where applicable)
  - [ ] Schema check (GraphQL SDL drift, OpenAPI drift)
  - [ ] Migration safety check
  - [ ] Secret scanner (gitleaks / trufflehog)
  - [ ] Dependency scanner (npm audit / pip-audit / osv-scanner / Snyk)
  - [ ] Image scanner (Trivy / Grype) with CRITICAL=fail
- [ ] Local hooks (Husky pre-commit / pre-push) treated as optimization, NOT substitute for server-side gate.
- [ ] `--no-verify` cannot bypass merge to protected branch.

## Branch protection

- [ ] Required reviewers > 0 on protected branches.
- [ ] Required status checks listed (cite GitHub branch-protection ruleset).
- [ ] Force-push disabled on protected branches.
- [ ] Linear history or merge-queue enforced.
- [ ] CODEOWNERS file present for security-sensitive paths (auth, RLS migrations, IaC, CI config).

## Secret scanning

- [ ] gitleaks / trufflehog in CI on every commit.
- [ ] Pre-commit hook present locally (defense-in-depth, not primary).
- [ ] Historical scan run at adoption; remediation tickets filed for findings.
- [ ] False-positive allowlist reviewed and capped.
- [ ] Secret scan covers `.env*`, `*.json`, `*.yaml`, `*.tf`, `*.tfstate*`, `*.md`.

## Dependency / SCA

- [ ] Lockfiles committed for every package manager.
- [ ] Renovate / Dependabot configured with PR reviewer rules.
- [ ] Pinned versions on high-risk deps (auth, crypto, parser, SQL driver).
- [ ] Direct + transitive vulnerability gate; CRITICAL fails build.
- [ ] License policy enforced (no GPL on closed-source distribution path, etc.).

## Container / image

- [ ] Multi-stage Dockerfile; runtime stage is distroless or minimal.
- [ ] Runtime tag is `:nonroot` (or explicit `USER 65532:65532`).
- [ ] No `:latest` references in deployed manifests.
- [ ] SBOM generated at build (Syft, Trivy SBOM, GitHub-native).
- [ ] Image signed (cosign / Notary); admission controller verifies signature.
- [ ] Image pulled from internal registry, not public Docker Hub, in deployed env.

## Build provenance

- [ ] Build runs on isolated, ephemeral runners (no persistent workspace).
- [ ] Build inputs: source SHA + lockfile hashes + toolchain pin recorded in artifact metadata.
- [ ] Reproducible build (or roadmap to it) documented.
- [ ] SLSA level documented (target SLSA 2 minimum for prod-bound artifacts).

## Deployment boundaries

- [ ] Deploy keys / SAs scoped: build-time SA cannot deploy; deploy-time SA cannot read source.
- [ ] Promotion gate: nonprod → prod requires separate approval + separate SA.
- [ ] Migration jobs run as a distinct DB role (BYPASSRLS) only at deploy time, not at request time.
- [ ] Rollback path tested (cite a documented rollback runbook).

## Secrets in CI

- [ ] CI secrets stored in cluster secret store (Buildkite cluster secrets, GitHub encrypted secrets, GCP Secret Manager via Workload Identity).
- [ ] No inline secrets in pipeline YAML.
- [ ] Job logs scrub secret values (cite the masking config).
- [ ] CI SA cannot read prod secrets (least privilege).

## Environment separation

- [ ] No prod data in nonprod (cite scrubbing / synthetic data policy).
- [ ] No nonprod tokens valid against prod services.
- [ ] No prod tokens valid against nonprod services.
- [ ] Cross-env references (e.g., `NEXT_PUBLIC_API_URL` baked at build) audited.

## Tests required

- Server-side gate bypass attempt (push with `--no-verify`).
- Secret scanner detects a planted test secret.
- Dependency scanner blocks a known-CRITICAL CVE in a fixture branch.
- Image scanner blocks a CRITICAL CVE in a fixture image.
- Branch-protection bypass attempt by non-reviewer.
- Promotion gate: nonprod → prod requires the second SA (verified by attempting with build-time SA).
