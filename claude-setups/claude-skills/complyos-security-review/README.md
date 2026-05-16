# complyos-security-review

> A SevenBelow Claude Skill for evidence-backed, multi-tenant SaaS security reviews.

Deep security review skill for Claude Code. Drives a structured, 15-phase audit of a multi-tenant SaaS platform — OWASP Top 10, ASVS Level 2, OWASP API Top 10, OWASP LLM Top 10, tenant isolation, RLS, evidence/document storage, AI/RAG, CI/CD, and cloud/IaC — and produces a findings register, remediation plan, and test-gap report with file/line evidence on every claim.

Built for [ComplyOS](https://complyos.app) by [SevenBelow](https://sevenbelow.com), then generalized so any multi-tenant SaaS team can use it.

---

## What it does

When invoked, the skill drives Claude through 15 review phases:

| Phase | Output artifact |
|---|---|
| 0 — Scope and Constraints | `00-scope.md` |
| 1 — Architecture and Trust Boundaries | `01-architecture-trust-boundaries.md` |
| 2 — Threat Model | `02-threat-model.md` |
| 3 — Authentication Review | `03-authentication-review.md` |
| 4 — Authorization Review | `04-authorization-review.md` |
| 5 — Tenant Isolation Review | `05-tenant-isolation-review.md` |
| 6 — API Security Review | `06-api-security-review.md` |
| 7 — Data, Document, Evidence Security | `07-data-evidence-security-review.md` |
| 8 — AI / RAG / Agent Security | `08-ai-rag-security-review.md` |
| 9 — Secrets, Config, Cryptography | `09-secrets-config-crypto-review.md` |
| 10 — CI/CD and Supply Chain | `10-cicd-supply-chain-review.md` |
| 11 — Cloud / IaC | `11-cloud-iac-review.md` |
| 12 — Logging, Audit, Monitoring | `12-logging-audit-monitoring-review.md` |
| 13 — Test Gap Review | `13-test-gap-report.md` |
| 14 — Findings Register and Remediation Plan | `14-findings-register.md` + `15-remediation-plan.md` |

Every finding cites file path, line number, route/resolver, and config evidence. Every PASS verdict cites implementation. Generic checklist output is rejected by design.

## Why this skill exists

Security reviews drift toward generic checklists. This skill enforces:

- **No PASS without implementation evidence.** Spec text and CLAUDE.md claims do not count.
- **No finding without an attack path + smallest-safe-fix + regression test.**
- **Tenant-isolation breaches default to Critical.**
- **Status separation:** `CONFIRMED` / `LIKELY` / `STATIC-ONLY` / `NEEDS-RUNTIME-TEST` / `BLOCKED`.
- **No runtime tests against deployed environments without explicit scope-doc authorization.**
- **No secret values read, printed, or written.** References to vault items by name only.

## Coverage

- OWASP Top 10:2021
- OWASP ASVS Level 2 (excerpted; auth, session, access, validation, crypto, errors, data, comms, files, API, config)
- OWASP API Security Top 10:2023
- OWASP LLM Top 10:2025 + Agentic AI 2026 preview (when AI/RAG is in scope)
- Tenant isolation (RLS, GUC propagation, BYPASSRLS paths, cross-tenant references, BOLA, BFLA, support elevation, signed URLs, AI/RAG tenant scope)
- Evidence and document storage (object storage, signed URLs, malware scan, retention, encryption)
- CI/CD and supply chain (lockfiles, SCA, secret scan, branch protection, image provenance, deploy boundaries)
- Cloud / IaC (IAM, service accounts, env separation, network exposure, Secret Manager, audit logs)

## Install

### Option 1 — Clone into your Claude skills directory

Claude Code looks for skills under `~/.claude/skills/` (user-scoped) or `.claude/skills/` (project-scoped).

```bash
# User-scoped install (available in every project)
mkdir -p ~/.claude/skills
cp -r /path/to/sevenbelow-resources/claude-setups/claude-skills/complyos-security-review ~/.claude/skills/

# OR project-scoped install
mkdir -p .claude/skills
cp -r /path/to/sevenbelow-resources/claude-setups/claude-skills/complyos-security-review .claude/skills/
```

Restart your Claude Code session, or run `/reload-plugins` to pick up the new skill.

### Option 2 — Symlink (recommended for active development)

```bash
ln -s "$(pwd)/sevenbelow-resources/claude-setups/claude-skills/complyos-security-review" ~/.claude/skills/complyos-security-review
```

### Option 3 — Sparse clone (just this skill)

```bash
git clone --filter=blob:none --sparse git@github.com:sevenbelowllc/sevenbelow-resources.git
cd sevenbelow-resources
git sparse-checkout set claude-setups/claude-skills/complyos-security-review
ln -s "$(pwd)/claude-setups/claude-skills/complyos-security-review" ~/.claude/skills/complyos-security-review
```

### Verify install

```bash
ls ~/.claude/skills/complyos-security-review/SKILL.md
```

In Claude Code, type `/` and confirm `complyos-security-review` appears in the slash-command picker, or ask Claude: "do you have the complyos-security-review skill?"

## Use

### Trigger phrases

The skill auto-invokes on:

- `/complyos-security-review`
- "security review"
- "security audit"
- "threat model"
- "tenant isolation review"
- "RLS review"
- "API security review"
- "AI security review"

### Minimal invocation

```
/complyos-security-review
  scope: <repo paths>
  auth_provider: <Clerk | Auth0 | Cognito | custom>
  api: <REST | GraphQL | both>
  db: <engine + tenancy model>
  cloud: <provider + iac>
  ai_rag: <yes | no>
  envs_in_scope: <env labels>
  runtime_authz: NONE
  output: <output-root>
```

The skill will halt at Phase 0 and emit `00-scope.md` if any required input is missing.

### Phase-targeted re-run

After fixing findings, verify by re-running a single phase:

```
/complyos-security-review --phase 5
  scope: <api-service>
  reason: "verify withTenantContext lint rule lands"
  output: docs/security-review/
```

### Single-finding verification

```
/complyos-security-review --verify FINDING-001
  scope: <api-service>
  branch: fix/finding-001
```

### Diff-scoped review (PR-sized)

```
/complyos-security-review --diff main..HEAD
  scope: <api-service>
  reason: "PR review — security-only pass on the diff"
```

See `examples/usage-prompt.md` and `examples/review-command.md` for fully worked invocations.

## Output

The skill writes a `security-review/` directory containing 15 artifacts:

```
security-review/
├── 00-scope.md
├── 01-architecture-trust-boundaries.md
├── 02-threat-model.md
├── 03-authentication-review.md
├── 04-authorization-review.md
├── 05-tenant-isolation-review.md
├── 06-api-security-review.md
├── 07-data-evidence-security-review.md
├── 08-ai-rag-security-review.md          # skipped if no AI/RAG
├── 09-secrets-config-crypto-review.md
├── 10-cicd-supply-chain-review.md
├── 11-cloud-iac-review.md
├── 12-logging-audit-monitoring-review.md
├── 13-test-gap-report.md
├── 14-findings-register.md
└── 15-remediation-plan.md
```

Every finding follows the format in `templates/finding-template.md` (severity, status, OWASP/CWE mapping, evidence, attack path, smallest safe fix, tests required, owner, priority).

## Severity model

| Severity | Triggers |
|---|---|
| **Critical** | Cross-tenant data access, auth bypass, privilege escalation, RCE, exposed prod secret, AI/RAG tenant leakage, forged publish/approval, destructive op without authz |
| **High** | BOLA / BFLA, unsafe upload/download, SQL/NoSQL/GraphQL injection, weak webhook validation, overbroad cloud IAM with sensitive-data path |
| **Medium** | Missing rate limits, missing audit event, sensitive error leakage, broad CORS, weak headers with plausible exploit, dep CVE without confirmed exploit, misconfigured nonprod |
| **Low** | Hardening gap, doc mismatch, missing non-critical header, non-sensitive info disclosure, minor test gap |
| **Info** | Defense-in-depth opportunity with no current exploit path |

## What the skill will refuse to do

- Run runtime tests against a deployed environment without an explicit scope-doc authorization signature.
- Print, exfiltrate, or generate fake production secret values.
- Mark a phase complete without an artifact file written.
- Issue a PASS verdict without implementation evidence.
- Bundle multiple defects into a single finding.
- Recommend a rewrite when a targeted change suffices.
- Treat spec / README / CLAUDE.md text as implementation evidence.

## Directory layout

```
complyos-security-review/
├── SKILL.md                                # operating contract: phases, rules, evidence, severity, completion criteria
├── checklists/
│   ├── owasp-top-10.md
│   ├── owasp-asvs-l2.md
│   ├── owasp-api-security.md
│   ├── owasp-llm-security.md
│   ├── tenant-isolation.md
│   ├── authn-authz.md
│   ├── data-evidence-security.md
│   ├── cicd-supply-chain.md
│   ├── cloud-iac.md
│   └── ai-rag-security.md
├── templates/
│   ├── finding-template.md
│   ├── findings-register-template.md
│   ├── scope-template.md
│   ├── threat-model-template.md
│   ├── remediation-plan-template.md
│   └── test-plan-template.md
├── scripts/                                # all Python 3.10+, no third-party deps
│   ├── init-review.py                      # bootstrap security-review/ output skeleton from templates
│   ├── validate-finding.py                 # lint a finding block against the template; exit 1 on violations
│   ├── aggregate-counts.py                 # produce severity/status/category tables from findings
│   └── scrub-check.py                      # detect publish-blocking secret patterns before sharing
└── examples/
    ├── usage-prompt.md
    └── review-command.md
```

## Helper scripts

The skill ships four small helpers under `scripts/`. All are optional; the
skill works as pure Markdown without them. Use them to enforce the operating
rules with deterministic checks instead of relying on Claude's self-discipline.

### `init-review.py` — bootstrap output skeleton

```bash
# Create the 14 standard artifact stubs (Phase 0..7 + 9..15)
python3 scripts/init-review.py path/to/output

# Include AI/RAG phase (08-ai-rag-security-review.md)
python3 scripts/init-review.py path/to/output --with-ai

# Force overwrite (default is skip-existing)
python3 scripts/init-review.py path/to/output --force
```

Idempotent: re-running skips files that already exist. Each stub pre-populates
header, scope-reminder, method, PASS, findings, and scope-gap sections so
Claude has a consistent shape to fill in.

### `validate-finding.py` — lint findings against the template

```bash
# Lint a register file
python3 scripts/validate-finding.py path/to/14-findings-register.md

# Or pipe in
cat finding.md | python3 scripts/validate-finding.py --stdin
```

Checks every `### FINDING-` block for:

- All 19 required fields present (Severity, Status, Category, OWASP Mapping, CWE, Affected Component, Tenant/Data Boundary, Evidence, observation, vulnerability, attack path, business + tenant impact, reproduction, smallest fix, tests, regression risk, owner, priority).
- Severity ∈ {Critical, High, Medium, Low, Info}.
- Status ∈ {CONFIRMED, LIKELY, STATIC-ONLY, NEEDS-RUNTIME-TEST, BLOCKED}.
- At least one Evidence subfield (File / Function/Class / Route/API / Config / Test).
- File evidence includes a line number.
- No invalid evidence phrases ("looks okay", "appears secure", "framework should handle this", etc.).

Tolerates both `- Severity: High` and `- **Severity:** High` markdown styles.
Exits 1 on any violation; suitable for CI gates.

### `aggregate-counts.py` — generate counts tables

```bash
# Single file
python3 scripts/aggregate-counts.py path/to/14-findings-register.md

# Whole review dir
python3 scripts/aggregate-counts.py path/to/security-review/
```

Emits Markdown tables ready to paste into the Aggregate Counts and Findings
By Category sections of `14-findings-register.md`. Counts severity, status,
and category per the controlled vocabularies.

### `scrub-check.py` — pre-publish secret scan

```bash
# Default secret patterns (JWTs, API keys, private keys)
python3 scripts/scrub-check.py path/to/security-review/

# With operator-supplied patterns (one regex per line, # for comments)
python3 scripts/scrub-check.py path/to/security-review/ --config my-patterns.txt
```

Scans for:

- JWT-shaped strings (`eyJ...` three-segment).
- Common API-key prefixes (`sk_live_`, `sk_test_`, `pk_*`, `ghp_`, `ghs_`, `gho_`, `AKIA`, `ASIA`, `AIza`, `xox[abps]-`).
- Private-key headers (`-----BEGIN ... PRIVATE KEY-----`).
- Private-key file references (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`).
- `PLACEHOLDER_*` literals are explicitly allowed (workspace-friendly convention).

Customer names, internal hostnames, and Jira project keys are operator-curated
via `--config <patterns-file>`. Exit 0 = clean, 1 = matches found.

### CI integration

Suggested CI gate to keep findings discipline mechanical:

```yaml
- name: Validate findings format
  run: python3 scripts/validate-finding.py docs/security-review/14-findings-register.md

- name: Scrub secrets before publish
  run: python3 scripts/scrub-check.py docs/security-review/ --config .scrub-patterns
```

All scripts target Python 3.10+ stdlib only (no `pip install` required).

## Compatibility

- **Claude Code** — primary target. Skills loaded via `~/.claude/skills/`.
- **Anthropic API / Agent SDK** — the skill is portable Markdown; load `SKILL.md` as a system-prompt fragment and reference checklists/templates by path.
- **Other CLI agents** (Copilot CLI, Codex, Gemini CLI) — content is platform-neutral; tool-name mapping is up to the host.

## Contributing

Issues and PRs welcome at [github.com/sevenbelowllc/sevenbelow-resources](https://github.com/sevenbelowllc/sevenbelow-resources).

When opening a PR:

- Keep the skill platform-neutral. No internal hostnames, customer names, or product-specific role IDs in checklists/templates.
- Add evidence for any new check ("how to verify this control").
- If you add a checklist category, add the corresponding test recommendations to `templates/test-plan-template.md`.

## License

See repository [LICENSE](../../../LICENSE).

## Credits

Authored by [SevenBelow](https://sevenbelow.com) for the [ComplyOS](https://complyos.app) compliance platform. Generalized for the broader Claude Code skills community.

If this skill saves your team a real audit — let us know. We learn from how it gets used in the wild.
