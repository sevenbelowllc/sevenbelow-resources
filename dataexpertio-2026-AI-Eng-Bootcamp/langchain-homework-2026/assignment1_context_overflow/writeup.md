# Assignment 1 Writeup: Fixing the Context Overflow Tool

## What Was Wrong

The `lookup_order_info` tool dumped the entire orders database (2,000 records) into the LLM
context window on every query. The tool serialized all records as a JSON blob and told the
LLM to "search through the above data to answer." This pushed data-filtering work onto the
LLM — the wrong place to do it.

The result: every query consumed ~150,000+ tokens, cost $0.50+ per question, frequently hit
context limits, and caused hallucinations because relevant data was buried in noise.

## How I Fixed It

### 1. Rewrote the Tool with Structured Parameters

The tool now accepts typed parameters (`order_id: str`, `email: str`) instead of a raw
query string. Python does the filtering:

- **By order ID:** scans `ORDERS_DB` for an exact match, returns one record.
- **By email:** filters all records matching the email.

Only five fields are returned per record: `order_id`, `customer_email`, `status`,
`delivery_date`, `items`. A single record is ~200 characters — down from ~150,000+.

### 2. Added Protective Middleware (`safe_lookup`)

After filtering, `safe_lookup` enforces three guardrails:

- **Field whitelist:** only customer-facing fields pass through (`_FIELDS_TO_KEEP`).
- **Pagination:** results exceeding `MAX_TOOL_ROWS` (5) are paginated — the first page
  is returned with a `has_more` flag and `total_matches` count, rather than a hard error.
- **Size cap:** serialized output exceeding `MAX_TOOL_OUTPUT_CHARS` (2,000) returns an
  explicit error instead of injecting bloated data into the LLM context.

These three layers prevent any future regression regardless of how the tool is called.

### 3. Built a Session-Aware Caching Layer (`SessionAwareAgent`)

The `SessionAwareAgent` wraps the `AgentExecutor` and resolves follow-up queries from
cached data without additional LLM or tool calls:

- **Order cache:** the first query about an order populates `active_order_data` and
  pre-fills `answered_fields` for status, delivery date, and items. Follow-up queries
  about the same order are answered instantly from the cache.
- **Email result cache (`active_email_orders`):** all orders matching an email are stored
  in the session, not just the first page. This allows refinement queries without re-fetching.
- **Refinement handling:** queries containing "more", "additional", "other", or "remaining"
  are answered from `active_email_orders` by surfacing orders not yet shown as the active
  order. If more results exist beyond the display limit, the user is prompted to narrow by
  order ID.

### 4. System Prompt with Cache-First Behavior and Output Format

The system prompt explicitly instructs the LLM to:
- **Check cached order context first** before calling any tools.
- **Always include the items list** in order responses unless the user asks for a single field.
- **Follow a strict output format**: `<order_id> | <status> | <delivery_date> | <items>` for
  single orders, one line per order for email lookups.

This ensures the LLM uses the cached data efficiently and returns structured, predictable
responses without redundant tool calls.

### 5. LLM Fallback for Ambiguous Queries

When the session cache cannot resolve a query (e.g., an email lookup with no specific field
requested), it falls through to the `AgentExecutor`. The LLM calls `lookup_order_info` with
the proper parameters, the tool returns trimmed data, and the LLM formats the response.
The cached context is passed to the LLM prompt via `{order_data}` to avoid redundant tool
calls.

For the 4 standard test queries, this results in exactly 1 LLM call (query 4, the email
lookup) while queries 1-3 are resolved entirely from the session cache.

## Token Usage: Before vs. After

| Metric | Before (broken) | After (fixed) |
|---|---|---|
| Records returned per tool call | 2,000 | 1 (paginated to 5 max) |
| Fields per record | all (~15) | 5 (whitelisted) |
| Approx. chars per tool response | ~150,000 | ~200 |
| Estimated tokens per tool call | ~37,500 | ~50 |
| LLM calls for 4 test queries | 4+ | 1 |
| Tool calls for follow-ups | 1 per query | 0 (session cache) |
| Refinement queries ("more orders?") | re-fetches from DB | 0 (session cache) |
| Estimated cost per session (gpt-4o-mini) | ~$0.50+ | ~$0.00008 |
| Context window risk | High (crashes) | None |

- **Starter:** ~2,278,078 input tokens, 4 failed LLM calls, ~$0.34 per session
- **Solution:** 415 input tokens, 1 LLM call, ~$0.00008 per session

## Key Principle

The root cause was a violation of a fundamental agent design rule: **data retrieval belongs
in Python, not in the LLM.** The LLM is good at reasoning over results; it is not a database
engine. The fixed tool executes a precise, bounded operation and returns a minimal, structured
result — and the session layer ensures that result is reused rather than re-fetched on every
follow-up query.
