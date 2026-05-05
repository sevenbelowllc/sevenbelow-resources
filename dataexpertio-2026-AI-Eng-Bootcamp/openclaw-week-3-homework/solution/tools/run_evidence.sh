#!/usr/bin/env bash
set -euo pipefail

# Orchestrates the full 28-run evidence matrix.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source infra/.env
export LANGFUSE_HOST LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY

CONTAINER="openclaw-openclaw-gateway-1"
LIVE_WS="$HOME/.openclaw/workspace"
V1_WS="$ROOT/baseline/workspace"
V2_WS="$ROOT/workspace"
TRACES="$ROOT/evidence/traces"
METRICS="$ROOT/evidence/metrics.json"
EXPECTED_V1_HASH="001f0d633a8ff7e0d11d29b737b00531a3cb665399acf907685a79f804bb97ed"

echo "=== Phase A: Pre-run checks ==="
docker compose -f "$ROOT/infra/docker-compose.yml" up -d
until curl -sf -o /dev/null "$LANGFUSE_HOST"; do sleep 3; done
echo "langfuse up at $LANGFUSE_HOST"

verify_hash() {
  local got
  got=$(shasum -a 256 "$LIVE_WS/HEARTBEAT.md" | awk '{print $1}')
  [[ "$got" == "$EXPECTED_V1_HASH" ]] || { echo "HEARTBEAT drift: $got"; exit 2; }
}

run_sim() {
  local variant="$1" script="$2"
  echo "--- sim/$variant ---"
  local out="$TRACES/sim/$variant"
  mkdir -p "$out"
  python3 "$script" scenarios.json --out-dir "$out"
  for f in "$out"/*.jsonl; do
    local sid
    sid=$(basename "$f" .jsonl)
    python3 tools/extract_metrics.py "$f" --track sim --variant "$variant" --scenario "$sid" \
      >> "$METRICS.lines"
    python3 tools/ingest_traces.py "$f" --track sim --variant "$variant" --scenario "$sid"
  done
}

run_real() {
  local variant="$1" src_ws="$2"
  echo "--- real/$variant ---"
  local out="$TRACES/real/$variant"
  mkdir -p "$out"
  cp -p "$src_ws"/*.md "$LIVE_WS"/
  if [[ ! -f "$src_ws/BOOTSTRAP.md" ]]; then rm -f "$LIVE_WS/BOOTSTRAP.md"; fi
  local order=(meeting action fyi no-new ambiguous-date malformed duplicate)

  # Reset the session file so V1 and V2 runs start from identical blank context.
  # Move existing sessions aside rather than delete (preserves audit trail).
  docker exec "$CONTAINER" bash -lc '
    cd /home/node/.openclaw/agents/main/sessions/
    ts=$(date -u +%Y%m%dT%H%M%SZ)
    for f in *.jsonl; do [[ -e "$f" ]] && mv "$f" "../sessions.archive-'"$variant"'-$ts/$f" 2>/dev/null || true; done
    mkdir -p ../sessions.archive-'"$variant"'-$ts
    for f in *.jsonl; do [[ -e "$f" ]] && mv "$f" ../sessions.archive-'"$variant"'-$ts/; done
    rm -f sessions.json
  ' >/dev/null 2>&1 || true

  # Fire one warmup heartbeat so a new session file is created; ignore its output.
  docker exec "$CONTAINER" bash -lc "openclaw agent --agent main --timeout 60 --thinking off -m 'session reset warmup' >/dev/null" || true
  sleep 1

  # Identify the currently active (largest/most-recent) session file.
  local session_fn
  session_fn=$(docker exec "$CONTAINER" bash -lc 'ls -1t /home/node/.openclaw/agents/main/sessions/*.jsonl 2>/dev/null | head -1')
  if [[ -z "$session_fn" ]]; then
    echo "ERROR: no session file found after reset"
    return 1
  fi
  echo "active session: $session_fn"

  for sid in "${order[@]}"; do
    local text before_lines after_lines
    text=$(python3 -c "
import json
d = json.load(open('scenarios.json'))
s = [x for x in d['scenarios'] if x['id']=='$sid'][0]
frm = s.get('from') or ''
sub = s.get('subject') or ''
body = s.get('body') or ''
if not frm and not body:
    print('Heartbeat tick. No inbox update. Process per HEARTBEAT.md.')
else:
    print(f'You received this email. Process per HEARTBEAT.md.\n\nFrom: {frm}\nSubject: {sub}\n\n{body}')
")
    before_lines=$(docker exec "$CONTAINER" bash -lc "wc -l < $session_fn" | tr -d ' ')
    docker exec "$CONTAINER" bash -lc "openclaw agent --agent main --timeout 180 --thinking off -m $(printf %q "$text") >/dev/null" \
      || echo "WARN: agent for $sid exited non-zero"
    sleep 1
    after_lines=$(docker exec "$CONTAINER" bash -lc "wc -l < $session_fn" | tr -d ' ')
    if [[ "$after_lines" -le "$before_lines" ]]; then
      echo "WARN: no new session lines for $sid ($before_lines -> $after_lines)"
      continue
    fi
    # Slice just the new lines for this scenario into a per-scenario JSONL.
    local start=$((before_lines + 1))
    docker exec "$CONTAINER" bash -lc "sed -n '${start},${after_lines}p' $session_fn" > "$out/$sid.jsonl"
    python3 tools/extract_metrics.py "$out/$sid.jsonl" --track real --variant "$variant" --scenario "$sid" \
      >> "$METRICS.lines"
    python3 tools/ingest_traces.py "$out/$sid.jsonl" --track real --variant "$variant" --scenario "$sid"
  done
}

echo "=== Phase B: V1 ==="
# Restore V1 to live workspace (idempotent across reruns).
cp -p "$V1_WS"/*.md "$LIVE_WS"/
verify_hash
: > "$METRICS.lines"
run_sim V1 inefficient_openclaw_workflow.py
if [[ "${SKIP_REAL:-0}" != "1" ]]; then run_real V1 "$V1_WS"; fi

echo "=== Phase C: V2 ==="
run_sim V2 efficient_openclaw_workflow.py
if [[ "${SKIP_REAL:-0}" != "1" ]]; then run_real V2 "$V2_WS"; fi

echo "=== Phase D: Aggregate ==="
python3 - <<'PY'
import json, pathlib
rows = [json.loads(l) for l in open("evidence/metrics.json.lines") if l.strip()]
pathlib.Path("evidence/metrics.json").write_text(json.dumps(rows, indent=2))
print(f"wrote {len(rows)} rows")
PY

echo "=== Phase E: Finalize ==="
if [[ "${SKIP_DEPLOY:-0}" != "1" ]]; then
  cp -p "$V2_WS"/*.md "$LIVE_WS"/
  echo "V2 deployed to $LIVE_WS"
fi
echo "done."
