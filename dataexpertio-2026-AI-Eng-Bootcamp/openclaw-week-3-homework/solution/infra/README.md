# Langfuse v3 self-hosted infra

See also: `../../planning/research/langfuse-self-host-setup.md` for the
full reference doc.

## Bring up

```bash
cp .env.example .env
# generate secrets and paste into .env (ENCRYPTION_KEY, SALT, NEXTAUTH_SECRET, db passwords)
openssl rand -hex 32    # ENCRYPTION_KEY, NEXTAUTH_SECRET
openssl rand -hex 16    # SALT
docker compose up -d

# Create the MinIO bucket used for event uploads.
# Langfuse v3 does NOT auto-create this; span exports 500 without it.
docker exec langfuse-openclaw-hw-minio-1 \
  mc alias set local http://localhost:9000 minio "$(grep LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY .env | cut -d= -f2)"
docker exec langfuse-openclaw-hw-minio-1 mc mb local/langfuse
```

UI: http://localhost:3333

First-run: sign up as the first user (becomes org owner); create API
keys under the `openclaw-week-3-homework` project and paste them into
`.env` as `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`. The Python SDK
reads `LANGFUSE_HOST` (not `LANGFUSE_BASE_URL`) — keep that name exact.

## Tear down (preserve volumes)

```bash
docker compose down
```

## Tear down + destroy volumes (DANGEROUS)

```bash
docker compose down -v
```
