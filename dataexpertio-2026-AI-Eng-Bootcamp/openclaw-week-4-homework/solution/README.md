# OpenClaw Week 4 — Solution Package

## Setup

```bash
cd openclaw-week-4-homework/solution
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env  # fill in sk-de-... and lsv2_pt_... values
```

## Pre-flight: confirm DataExpert proxy reachable

```bash
source ../.env
curl -sS -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -H "x-session-id: ${OPENCLAW_SESSION_ID:-preflight}" \
  -d '{"model":"claude-haiku-4-5","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

Expected: a JSON `message` response with `content`. A 401 means the
`sk-de-...` key is inactive — regenerate it from the bootcamp dashboard.

## Run the agent

```bash
python ../fixed_openclaw_agent.py
```

## Run tests

```bash
pytest
```

## Run LangSmith evaluation

```bash
python evals/run_eval.py
```
