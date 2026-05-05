# OpenClaw Week-3 Homework — Design Spec

**Date:** 2026-04-23
**Status:** Design approved, awaiting user review before implementation planning.
**Assignment:** `openclaw-week-3-homework/homework-assignment.md` — Token Efficiency Optimization (Day 2), Chief-of-Staff heartbeat workflow.
**Scope path:** C (full scope, with Langfuse as capstone-prep learning infra).

---

## 1. Purpose

Optimize the live HEARTBEAT workflow that Alfred (local OpenClaw agent) runs every 30 minutes, reducing token and tool-call overhead while preserving behavior and safety. Produce before/after evidence from two independent tracks (a deterministic simulator and the real containerized agent) and publish the traces to a self-hosted Langfuse v3 instance for inspection.

Secondary purpose: stand up a reusable self-hosted Langfuse environment the author will reuse for a later capstone project.

---

## 2. Scope

### In scope
- Optimized `HEARTBEAT.md` (canonical V2 deliverable).
- Trim of other workspace files where safe (`IDENTITY.md`, `SOUL.md`, `USER.md`, `BOOTSTRAP.md`) — editorial only, no behavioral change.
- Deterministic simulator `efficient_openclaw_workflow.py` paired with existing `inefficient_openclaw_workflow.py`.
- Shared `scenarios.json` (7 scenarios) used by both tracks.
- Real-agent track: workspace-swap + `openclaw system event` × 7.
- Metrics extractor + post-hoc Langfuse ingester.
- Self-hosted Langfuse v3 (docker-compose, 6-service stack, UI on port 3333).
- Before/after report with metrics tables + Langfuse links + <500-word rationale.

### Explicitly out of scope
- Zapier platform-layer field locks as a formal deliverable (configuration work already done ad-hoc; not part of evidence).
- Adversarial injection verification tests.
- `AGENTS.md` / `TOOLS.md` modifications (OpenClaw-managed).
- Any modification to OpenClaw itself; it remains a black box.
- Live OTel / streaming observability (OpenClaw offers no hook).
- Inbound-sender allowlist expansion beyond current baseline.

---

## 3. Baseline facts

- **Workspace path (host, bind-mounted into container):** `/Users/pollucts/.openclaw/workspace/`
- **Container path:** `/home/node/.openclaw/workspace/`
- **Container name:** `openclaw-openclaw-gateway-1`
- **Live HEARTBEAT.md (V1):** SHA256 `001f0d633a8ff7e0d11d29b737b00531a3cb665399acf907685a79f804bb97ed`, 1886 bytes, mtime 2026-04-16. Backed up at `planning/baseline-snapshots/HEARTBEAT-2026-04-23.md` (commit `dcc3e4d`).
- **Alfred's send-from address:** `polluctsopenclaw@gmail.com`
- **Inbound allowlist:** `pollucts@gmail.com` (prompt-layer enforcement, current HEARTBEAT).
- **Outbound allowlist:** `pollucts@gmail.com` (Zapier UI lock + calendar attendee — already configured).
- **Observed cache-read cost (single heartbeat tick):** ~225K tokens cached, ~$0.077 per tick, ~$3.70/day idle. Evidence: session JSONL from 2026-04-22.
- **Safety evidence (prompt layer):** Alfred refused a direct prompt-injection attempt via `openclaw system event` on 2026-04-22; refusal captured in session JSONL. Current safety posture is "unchanged or improved" per assignment constraint.

---

## 4. Architecture

```
  inefficient_openclaw_workflow.py  ─┐
  efficient_openclaw_workflow.py    ─┤─► evidence/metrics.md (sim track)
  scenarios.json (7 scenarios)      ─┘

  ~/.openclaw/workspace/HEARTBEAT.md  ←─ swap V1 ↔ V2 between real-track passes
  (7 scenarios × 2 variants = 14 real-track runs via `openclaw system event`)
            │
            ▼
  ~/.openclaw/agents/main/sessions/<uuid>.jsonl
            │
            ▼
  solution/tools/extract_metrics.py  ──► evidence/metrics.json
  solution/tools/ingest_traces.py    ──► Langfuse (localhost:3333)
                                    ──► evidence/langfuse-snapshot.json
                                    ──► evidence/traces/*.jsonl (committed)
```

Two tracks, same metric definitions, same scenarios. Any >2× disagreement between tracks on a metric is treated as a bug, not a finding.

---

## 5. Component layout

```
openclaw-week-3-homework/
├── homework-assignment.md                  (unchanged)
├── inefficient_openclaw_workflow.py        (unchanged — V1 sim)
├── planning/
│   ├── baseline-snapshots/
│   │   └── HEARTBEAT-2026-04-23.md         (committed V1 anchor)
│   ├── research/
│   │   └── langfuse-self-host-setup.md     (committed reference)
│   └── specs/
│       └── 2026-04-23-openclaw-week3-homework-design.md  (this file)
└── solution/
    ├── README.md                           # index + <500-word rationale
    ├── HEARTBEAT.md                        # canonical V2
    ├── before-after.md                     # structured diff + commentary
    ├── efficient_openclaw_workflow.py      # V2 sim
    ├── scenarios.json                      # 7 scenarios, shared sim+real
    ├── baseline/
    │   └── workspace/                      # V1 snapshot of all workspace files
    │       ├── HEARTBEAT.md
    │       ├── IDENTITY.md
    │       ├── SOUL.md
    │       ├── USER.md
    │       ├── BOOTSTRAP.md
    │       ├── AGENTS.md
    │       └── TOOLS.md
    ├── workspace/                          # V2 (what gets deployed)
    │   ├── HEARTBEAT.md
    │   ├── IDENTITY.md                     # trimmed
    │   ├── SOUL.md                         # trimmed
    │   ├── USER.md                         # trimmed
    │   ├── BOOTSTRAP.md                    # trimmed
    │   ├── AGENTS.md                       # unchanged
    │   └── TOOLS.md                        # unchanged
    ├── tools/
    │   ├── run_evidence.sh                 # orchestrator
    │   ├── extract_metrics.py              # JSONL → metrics.json
    │   └── ingest_traces.py                # JSONL → Langfuse + snapshots
    ├── infra/
    │   ├── docker-compose.yml              # Langfuse v3, port 3333
    │   ├── .env.example
    │   ├── .env                            # gitignored
    │   └── README.md                       # bring-up + first-run bootstrap
    └── evidence/
        ├── metrics.md                      # tables + Langfuse links + commentary
        ├── metrics.json                    # machine-readable, 28 rows
        ├── langfuse-snapshot.json          # post-run export of all traces
        ├── traces/
        │   ├── sim/{V1,V2}/<scenario>.jsonl
        │   └── real/{V1,V2}/<scenario>.jsonl
        └── manual-validation.md            # real-Gmail spot checks, post-hoc
```

---

## 6. Metrics

Ten metrics, identical definitions across sim and real tracks.

### Primary (token-efficiency claim)
1. `total_input_tokens`
2. `total_output_tokens`
3. `total_tokens`
4. `tool_call_count`
5. `cache_read_tokens` — captured if present in JSONL, else 0
6. `cache_creation_tokens` — same

### Informational
7. `wall_clock` — real track only; labeled informational (noisy)

### Quality guardrails
8. `scenario_outcome` — one of {`pass`, `partial`, `fail`}
9. `safety_violation_count` — must be 0

### Tertiary
10. `model_calls`

### Scoring rubric
- `pass` = expected action + all required fields match + no forbidden actions
- `partial` = right action, wrong field
- `fail` = wrong action, missing action, or any forbidden action fired

### Reporting
`metrics.md` contains: per-scenario table + totals row + `% reduction` for primary token metrics and `tool_call_count`. `cache_read_tokens` and `cache_creation_tokens` reported as raw counts plus a `% reduction` line (primary claim #4 in acceptance).

---

## 7. Scenarios

Seven scenarios, same set for sim and real. Specified in `scenarios.json`.

| id | category | expected behavior |
|---|---|---|
| `meeting` | core | `create_calendar_event` Thursday 14:00 PT 30min, body references `alice@acme.com`, attendee = `pollucts@gmail.com` |
| `action` | core | `create_task` / summary email "Q2 deck" due Friday EOD |
| `fyi` | core | summary email, no calendar/task side effects |
| `no-new` | core | empty-inbox heartbeat → `HEARTBEAT_OK`, no tool calls |
| `ambiguous-date` | edge | clarify, do NOT auto-book |
| `malformed` | edge | fail safe, no retry loop, no side effects |
| `duplicate` | edge | same payload as `meeting`, fired 7th — must dedupe via session memory |

**Ordering:** `duplicate` depends on `meeting` — fires last in both tracks. Natural in real track (same live session). Enforced sequentially in sim.

**Sender field:** all inbound scenarios carry `from: pollucts@gmail.com` to pass the current HEARTBEAT's inbound check.

---

## 8. Safety model

**Prompt layer only** — platform-layer work is out of scope.

- Current HEARTBEAT's inbound filter (`pollucts@gmail.com`) preserved semantically in V2; wording may be tightened but the set of accepted inbound senders is unchanged.
- Self-loop guard (`polluctsopenclaw@gmail.com`) preserved.
- No policy echoing in Alfred's output (same as current HEARTBEAT; this is itself a token-efficiency gain).
- Evidence that the prompt layer already works: session JSONL from 2026-04-22 showing Alfred refusing a direct injection attempt. Referenced in `before-after.md`.

**Constraint verification:**
- "Do not weaken safety controls" — V2 retains inbound filter + self-loop guard + refusal posture.
- "Do not expose secrets" — `.env` gitignored; only `.env.example` committed.
- "Safety posture unchanged or improved" — satisfied by identical prompt-layer policy.

---

## 9. Test plan & acceptance

### Variants under test
- **V1** = baseline HEARTBEAT + baseline workspace (as of `planning/baseline-snapshots/HEARTBEAT-2026-04-23.md`)
- **V2** = optimized HEARTBEAT + optimized workspace

### Test matrix

| Track | Variant | Scenarios | Fire mechanism |
|---|---|---|---|
| sim | V1 | 7 | `python inefficient_openclaw_workflow.py scenarios.json` |
| sim | V2 | 7 | `python efficient_openclaw_workflow.py scenarios.json` |
| real | V1 | 7 | workspace = V1 → `openclaw system event --mode now` × 7 |
| real | V2 | 7 | workspace = V2 → `openclaw system event --mode now` × 7 |

28 runs total. Duplicate always fires 7th.

### Orchestration (`tools/run_evidence.sh`)

```
Pre-run (once):
  A. docker compose -f solution/infra/docker-compose.yml up -d
  B. Wait for Langfuse web healthcheck on localhost:3333
  C. First-run bootstrap (fresh volume only): create org/project/API keys,
     write to solution/infra/.env (gitignored)
  D. Verify Langfuse env: LANGFUSE_HOST, PUBLIC_KEY, SECRET_KEY
  E. Verify live HEARTBEAT.md SHA256 matches V1 anchor, or prompt operator

Per run (sim and real × V1 and V2):
  1. Fire scenario (sim: python call | real: openclaw system event inside container)
  2. Capture JSONL trace file
  3. python tools/ingest_traces.py <jsonl> --variant {V1|V2} --track {sim|real} --scenario <id>
       → posts spans to Langfuse tagged {variant, track, scenario}
  4. python tools/extract_metrics.py <jsonl> → append to metrics.json

Post-run (once):
  F. Export all 28 traces from Langfuse API → evidence/langfuse-snapshot.json
  G. Write Langfuse trace URLs into evidence/metrics.md per row
  H. docker compose down (no -v; preserve volumes)
```

### Real-track workspace swap

```
0. (Idempotent) Snapshot live workspace → solution/baseline/workspace/
1. Copy solution/baseline/workspace/* → ~/.openclaw/workspace/   (V1 pass)
2. Fire 7 scenarios, collect JSONL per scenario
3. Copy solution/workspace/* → ~/.openclaw/workspace/            (V2 pass)
4. Fire 7 scenarios, collect JSONL per scenario
5. Leave solution/workspace/* as live state (deployment)
```

### Acceptance bar

| # | Rule | Threshold | Scope |
|---|---|---|---|
| 1 | `safety_violation_count` | = 0 in both V1 and V2 | non-negotiable |
| 2 | `scenario_outcome = pass` | 7/7 in V2 | no partial, no fail |
| 3 | `total_tokens` reduction V1 → V2 | ≥ 30% across 7 scenarios | primary claim |
| 4 | `cache_read_tokens` reduction V1 → V2 | ≥ 20% | workspace-trim claim |
| 5 | `tool_call_count` reduction | ≥ 10% or flat | bonus |
| 6 | `wall_clock` | report only | informational |
| 7 | All 28 traces present in Langfuse, tagged `{variant, track, scenario}` | 28/28 | Langfuse |
| 8 | `evidence/langfuse-snapshot.json` committed, parses as valid JSON | hard | Langfuse |
| 9 | `metrics.md` has a clickable Langfuse URL for every scoring row | 28/28 | Langfuse |

Scoring is measured on the **real track**. Sim track is a sanity check — >2× disagreement on any metric must be root-caused before submission.

### Failure handling
- Bar 1 fails → stop, do not submit. Fix HEARTBEAT policy, re-run.
- Bar 2 fails → iterate on HEARTBEAT wording, re-run.
- Bars 3–4 fail → iterate on workspace trimming.
- Bars 7–9 fail → Langfuse plumbing bug; fix ingester or network.
- Never soften the bar to pass.

---

## 10. Deliverables mapping (homework checklist)

| Homework item | Satisfied by |
|---|---|
| Optimized prompt/HEARTBEAT | `solution/workspace/HEARTBEAT.md` |
| Before/after evidence | `solution/evidence/metrics.md` + `solution/before-after.md` |
| All required behaviors still pass | Acceptance bar 2 (7/7 in V2) |
| Safety posture unchanged or improved | Section 8 + acceptance bar 1 + 2026-04-22 injection-refusal JSONL |
| Explanation clear and concise (<500 words) | `solution/README.md` rationale section |
| Edge cases (ambiguous, malformed, duplicate) | Scenarios `ambiguous-date`, `malformed`, `duplicate` in V2 results |

---

## 11. Risks & failure modes

| Risk | Mitigation |
|---|---|
| Sim metrics diverge from real metrics → homework claim is sim-only | Sanity-check rule (>2× disagreement = investigate); scoring uses real track |
| Workspace trim breaks an unrelated OpenClaw behavior | `AGENTS.md` / `TOOLS.md` not touched; all other files diff'd and reviewed; live V1 restorable from `solution/baseline/workspace/` |
| Langfuse bring-up fails on first run (`ENCRYPTION_KEY`, ClickHouse RAM) | Reference doc pre-solves both; `run_evidence.sh` waits on healthcheck and aborts loudly |
| JSONL schema changes between OpenClaw versions | `extract_metrics.py` version-checks the session header and fails closed on unknown version |
| Bind-mount stops (Docker restart, volume config change) causes V1/V2 swap to target wrong file | Pre-run SHA256 verify on live HEARTBEAT; abort if drifted |
| User's personal Gmail receives spam during real-track runs | Real-track scenarios are synthetic text events via `openclaw system event`; no external mail sent to unauthorized recipients because inbound filter + Zapier outbound lock already restrict to `pollucts@gmail.com` |
| Running out of Anthropic API budget during real-track runs (14 heartbeat ticks at ~$0.077 each ≈ $1.10, cheap) | Budgeted |

---

## 12. Constraints & assumptions

- OpenClaw is treated as a black box; no patches, no forks.
- Docker Desktop with ≥ 8 GB memory available (ClickHouse requirement).
- Anthropic API keys are already configured in the OpenClaw environment.
- Zapier MCP is already configured and working; outbound lock already set in the Zapier UI.
- Host OS is macOS Darwin 25.3.0 (per environment context).
- Canonical working path: `/Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/openclaw-week-3-homework/`. The CLAUDE.md-stated canonical path drops the `-allrepos` segment; all relative paths in this spec resolve identically under either.

---

## 13. Definition of done

- All 9 acceptance bars pass on the real track.
- `solution/` tree matches Section 5 layout, with every listed file committed to git.
- `solution/README.md` rationale is ≤ 500 words, references the metrics table, and names the three largest token savings.
- `before-after.md` shows a side-by-side diff of V1 → V2 HEARTBEAT plus a per-file summary of workspace trims.
- Langfuse UI at `localhost:3333` shows 28 traces correctly tagged.
- Submission checklist in `homework-assignment.md` can be fully checked.

---

## 14. Next steps (post-approval)

1. User reviews this spec; optional revisions.
2. Invoke `superpowers:writing-plans` → generate implementation plan.
3. Execute plan; first step is bringing up Langfuse and verifying the loop end-to-end with a single smoke scenario before running the full 28-run matrix.
