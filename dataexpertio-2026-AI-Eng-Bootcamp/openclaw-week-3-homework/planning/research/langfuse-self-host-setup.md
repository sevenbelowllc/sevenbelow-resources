# Langfuse v3 — Self-Hosted Setup Reference

**Status:** Reference material for the Week-3 OpenClaw homework. **Not** a committed solution artifact. This is what I'd hand a teammate who asked "how do I bring up Langfuse locally for post-hoc trace ingestion?"

**Scope:** single-host Docker Compose bring-up, rehearsal-grade. Port remapped to **3333** to avoid collisions with the many other tools that squat on 3000. Not hardened for production — see the "For production" notes at the bottom.

---

## 1. What Langfuse v3 actually is (before you install it)

Langfuse v3 is **not one container**. The minimum stack is six services:

| Service | Image | Purpose |
|---|---|---|
| `langfuse-web` | `langfuse/langfuse:3` | UI + ingestion API (you hit this one) |
| `langfuse-worker` | `langfuse/langfuse-worker:3` | Async processing (batching, aggregations) |
| `postgres` | `postgres:15` | Auth, projects, API keys, prompts, scores |
| `clickhouse` | `clickhouse/clickhouse-server` | Traces, observations, generations (the heavy table) |
| `redis` | `redis:7` | Queues + caches between web & worker |
| `minio` | `minio/minio` | S3-compatible blob store for large event payloads |

The upstream repo ships a `docker-compose.yml` that wires all six together. Use it. Don't roll your own from scratch unless you have a reason.

---

## 2. Prerequisites

- Docker Desktop (or equivalent) with ≥ 8 GB allocated to the VM. ClickHouse is the memory hog.
- `openssl` (for secret generation — already on macOS/Linux).
- ~5 GB free disk for volumes.
- Port **3333** free on the host. (Langfuse internally still listens on 3000 — we remap at the host edge.)
- A shell. That's it.

---

## 3. Bring-up (copy-paste)

```bash
# 1. Clone the Langfuse repo somewhere outside this homework repo
#    (we don't vendor it — we just use its compose file)
git clone https://github.com/langfuse/langfuse.git ~/src/langfuse
cd ~/src/langfuse

# 2. Check out the production branch (main may be unstable)
git checkout production

# 3. Generate secrets — DO THIS, do not use the defaults in their example
export NEXTAUTH_SECRET="$(openssl rand -base64 32)"
export SALT="$(openssl rand -base64 32)"
export ENCRYPTION_KEY="$(openssl rand -hex 32)"   # MUST be 64 hex chars (32 bytes)

# 4. Create a .env file with the generated secrets and the port remap
cat > .env <<EOF
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
SALT=${SALT}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
NEXTAUTH_URL=http://localhost:3333
TELEMETRY_ENABLED=false
EOF

# 5. Bring it up
docker compose up -d
```

Then **edit the compose file's port mapping** for the `langfuse-web` service so the host side is 3333:

```yaml
  langfuse-web:
    # ...
    ports:
      - "3333:3000"   # host 3333 → container 3000
```

Re-run `docker compose up -d` after the edit.

---

## 4. First-run bootstrap

1. Open **http://localhost:3333** in a browser.
2. Sign up (first account becomes the instance owner — no email verification on self-host by default).
3. Create an **Organization** → inside it create a **Project**. Name it `openclaw-week3`.
4. In the project, go to **Settings → API Keys** → create a new key pair. You'll get:
   - `LANGFUSE_PUBLIC_KEY` (starts with `[langfuse-pk-removed]`)
   - `LANGFUSE_SECRET_KEY` (starts with `[langfuse-sk-removed]`)
5. Save these in the homework's `solution/infra/.env` (gitignored) — the Python ingester will read them:

   ```bash
   LANGFUSE_HOST=http://localhost:3333
   LANGFUSE_PUBLIC_KEY=[langfuse-pk-removed]
   LANGFUSE_SECRET_KEY=[langfuse-sk-removed]
   ```

6. Smoke-test with the Python SDK:

   ```python
   from langfuse import get_client
   lf = get_client()            # reads env vars
   lf.auth_check()              # prints True on success
   with lf.start_as_current_span(name="smoke-test") as s:
       s.update(input={"hello": "world"}, output={"ok": True})
   lf.flush()
   ```

   Refresh the Langfuse UI → you should see one trace under the project. If you don't, check `docker compose logs langfuse-web`.

---

## 5. Day-to-day operation

```bash
docker compose ps                    # is everything up?
docker compose logs -f langfuse-web  # tail the UI/ingestion logs
docker compose logs -f langfuse-worker
docker compose restart langfuse-web  # after .env or compose edits
docker compose down                  # stop (preserves volumes)
docker compose down -v               # stop AND wipe data — destructive
```

**Data lives in named Docker volumes.** `docker compose down` keeps them. `docker compose down -v` destroys them — all traces, projects, keys, prompts gone. Don't confuse the two.

---

## 6. Connecting the OpenClaw week-3 ingester

The ingester (`solution/tools/ingest_traces.py`) is a plain Python script that:

1. Reads committed JSONL from `solution/evidence/traces/**/*.jsonl`.
2. For each session, creates a Langfuse trace with metadata (`variant=inefficient|efficient`, `scenario=<id>`, `track=sim|real`).
3. For each event in the session, creates a nested span or generation with the right token counts.
4. Calls `lf.flush()` at the end.

It requires the three env vars from §4 step 5. That's it — no OTel collector, no Pub/Sub, no sidecar. Post-hoc by design because OpenClaw doesn't expose an instrumentation point (see Section 1 of the brainstorm checkpoint).

---

## 7. Cost / safety notes

- **This is rehearsal-grade, not production.** MinIO runs with default credentials, Postgres password is whatever the compose file ships, there's no TLS, no backup, no auth in front of the UI beyond Langfuse's own signup flow.
- **Do not expose port 3333 to the internet.** Bind it to localhost-only (which Docker does by default on Mac/Linux) or put it behind a VPN/tunnel if you need remote access.
- **Do not commit `.env`.** Only commit `.env.example` with placeholder values. The homework repo's `.gitignore` should already cover this — double-check before the first commit.

---

## 8. For production (out of scope for this homework, but for reference)

If you were actually running this for a live agent service in GCP (see brainstorm discussion), you would NOT use this compose stack. You'd use one of:

- **Langfuse Cloud** (`cloud.langfuse.com`) — they run it, you just send events.
- **Langfuse Terraform module** for AWS (`langfuse/langfuse-terraform-aws`) — EKS + Aurora + ElastiCache + S3.
- **Helm chart** (`langfuse/langfuse-k8s`) on GKE — with external Postgres (Cloud SQL), Memorystore for Redis, ClickHouse Cloud or self-managed, and GCS for blobs.

Plus a durability layer in front of it (Pub/Sub buffer + consumer) so a Langfuse outage doesn't lose traces. That pattern is the Week-3 brainstorm's "Pattern B."

---

## 9. Troubleshooting quick hits

| Symptom | Likely cause |
|---|---|
| `langfuse-web` keeps restarting, logs mention `ENCRYPTION_KEY` | Key is not 64 hex chars. Regenerate with `openssl rand -hex 32`. |
| UI loads but signup 500s | Postgres not ready yet. `docker compose logs postgres` — wait for it to finish init, then `docker compose restart langfuse-web`. |
| Traces never appear in UI | Public/secret key mismatch, or `LANGFUSE_HOST` pointed at a different instance. Run `lf.auth_check()` from the smoke test. |
| ClickHouse OOM-killed | Docker VM has < 8 GB RAM. Bump it in Docker Desktop settings. |
| Port 3333 already in use | Some other tool is squatting. Pick 3334 and update both `.env` (`NEXTAUTH_URL`) and the compose port mapping. |

---

## 10. Source material

- Upstream repo: https://github.com/langfuse/langfuse
- Self-hosting docs: https://langfuse.com/self-hosting
- v2 → v3 upgrade guide (explains why the stack got bigger): https://langfuse.com/self-hosting/upgrade-guides/upgrade-v2-to-v3
- Python SDK: https://langfuse.com/docs/sdk/python
