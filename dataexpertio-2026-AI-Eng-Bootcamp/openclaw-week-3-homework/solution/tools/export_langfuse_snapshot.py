#!/usr/bin/env python3
"""Export all recent Langfuse traces tagged track:{sim,real} to a JSON snapshot."""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def lf_get(host: str, path: str, pk: str, sk: str):
    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    url = f"{host.rstrip('/')}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    host = os.environ["LANGFUSE_HOST"]
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]

    here = Path(__file__).resolve().parents[1]
    out_path = here / "evidence" / "langfuse-snapshot.json"

    # Pull traces tagged track:sim or track:real. Page generously.
    all_traces = []
    for track in ("sim", "real"):
        page = 1
        while True:
            query = urllib.parse.urlencode({"tags": f"track:{track}", "page": str(page), "limit": "100"})
            data = lf_get(host, f"/api/public/traces?{query}", pk, sk)
            batch = data.get("data", [])
            all_traces.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    # Deduplicate by trace id, keep most recent per (track, variant, scenario).
    by_key = {}
    for t in all_traces:
        tags = set(t.get("tags") or [])
        track = next((x.split(":", 1)[1] for x in tags if x.startswith("track:")), None)
        variant = next((x.split(":", 1)[1] for x in tags if x.startswith("variant:")), None)
        scenario = next((x.split(":", 1)[1] for x in tags if x.startswith("scenario:")), None)
        if not (track and variant and scenario):
            continue
        key = (track, variant, scenario)
        existing = by_key.get(key)
        if not existing or t.get("timestamp", "") > existing.get("timestamp", ""):
            by_key[key] = t

    kept = sorted(by_key.values(), key=lambda x: (x.get("tags") or []))
    out_path.write_text(json.dumps(kept, indent=2))
    print(f"wrote {len(kept)} trace records to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
