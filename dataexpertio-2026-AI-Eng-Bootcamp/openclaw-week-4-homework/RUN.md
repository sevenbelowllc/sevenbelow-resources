# Run Instructions — OpenClaw Week 4 Homework

How to set up the runtime venv and execute the fixed agent + LangSmith
evaluation.

---

## 1. Create venv + install deps

```bash
cd openclaw-week-4-homework
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ./solution        # makes openclaw_agent importable as a real package
```

The `pip install -e ./solution` step is technically optional —
`fixed_openclaw_agent.py` adds `solution/src` to `sys.path` at startup —
but installing the package keeps `pytest` and `python -c "import
openclaw_agent"` working from any directory.

---

## 2. Configure `.env`

```bash
cp .env.example .env
```

Then edit `.env` and fill in real values:

```
ANTHROPIC_API_KEY=sk-de-<your-bootcamp-key>
ANTHROPIC_BASE_URL=https://www.dataexpert.io/api/v1/anthropic
OPENCLAW_SESSION_ID=openclaw-week4-<your-handle>

# Optional — @traceable becomes a no-op without these.
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_<your-personal-key>
LANGSMITH_PROJECT=openclaw-week4-homework
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

`.env` is gitignored. Never commit it.

---

## 3. Pre-flight (recommended)

`preflight.py` at the homework root checks .env, raw HTTP to the proxy,
and the LangChain wiring in one shot:

```bash
python preflight.py
```

Three sections print: `.env` snapshot, raw HTTP ping, LangChain ping. A
green third section means the agent will work.

## 3a. (Optional) Pre-flight the DataExpert proxy with curl

Confirms the `sk-de-...` key is active before any LangChain call:

```bash
source .env
curl -sS -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -H "x-session-id: ${OPENCLAW_SESSION_ID:-preflight}" \
  -d '{"model":"claude-haiku-4-5","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

A streaming SSE response (begins with `event: message_start`) = good.
`401` = key inactive — regenerate at the bootcamp dashboard.

**Note:** the DataExpert proxy ALWAYS returns SSE streaming responses,
even when the request body sets `"stream": false`. `build_llm()` in
`solution/src/openclaw_agent/classifier.py` therefore configures
ChatAnthropic with `streaming=True`. Without that flag the SDK fails
with `AttributeError: 'str' object has no attribute 'model_dump'` when
it tries to deserialize the SSE chunks as a single JSON object.

---

## 4. Run the fixed agent

```bash
python fixed_openclaw_agent.py
```

Expected tail:

```
=== METRICS ===
Result: HEARTBEAT_OK
Tool calls: 3
Estimated token proxy: <small number>
```

Tool calls = 3 corresponds to: 1 fetch + 1 calendar event for `e1` + 1
send_email for `e2`. `e3` and `e4` are dropped at the sender allowlist.

---

## 5. Run the test suite

```bash
cd solution
pytest -v
```

Expected: `39 passed`. No network access required — the classifier is
mocked in pytest.

---

## 6. Run the LangSmith evaluation

Requires both `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY`.

```bash
cd solution
python evals/run_eval.py
```

The runner uploads (or reuses) the `openclaw-week4-scenarios` dataset,
runs the agent against all 7 scenarios, scores them with the 6
evaluators, and prints:

```
Experiment URL: https://smith.langchain.com/...
```

Paste that URL into the **Link to LangSmith Traces** placeholder in
`SUBMISSION.md`.

---

## 7. Capture before/after metrics (already committed)

The metrics JSON at `solution/metrics/{before,after}.json` is already
checked in (committed by `solution/scripts/capture_metrics.py`). Re-run
only if you change the agent or starter inbox:

```bash
python solution/scripts/capture_metrics.py
```

---

## 8. Pre-commit secret guard

Optional but recommended — wire into `.git/hooks/pre-commit`:

```bash
ln -s ../../openclaw-week-4-homework/solution/scripts/check-secrets.sh \
      .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Blocks any commit containing `sk-de-...` or `lsv2_pt_...` outside
`.env.example`.

---

## File map

```
openclaw-week-4-homework/
├── README.md                    # original assignment brief
├── RUN.md                       # this file
├── SUBMISSION.md                # video + LangSmith URLs go here
├── fix-report.md                # 12-issue analysis + before/after
├── tests.md                     # narrative grader walkthrough
├── requirements.txt             # runtime + test deps
├── .env.example                 # env template (committed)
├── .env                         # real values (gitignored)
├── broken_openclaw_agent.py     # original starter (do not modify)
├── fixed_openclaw_agent.py      # grader entrypoint
└── solution/
    ├── pyproject.toml           # package definition
    ├── README.md                # package-level setup
    ├── src/openclaw_agent/      # models, safety, tools, classifier, agent
    ├── tests/                   # pytest scenarios (39 tests)
    ├── evals/                   # LangSmith dataset + evaluators + runner
    ├── scripts/                 # capture_metrics.py, check-secrets.sh
    └── metrics/                 # before.json, after.json
```

---

## Submission checklist

- [ ] `pytest` → 39 passed
- [ ] `python fixed_openclaw_agent.py` → `Result: HEARTBEAT_OK`, `Tool calls: 3`
- [ ] `python solution/evals/run_eval.py` → Experiment URL captured
- [ ] Video walkthrough recorded
- [ ] `SUBMISSION.md` `<paste …>` placeholders replaced
- [ ] PR #2 reflects final state
