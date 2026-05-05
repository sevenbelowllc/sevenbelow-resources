# CLAUDE.md — Release Radar

## Project Overview

Release Radar is a dual-mode GitHub activity summarizer built on the Anthropic Claude API.

**Interactive mode:** Claude Code skill invocations. Each skill in `claude_skills/` has a
`SKILL.md` file that Claude Code loads as the system prompt when the user invokes the skill
by name (e.g., `/triage-issue`, `/summarize-pr`, `/digest-commits`, `/draft-email`, `/handoff`).

**Batch CLI mode:** A Python CLI at `scripts/release_radar.py` that reads JSON input files,
applies a guardrail chain around every Claude API call, and writes JSON output to stdout.
Subcommands: `triage`, `summarize`, `digest`, `email`, `--weekly`.

Both modes share the same guardrails and the same Claude model
(`claude-sonnet-4-20250514`).

---

## Build / Test / Lint Commands

```bash
# Install dependencies (from project root)
pip install -r requirements.txt

# Lint — must pass before any commit
ruff check .
ruff format --check .

# Type checking
mypy scripts/ guardrails/ --ignore-missing-imports

# Unit tests only (no API calls)
pytest tests/unit/ -v

# Integration tests (requires ANTHROPIC_API_KEY in .env)
pytest tests/integration/ -v

# Full validation — run this before claiming any task is done
ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest tests/unit/ -v
```

### Validation

**Do NOT claim a task is done without passing validation output.**

Before marking any task complete, run the full validation command above and confirm:
- `ruff check .` exits 0 (no lint errors)
- `ruff format --check .` exits 0 (no formatting violations)
- `mypy` exits 0 or shows only expected import warnings
- All unit tests pass (`pytest tests/unit/ -v`)

Integration tests require a live `ANTHROPIC_API_KEY` and make real API calls — they are
optional for local development but must pass in CI.

---

## Folder Map

```
release-radar/
  claude_skills/          # One subdirectory per skill, each with SKILL.md
    digest-commits/
    draft-email/
    handoff/
    summarize-pr/
    triage-issue/
  guardrails/             # Guardrail chain — pre and post processing
    base.py               # GuardrailError, Guardrail base class
    chain.py              # GuardrailChain (run_pre / run_post)
    citation.py           # Require source citations in output
    insufficient_context.py  # Reject inputs that lack required fields
    pii_redaction.py      # Regex-based PII scrubbing (12+ patterns)
    schema_validation.py  # Validate output against JSON schema
    schemas.py            # Pydantic-free JSON schema definitions
    uncertainty.py        # Flag low-confidence outputs
    hooks/                # Claude Code hook scripts (pre-tool, post-tool)
  scripts/
    release_radar.py      # Batch CLI entrypoint
    gh_adapter.py         # GitHub API adapter (mock + live)
  tests/
    unit/                 # Fast tests, no API calls, all mocked
    integration/          # Live API tests, marked with @pytest.mark.integration
    conftest.py           # Shared fixtures
  data/                   # Sample JSON inputs for manual testing
  docs/                   # Design notes and rationale documents
  pyproject.toml          # Ruff, mypy, pytest config
  requirements.txt        # Runtime + dev dependencies
```

---

## Coding Conventions

- **Python 3.11+** — use `dict | None` union syntax, `match` statements where appropriate
- **100-character line limit** — enforced by ruff (`line-length = 100` in pyproject.toml)
- **Guardrail interface** — every guardrail inherits from `guardrails.base.Guardrail` and
  overrides `check_input(data, skill)` and/or `check_output(data, skill)`. Raise
  `GuardrailError` on failure; return the (possibly mutated) dict on success.
- **Skill format** — each skill directory must contain exactly one `SKILL.md` that serves as
  the Claude system prompt. The SKILL.md must instruct Claude to return only valid JSON.
- **JSON output contract** — all Claude responses must be parseable JSON. The CLI extracts
  the first fenced JSON block from the response text before parsing.
- **No secrets in code** — all API keys via `.env` (python-dotenv); `.env` is gitignored.
- **Type hints required** on all public functions and methods.
- **Imports** — sorted by ruff/isort. Standard lib first, third-party second, local last.

---

## Deployment / Runtime Constraints

- Requires **Python 3.11+**
- Runs inside **Claude Code** for interactive skill mode
- Requires `.env` file with:
  - `ANTHROPIC_API_KEY` — for all Claude API calls
  - `GITHUB_TOKEN` — optional, for live GitHub adapter (`--live` flag)
- No database; all state is in-memory or in JSON files
- Model pinned to `claude-sonnet-4-20250514` — do not change without updating tests
- Integration tests make real API calls and will consume tokens

---

## Security / Privacy Boundaries

- **PII redaction is mandatory** — `PIIRedactionGuardrail` runs as both pre- and post-guardrail
  on every CLI invocation. Never bypass it.
- Patterns covered: email, SSN, phone, credit card, IPv4, API keys, private keys, connection
  strings, internal URLs, and more.
- **`.env` must be gitignored** — verify before any commit touching environment config.
- Do not log raw API responses to stdout in production paths.
- The `handoff` skill writes to `memory/HANDOFF.md` — review before committing that file.

---

## Do / Don't

**Do:**
- Run the full validation command before marking any task done
- Add a unit test for every new guardrail or guardrail behavior
- Add an integration test when adding a new CLI subcommand
- Keep SKILL.md files concise — Claude reads them as system prompts on every invocation
- Use mock data from `data/` for unit tests; never call real APIs in unit tests
- Update `schemas.py` when the output shape of a skill changes

**Don't:**
- Skip the guardrail chain for any Claude API call in the CLI
- Hardcode API keys, tokens, or secrets anywhere in the codebase
- Write unit tests that make real HTTP calls (use fixtures and mocks)
- Add a new skill without a corresponding `SKILL.md`
- Modify `pyproject.toml` ruff or mypy settings without updating this file

---

## Common Pitfalls

**Rate limits** — The Anthropic API enforces per-minute token limits. The `--weekly` command
calls Claude multiple times in sequence. If you hit a rate limit error, add a short sleep
between skill calls or reduce the number of items processed.

**Mock vs. live tests** — `gh_adapter.py` defaults to mock mode. Integration tests that use
`--live` require a valid `GITHUB_TOKEN` and will make real API calls. Do not run integration
tests in environments without credentials.

**Schema drift** — If you change what a SKILL.md instructs Claude to return, update the
corresponding JSON schema in `schemas.py` and the `SchemaValidationGuardrail` validation logic.
Mismatches cause silent validation failures.

**JSON extraction fragility** — The CLI extracts JSON from Claude's response by splitting on
`` ```json `` or `` ``` `` fences. If Claude returns JSON without fences (or with extra text
before the fence), parsing will fail. Ensure SKILL.md files explicitly instruct Claude to wrap
output in a JSON code fence.

**Hook API syntax** — Claude Code hooks use a specific JSON schema for stdin/stdout. If a hook
script fails silently, check that it reads from stdin and writes to stdout in the expected
format. See `guardrails/hooks/` for reference implementations.

**Expensive integration tests** — Each integration test call costs real tokens. Do not add
integration tests for trivial behavior that can be unit-tested with mocks.
