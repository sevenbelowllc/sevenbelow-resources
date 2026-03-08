# Claude Operating Contract — compliance-ui

## Repo Role

This is an **EXECUTION ONLY** repository. It contains the [YOUR PRODUCT NAME] frontend application. You write UI code here — components, hooks, pages, tests. Nothing else.

---

## Figma AI Source — MANDATORY Visual Reference (NON-NEGOTIABLE)

**Path:** `~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source/src/`

**When building or modifying any page/component, you MUST:**
1. FIRST read the corresponding Figma AI source file to understand the intended layout, fields, sections, and visual hierarchy
2. Match the Figma design — layout, component structure, field placement, visual patterns
3. Do NOT invent layouts, modals, or UI patterns that differ from Figma
4. If a Figma component exists for the page you're working on, your output MUST visually match it

**Figma AI source** = authoritative for visual design, layout, UX patterns, component structure.
**This repo (compliance-ui)** = authoritative for business logic, data wiring, GraphQL integration, state management.

**Why:** Production UI repeatedly diverged from Figma designs because agents ignored the reference files. Decision 194, `decisions/FIGMA_MANDATORY_REFERENCE.md`.

---

## Repo Roles (LOCKED)

| Repository | Role |
|------------|------|
| `compliance-os-goldmaster-prds` | AUTHORITY — normative docs, contracts, guard scripts |
| `[ORCHESTRATOR-REPO]` | ORCHESTRATION — .planning/, handoffs, runbooks, decisions |
| `compliance-core` | EXECUTION — backend code |
| **`compliance-ui`** | **EXECUTION — frontend code lives here** |
| `compliance-tpis` | EXECUTION — third-party integration microservice |
| `[TERRAFORM-MODULES]-*` | INFRA — Terraform modules |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 14.2 |
| Runtime | React | 18.3 |
| Language | TypeScript | 5.4 (strict mode) |
| Styling | Tailwind CSS | 3.4 |
| GraphQL Client | Apollo Client | 3.9 |
| Auth | Clerk | @clerk/nextjs 5.0 |
| Rich Text | TipTap | 3.17 |
| Icons | lucide-react | 0.400 |
| WebSocket | socket.io-client | 4.8 |
| Feature Flags | Harness | @harnessio/ff-react-client-sdk 2.4 |
| Push | OneSignal | react-onesignal 3.4 |
| Monitoring | Sentry | @sentry/nextjs 10.38 |
| Testing | Jest + React Testing Library | 29.7 / 15.0 |
| E2E Testing | Playwright | 1.40 |
| Dev Server | Turbopack | `next dev --turbo` |

---

## Project Structure

```
src/
  app/                    # Next.js App Router pages
    (auth)/               # Auth-protected routes (Clerk)
    (dashboard)/          # Dashboard routes (protected)
    api/                  # API routes (Next.js server functions)
    audit-portal/         # External auditor portal
    onboarding/           # Onboarding flows
    pricing/              # Pricing page
  components/             # SHARED UI components only
    ui/                   # Design system primitives (Button, Card, Modal, etc.)
    layout/               # Layout components (Header, Sidebar, etc.)
    shared/               # Shared components
    providers/            # Context providers
  features/               # ISOLATED feature domains
    activities/           # Activity runs
    admin/                # Admin panel
    approvals/            # Approval workflows
    audit-portal/         # Internal audit management
    audits/               # Audit domain
    comments/             # Comments/threads
    contracts/            # Contract management
    controls/             # Control management
    dashboard/            # Dashboard tabs
    documents/            # Document management
    evidence/             # Evidence domain
    excerpts/             # Excerpt management
    frameworks/           # Compliance frameworks
    notifications/        # Notification system
    onboarding/           # Onboarding wizard
    policies/             # Policy management
    reports/              # Reporting
    risks/                # Risk management
    search/               # Global search
    settings/             # Settings pages
    [admin-directory]/           # [YOUR PRODUCT] admin
    vendors/              # Vendor management
    workflows/            # Workflow configuration
  hooks/                  # SHARED hooks only (auth, data scoping)
  lib/                    # SHARED utilities
    types/                # Shared TypeScript types
    utils/                # Utility functions
  contexts/               # React contexts
```

---

## Path Alias

```typescript
import { something } from '@/components/ui/Button';
// resolves to ./src/components/ui/Button
```

---

## Key Patterns (ENFORCED)

### Feature-Based Isolation (NON-NEGOTIABLE)

```typescript
// CORRECT — import via public API
import { ApprovalActions } from '@/features/approvals';

// WRONG — never import internal files from other features
import { X } from '@/features/approvals/components/X';
```

Each feature directory has:
```
features/{domain}/
  components/     # Feature-specific UI
  hooks/          # Feature-specific hooks (GraphQL)
  types/          # Feature-specific types
  utils/          # Feature-specific utils
  index.ts        # PUBLIC API (only importable entry point)
```

### No Frontend State Machines
- Backend returns `allowedTransitions[]`
- Frontend renders buttons based on allowed transitions
- Frontend NEVER computes what transitions are valid

### No localStorage — DB-Backed Storage ONLY (NON-NEGOTIABLE)
- **localStorage is BANNED** for all data: business data, user preferences, feature interest, UI state — everything
- `use[YOUR PRODUCT]Auth` is the ONLY exception (dev mode only)
- All business data comes from GraphQL hooks backed by the database
- All user preferences and state MUST be stored in the database via GraphQL mutations
- All localStorage business hooks were removed in Phase 10
- **Why:** User decision 166 (2026-02-17). No client-only state that can't be synced across devices or audited.

### Activities Domain Model v2 (Decision 198 — NON-NEGOTIABLE)

- **Activity** = main entity (title, owner, due date, icon, color, key, department, steps, status)
- **Activity Type** = settings-managed dropdown category (just a name, NOT a rich template)
- Ships with "Activity Run" (recurring, SOP/WIS linked, has cadence) + "AdHoc/Custom" (one-off)
- **ONE Create Activity modal** — Activity Type dropdown conditionally shows/hides SOP picker + cadence fields
- System auto-creates next Activity Run on completion
- Notification at 50% of cadence interval before due (configurable per activity)
- Dashboard shows individual Activities with toggle to group by Activity Type
- **NO template→instance relationship** — there is no "Create Activity Type" creation flow
- Activity Type settings page = simple name list management (manage a dropdown)
- Document Review and Control Review are Approvals, NOT activity types

### Hook Mocking Pattern for Tests
- Mock hooks directly, not GraphQL MockedProvider
- Pattern: `jest.mock('@/features/{domain}/hooks')`

---

## Design System Rules (ENFORCED)

Authority: `[goldmaster-prds] 02-design-system/design-system-enforcement.md`
Tokens: `[goldmaster-prds] 02-design-system/tokens.md`

| Rule | Requirement |
|------|-------------|
| Action buttons | `action.primary.gradient` (pink-600 to purple-600) |
| Toggle active | `toggle.active.brand` (NOT action gradient) |
| Icons | `lucide-react` ONLY (no custom SVGs, no other icon libs) |
| Status colors | Per global status table in tokens.md |
| No hardcoded colors | Must use Tailwind token classes |
| Fonts | Inter (sans), JetBrains Mono (mono) |

### Tailwind Token Colors (from tailwind.config.ts)
- Brand: pink-500/600, purple-500/600 gradients
- Status: draft, in-review, approved, published, deprecated, rejected, returned, active, open, done
- Severity: critical, high, medium, low
- Document types: SOP=cyan, POL=purple, WIS=slate, FOR=blue

---

## Authority References

When implementing features, these documents in `compliance-os-goldmaster-prds` are authoritative:

| Document | Path (relative to goldmaster-prds) |
|----------|-----|
| Design System Enforcement | `02-design-system/design-system-enforcement.md` |
| Design Tokens | `02-design-system/tokens.md` |
| State Registry | `03-governance/state-registry.md` |
| Cross-Domain Contracts | `04-cross-domain-contracts/cross-domain-governance-contracts-index.md` |
| Approval Workflows | `20-feature-prds/approval-workflows/feature.md` |
| Significant Change Policy | `20-feature-prds/approval-workflows/significant-change-policy.md` |

**If your UI contradicts these specifications, your UI is wrong.**

---

## What You MUST NOT Do

- Write planning documents, roadmaps, or GSD state (belongs in orchestrator)
- Modify or create authority documents (belongs in goldmaster-prds)
- Write backend code (belongs in compliance-core)
- Write infrastructure code (belongs in terraform repos)
- Invent lifecycle states not in `state-registry.md`
- Compute state transitions in the frontend
- Use localStorage for business data
- Use icons other than lucide-react
- Hardcode colors (use Tailwind tokens)
- Import internal files from other feature directories
- Show document create/edit/approve/delete actions to auditor roles (Decision 167: both `EXTERNAL_AUDITOR` and `INTERNAL_AUDITOR` get read-only access to Controlled Documents; they CAN comment and create evidence requests)
- Write real secret values into ANY file (code, .env.example, docs). Use `REPLACE_ME` placeholders and `process.env.*` in code. All secrets live in GCP Secret Manager ONLY.

---

## Implementation Instructions

Implementation plans and handoff context come from:
```
[ORCHESTRATOR-REPO]/handoffs/ui/
```

If no handoff exists for your current task, ask the user for context or reference the orchestrator's `.planning/` state.

---

## Development

```bash
npm run dev          # Next.js dev server with Turbopack
npm run build        # Production build
npm run lint         # ESLint
npm test             # Jest unit tests
npm run test:e2e     # Playwright E2E tests
npm run check:no-mock  # Verify no mock data in production code
```

**Dev server:** http://localhost:3000
**Backend expects:** http://localhost:4000 (set via `NEXT_PUBLIC_API_URL`)

---

## Security Standards Adherence (NON-NEGOTIABLE)

Authority: `compliance-os-goldmaster-prds/00-product-foundation/security-standards-contract.md`
CARL domains: `security`

- NEVER invent security parameters. All values MUST cite OWASP/NIST/CIS.
- Security headers (CSP, HSTS, X-Frame-Options) MUST be configured in next.config.js.
- All API calls MUST include authentication tokens (Clerk JWT).
- No sensitive data in client-side storage (localStorage/sessionStorage).
- CSP must allow Next.js bundle scripts (use nonce or hash approach).

---

*This contract is loaded automatically by Claude Code. Follow it exactly.*
