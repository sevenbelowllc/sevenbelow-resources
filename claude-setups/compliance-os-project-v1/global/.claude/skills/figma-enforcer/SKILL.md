---
name: figma-enforcer
description: "MANDATORY Figma AI source enforcement for ALL UI work. Auto-activates when creating, modifying, or planning ANY compliance-ui component, page, or modal. Forces Figma source read BEFORE any code changes. Prevents layout invention."
---

# Figma AI Source Enforcer (NON-NEGOTIABLE)

**This skill is MANDATORY for ALL UI work. No exceptions.**

## When to Activate (AUTO — do not wait for user to invoke)

- Creating any new UI component
- Modifying any existing UI component in `compliance-ui/`
- Planning any phase that touches UI (GSD plan-phase, discuss-phase, research-phase)
- Reviewing UI work (verify-work, audit)
- Any time a user shows a screenshot and says "this doesn't match Figma"
- Any time the word "modal", "dashboard", "page", "layout", "component" appears in UI context

## When NOT to Activate

- Pure backend work (compliance-core GraphQL, migrations, services)
- Infrastructure (Terraform, GKE, Buildkite)
- Planning/orchestration docs with no UI deliverables

---

## PROTOCOL (Execute These Steps IN ORDER)

### Step 1: Identify the Figma AI Source File

**Figma AI source root:**
```
~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source/src/components/
```

Map the production component to its Figma equivalent:

| Production Feature Directory | Figma Source Directory |
|------------------------------|----------------------|
| `features/activities/` | `activityRuns/` |
| `features/audit-portal/` | `auditPortal/` |
| `features/audits/` | `audits/` |
| `features/controls/` | `controls/` |
| `features/dashboard/` | `dashboard/` |
| `features/documents/` | `documents/` |
| `features/evidence/` | `evidence/` |
| `features/frameworks/` | `frameworks/` |
| `features/risks/` | `risks/` |
| `features/settings/` | `settings/` |
| `features/vendors/` | `vendors/` |
| `features/contracts/` | `contracts/` |
| `components/layout/` | `layout/` |
| `components/ui/` | `ui/` |

If unsure of the mapping, run:
```bash
ls ~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source/src/components/
```

Also check for Figma types:
```
~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source/src/lib/types/
```

And Figma utilities:
```
~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source/src/lib/utils/
```

### Step 2: Read the Figma AI Source File (MANDATORY)

**You MUST read the Figma source file BEFORE writing or modifying any production code.**

Read the FULL file. Do not skim. Do not skip. Extract:

1. **Component interface/props** — what data does Figma expect?
2. **Layout structure** — sections top-to-bottom, grid columns, sidebar vs main
3. **Visual elements** — gradients, icons, badges, colors, spacing
4. **Interactions** — onClick handlers, state changes, navigation callbacks
5. **Conditional rendering** — what shows/hides based on state
6. **Helper functions** — imported utilities that transform data

### Step 3: Read the Production File

Now read the production equivalent. Compare against Step 2.

### Step 4: Produce Gap List (BEFORE Writing Code)

Before touching any code, produce a gap list in this format:

```
## Figma vs Production Gaps: [ComponentName]

### Layout
- [ ] GAP: [description] (Figma line X vs Production line Y)

### Fields/Props
- [ ] GAP: [description]

### Visual
- [ ] GAP: [description]

### Interactions
- [ ] GAP: [description]

### Data Types
- [ ] GAP: [description]
```

### Step 5: Fix Production to Match Figma

Now — and ONLY now — modify the production code to close each gap.

**Rules:**
- **Figma is the visual authority.** Match the layout, sections, field order, colors, gradients.
- **Production hooks are the data authority.** Use production GraphQL hooks, NOT Figma helper functions.
- **If Figma uses a helper that doesn't exist in production**, implement the equivalent logic inline or create a helper in the production feature directory.
- **If Figma has fields/types not in production**, flag this as a backend gap — do NOT silently drop fields.
- **NEVER invent a layout, modal, or visual pattern that differs from Figma.**

---

## BANNED Behaviors

1. **BANNED:** Modifying a UI component without first reading its Figma source
2. **BANNED:** Saying "I'll check Figma later" or "Let me skip Figma for now"
3. **BANNED:** Using a screenshot as a substitute for reading the actual Figma source file
4. **BANNED:** Inventing layouts, field orders, or visual patterns not in Figma
5. **BANNED:** Assuming production is correct when it differs from Figma
6. **BANNED:** Planning UI work without citing specific Figma source file paths
7. **BANNED:** Marking UI work as complete without verifying Figma alignment

---

## For GSD Agents (Research, Plan, Execute)

### Research Agents
When researching a phase that includes UI work:
- List ALL Figma source files relevant to the phase
- Read each one and document the intended layout
- Note gaps between Figma and production in RESEARCH.md

### Plan Agents
When planning UI tasks:
- Each task MUST reference the specific Figma source file path
- Each task description MUST include "Match Figma layout from [path]"
- Plans without Figma references for UI tasks are INVALID

### Execute Agents
When executing UI tasks:
- Read Figma source file FIRST (Step 2) before any code changes
- Produce gap list (Step 4) in the commit message or summary
- Verify final output matches Figma layout

---

## Quick Reference: Figma Source Paths

```
FIGMA_ROOT="~/workdir/[admin-directory]/[YOUR-PROJECT]/compliance-os-goldmaster-prds/02-design-system/figma-ai-source"

# Components
$FIGMA_ROOT/src/components/activityRuns/
$FIGMA_ROOT/src/components/auditPortal/
$FIGMA_ROOT/src/components/audits/
$FIGMA_ROOT/src/components/contracts/
$FIGMA_ROOT/src/components/controls/
$FIGMA_ROOT/src/components/dashboard/
$FIGMA_ROOT/src/components/documents/
$FIGMA_ROOT/src/components/evidence/
$FIGMA_ROOT/src/components/frameworks/
$FIGMA_ROOT/src/components/risks/
$FIGMA_ROOT/src/components/settings/
$FIGMA_ROOT/src/components/vendors/

# Types
$FIGMA_ROOT/src/lib/types/

# Utilities
$FIGMA_ROOT/src/lib/utils/
```

---

## Enforcement Verification

After any UI work session, verify:

```bash
# Check: did I read the Figma source?
# Check: does production layout match Figma sections top-to-bottom?
# Check: are all Figma fields present in production (or flagged as backend gaps)?
# Check: do gradients, colors, icons match Figma?
```

If ANY check fails, the work is NOT complete.

---

## Why This Exists

The user has repeatedly had to provide screenshots and say "this doesn't match Figma" because agents:
1. Skip reading Figma source files
2. Assume production is correct
3. Invent layouts instead of matching the design
4. Mark work as complete without visual verification

**This is the fix. Follow the protocol. No shortcuts.**
