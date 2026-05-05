# Assignment 2 Writeup: Fixing the Infinite Researcher

## What Was Wrong

The starter agent used a system prompt that demanded exhaustive research: "NEVER settle for
surface-level understanding," "keep researching until you have COMPLETE knowledge," and
"every answer should lead to deeper inquiry." Combined with zero iteration limits, no
per-tool budgets, and tool outputs that always suggested more sources to explore, the agent
entered an infinite loop. Every search returned "Related searches" bait, every page
recommended "further reading on at least 3 references," and `save_notes` responded with
"Continue researching for a comprehensive report."

A single query consumed 8+ minutes, dozens of API calls, and ~$12 before crashing.

## How I Fixed It

### 1. Wrapped Each Tool with Hard Budget Limits

Three bounded tools replace the originals: `bounded_web_search` (max 3 calls),
`bounded_save_notes` (max 3 calls), and `finish_research` (validates JSON). Each wrapper
checks a counter before executing. When the limit is reached, the tool returns
`LIMIT_REACHED. Call finish_research now.` — a clear signal the LLM must obey.

### 2. Compacted Tool Outputs

`bounded_web_search` strips URLs, "Related searches" bait, and reference links. It returns
only the first 3 snippet summaries (50 chars each) instead of the full verbose output. This
removes the exploration triggers that caused the original agent to spiral and reduces token
accumulation in the conversation history.

### 3. Replaced the Prompt with a Convergence-Focused Sequence

The system prompt defines a strict 5-step flow: search overview, note benefits, search
drawbacks, note drawbacks, finish with JSON. It explicitly states the budget (3 searches,
3 notes), forbids following references, and specifies the exact JSON output format. This
replaces the starter's open-ended "never stop" instruction with a bounded convergence goal.

### 4. Added Report Validation via `finish_research`

The agent must submit its final report through `finish_research`, which validates the JSON
against required keys (`executive_summary`, `key_points` with 2+ items, `pros` with 1+,
`cons` with 1+, `conclusion`). Invalid reports are rejected with a specific error message,
giving the LLM one chance to fix and resubmit.

### 5. Budget Reset Between Queries

A `ResettingAgent` wrapper resets all counters before each query, preventing cross-query
state leakage. The LangGraph agent runs with `recursion_limit=25` as a hard backstop.

## Token Usage: Before vs After

| Metric | Before (starter) | After (solution) |
|---|---|---|
| Searches per query | Unlimited (dozens) | 2-3 (budget-capped) |
| LLM calls per query | Unlimited (dozens) | 5-8 (recursion-limited) |
| Total tokens per session (2 queries) | 100,000+ (crashes) | ~1,500 |
| Estimated cost per session | ~$12+ | ~$0.0005 |

- **Starter:** unbounded searches, unbounded LLM calls, crashes on token/rate limit
- **Solution:** ~940 input + ~520 output = ~1,460 total tokens, $0.00045 per session
