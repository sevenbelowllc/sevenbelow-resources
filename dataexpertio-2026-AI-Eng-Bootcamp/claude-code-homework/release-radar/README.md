# Release Radar

GitHub activity summarizer powered by Claude. Triage issues, summarize PRs, digest commits,
and draft stakeholder emails — interactively via Claude Code skills or in batch via CLI.

---

## Setup

```bash
# 1. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env   # then edit with your keys
# Required: ANTHROPIC_API_KEY
# Optional: GITHUB_TOKEN (for --live mode)
```

---

## Interactive Mode (Claude Code Skills)

Open this project in Claude Code. The following skills are available — invoke them by
typing the skill name in the Claude Code chat:

| Skill | What it does |
|---|---|
| `triage-issue` | Classify a GitHub issue by severity, type, and actionability |
| `summarize-pr` | Summarize a pull request: changes, risks, and review guidance |
| `digest-commits` | Group commits into themed categories for a date range |
| `draft-email` | Write a non-technical stakeholder update from a commit digest |
| `send-email` | Create a Gmail draft from `draft-email` output via the Gmail MCP server |
| `handoff` | Generate a session handoff document and save to `memory/HANDOFF.md` |

Each skill reads its system prompt from `claude_skills/<skill-name>/SKILL.md`.

### Gmail MCP Integration (`send-email`)

The `send-email` skill requires the **Gmail MCP server** connected in Claude Code:

1. In Claude Code, open `/mcp` and connect the Gmail MCP server
2. Authenticate with your Google account when prompted
3. Run `/draft-email` to generate email content, then `/send-email` — it calls
   `gmail_create_draft` (exact MCP tool name) to save a reviewable draft
4. The skill confirms subject/recipient before creating the draft and warns on any PII

Sample draft IDs from verified runs: `r8473920184739201` and `r1920384756192038`
(visible in `docs/design-note.md` screenshots and `docs/screenshots/`)

---

## Batch CLI Mode

Run `scripts/release_radar.py` directly. All subcommands read JSON input files and write
JSON to stdout.

### Triage issues

```bash
python scripts/release_radar.py triage --input data/issues.json
```

Input: array of GitHub issue objects.
Output: array of `{issue_id, result}` objects with triage classification.

### Summarize PRs

```bash
python scripts/release_radar.py summarize --input data/pull_requests.json
```

Input: array of GitHub PR objects.
Output: array of `{pr_id, result}` objects with PR summaries.

### Digest commits

```bash
python scripts/release_radar.py digest --input data/commits.json
```

Input: array of commit objects (or `{commits: [...], date_range: {...}}`).
Output: categorized commit digest with themes and highlights.

### Draft stakeholder email

```bash
python scripts/release_radar.py email --input data/commits.json --prs data/pull_requests.json
```

`--prs` is optional. Combines a commit digest and up to 5 PR summaries into a draft email.

### Full weekly report

```bash
# Mock data (default)
python scripts/release_radar.py --weekly --since 2026-04-01 --until 2026-04-07

# Live GitHub data
python scripts/release_radar.py --weekly --live --repo owner/repo \
  --since 2026-04-01 --until 2026-04-07 --token ghp_yourtoken
```

Runs all four skills in sequence and outputs a combined JSON report.

---

## Guardrails

Every CLI invocation applies a five-guardrail chain around each Claude API call:

| Guardrail | Stage | What it does |
|---|---|---|
| `InsufficientContextGuardrail` | Pre | Rejects inputs missing required fields |
| `PIIRedactionGuardrail` | Pre + Post | Scrubs email, SSN, phone, CC, API keys, and more |
| `SchemaValidationGuardrail` | Post | Validates output against the expected JSON schema |
| `CitationGuardrail` | Post | Requires source citations where applicable |
| `UncertaintyGuardrail` | Post | Flags outputs with low-confidence language |

PII redaction is applied to both input and output on every call. It cannot be bypassed.

---

## Testing

```bash
# Unit tests (no API calls)
pytest tests/unit/ -v

# Integration tests (requires ANTHROPIC_API_KEY in .env)
pytest tests/integration/ -v

# Lint and format check
ruff check .
ruff format --check .

# Type checking
mypy scripts/ guardrails/ --ignore-missing-imports

# Full validation (run before marking any task done)
ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest tests/unit/ -v
```

---

## Project Details

See [CLAUDE.md](CLAUDE.md) for the full coding conventions, guardrail interface contract,
deployment constraints, security boundaries, and common pitfalls.
