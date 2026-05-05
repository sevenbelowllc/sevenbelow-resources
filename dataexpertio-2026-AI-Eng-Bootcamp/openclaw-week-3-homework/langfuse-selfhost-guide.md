# Self-hosted Langfuse v3 on macOS (with DataExpert proxy wired in)

Authored by [David Kramer](https://www.linkedin.com/in/davidkramer13/) at [SevenBelow](https://sevenbelow.com).

A working recipe for running Langfuse v3 locally, pointing the Python SDK at it, and wiring its in-UI LLM features (Playground, LLM-as-a-Judge, Prompt Experiments) at the DataExpert bootcamp Anthropic proxy instead of direct Anthropic API.

Everything below has been verified end-to-end on Docker Desktop for Mac (Darwin 25.3.0). The two gotchas that will burn you are marked **🔥** — don't skip them.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project layout](#2-project-layout)
3. [`docker-compose.yml`](#3-docker-composeyml)
4. [`.env.example`](#4-envexample)
5. [Generate `.env`](#5-generate-env)
6. [Bring the stack up](#6-bring-the-stack-up)
7. [First-run bootstrap in the UI](#7-first-run-bootstrap-in-the-ui)
8. [Python SDK — minimal tracing example](#8-python-sdk--minimal-tracing-example)
9. [Configuring the DataExpert proxy as a Langfuse LLM Connection](#9-configuring-the-dataexpert-proxy-as-a-langfuse-llm-connection)
    - 9.0 [What this actually does (and doesn't)](#90-what-this-actually-does-and-doesnt)
    - 9.1 [Prerequisites](#91-prerequisites)
    - 9.2 [Pre-flight verification from the terminal](#92-pre-flight-verification-from-the-terminal)
    - 9.3 [UI navigation: getting to the form](#93-ui-navigation-getting-to-the-form)
    - 9.4 [Every field in the New LLM Connection form — exact values](#94-every-field-in-the-new-llm-connection-form--exact-values)
    - 9.5 [Under the hood — what happens when Langfuse calls the proxy](#95-under-the-hood--what-happens-when-langfuse-calls-the-proxy)
    - 9.6 [Testing the connection](#96-testing-the-connection)
    - 9.7 [Using the connection in other Langfuse features](#97-using-the-connection-in-other-langfuse-features)
    - 9.8 [Every failure mode and its fix](#98-every-failure-mode-and-its-fix)
    - 9.9 [Key rotation and maintenance](#99-key-rotation-and-maintenance)
    - 9.10 [Quick-reference one-page summary](#910-quick-reference-one-page-summary)
10. [Bring down / reset](#10-bring-down--reset)
11. [Troubleshooting cheatsheet](#11-troubleshooting-cheatsheet)
12. [Further reading](#12-further-reading)

---

## 1. Prerequisites

- Docker Desktop running, with **≥ 8 GB memory** allocated (Settings → Resources). ClickHouse won't start below that.
- Python 3.11+ and `pip`.
- Your DataExpert proxy API key (the `sk-de-...` one). If you don't have one, regenerate it from the bootcamp dashboard — inactive keys will silently fail the Langfuse connection test.

---

## 2. Project layout

Make a folder for the stack. Everything here sits side by side:

```
langfuse-selfhost/
├── docker-compose.yml
├── .env.example
└── .env          # gitignored — you generate this
```

---

## 3. `docker-compose.yml`

Drop this in verbatim. 6 services: web, worker, Postgres (metadata), ClickHouse (spans/events), Redis (queue), MinIO (blob events).

```yaml
name: langfuse-selfhost

services:
  langfuse-web:
    image: langfuse/langfuse:3
    restart: unless-stopped
    depends_on:
      postgres: { condition: service_healthy }
      clickhouse: { condition: service_healthy }
      redis: { condition: service_healthy }
      minio: { condition: service_healthy }
    ports:
      - "3333:3000"
    env_file: .env

  langfuse-worker:
    image: langfuse/langfuse-worker:3
    restart: unless-stopped
    depends_on:
      postgres: { condition: service_healthy }
      clickhouse: { condition: service_healthy }
      redis: { condition: service_healthy }
      minio: { condition: service_healthy }
    env_file: .env

  postgres:
    image: postgres:16
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 20
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data

  clickhouse:
    image: clickhouse/clickhouse-server:24
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--spider", "http://localhost:8123/ping"]
      interval: 5s
      timeout: 5s
      retries: 40
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: ${CLICKHOUSE_USER}
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
    ulimits:
      nofile: { soft: 262144, hard: 262144 }
    volumes:
      - clickhouse-data:/var/lib/clickhouse

  redis:
    image: redis:7
    restart: unless-stopped
    command: ["redis-server", "--requirepass", "${REDIS_AUTH}"]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_AUTH}", "ping"]
      interval: 5s
      timeout: 5s
      retries: 20
    volumes:
      - redis-data:/data

  minio:
    image: minio/minio:latest
    restart: unless-stopped
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 20
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: ${LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY}
    volumes:
      - minio-data:/data

volumes:
  postgres-data:
  clickhouse-data:
  redis-data:
  minio-data:
```

The web UI is on port **3333** to avoid colliding with other local services that squat on 3000.

---

## 4. `.env.example`

```dotenv
# Langfuse v3 self-host env template. Copy to .env and fill.
#
# Generate secrets:
#   openssl rand -hex 32   (ENCRYPTION_KEY, NEXTAUTH_SECRET)
#   openssl rand -hex 16   (SALT)

# Web + worker
NEXTAUTH_URL=http://localhost:3333
NEXTAUTH_SECRET=CHANGE_ME_32_HEX
SALT=CHANGE_ME_16_HEX
ENCRYPTION_KEY=CHANGE_ME_64_HEX
TELEMETRY_ENABLED=false
LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=false

# Postgres (metadata)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_POSTGRES
POSTGRES_DB=postgres
DATABASE_URL=postgresql://postgres:CHANGE_ME_POSTGRES@postgres:5432/postgres

# ClickHouse (events + spans)
CLICKHOUSE_MIGRATION_URL=clickhouse://clickhouse:9000
CLICKHOUSE_URL=http://clickhouse:8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=CHANGE_ME_CLICKHOUSE
CLICKHOUSE_CLUSTER_ENABLED=false

# Redis (queue + cache)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_AUTH=CHANGE_ME_REDIS

# MinIO / S3 (blob events)
LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse
LANGFUSE_S3_EVENT_UPLOAD_REGION=auto
LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=CHANGE_ME_MINIO
LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://minio:9000
LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/

# Python SDK client config (populated after first-run bootstrap, see §7)
LANGFUSE_HOST=http://localhost:3333
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

---

## 5. Generate `.env`

```bash
cp .env.example .env

# Fill the five CHANGE_ME_* values
sed -i '' "s/CHANGE_ME_32_HEX/$(openssl rand -hex 32)/"          .env   # NEXTAUTH_SECRET
sed -i '' "s/CHANGE_ME_16_HEX/$(openssl rand -hex 16)/"          .env   # SALT
sed -i '' "s/CHANGE_ME_64_HEX/$(openssl rand -hex 32)/"          .env   # ENCRYPTION_KEY (32 bytes hex = 64 chars)
sed -i '' "s/CHANGE_ME_POSTGRES/$(openssl rand -hex 16)/g"       .env   # Postgres password (both places)
sed -i '' "s/CHANGE_ME_CLICKHOUSE/$(openssl rand -hex 16)/"      .env   # ClickHouse password
sed -i '' "s/CHANGE_ME_REDIS/$(openssl rand -hex 16)/"           .env   # Redis password
sed -i '' "s/CHANGE_ME_MINIO/$(openssl rand -hex 16)/"           .env   # MinIO password
```

`ENCRYPTION_KEY` must be **exactly 64 hex characters** (32 bytes). Langfuse refuses to boot otherwise.

---

## 6. Bring the stack up

```bash
docker compose up -d
docker compose ps      # wait until all 6 are "running (healthy)" where applicable
```

### 🔥 Gotcha 1 — create the MinIO bucket

**Langfuse v3 uploads event JSON to S3/MinIO but does not auto-create the bucket.** If you skip this step, the Python SDK's `flush()` will look fine but spans will fail to export with "The specified bucket does not exist" in the `langfuse-web` logs.

```bash
# The container name is "<compose-project>-minio-1"; adjust if you renamed the project.
PROJECT=langfuse-selfhost
docker exec "${PROJECT}-minio-1" \
  mc alias set local http://localhost:9000 minio \
  "$(grep LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY .env | cut -d= -f2)"
docker exec "${PROJECT}-minio-1" mc mb local/langfuse
```

Verify: `docker exec "${PROJECT}-minio-1" mc ls local` should show `langfuse/`.

---

## 7. First-run bootstrap in the UI

1. Open http://localhost:3333. You'll see the Langfuse login page.
2. Click **Sign up** (there are no users yet — the first account becomes the admin).
3. Create an **Organization** (any name).
4. Create a **Project** inside it.
5. **Settings → API Keys → Create new API keys**. You get a public key (`pk-lf-…`) and a secret key (`sk-lf-…`). Copy both now; the secret is only shown once.
6. Paste them into your `.env`:

```dotenv
LANGFUSE_HOST=http://localhost:3333
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### 🔥 Gotcha 2 — the env var is `LANGFUSE_HOST`, not `LANGFUSE_BASE_URL`

The Python SDK reads `LANGFUSE_HOST`. If you call it `LANGFUSE_BASE_URL` (which would match the OpenAI / Anthropic SDK convention) the client will fall back to the Langfuse Cloud URL and you'll get 401s that look like your keys are wrong.

---

## 8. Python SDK — minimal tracing example

```bash
pip install 'langfuse>=3.0.0' python-dotenv
```

```python
# trace_example.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE importing langfuse — the client reads env at import time.
load_dotenv(Path(__file__).parent / ".env")

from langfuse import get_client, observe, propagate_attributes


@observe(name="tool.lookup")
def lookup(q: str) -> dict:
    get_client().update_current_span(input={"query": q})
    return {"answer": 42}


@observe(name="handle_request", capture_input=False, capture_output=False)
def handle_request(user_msg: str) -> str:
    lf = get_client()
    lf.set_current_trace_io(input={"user_msg": user_msg})
    result = lookup(user_msg)
    lf.set_current_trace_io(output={"answer": result["answer"]})
    return f"answer: {result['answer']}"


if __name__ == "__main__":
    with propagate_attributes(
        trace_name="demo-request",
        tags=["env:dev", "feature:demo"],
        metadata={"service": "trace_example"},
    ):
        handle_request("what is the meaning of life?")

    # REQUIRED in short-lived scripts — flush buffered spans before exit.
    get_client().flush()
    print("done")
```

Run it:

```bash
python3 trace_example.py
```

Open http://localhost:3333 → **Tracing** in the sidebar. You should see a trace named `demo-request` with a child `handle_request` span and a grandchild `tool.lookup` span, tagged `env:dev` and `feature:demo`.

### SDK baseline best practices

- **Always `flush()` before a short-lived process exits.** Otherwise spans stay buffered and never send.
- **Load env vars before importing `langfuse`.** The client initializes from env at import time.
- **Prefer `@observe` decorators over manual spans.** Cleaner and captures timings/errors automatically.
- **`propagate_attributes(...)` is how you set trace-level tags/metadata in the v4 SDK.** There is no `update_current_trace()` method — v3→v4 refactored this.
- **Use `capture_input=False, capture_output=False` on the outer function** when its raw args contain things you don't want in the UI (API keys, large blobs). Then set what you want explicitly via `set_current_trace_io(input=..., output=...)`.

---

## 9. Configuring the DataExpert proxy as a Langfuse LLM Connection

### 9.0 What this actually does (and doesn't)

**This configures Langfuse's *server-side* LLM calls.** It enables four Langfuse features:

| Feature | What it does | What it needs |
|---|---|---|
| **Playground** | Chat UI to test prompts against models | LLM Connection |
| **Prompt Experiments** | Run a prompt variant over a dataset and score results | LLM Connection |
| **LLM-as-a-Judge** | Auto-score traces by sending them to an LLM with a grading rubric | LLM Connection |
| **Prompt Optimization** | Automated prompt tuning | LLM Connection |

**It does NOT affect how your app sends traces to Langfuse.** That path is:

```
Your Python/JS code  ──(LANGFUSE_HOST + PUBLIC_KEY + SECRET_KEY)──►  Langfuse
```

The LLM Connection path is separate:

```
Langfuse web/worker  ──(API Base URL + API Key + Extra Headers)──►  DataExpert proxy  ──►  Anthropic
```

You can have tracing working perfectly while the LLM Connection is broken, and vice versa.

### 9.1 Prerequisites

- Self-hosted Langfuse v3 running (you've completed §1–§7 above).
- An **active** DataExpert proxy key in the form `sk-de-<64 hex chars>` (total 67 chars). Get it from the bootcamp dashboard. Inactive keys silently pass the UI's form validation but fail on every actual call.
- Network egress from the `langfuse-web` container to `www.dataexpert.io:443`. On Docker Desktop for Mac this works by default; on locked-down corp networks you may need to allowlist.

### 9.2 Pre-flight verification from the terminal

**Do this before touching the UI.** It confirms three things independently of Langfuse: the proxy is reachable, your key is active, and the request format is right. If this fails, stop — no UI configuration will fix it.

```bash
KEY="sk-de-REPLACE_WITH_YOUR_KEY"

curl -sS -D /tmp/headers.txt \
  -X POST "https://www.dataexpert.io/api/v1/anthropic/v1/messages" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-session-id: preflight-$(date +%s)" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-haiku-4-5",
    "max_tokens": 32,
    "messages": [{"role": "user", "content": "ping"}]
  }' \
  -o /tmp/body.txt

head -1 /tmp/headers.txt
head -c 400 /tmp/body.txt; echo
```

**Reading the result:**

| Output | Meaning | Action |
|---|---|---|
| `HTTP/2 200` + SSE body starting with `event: message_start` | Proxy works, key is active | ✅ Continue to §9.3 |
| `{"error":{"message":"API key is inactive"}}` | Key disabled on proxy side | Regenerate in DataExpert dashboard |
| `{"error":{"code":"missing_session_id"}}` | You omitted `x-session-id` header | Re-run with it |
| `{"error":{"message":"Invalid bearer token"}}` | Key format wrong, or sent as `Authorization: Bearer` | Use `x-api-key` header, not `Authorization` |
| HTML / `404 Not Found` | Wrong URL path | Check base URL and `/v1/messages` suffix |
| Hangs / connection refused | Network blocked | Check firewall / VPN |

**Three things the pre-flight tells you about the proxy's contract:**

1. **Auth is Anthropic-style, not OpenAI-style.** The key goes in `x-api-key`, not `Authorization: Bearer`.
2. **The proxy mandates a session identifier.** `x-session-id` is required on every request. The value can be anything — the proxy just wants a non-empty string. Alternatives the proxy also accepts: `x-correlation-id`, `metadata.session_id` in the JSON body, or a `"user"` field in the JSON body.
3. **The proxy always returns a streaming SSE response**, even when the request doesn't set `"stream": true`. This matters for the Langfuse Anthropic adapter (see §9.5.3).

### 9.3 UI navigation: getting to the form

Two ways:

**Option A — from Playground** (if you're already staring at it)
- Sidebar → **Playground**
- Yellow banner "No Model Configured" → click **LLM Connection Settings** link
- Or: under the Model box, click **+ Add LLM Connection**

**Option B — directly from Settings**
- Top-right project selector → **Settings**
- Left nav → **LLM Connections**
- Button: **+ Add LLM Connection**

Either opens the **New LLM Connection** modal.

### 9.4 Every field in the New LLM Connection form — exact values

#### 9.4.1 `LLM adapter`

**Value: `anthropic`**

- Dropdown options include `openai`, `anthropic`, `azure`, `bedrock`, `vertex-ai`, etc.
- The adapter determines which request schema Langfuse speaks. Because the env var is `ANTHROPIC_BASE_URL` and the endpoint lives under `/anthropic`, the proxy speaks Anthropic's `/v1/messages` schema.
- There is also an OpenAI-compatible endpoint at `https://www.dataexpert.io/api/v1/openai`. If you prefer GPT-shaped tooling (`/chat/completions`, `role: system`), choose the `openai` adapter instead. The rest of this section assumes `anthropic`.

**Why not `openai` with the anthropic URL?** The `openai` adapter sends `POST /chat/completions` with `Authorization: Bearer <key>`. The anthropic endpoint rejects both.

#### 9.4.2 `Provider name`

**Value: `dataexpert-anthropic`** (or any label you want)

- This is a **local identifier only** — Langfuse uses it to group connections in dropdowns.
- Cannot contain colons.
- You can have multiple connections with different provider names pointing at the same proxy (e.g., `dataexpert-anthropic-prod` and `dataexpert-anthropic-test`) if you want to A/B keys.

#### 9.4.3 `API Key`

**Value: your full DataExpert key, e.g. `sk-de-8b6883...24c3`**

- Paste the entire key. No prefix/suffix manipulation.
- Langfuse encrypts this at rest in Postgres using your `ENCRYPTION_KEY`. Rotate your Langfuse `ENCRYPTION_KEY` and you'll need to re-paste all LLM Connection keys.
- The key is never shown back in the UI after save — Langfuse only shows whether a key is set, not its value.

#### 9.4.4 Click **Show advanced settings**

Reveals three more fields.

#### 9.4.5 `API Base URL`

**Value: `https://www.dataexpert.io/api/v1/anthropic`**

- **No trailing slash.**
- **Do not append `/v1/messages`** — the `anthropic` adapter adds that automatically. If you set the base URL to `.../anthropic/v1/messages` you'll end up hitting `.../anthropic/v1/messages/v1/messages` and get 404s.
- The default base URL (`https://api.anthropic.com`) is shown as placeholder — you're overriding it.

#### 9.4.6 `Extra Headers` → click **+ Add Header**

Add **one** header. This is the single most important configuration detail — without it, 100% of calls fail.

| Header name | Header value |
|---|---|
| `x-session-id` | `langfuse-ui` |

**Why this is required:** the proxy enforces a session identifier on every upstream request for audit/billing purposes. The Langfuse Anthropic adapter does not set `x-session-id` natively (it's not a standard Anthropic API header), so you must supply one via Extra Headers.

**What value to use:**
- `langfuse-ui` is a stable, human-readable choice. Use it.
- Anything non-empty works. `langfuse`, `my-name-langfuse`, even a UUID. It just needs to be present.
- Don't use the literal string `$(...)` or similar shell substitution syntax — this field is a plain string, not interpreted.

**What NOT to do:**
- Do not add `anthropic-version` — the adapter sets it automatically.
- Do not add `Authorization: Bearer <key>` — that's the wrong auth scheme for the anthropic endpoint and will silently override what the adapter sends.
- Do not add `x-api-key` here — the adapter sets that from the API Key field.

#### 9.4.7 `Enable default models`

**Value: on (checked)**

- When on, Langfuse surfaces a curated list of Anthropic model slugs in dropdowns (Playground model picker, LLM-as-a-Judge model picker, etc.).
- With the DataExpert proxy, **the default list may include models the proxy doesn't expose.** Examples from the default list that may not be available: older Claude 2.x, Claude 3 Haiku. Picking an unavailable one returns `{"error":{"message":"model not found"}}` at call time.
- Safer play: keep it on, but also populate Custom models (§9.4.8) with the ones you know work. Custom models always appear.

#### 9.4.8 `Custom models`

**Add these three, one per line, confirmed working through the proxy:**

```
claude-haiku-4-5
claude-sonnet-4-5
claude-opus-4-5
```

Process:
1. Click **+ Add custom model name**.
2. Type `claude-haiku-4-5`. Press Enter (it becomes a chip).
3. Repeat for the other two.

Each becomes available in every model-picker dropdown across Langfuse after Save.

**Slug rules** — must match exactly what the proxy accepts. The Haiku slug the proxy returns in responses is `claude-haiku-4-5-20251001` (the full dated form), but the short form `claude-haiku-4-5` also works (the proxy resolves to latest).

#### 9.4.9 Final form — full state before Save

| Field | Value |
|---|---|
| LLM adapter | `anthropic` |
| Provider name | `dataexpert-anthropic` |
| API Key | `sk-de-...` (your real key) |
| API Base URL | `https://www.dataexpert.io/api/v1/anthropic` |
| Extra Headers | 1 row: `x-session-id` = `langfuse-ui` |
| Enable default models | on |
| Custom models | `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-opus-4-5` |

Click **Create connection**.

### 9.5 Under the hood — what happens when Langfuse calls the proxy

Understanding this helps you debug.

#### 9.5.1 Request composition

When you click **Run** in Playground with `claude-haiku-4-5`, the `langfuse-web` container makes this outbound call:

```http
POST https://www.dataexpert.io/api/v1/anthropic/v1/messages
x-api-key: sk-de-...                  ← from "API Key" field
anthropic-version: 2023-06-01         ← injected by adapter
x-session-id: langfuse-ui             ← from "Extra Headers"
content-type: application/json

{
  "model": "claude-haiku-4-5",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "..."}
  ]
}
```

- `x-api-key` and `anthropic-version` are adapter-controlled.
- `x-session-id` is the only reason Extra Headers exists.
- `max_tokens` comes from the Playground "Output tokens" slider.

#### 9.5.2 Response path

Proxy returns SSE stream → Langfuse adapter accumulates tokens → Langfuse UI renders the completed message and tracks usage tokens for the Playground session.

#### 9.5.3 Streaming gotcha

The proxy returns SSE even without `"stream": true` in the request. Langfuse's Anthropic adapter handles both streaming and non-streaming responses, so this works. But **if you ever see "invalid JSON in response"**, suspect streaming mismatch — the fix is on the proxy side, not Langfuse.

#### 9.5.4 What Langfuse stores

- The API Key, encrypted with `ENCRYPTION_KEY`, in Postgres.
- The base URL, extra headers, and custom model list, in plain text.
- **Every Playground run is logged as a Trace** in your current project, with full request/response + usage. This is intentional — it's how you evaluate prompts.

### 9.6 Testing the connection

#### 9.6.1 Playground smoke test

1. Sidebar → **Playground**.
2. **Model** dropdown → select `claude-haiku-4-5` (under "dataexpert-anthropic").
3. Ignore "System" box.
4. "User" box: type `reply only with: ok`
5. Click **Run** (top right).
6. Expected: **"ok"** appears in Assistant output within ~2 seconds, with usage tokens shown (input≈10, output≈2).

#### 9.6.2 Check the trace

Open **Tracing** in the sidebar. There's a new trace for the Playground run, showing the full prompt + completion + usage. Good: you can click in and see everything. **Be aware:** Playground calls live in the same trace list as your instrumented app. Filter by tag if you want to separate.

#### 9.6.3 Deeper test — temperature + max_tokens

Back in Playground, expand the model parameters panel:
- `temperature`: `0.7`
- `max_tokens`: `64`
- User: `write a haiku about docker`

Run. Expected: a haiku, output ≈ 30–50 tokens.

If the call fails here but §9.6.1 passed, the parameter values you set aren't supported by the proxy — try lowering `max_tokens` or resetting to defaults.

### 9.7 Using the connection in other Langfuse features

#### 9.7.1 LLM-as-a-Judge

1. Sidebar → **LLM-as-a-Judge** → **+ New evaluator**.
2. Template: pick one (e.g. **Hallucination**) or start blank.
3. **Model**: select your `claude-haiku-4-5` under `dataexpert-anthropic`.
4. Configure filter (which traces to judge), variable mapping, score schema.
5. **Execute** (one-shot) or **Activate** (continuous on new traces).

Each evaluation sends one LLM call through the proxy. At Haiku rates through the proxy, this is cheap.

#### 9.7.2 Prompt Experiments

1. Sidebar → **Datasets** → create/open a dataset with input/expected items.
2. Sidebar → **Prompts** → create a prompt version.
3. **Prompt Experiments** → new experiment → pick the dataset + prompt + model (your Haiku).
4. Run.

Each dataset item = one LLM call through the proxy. Watch the proxy's rate limits on large datasets.

#### 9.7.3 Prompts → Run in Playground

Any prompt version has a **Run in Playground** button that preloads that prompt, ready to test against your connected model. Same call path as §9.6.

### 9.8 Every failure mode and its fix

#### 9.8.1 At connection-creation time

| Error in UI | Cause | Fix |
|---|---|---|
| "Invalid base URL" | Trailing slash or malformed URL | Use exactly `https://www.dataexpert.io/api/v1/anthropic`, no trailing slash |
| Form hangs, no save | UI bug, rare | Refresh, retry |

#### 9.8.2 At first call (Playground Run / Eval execution)

These are the ones you'll actually see. Error messages are paraphrased but recognizable.

| Error message | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | API Key wrong/missing | Re-open connection, re-paste key |
| `API key is inactive` | Proxy disabled this key | Regenerate in DataExpert dashboard, update connection |
| `missing_session_id` | Extra Headers row absent or blank | Add `x-session-id: langfuse-ui` to Extra Headers |
| `model not found` / `404` | Model slug not on this proxy | Remove from Custom models; pick a different slug |
| `Invalid bearer token` | `Authorization: Bearer` header was added manually | Remove that Extra Header row — adapter handles auth |
| Connection timeout / DNS error | Docker container can't reach `www.dataexpert.io` | Check host network / VPN / corp proxy |
| `Rate limit exceeded` | Too many concurrent calls | Reduce experiment parallelism, or add a second key |
| HTML returned instead of JSON | Wrong base URL path | Reset to `.../api/v1/anthropic` exactly |
| `anthropic-version header required` | Adapter not adding it (odd) | Manually add `anthropic-version: 2023-06-01` as Extra Header |

#### 9.8.3 Silent failures

- **Playground returns empty output** but no error → raise `max_tokens`. The proxy may truncate if max_tokens is below the model's minimum-output.
- **LLM-as-a-Judge stuck at "running"** → worker container can't reach proxy. Check `docker logs <project>-langfuse-worker-1 --tail 50` for network errors. Restart if needed.
- **Usage tokens show as 0** in the trace for a successful call → proxy didn't return usage metadata on that response. Not actionable from Langfuse side.

#### 9.8.4 How to see real error detail

Langfuse sometimes surfaces a pithy message and swallows the proxy's JSON error body. To see the raw upstream error:

```bash
docker logs <project>-langfuse-web-1 --tail 100 | grep -iE "error|anthropic|proxy"
```

The web container logs the outbound call result, including the full response body on non-2xx.

### 9.9 Key rotation and maintenance

#### 9.9.1 Rotating the DataExpert key

When the bootcamp rotates your key (or you regenerate one), update both places:

1. Any `.env` file you use locally (e.g., the same key lives in your `ANTHROPIC_API_KEY` env for direct SDK use).
2. **Langfuse UI** → Settings → LLM Connections → your provider → **Edit** → paste new key → Save.

You cannot see the old key after save, so you can't "check" it — you just overwrite.

#### 9.9.2 Deleting the connection

Settings → LLM Connections → trash icon. **Deletes historical Playground and eval traces' access to the model** but the trace data itself is retained.

#### 9.9.3 Multiple environments

You can scope connections per-project but not per-environment. If you need "production" vs "staging" keys, create separate Langfuse projects, each with its own connection.

### 9.10 Quick-reference one-page summary

Copy-pasteable into your notes:

```
Langfuse → Settings → LLM Connections → + Add LLM Connection

  LLM adapter          anthropic
  Provider name        dataexpert-anthropic
  API Key              sk-de-... (from DataExpert dashboard)
  Show advanced settings:
    API Base URL       https://www.dataexpert.io/api/v1/anthropic
    Extra Headers      x-session-id = langfuse-ui
    Enable defaults    on
    Custom models      claude-haiku-4-5
                       claude-sonnet-4-5
                       claude-opus-4-5

  Pre-flight curl (run BEFORE touching UI):
    curl -X POST "https://www.dataexpert.io/api/v1/anthropic/v1/messages" \
      -H "x-api-key: $KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "x-session-id: preflight-$(date +%s)" \
      -H "content-type: application/json" \
      -d '{"model":"claude-haiku-4-5","max_tokens":16,
           "messages":[{"role":"user","content":"ping"}]}'
    → HTTP 200 + "event: message_start" = proceed
```

---

## 10. Bring down / reset

**Stop the stack, keep the data:**

```bash
docker compose down
```

**Nuke everything (destroys all traces, users, API keys — you'll need to sign up again):**

```bash
docker compose down -v
```

After `-v` you'll also need to re-create the MinIO bucket from §6 before traces start flowing again.

---

## 11. Troubleshooting cheatsheet

| Symptom | Cause | Fix |
|---|---|---|
| Python: `401 Unauthorized` on flush | `LANGFUSE_HOST` missing/wrong, or keys blank | Set `LANGFUSE_HOST=http://localhost:3333` and paste both keys |
| Python: `500 Internal Server Error` on flush, retries | MinIO bucket missing | Run the `mc mb local/langfuse` command from §6 |
| Python: `update_current_trace` AttributeError | v3 API on v4 SDK | Use `propagate_attributes(...)` + `set_current_trace_io(...)` instead |
| UI banner "No Model Configured" in Playground | No LLM connection created yet | Settings → LLM Connections → Add |
| LLM Connection test fails with `API key is inactive` | DataExpert key disabled | Regenerate in bootcamp dashboard |
| LLM Connection test fails with `missing_session_id` | Proxy rejects requests without session id | Add Extra Header `x-session-id: langfuse-ui` |
| `ENCRYPTION_KEY` boot error | Not 64 hex chars | `openssl rand -hex 32` |
| ClickHouse exits on start | < 8 GB allocated to Docker Desktop | Settings → Resources → bump memory |

---

## 12. Further reading

- Langfuse docs — https://langfuse.com/docs
- Python SDK reference — https://python.reference.langfuse.com/langfuse
- v3 → v4 Python migration (important if you follow older tutorials) — https://langfuse.com/docs/observability/sdk/upgrade-path
- Anthropic-compatible endpoint format — https://docs.anthropic.com/en/api/messages
