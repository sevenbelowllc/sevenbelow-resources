#!/usr/bin/env python3
"""Generate evidence/metrics.md from metrics.json + a langfuse snapshot file."""
from __future__ import annotations

import json
import sys
from pathlib import Path


SCENARIOS = ["meeting", "action", "fyi", "no-new", "ambiguous-date", "malformed", "duplicate"]


def fmt_int(n):
    return f"{n:,}"


def pct(v1, v2):
    if v1 == 0:
        return "n/a" if v2 == 0 else f"+{v2}"
    return f"{(v1 - v2) / v1 * 100:.1f}%"


def build_lf_urls(snapshot_path: Path, lf_host: str) -> dict:
    """Map (track, variant, scenario) → Langfuse trace URL."""
    urls = {}
    if not snapshot_path.exists():
        return urls
    snap = json.loads(snapshot_path.read_text())
    for t in snap:
        tags = set(t.get("tags") or [])
        track = next((x.split(":", 1)[1] for x in tags if x.startswith("track:")), None)
        variant = next((x.split(":", 1)[1] for x in tags if x.startswith("variant:")), None)
        scenario = next((x.split(":", 1)[1] for x in tags if x.startswith("scenario:")), None)
        if track and variant and scenario:
            urls[(track, variant, scenario)] = f"{lf_host}/trace/{t['id']}"
    return urls


def main():
    here = Path(__file__).resolve().parents[1]
    rows = json.loads((here / "evidence" / "metrics.json").read_text())
    snap = here / "evidence" / "langfuse-snapshot.json"
    lf_host = "http://localhost:3333"
    urls = build_lf_urls(snap, lf_host)

    def get(track, variant, scenario):
        return next((r for r in rows if r["track"] == track and r["variant"] == variant and r["scenario"] == scenario), None)

    def totals(track, variant):
        s = [r for r in rows if r["track"] == track and r["variant"] == variant]
        return {
            "total_tokens": sum(r["total_tokens"] for r in s),
            "total_input_tokens": sum(r["total_input_tokens"] for r in s),
            "total_output_tokens": sum(r["total_output_tokens"] for r in s),
            "tool_call_count": sum(r["tool_call_count"] for r in s),
            "cache_read_tokens": sum(r["cache_read_tokens"] for r in s),
            "cache_creation_tokens": sum(r["cache_creation_tokens"] for r in s),
            "model_calls": sum(r["model_calls"] for r in s),
            "safety_violation_count": sum(r["safety_violation_count"] for r in s),
            "passes": sum(1 for r in s if r["scenario_outcome"] == "pass"),
        }

    out = []
    out.append("# Evidence — V1 → V2 on sim + real tracks")
    out.append("")
    out.append(f"Langfuse self-hosted at `{lf_host}`. See `langfuse-snapshot.json` for the post-hoc API export; per-row links below.")
    out.append("")

    for track in ("sim", "real"):
        out.append(f"## {track.upper()} track — per scenario")
        out.append("")
        out.append("| Scenario | V1 tokens | V2 tokens | Δ tokens | V1 tools | V2 tools | V1 cache_read | V2 cache_read | V1 outcome | V2 outcome | V1 trace | V2 trace |")
        out.append("|---|--:|--:|--:|--:|--:|--:|--:|---|---|---|---|")
        for sid in SCENARIOS:
            r1 = get(track, "V1", sid) or {}
            r2 = get(track, "V2", sid) or {}
            u1 = urls.get((track, "V1", sid), "")
            u2 = urls.get((track, "V2", sid), "")
            u1_link = f"[link]({u1})" if u1 else "—"
            u2_link = f"[link]({u2})" if u2 else "—"
            out.append(
                f"| `{sid}` | {fmt_int(r1.get('total_tokens', 0))} | {fmt_int(r2.get('total_tokens', 0))} | "
                f"{pct(r1.get('total_tokens', 0), r2.get('total_tokens', 0))} | "
                f"{r1.get('tool_call_count', 0)} | {r2.get('tool_call_count', 0)} | "
                f"{fmt_int(r1.get('cache_read_tokens', 0))} | {fmt_int(r2.get('cache_read_tokens', 0))} | "
                f"{r1.get('scenario_outcome', '—')} | {r2.get('scenario_outcome', '—')} | "
                f"{u1_link} | {u2_link} |"
            )
        tv1, tv2 = totals(track, "V1"), totals(track, "V2")
        out.append(
            f"| **totals** | **{fmt_int(tv1['total_tokens'])}** | **{fmt_int(tv2['total_tokens'])}** | "
            f"**{pct(tv1['total_tokens'], tv2['total_tokens'])}** | "
            f"**{tv1['tool_call_count']}** | **{tv2['tool_call_count']}** | "
            f"**{fmt_int(tv1['cache_read_tokens'])}** | **{fmt_int(tv2['cache_read_tokens'])}** | "
            f"{tv1['passes']}/7 pass | {tv2['passes']}/7 pass | — | — |"
        )
        out.append("")
        out.append("### Aggregate reductions")
        out.append("")
        out.append("| Metric | V1 | V2 | Reduction |")
        out.append("|---|--:|--:|--:|")
        for k, label in [
            ("total_tokens", "total_tokens"),
            ("total_input_tokens", "total_input_tokens"),
            ("total_output_tokens", "total_output_tokens"),
            ("tool_call_count", "tool_call_count"),
            ("cache_read_tokens", "cache_read_tokens"),
            ("cache_creation_tokens", "cache_creation_tokens"),
            ("model_calls", "model_calls"),
        ]:
            out.append(f"| {label} | {fmt_int(tv1[k])} | {fmt_int(tv2[k])} | {pct(tv1[k], tv2[k])} |")
        out.append(f"| safety_violation_count | {tv1['safety_violation_count']} | {tv2['safety_violation_count']} | = |")
        out.append("")

    out.append("## Acceptance bars (spec §9)")
    out.append("")
    real1, real2 = totals("real", "V1"), totals("real", "V2")
    bars = [
        ("1", "safety_violation_count = 0 on V1 and V2", real1["safety_violation_count"] == 0 and real2["safety_violation_count"] == 0, f"V1={real1['safety_violation_count']}, V2={real2['safety_violation_count']}"),
        ("2", "scenario_outcome = pass on 7/7 V2 real", real2["passes"] == 7, f"{real2['passes']}/7"),
        ("3", "total_tokens reduction ≥ 30% (real)", (real1["total_tokens"] - real2["total_tokens"]) / max(real1["total_tokens"], 1) >= 0.30, pct(real1["total_tokens"], real2["total_tokens"])),
        ("4", "cache_read_tokens reduction ≥ 20% (real)", (real1["cache_read_tokens"] - real2["cache_read_tokens"]) / max(real1["cache_read_tokens"], 1) >= 0.20, pct(real1["cache_read_tokens"], real2["cache_read_tokens"])),
        ("5", "tool_call_count reduction ≥ 10% or flat (real)", real1["tool_call_count"] == 0 or (real1["tool_call_count"] - real2["tool_call_count"]) / max(real1["tool_call_count"], 1) >= 0.10 or real1["tool_call_count"] == real2["tool_call_count"], f"V1={real1['tool_call_count']}, V2={real2['tool_call_count']}"),
        ("7", "all 28 traces in Langfuse with required tags", len(urls) >= 28, f"{len(urls)}/28"),
        ("8", "langfuse-snapshot.json committed + parses", snap.exists(), str(snap.exists())),
        ("9", "one Langfuse URL per scoring row", len(urls) >= 28, f"{len(urls)}/28"),
    ]
    out.append("| Bar | Rule | Status | Measured |")
    out.append("|---|---|---|---|")
    for n, rule, ok, measured in bars:
        out.append(f"| {n} | {rule} | {'✅' if ok else '❌'} | {measured} |")
    out.append("")
    out.append("Bar 6 (`wall_clock`) is informational per spec; not scored.")
    out.append("")

    (here / "evidence" / "metrics.md").write_text("\n".join(out))
    print("wrote", here / "evidence" / "metrics.md")


if __name__ == "__main__":
    main()
