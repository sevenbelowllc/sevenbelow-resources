#!/usr/bin/env python3
"""V1 simulator — deliberately inefficient chief-of-staff heartbeat.

Matches the CLI contract of efficient_openclaw_workflow.py (scenarios.json
-> one JSONL per scenario) so the orchestrator can call both.

Inefficient characteristics (mirroring the root-level
inefficient_openclaw_workflow.py demo):
  - 3 overlapping inbox scans per tick
  - full paraphrase + executive summary + risk summary per email
  - verbose policy restatement
  - full cache rewrites per call (no reuse)

Token numbers are proxies, not real model usage.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _emit(out, **ev):
    out.write(json.dumps(ev) + "\n")


def _classify(body: str) -> str:
    b = (body or "").lower()
    if not b.strip():
        return "none"
    if any(k in b for k in ["schedule", "meeting", "sync", "set up", "next ", " at "]):
        return "calendar"
    if any(k in b for k in ["please", "remind", "handle", "can you"]):
        return "action_email"
    return "fyi_email"


def _run_scenario(sc: dict[str, Any], out_path: Path) -> None:
    with out_path.open("w") as out:
        _emit(out, event="start", scenario=sc["id"], variant="V1", track="sim")
        body = sc.get("body") or ""
        frm = sc.get("from")

        # V1 always does 3 overlapping inbox scans, regardless of outcome.
        for query in ("last 24h", "unread", f"from:{frm or 'owner'}"):
            _emit(out, event="tool_call", name="find_email", args={"query": query, "limit": 50})

        if frm != "pollucts@gmail.com":
            # V1 still restates the full policy block even on empty inbox.
            _emit(out, event="model_call",
                  input_tokens=900, output_tokens=120,
                  cache_read_tokens=0, cache_creation_tokens=900)
            _emit(out, event="end", outcome="pass")
            return

        # V1 pays triple-summary + verbose reasoning + restated policy cost.
        _emit(out, event="model_call",
              input_tokens=1600, output_tokens=420,
              cache_read_tokens=0, cache_creation_tokens=1600)

        kind = _classify(body)
        if kind == "calendar":
            _emit(out, event="tool_call", name="create_calendar_event",
                  args={"attendees": ["pollucts@gmail.com"], "duration_minutes": 30})
        elif kind == "action_email":
            _emit(out, event="tool_call", name="send_email",
                  args={"to": "pollucts@gmail.com", "subject": "Action Required"})
        elif kind == "fyi_email":
            _emit(out, event="tool_call", name="send_email",
                  args={"to": "pollucts@gmail.com", "subject": "FYI from your Chief of Staff"})

        # V1 re-checks inbox after handling.
        _emit(out, event="tool_call", name="find_email",
              args={"query": f"from:{frm} unread", "limit": 50})

        _emit(out, event="end", outcome="pass")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    data = json.loads(args.scenarios.read_text())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for sc in data["scenarios"]:
        out = args.out_dir / f"{sc['id']}.jsonl"
        _run_scenario(sc, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
