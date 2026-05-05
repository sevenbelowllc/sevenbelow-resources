# LangChain Homework 2026 — Project Plan

**Last updated:** 2026-04-05

---

## Overview

Three assignments on real-world LLM agent failure modes. Each requires a `solution.py`,
a `writeup.md`, and supporting evidence (token reports, sample output, or before/after comparisons).

---

## Assignment Status

| # | Title | Solution | Writeup | Evidence | Status |
|---|-------|----------|---------|----------|--------|
| A1 | Context Overflow Tool | done (`solution.py`, `solution-g8.py`) | needs replacement | needs token report | **In progress** |
| A2 | The Infinite Researcher | done (`solution.py`) | needs update | 13/13 test checks pass | **In progress** |
| A3 | MCP Tool Overload | not started | not started | not started | **Pending** |

---

## Assignment 1 — Context Overflow Tool

### What exists
- `a1/starter.py` — broken agent (dumps entire DB into context)
- `a1/solution.py` — fixed agent
- `a1/solution-g8.py` — alternate / grade-8 variant
- `a1/writeup.md` — exists but will be replaced

### Work items

#### 1.1 Token Usage Comparison Script
**File:** `a1/token_report.py`

Runs both `starter.py` and `solution.py` against the live OpenAI API using the
same set of test queries. Captures real token usage from API response metadata
(`usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`).

Requirements:
- Use the same fixed query set for both runs (defined as a constant in the script)
- Capture per-query token counts from response metadata
- Print a side-by-side table: query | starter tokens | solution tokens | reduction %
- Print aggregate totals and cost estimate (gpt-4o-mini pricing)
- Write results to `a1/token_report.md` for submission

Constraints:
- Requires `OPENAI_API_KEY` in `.env` (fail fast with a clear error if missing)
- Must not modify `starter.py` or `solution.py`
- Starter.py will be expensive to run; add a `--dry-run` flag that skips it and
  uses hardcoded baseline numbers from the writeup instead

#### 1.2 New Writeup
**File:** `a1/writeup.md` (replace existing)

Fresh writeup covering:
- What was broken and why (root cause, not just symptoms)
- The fix: typed params, Python-side filtering, output cap, session caching
- Token usage table (populated from `token_report.py` output)
- Key design principle: data retrieval belongs in Python, not the LLM

Target: 400–500 words + token table.

---

## Assignment 2 — The Infinite Researcher

### What exists
- `a2/starter.py` — runaway ReAct research agent

### Work items (plan only — implementation deferred)

#### 2.1 Spec File
**File:** `planning/specs/a2_infinite_researcher.md`

Capture before implementing:
- Root cause analysis of why the agent loops forever
- Proposed stopping conditions (step budget, note saturation check, confidence score)
- Proposed cost controls (token budget, max search calls)
- Prompt changes needed to make the agent converge
- Definition of done: agent answers "pros and cons of microservices" in ≤ 10 steps,
  under a defined token budget, without crashing

#### 2.2 Solution
**File:** `a2/solution.py`
- Deferred until spec is approved

#### 2.3 Writeup
**File:** `a2/writeup.md`
- Deferred until solution is working

#### 2.4 Evidence
- Sample console output showing convergence within bounds
- Deferred until solution is working

---

## Assignment 3 — MCP Tool Overload

### What exists
- `a3/starter.py` — agent with all 53 tools loaded

### Work items (plan only — implementation deferred)

#### 3.1 Spec File
**File:** `planning/specs/a3_mcp_tool_overload.md`

Capture before implementing:
- Root cause: 53 tool schemas in every prompt (~8K tokens of overhead)
- Middleware design: query classifier → select N relevant tools → inject only those
- Tool routing: pre-classify query to GitHub / Slack / Database server
- Embedding vs. keyword routing tradeoff (simple keyword first)
- Definition of done: average tool count per query ≤ 10, correct tool selected
  for a standard test query set, token overhead < 2K per turn

#### 3.2 Solution
**File:** `a3/solution.py`
- Deferred until spec is approved

#### 3.3 Writeup
**File:** `a3/writeup.md`
- Deferred until solution is working
- Must include ASCII or Mermaid architecture diagram

#### 3.4 Evidence
**File:** `a3/comparison.md`
- Before/after table: tool count per query, response accuracy, token usage
- Deferred until solution is working

---

## Execution Order

1. **A1 token report script** — write `a1/token_report.py`
2. **A1 writeup** — run report, write `a1/writeup.md`
3. **A2 spec** — analyze `a2/starter.py`, write `planning/specs/a2_infinite_researcher.md`
4. **A3 spec** — analyze `a3/starter.py`, write `planning/specs/a3_mcp_tool_overload.md`
5. **A2 solution** — implement after spec review
6. **A3 solution** — implement after spec review
7. **A2 writeup + evidence** — after solution is working
8. **A3 writeup + evidence** — after solution is working

---

## Notes

- All scripts require `OPENAI_API_KEY` in `a1/.env` (copy from `.env.example`)
- Use `gpt-4o-mini` for all runs unless the assignment specifies otherwise
- Activate venv before running: `source .venv/bin/activate`
