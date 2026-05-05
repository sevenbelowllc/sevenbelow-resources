# OpenClaw Week 3 — Token Efficiency Solution

## Index

- `HEARTBEAT.md`, `workspace/` — V2 optimized prompt + workspace files.
- `baseline/workspace/` — V1 baseline snapshot (SHA256 anchor committed to spec).
- `scenarios.json` — 7 test scenarios shared across sim + real tracks.
- `inefficient_openclaw_workflow.py`, `efficient_openclaw_workflow.py` — V1/V2 sim runners.
- `tools/run_evidence.sh` — full matrix orchestrator (14 sim + 14 real = 28 runs).
- `tools/extract_metrics.py`, `tools/ingest_traces.py` — metrics extractor + Langfuse ingester.
- `evidence/metrics.md`, `evidence/metrics.json`, `evidence/langfuse-snapshot.json` — before/after data.
- `before-after.md` — side-by-side V1 → V2 diff + per-file commentary.
- `infra/` — self-hosted Langfuse v3 docker-compose + `.env.example`.

## Rationale (<500 words)

**Goal.** Shrink per-tick cost of the live Alfred heartbeat without weakening safety or breaking any Day-2 required behavior.

**Method.** Author a V2 `HEARTBEAT.md` + trim warm-path workspace files; measure across 7 scenarios on two tracks (deterministic sim + real containerized agent), logged to self-hosted Langfuse v3.

**Three highest-impact changes (V2.1).**

1. **Hoisted edge-case screen above routing rules in `HEARTBEAT.md`.** V1's edge-case hints were buried; in the initial V2 draft they were listed *after* the routing table, so the live agent still matched `scheduling` first on `ambiguous-date` and booked a placeholder event. V2.1 makes "first screen for duplicate / ambiguous / malformed, reply in text with zero tool calls" the first step. Result on real: `malformed` went from 249 tokens / 1 tool call to **40 tokens / 0 calls**; `duplicate` from 61 / 0 to 31 / 0; `ambiguous-date` no longer triggers a spurious calendar booking.

2. **Added tool-discipline clause to stop Zapier retry loops.** "Call each tool exactly once per email. If a tool response includes a `followUpQuestion`, the call has already succeeded — do not re-invoke." The initial V2 run hit Zapier's confirmation-loop behavior on `meeting` and `malformed`, doubling tool calls and cache_read for those scenarios. V2.1 explicitly closes that loop.

3. **Deleted `BOOTSTRAP.md` (1471 → 0 bytes) + compressed `USER.md` / `SOUL.md` (−31% each).** `BOOTSTRAP.md` self-instructs deletion post-first-run; Alfred is months past. `USER.md` credentials flattened from 7 bullets to 2 lines (facts preserved). `SOUL.md` lost italic framing + external link; Core Truths / Boundaries / Vibe / Continuity preserved verbatim.

**Safety posture — unchanged.** All three prompt-layer predicates verbatim: inbound `pollucts@gmail.com`, self-loop guard `polluctsopenclaw@gmail.com`, outbound recipient `pollucts@gmail.com`. 0 safety violations across 28 runs. Prior injection-refusal evidence in session JSONL from 2026-04-22.

**Untouched:** `AGENTS.md`, `TOOLS.md` (spec §2 out of scope), `IDENTITY.md` (377 bytes, too small), `compliance-os-intel.md`, `daily-reading-list.md` (personal notes).

**Two tracks.** Sim = Python runners modeling the homework's V1 inefficiencies (sanity check on the pipeline). Real = `openclaw agent --agent main` invocations against live Alfred, isolated session per variant, 7 scenarios each.

**Evidence path.** Per-scenario JSONL → `extract_metrics.py` → `evidence/metrics.json`; same JSONL → `ingest_traces.py` → Langfuse tagged `{variant, track, scenario}`; `export_langfuse_snapshot.py` writes `evidence/langfuse-snapshot.json` (29 records); `write_metrics_md.py` emits the scored table.

**Reproducing the run.** From `solution/`:

```bash
bash tools/run_evidence.sh
```

Brings Langfuse up, runs the full matrix, writes `evidence/*`, deploys V2 to `~/.openclaw/workspace/`. See `before-after.md` for diffs and `evidence/metrics.md` for the scored table.

**Headline numbers.**
- **Sim track:** 80.3% total-token reduction, 81.8% tool-call reduction, 7/7 V2 pass, 0 safety violations.
- **Real track (V2.1):** 7/7 V2 pass, 0 safety violations; V2 cheaper than V1 on all three cost metrics — **total_tokens −10.9%, tool_call_count −20.0%, cache_read_tokens −10.2%**. Bars 1, 2, 5, 7, 8, 9 pass. Bars 3 and 4 (≥30% total_tokens / ≥20% cache_read) miss threshold with direction correct — production Alfred is already ~11× tighter than the sim's V1 (1,520 tok vs 13,140 tok), and cache_read is dominated by `AGENTS.md` + OpenClaw framework overhead (spec §2 out of scope).

Full analysis in `evidence/metrics.md § Commentary`.
