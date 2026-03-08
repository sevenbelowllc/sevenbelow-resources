# Claude Code Configuration

## Project Directory Enforcement (NON-NEGOTIABLE)

**Canonical project root:** `~/workdir/[admin-directory]/[YOUR-PROJECT]/`

ALL [YOUR PRODUCT]/Compliance OS repositories live under this directory. The full repo map:

| Repository | Path |
|------------|------|
| `[ORCHESTRATOR-REPO]` | `[YOUR-PROJECT]/[ORCHESTRATOR-REPO]/` |
| `compliance-core` | `[YOUR-PROJECT]/compliance-core/` |
| `compliance-ui` | `[YOUR-PROJECT]/compliance-ui/` |
| `compliance-os-goldmaster-prds` | `[YOUR-PROJECT]/compliance-os-goldmaster-prds/` |
| `[TERRAFORM-ROOT]` | `[YOUR-PROJECT]/[TERRAFORM-ROOT]/` |
| `[TERRAFORM-META]` | `[YOUR-PROJECT]/[TERRAFORM-META]/` |
| `compliance-tpis` | `[YOUR-PROJECT]/compliance-tpis/` |

**Rules:**
- **NEVER** `git clone` a repo outside of `[YOUR-PROJECT]/`
- **NEVER** create working copies, temp clones, or shallow clones elsewhere
- Before operating on any repo, verify the path starts with `~/workdir/[admin-directory]/[YOUR-PROJECT]/`
- If a repo is missing from the project directory, ask the user — do NOT clone it yourself to a different location

**Why:** A stray clone was created at `~/workdir/[admin-directory]/compliance-core/` (outside the project directory), diverged from the real repo, and caused confusion. This rule prevents that from happening again.

---

<!-- CARL-MANAGED: Do not remove this section -->
## CARL Integration

Follow all rules in <carl-rules> blocks from system-reminders.
These are dynamically injected based on context and MUST be obeyed.
<!-- END CARL-MANAGED -->

---

## Security Standards Adherence (NON-NEGOTIABLE)

**NEVER invent security parameters.** All security decisions (rate limits, thresholds, firewall rules, header values, encryption settings, access controls) MUST cite one of:
- **OWASP** — Top 10, ASVS, API Security Top 10, Testing Guide
- **NIST** — SP 800-53, SP 800-63, SP 800-123, CSF
- **CIS Benchmarks** — GKE v1.4, GCP v1.3, or relevant platform benchmark

If no standard covers the specific parameter, research industry practice from major providers (Cloudflare, AWS, GCP Cloud Armor) BEFORE proposing values. State the source.

**Why:** Security parameters fabricated without standards reference led to proposing invalid rate limits during Phase 31 planning (2026-02-14). This rule prevents that from happening again.

---

## Secret Values Ban (NON-NEGOTIABLE)

**NEVER write real secret values into ANY file — not code, not .env.example, not runbooks, not planning docs, not MEMORY.md, not CLAUDE.md, NOWHERE.**

This includes but is not limited to:
- API keys (Clerk `sk_test_*`/`pk_test_*`, Stripe `sk_*`/`pk_*`, Vercel tokens, OneSignal keys)
- Webhook signing secrets (`whsec_*`)
- Database passwords
- OAuth client secrets
- Any value that grants access to a service

**What to write instead:**
- In `.env.example` files: `sk_test_REPLACE_ME`, `pk_test_REPLACE_ME`, `whsec_REPLACE_ME`
- In source code: `process.env.VARIABLE_NAME` — NEVER hardcode
- In runbooks/docs: "Get from [Dashboard Name] > [Path]" or "Stored in GCP Secret Manager as `secret-name`"
- In MEMORY.md: Only the `gcloud` command path, NEVER the actual value

**Enforcement:** All repos have gitleaks pre-commit hooks. If gitleaks blocks your commit, the secret MUST be removed — do NOT bypass the hook.

**Why:** Real Clerk secret keys, Stripe keys, and Vercel tokens were committed to `.env.example` files and hardcoded in source code (2026-02-15). They ended up in git history and required emergency rotation. This rule prevents that from happening again.
