# Claude Operating Contract — [YOUR PRODUCT NAME] (Gold Master)

## Role Definition

You are operating inside the **Gold Master PRD repository** for [YOUR PRODUCT NAME].

Your responsibility is to:
- Preserve governance integrity
- Prevent domain drift
- Enforce explicit decision-making
- Maintain audit defensibility

You are NOT here to optimize speed at the expense of correctness.

---

## Repo Roles (LOCKED)

| Repository | Role | Contents |
|------------|------|----------|
| **`compliance-os-goldmaster-prds`** | **AUTHORITY ONLY** | Normative docs, contracts, guard scripts |
| `[ORCHESTRATOR-REPO]` | ORCHESTRATION ONLY | .planning/, context packs, runbooks, handoffs |
| `compliance-core` | EXECUTION ONLY | Backend (Node.js, GraphQL, PostgreSQL) |
| `compliance-ui` | EXECUTION ONLY | Frontend (Next.js, React, TypeScript) |
| `compliance-tpis` | EXECUTION ONLY | Third-party integration microservice |
| `[TERRAFORM-META]` | INFRA (metadata) | Centralized Terraform metadata |
| `[TERRAFORM-ROOT]` | INFRA (execution) | Terraform root modules |

**This repo is AUTHORITY ONLY.** No application code, no planning state, no orchestration artifacts.

---

## Root Authority Order (LOCKED)

These documents form the constitutional authority chain. Read in order; earlier documents take precedence:

1. **`00-product-foundation/repo-layout-contract.md`** — Directory structure and repo boundary rules
2. **`00-product-foundation/Compliance_OS_Final_MVP_LOCK.md`** — Frozen MVP scope definition
3. **`00-product-foundation/vision-and-ethos.md`** — Product vision and guiding principles
4. **`03-governance/state-registry.md`** — Single source of truth for ALL lifecycle states

**If any document in this repo contradicts the Root Authority Order, the Root Authority Order wins.**

---

## Authoritative Documents (HARD)

The following documents override all others:

- `04-cross-domain-contracts/cross-domain-governance-contracts-index.md`
- `20-feature-prds/approval-workflows/feature.md`
- `20-feature-prds/approval-workflows/significant-change-policy.md`
- `02-design-system/design-system-enforcement.md`
- `02-design-system/tokens.md`

If your output conflicts with these, your output is wrong.

---

## Domain Separation Rules (NON-NEGOTIABLE)

You MUST treat these as separate concerns:

- Vendor qualification ≠ vendor approval
- Vendor approval ≠ risk acceptance
- Contract approval ≠ vendor qualification
- Risk existence ≠ mitigation
- Approval ≠ domain ownership

No inference is allowed.

---

## Risk Handling Rules

- Risks are explicit
- Risks are intentional
- Risks are never implicit
- Absence of a Risk ≠ acceptance

Customer choice is authoritative.

---

## Approval Rules

Approvals:
- Are explicit approval decisions across domains
- Document Approvals are automatically triggered only by Document Significant Change
- Do not mutate domain content
- Do not infer outcomes
- Are immutable once decided

---

## Cross-Domain Behavior

Cross-domain rules live ONLY in:
- `04-cross-domain-contracts/`

Authoritative entrypoint:
- `04-cross-domain-contracts/cross-domain-governance-contracts-index.md`

Validation only (NOT a spec):
- `04-cross-domain-contracts/cross-domain-audit.md`

If behavior spans multiple domains:
1. Check Cross-Domain Contracts
2. Then Core Domain PRDs
3. Then Feature PRDs

Never reverse this order.

---

## Output Requirements (HARD)

Every response that proposes, modifies, or replaces files MUST include:

Target Path: `<relative/path/from/repo/root>`

No Target Path = invalid output.

You MUST:
- Respect canonical repo layout
- Reference governing contracts
- Avoid creating or renaming directories

If unsure:
- Ask questions
- Do NOT proceed

---

## Design Authority

- `02-design-system/design-system-enforcement.md` is authoritative
- `02-design-system/tokens.md` is the bridge artifact
- Figma tokens/components are the source of truth until code cutover
- You MUST NOT reinterpret brand intent

### Figma AI Source (Historical Reference)

**Original Source Path:**
```
~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source
```

~299 React/TypeScript prototype components. Migration to production repos is ~95% complete (2026-02-07). Remaining unmigrated: File upload components (3) — explicitly deferred.

**DO NOT use as source for new work.** Production repos (`compliance-ui`, `compliance-core`) are now authoritative for implementation. Figma source is reference only for visual design intent verification.

**DO NOT use any other source directory** (working-compliance-os, feature-figma-dashboard-*, drift-backup-*, etc.)

### Design System Enforcement

Mandatory rules (enforced in execution repos):
- All state-mutating actions use `action.primary.gradient`
- Toggles use `toggle.active.brand`
- Status colors follow the global status table
- Icons must be `lucide-react` only
- No inline hard-coded colors

---

## No Mock Data Policy (NON-NEGOTIABLE)

**NEVER use inline mock data arrays in components.**

### Forbidden Patterns

```typescript
// NEVER DO THIS
const mockUsers = [{ id: '1', name: 'Test User' }];
const [items, setItems] = useState([{ id: '1', title: 'Fake' }]);
const MOCK_DATA = [...];
const sampleData = [...];
```

### Required Pattern

```typescript
// ALWAYS use GraphQL hooks
import { useUsers } from '../api/hooks';
const { users, loading, error } = useUsers();
```

### If Data Is Needed For Development

**Create seed data in the database:**
1. Add to `compliance-core/src/db/seeds/`
2. Run `npm run seed`
3. Components fetch real data via GraphQL

### Why

- Mock data rots and hides integration bugs
- Empty states and loading states must work correctly
- Seed data is the single source of truth

**This rule applies to ALL components, pages, and features.**

---

## Modification Rules

- **Default mode: READ-ONLY.** Do not modify documents unless explicitly instructed by the project owner.
- **Material changes** to authority documents require the significant change process defined in `20-feature-prds/approval-workflows/significant-change-policy.md`.
- **New documents** must follow templates in `99-templates/` and include the `## AUTHORITY BOUNDARY (MANDATORY)` banner.
- **Deletions** are never performed. Deprecated documents are marked as such, not removed.

---

## Secret Values Ban (NON-NEGOTIABLE)

**NEVER write real secret values into ANY file — not code, not .env.example, not runbooks, not planning docs, not MEMORY.md, NOWHERE.** Use `REPLACE_ME` placeholders in examples, `process.env.*` in code. All secrets live in GCP Secret Manager ONLY. gitleaks pre-commit hooks enforce this.

---

## Behavior Rules

You MUST NOT:
- Optimize around governance contracts
- Merge domain responsibilities
- Invent missing rules
- Patch inconsistencies locally
- Modify files in other repositories

If ambiguity exists:
- STOP
- Cite the conflict
- Ask clarifying questions

---

## Enforcement Mindset

When in doubt:
- Be strict
- Be explicit
- Be auditable

Silence is failure.
