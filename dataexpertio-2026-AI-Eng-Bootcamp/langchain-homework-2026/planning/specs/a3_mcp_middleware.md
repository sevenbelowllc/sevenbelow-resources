# Spec: Assignment 3 — MCP Tool Overload

**Created:** 2026-04-07
**Status:** Implemented — all 7 queries pass, token report generated
**Target file:** `assignment3_mcp_middleware/solution.py`

---

## Context

The starter loads all 25 tools from 3 MCP servers (GitHub 8, Slack 6, Database 11) into
every agent call. This causes ~2,200 tokens of tool descriptions per turn, tool confusion,
and inflated cost. The fix: keyword-based router middleware that selects only relevant
tools per query.

---

## Protected Sections (DO NOT MODIFY)

These must be copied verbatim from `starter.py`:

1. **Module docstring + imports** (starter lines 1-25)
2. **`_make_tool()` function** (starter lines 33-56)
3. **`GITHUB_TOOLS`** (starter lines 59-77) — 8 tools
4. **`SLACK_TOOLS`** (starter lines 80-93) — 6 tools
5. **`DATABASE_TOOLS`** (starter lines 96-119) — 11 tools
6. **`ALL_TOOLS` block + diagnostic prints** (solution lines 122-136):
   ```python
   ALL_TOOLS = GITHUB_TOOLS + SLACK_TOOLS + DATABASE_TOOLS

   print(f"📊 Total tools loaded: {len(ALL_TOOLS)}")
   print(f"   GitHub:   {len(GITHUB_TOOLS)} tools")
   print(f"   Slack:    {len(SLACK_TOOLS)} tools")
   print(f"   Database: {len(DATABASE_TOOLS)} tools")

   total_desc_chars = sum(len(t.name) + len(t.description) + len(str(t.args_schema.model_json_schema())) for t in ALL_TOOLS)
   estimated_tokens = total_desc_chars // 4
   print(f"   Estimated tool description tokens: ~{estimated_tokens:,}")
   ```
7. **`TEST_QUERIES`** (starter lines 173-186) — 7 queries
8. **`main()` function** (starter lines 189-210)

**Note:** Starter imports `AgentExecutor` + `create_tool_calling_agent` which don't exist
in langchain 1.2.15. Solution replaces with `create_react_agent` from `langgraph.prebuilt`.

---

## Broken Sections (MUST FIX)

1. **`ALL_TOOLS` block** (starter lines 126-136) — dumps all tools with no routing
2. **`create_overloaded_agent()`** (starter lines 143-166) — loads ALL tools into one agent

---

## Solution Architecture

### Keyword Router (`route_query`)

Zero-cost Python string matching — no LLM calls:

```
GitHub keywords:   issue, bug, error, pr, repo, code, commit, branch, merge, github
Slack keywords:    message, channel, slack, dm, send, post, notify, #
Database keywords: table, query, sql, database, row, count, schema, production, errors
```

- Single match → one server's tools
- Multiple matches → tools from all matched servers
- No match → fallback to all tools

### Tool Selector (`select_tools`)

Filters `ALL_TOOLS` by server name using `TOOLS_BY_SERVER` dict.

### Per-Query Agent (`create_routed_agent`)

Each query gets a fresh `create_react_agent` with:
- Only the routed tools (6-19 vs 25)
- Dynamic system prompt naming active servers
- `recursion_limit=15`

---

## Routing Results

| # | Query | Servers | Tools | Reduction |
|---|-------|---------|-------|-----------|
| 1 | Create GitHub issue | github | 8 | 68% fewer |
| 2 | Send Slack message | slack | 6 | 76% fewer |
| 3 | Count database rows | database | 11 | 56% fewer |
| 4 | Search for auth bug | github | 8 | 68% fewer |
| 5 | Messages or issues about deploy | github, slack | 14 | 44% fewer |
| 6 | GitHub issue + post to Slack | github, slack | 14 | 44% fewer |
| 7 | Query DB + create issue | github, database | 19 | 24% fewer |

---

## Token Usage

- **Solution:** 21 LLM calls, 16,313 input + 803 output = 17,116 tokens, $0.003
- **Starter:** Cannot run (import error in langchain 1.2.15)

---

## Files

| File | Status |
|------|--------|
| `assignment3_mcp_middleware/solution.py` | Complete, runs |
| `assignment3_mcp_middleware/writeup.md` | Complete, ~460 words |
| `assignment3_mcp_middleware/token-usage.txt` | Generated |

---

## Grading Rubric Concerns

Based on a1/a2 grading experience, the rubric evaluates:

| Item | How solution addresses it |
|------|--------------------------|
| Context Management | Router reduces tool descriptions per call by 44-76% |
| Prompt Clarity | Dynamic system prompt names active servers explicitly |
| System Prompt Usage | Per-query system prompt with server context |
| Skills/Tool Usage | LLM calls tools via tool-calling API (visible in trace) |
| Token Efficiency | Fewer tool descriptions = fewer tokens per call |
| Output Format | Tool responses are structured JSON |
| Conversation Design | Multi-turn agent loop with tool calls |

---

## Verification

1. `python assignment3_mcp_middleware/solution.py` — all 7 queries complete
2. Each query prints router output and tool count
3. `python token_report.py -a a3` — generates token-usage.txt
4. writeup.md includes ASCII diagram and before/after table
