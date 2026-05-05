# Assignment 3 Writeup: Fixing the MCP Tool Overload

## What Was Wrong

The starter agent loaded all 25 tools from 3 MCP servers (GitHub 8, Slack 6, Database 11)
into every prompt. Each tool description includes its name, server tag, parameter schema,
and description text — totaling ~2,209 tokens of tool definitions sent on every LLM call.
The LLM had to parse all 25 tool schemas before selecting one, causing confusion between
similar tools (e.g., `search_code` vs `query_sql`), slower responses, and inflated cost.

## How I Fixed It

### Two-Layer Middleware

Layer 1 is a keyword-based router that classifies each query to the relevant MCP
server(s). Layer 2 is a context-aware tool filter that removes discovery tools
(`list_databases`, `list_tables`, `describe_table`) when the query already names the
target table or database. Both layers are pure Python — zero LLM calls for routing.

```
User Query
    |
    v
+---------------------+
| Keyword Router      |  "bug", "issue" -> github
| (frozenset lookup)  |  "message", "#"  -> slack
+---------------------+  "table", "query" -> database
    |
    v
+---------------------+
| Discovery Filter    |  Query names a table?
| (context-aware)     |  -> remove list_databases,
+---------------------+     list_tables, describe_table
    |
    v
+---------------------+
| LangGraph Agent     |  Sees 6-16 tools instead
| (per-query)         |  of 25
+---------------------+
    |
    v
Structured JSON Response
```

### Keyword Sets

Three `frozenset` keyword sets map queries to servers:
- **GitHub:** issue, bug, error, pr, repo, code, commit, branch, merge
- **Slack:** message, channel, send, post, dm, notify, #
- **Database:** table, query, sql, database, row, count, schema, production, errors

Multi-server queries (e.g., "query the errors table and create a GitHub issue") match
multiple keyword sets and receive tools from all matched servers. Unmatched queries
fall back to all tools.

### Discovery Tool Filtering

When a query mentions a specific table name (e.g., "errors table", "users table",
"production database"), the middleware removes `list_databases`, `list_tables`, and
`describe_table` from the tool set. This prevents the agent from wasting 3-4 tool calls
on unnecessary exploration before the actual query.

### Compact System Prompt

Each per-query agent gets a minimal system prompt (~150 tokens) that names only the
active servers, enforces one-tool-per-goal discipline, requires between-step
summarization, and specifies a JSON output format.

## Before vs After

| Metric | Before (starter) | After (solution) |
|---|---|---|
| Tools per single-server query | 25 | 6-8 |
| Tools per cross-server query | 25 | 14-16 |
| Tool description tokens (single) | ~2,209 | ~482-808 |
| Tool description tokens (cross) | ~2,209 | ~1,234-1,560 |
| Discovery calls on named tables | 3-4 wasted | 0 |
| Average token reduction | 0% | 56% |
| Routing cost | N/A | 0 (keyword-based) |

### Per-Query Routing Results

| # | Query | Servers | Tools | Desc Tokens | Reduction |
|---|-------|---------|-------|-------------|-----------|
| 1 | Create GitHub issue | github | 8 | 752 | 66% |
| 2 | Send Slack message | slack | 6 | 482 | 78% |
| 3 | Count database rows | database | 8 | 808 | 63% |
| 4 | Search for auth bug | github | 8 | 752 | 66% |
| 5 | Messages or issues about deploy | github, slack | 14 | 1,234 | 44% |
| 6 | GitHub issue + post to Slack | github, slack | 14 | 1,234 | 44% |
| 7 | Query DB + create issue | github, database | 16 | 1,560 | 29% |

### Token Usage (Live Execution)

| Script | LLM Calls | Input Tokens | Output Tokens | Total | Cost |
|--------|-----------|-------------|---------------|-------|------|
| starter.py | 0 (import error) | 0 | 0 | 0 | $0.00 |
| solution.py | 20 | 14,922 | 804 | 15,726 | $0.003 |
