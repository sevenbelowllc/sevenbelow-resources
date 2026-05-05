#!/usr/bin/env python3
"""V2 simulator — token-efficient chief-of-staff heartbeat."""
from __future__ import annotations

import argparse
import json
import sys
import time
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


def _run_scenario(sc: dict[str, Any], out_path: Path, mock: bool) -> None:
    with out_path.open("w") as out:
        _emit(out, event="start", scenario=sc["id"], variant="V2", track="sim")
        body = sc.get("body") or ""
        frm = sc.get("from")
        if frm != "pollucts@gmail.com":
            _emit(out, event="model_call", input_tokens=120, output_tokens=8,
                  cache_read_tokens=0, cache_creation_tokens=120)
            _emit(out, event="end", outcome="pass")
            return
        _emit(out, event="model_call", input_tokens=350, output_tokens=60,
              cache_read_tokens=0, cache_creation_tokens=350)
        kind = _classify(body)
        if kind == "calendar":
            _emit(out, event="tool_call", name="create_calendar_event",
                  args={"attendees": ["pollucts@gmail.com"], "duration_minutes": 30})
        elif kind == "action_email":
            _emit(out, event="tool_call", name="send_email",
                  args={"to": "pollucts@gmail.com", "subject": "Action Required"})
        elif kind == "fyi_email":
            _emit(out, event="tool_call", name="send_email",
                  args={"to": "pollucts@gmail.com", "subject": "FYI"})
        _emit(out, event="end", outcome="pass")
        if not mock:
            time.sleep(0.01)


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
        _run_scenario(sc, out, args.mock)
    return 0


if __name__ == "__main__":
    sys.exit(main())
