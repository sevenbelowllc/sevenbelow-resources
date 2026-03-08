# EXECUTION ONLY (LOCKED) — COMPLIANCE CORE (BACKEND)

This repository is **execution-only** for the Compliance OS backend (Core API/service).

## Allowed Content
- Backend source code (API, services, domain logic)
- Tests (unit/integration), fixtures/mocks
- DB migrations / seeds (if applicable)
- Build tooling required to build/test/deploy the backend (package manifests, CI config)
- Backend implementation notes directly tied to code changes

## Forbidden Content
- **Authority** documents (PRDs, contracts, scope locks, governance rules)
- **Orchestration** content (planning, runbooks, context packs, task trackers, agent reset guides)
- Cross-repo “control plane” logic or planning state (no `.planning/` here)

## Boundaries
- **Authority lives here:** `compliance-os-goldmaster-prds`
  - Root Authority Order (LOCKED):
    1. `00-product-foundation/repo-layout-contract.md`
    2. `00-product-foundation/Compliance_OS_Final_MVP_LOCK.md`
    3. `00-product-foundation/vision-and-ethos.md`
    4. `03-governance/state-registry.md`
- **Orchestration lives here:** `[ORCHESTRATOR-REPO]`
  - Handoffs, workstreams, runbooks, context packs, `.planning/`

## Operating Rules
- Do not write outside this repo.
- Do not modify authority docs unless explicitly instructed and done in the authority repo.
- Backend implementation must conform to authority docs; if conflict is discovered, stop and escalate via orchestrator.

## Entry Point
Backend work must start from an approved handoff in:
`[ORCHESTRATOR-REPO]/handoffs/core/`