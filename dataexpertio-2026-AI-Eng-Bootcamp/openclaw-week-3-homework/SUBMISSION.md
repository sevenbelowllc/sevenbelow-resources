# Week 3 Homework Submission — Token Efficiency Optimization

**Submitter:** David Kramer ([LinkedIn](https://www.linkedin.com/in/davidkramer13/), [SevenBelow](https://sevenbelow.com))
**Branch:** `feat/openclaw-week3-solution` (17 commits, clean working tree)
**Evidence track:** real (scored on live OpenClaw Alfred) + sim (deterministic, homework-designed baseline)

## TL;DR

- **Optimized HEARTBEAT + workspace deployed** (V2.1 after one iteration on real-track feedback): HEARTBEAT 1886 → 1817 bytes; total workspace 27,894 → 24,325 bytes (−12.8%).
- **7/7 scenarios pass on V1 and V2 real tracks; 0 safety violations on both variants, both tracks.**
- **Sim track:** 80.3% total-token reduction, 81.8% tool-call reduction.
- **Real track:** **V2 cheaper than V1 on all three cost metrics** — total_tokens −10.9%, tool_call_count −20.0%, cache_read_tokens −10.2%. The ≥30%/≥20% spec thresholds for bars 3/4 are not met because production Alfred is already ~11× tighter than the sim's inefficient baseline (V1 real 1,520 tok vs V1 sim 13,140 tok) and cache_read is dominated by OpenClaw framework + `AGENTS.md` (spec §2 out of scope). Direction is correct; headroom is bounded. Full analysis in `solution/evidence/metrics.md § Commentary`.

## Submission Checklist (from `homework-assignment.md`)

| # | Item | Satisfied by |
|---|---|---|
| 1 | Optimized prompt/HEARTBEAT included | [`solution/workspace/HEARTBEAT.md`](solution/workspace/HEARTBEAT.md) (deployed to `~/.openclaw/workspace/HEARTBEAT.md`) |
| 2 | Before/after evidence included | [`solution/before-after.md`](solution/before-after.md) (diff + predicate-preservation map), [`solution/evidence/metrics.md`](solution/evidence/metrics.md) (28-run scored table + Langfuse URLs), [`solution/evidence/metrics.json`](solution/evidence/metrics.json) (machine-readable), [`solution/evidence/langfuse-snapshot.json`](solution/evidence/langfuse-snapshot.json) (29 API records), [`solution/evidence/traces/`](solution/evidence/traces/) (28 raw trace JSONLs) |
| 3 | All required behaviors still pass | Real V2 **7/7 pass** (see `evidence/metrics.md` REAL table) |
| 4 | Safety posture unchanged or improved | 0 safety_violation_count on V1 and V2, both tracks. Inbound allowlist, self-loop guard, outbound recipient: preserved byte-for-byte — predicate-mapping table in `before-after.md § Preserved byte-for-byte semantics` |
| 5 | Explanation is clear and concise | [`solution/README.md`](solution/README.md) — 468-word rationale section; names three largest token savings + safety-preservation summary |

## Test Case Coverage

| Suggested test (assignment) | Scenario id in `scenarios.json` | Real V1 outcome | Real V2 outcome |
|---|---|---|---|
| Meeting request | `meeting` | pass | pass |
| Action item | `action` | pass | pass |
| FYI | `fyi` | pass | pass |
| No new email → `HEARTBEAT_OK` | `no-new` | pass | pass |
| **Edge: ambiguous date/time** | `ambiguous-date` | pass | pass (V2 explicitly replies asking for clarification) |
| **Edge: malformed/partial** | `malformed` | pass | pass (V2 sends safe FYI with "garbled content" flag) |
| **Edge: duplicate email** | `duplicate` | pass | pass (V2 detects and skips with "duplicate of prior tick") |

## What Changed in V2

| File | V1 → V2 | Change |
|---|---|---|
| `HEARTBEAT.md` | 1886 → 1817 bytes (−3.7%) | Emoji-headed routing rules (4 sections, 3 heading levels) collapsed to a 3-section decision flow: (1) edge-case screen (duplicate / ambiguous / malformed, zero tool calls), (2) intent routing (scheduling / action / FYI, one tool call), (3) tool discipline (one call per email, `followUpQuestion` is done, ≤1-sentence replies). Tool names, required fields, subject strings identical. Safety predicates preserved verbatim. |
| `SOUL.md` | 1747 → 1207 (−31%) | Removed italic framing and external `/concepts/soul` link. All Core Truths / Boundaries / Vibe / Continuity preserved verbatim. |
| `USER.md` | 2127 → 1458 (−31%) | 7-bullet credentials compressed to 2 lines. All other sections verbatim. |
| `BOOTSTRAP.md` | 1471 → 0 bytes (deleted) | File self-instructs deletion post-bootstrap. Alfred is months past first-run. |
| `IDENTITY.md` | 377 → 377 | Unchanged (too small to trim safely). |
| `AGENTS.md`, `TOOLS.md` | unchanged | OpenClaw-managed, spec §2 out of scope. |

## Constraints Respected

- **"Do not remove core functionality"** — all 7 scenarios (including the 3 required in the assignment) pass on V2 real. Tool names, subject strings, default meeting duration, attendee defaults, Google Meet inclusion, reminder schedule, memory key — all byte-for-byte preserved.
- **"Do not weaken safety controls"** — inbound allowlist (`pollucts@gmail.com`), self-loop guard (`polluctsopenclaw@gmail.com`), outbound recipient allowlist all preserved. V2 additionally strengthens three edge-case specifications by making them explicit rather than implicit. 0 safety violations measured across 28 runs.
- **"Do not expose secrets"** — `solution/infra/.env` gitignored; only `.env.example` committed. API keys never echoed in traces (verified in Langfuse UI).

## How to Reproduce

From `openclaw-week-3-homework/solution/`:

```bash
bash tools/run_evidence.sh
```

Brings up Langfuse (6-service Docker stack, 3333), creates MinIO bucket, runs sim V1 + sim V2 + real V1 + real V2 (reset session between V1/V2 to keep them apples-to-apples), extracts metrics into `evidence/metrics.json`, ingests traces into Langfuse tagged `{variant, track, scenario}`, and deploys V2 to `~/.openclaw/workspace/` at the end.

Unit tests (run from `openclaw-week-3-homework/`, not from `solution/`):

```bash
python3 -m pytest solution/tools/tests/ -v
```

5 tests, all pass: sim metric extraction, real-format metric extraction, safety-violation detection, V2 sim CLI contract, Langfuse ingester shape.

## Response to Grader Feedback

### "Output-length policy" — tested, V2.1 retained

Three iterations past V2.1 were run to test tighter output caps on email bodies (≤ 2 sentences for FYI, ≤ 2 sentences for Action, strict "one short sentence confirmation" after tool calls, explicit anti-retry language). Results (same 7-scenario real-track matrix, fresh session per variant):

| Variant | Real total_tokens | Tool calls | Real cache_read | Notes |
|---|--:|--:|--:|---|
| V1 baseline | 1,520 | 5 | 317,668 | |
| **V2.1 (submitted)** | **1,355** | **4** | **285,239** | All three fall V1→V2. 7/7 pass. |
| V2.2 (+output caps) | 1,463 | 4 | 292,270 | `fyi` Alfred interpreted "no action needed" sender note as permission to skip the FYI send — scenario regression. |
| V2.3 (V2.2 + "FYI always send" + "retry once on tool error") | 2,291 | 7 | 357,349 | "Retry once on error" bled into ambiguous-date / malformed (2 tool calls each) — aggregate regression. |
| V2.4 (V2.1 + body-length caps only) | 1,614 | 6 | 320,726 | "FYI = everything else" + body-cap wording pulled `duplicate` out of the edge-case screen — Alfred sent FYI for a duplicate. |

The V2.1 HEARTBEAT already carries `Reply to the user in ≤ 1 short sentence; tool side-effects speak for themselves` under tool discipline, which captures the spirit of the output-length policy without bleeding into the edge-case / duplicate detection rules. Tightening further invariably perturbed one of the edge cases on real track — the agent over-interprets the caps. V2.1 was restored as the final.

All four experiment traces are preserved in `sessions.archive-V2*` in the OpenClaw container if needed for audit.

### "Heartbeat isolation" — documented as infra-layer future work

`AGENTS.md` (out of scope per spec §2) does suggest this split explicitly: *"Use cron when: ... Task needs isolation from main session history ... You want a different model or thinking level for the task ... Output should deliver directly to a channel without main session involvement."* Moving the heartbeat from `openclaw system event` to an `openclaw cron` job with `--thinking off`, an isolated session id, and a constrained model (e.g. `claude-haiku-4-5`) would target `cache_read_tokens` directly by avoiding full-session hydration. Implementing this requires edits to `~/.openclaw/openclaw.json` (`agents.defaults.model`, scheduler config) rather than `HEARTBEAT.md`, so it's out of scope for a prompt-layer optimization homework.

### "Model / max_tokens" — documented as infra-layer future work

Same path as above. The OpenClaw agent defaults to `anthropic/claude-sonnet-4-6`. A heartbeat-specific override to a smaller model and a `max_tokens` ceiling would compress output tokens further (the current bottleneck — 98% of real-track total is output). This is a runtime configuration change, not a HEARTBEAT.md edit.

## Additional Deliverables (Beyond Assignment)

- [`langfuse-selfhost-guide.md`](langfuse-selfhost-guide.md) — shareable class-wide guide for self-hosting Langfuse v3 on macOS and wiring the DataExpert proxy as an in-UI LLM connection (docker-compose, `.env` template, MinIO bucket gotcha, Python SDK minimal tracing example, DataExpert proxy configuration with `x-session-id` header, failure-mode table).
- `.claude/skills/langfuse/` — Langfuse agent skill installed from github.com/langfuse/skills for future audit/instrumentation work.
- `solution/tools/run_evidence.sh` — reusable orchestrator for future A/B prompt experiments on OpenClaw.
- `solution/tools/{extract_metrics,ingest_traces,export_langfuse_snapshot,write_metrics_md}.py` — all unit-tested, all v4 SDK.

---

*Spec:* [`planning/specs/2026-04-23-openclaw-week3-homework-design.md`](planning/specs/2026-04-23-openclaw-week3-homework-design.md)
*Plan:* [`planning/plans/2026-04-23-openclaw-week3-homework-plan.md`](planning/plans/2026-04-23-openclaw-week3-homework-plan.md)
