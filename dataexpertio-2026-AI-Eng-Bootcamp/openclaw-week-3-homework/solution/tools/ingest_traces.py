#!/usr/bin/env python3
"""Post-hoc ingestion of OpenClaw session JSONL (or sim JSONL) into Langfuse.

Emits one root span per (track, variant, scenario) run. Tool-use blocks
become child spans; assistant text blocks become child generations with
usage_details derived from the session JSONL.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from langfuse import Langfuse, propagate_attributes  # type: ignore
except ImportError:  # allow tests to patch without install
    Langfuse = None  # type: ignore
    propagate_attributes = None  # type: ignore


def _iter_jsonl(path: Path):
    with path.open() as f:
        for raw in f:
            raw = raw.strip()
            if raw:
                yield json.loads(raw)


def run(
    *,
    jsonl: Path,
    track: str,
    variant: str,
    scenario: str,
    host: str,
    public_key: str,
    secret_key: str,
) -> str:
    assert Langfuse is not None, "langfuse SDK not installed"
    client = Langfuse(host=host, public_key=public_key, secret_key=secret_key)
    trace_name = f"openclaw.{track}.{variant}.{scenario}"
    tags = [f"track:{track}", f"variant:{variant}", f"scenario:{scenario}"]

    with propagate_attributes(
        trace_name=trace_name,
        tags=tags,
        metadata={"track": track, "variant": variant, "scenario": scenario},
    ):
        with client.start_as_current_observation(
            as_type="span",
            name=trace_name,
            input={"scenario": scenario},
        ) as root:
            trace_id = client.get_current_trace_id() or trace_name

            for ev in _iter_jsonl(jsonl):
                if track == "real":
                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message", {}) or {}
                    usage = msg.get("usage") or {}
                    for block in (msg.get("content") or []):
                        btype = block.get("type")
                        if btype == "tool_use":
                            span = client.start_observation(
                                as_type="span",
                                name=block.get("name", "tool_use"),
                                input=block.get("input"),
                            )
                            span.end()
                        elif btype == "text":
                            gen = client.start_observation(
                                as_type="generation",
                                name="assistant.text",
                                output=block.get("text", ""),
                                usage_details={
                                    "input": int(usage.get("input", 0)),
                                    "output": int(usage.get("output", 0)),
                                    "cache_read_input_tokens": int(usage.get("cacheRead", 0)),
                                    "cache_creation_input_tokens": int(usage.get("cacheWrite", 0)),
                                },
                            )
                            gen.end()
                else:  # sim
                    t = ev.get("event")
                    if t == "tool_call":
                        span = client.start_observation(
                            as_type="span",
                            name=ev.get("name", "tool_call"),
                            input=ev.get("args"),
                        )
                        span.end()
                    elif t == "model_call":
                        gen = client.start_observation(
                            as_type="generation",
                            name="model_call",
                            usage_details={
                                "input": int(ev.get("input_tokens", 0)),
                                "output": int(ev.get("output_tokens", 0)),
                                "cache_read_input_tokens": int(ev.get("cache_read_tokens", 0)),
                                "cache_creation_input_tokens": int(ev.get("cache_creation_tokens", 0)),
                            },
                        )
                        gen.end()

            root.update(output={"status": "ingested"})

    client.flush()
    return trace_id


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--track", choices=["sim", "real"], required=True)
    ap.add_argument("--variant", choices=["V1", "V2"], required=True)
    ap.add_argument("--scenario", required=True)
    args = ap.parse_args()
    host = os.environ["LANGFUSE_HOST"]
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    trace_id = run(
        jsonl=args.jsonl,
        track=args.track,
        variant=args.variant,
        scenario=args.scenario,
        host=host,
        public_key=pk,
        secret_key=sk,
    )
    print(trace_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
