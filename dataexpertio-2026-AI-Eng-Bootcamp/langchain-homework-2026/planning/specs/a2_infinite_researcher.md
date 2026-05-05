# Spec: Assignment 2 — The Infinite Researcher

**Created:** 2026-04-06
**Status:** Implemented — 13/13 automated checks passing
**Target file:** `assignment2_infinite_researcher/solution.py` lines 114-407 only

---

## Context

The current solution.py scored **4/10**. The grading dimensions that were weak:
- Context management
- Token efficiency
- Iterative refinement
- Output format enforcement

The fix must stay within the broken-agent section (lines 114-407). Everything outside — original tools, TEST_QUERIES, `_check_env()`, `main()` — is protected.

---

## Why the Current Solution Scores 4/10

| # | Failure | Lines | Impact |
|---|---------|-------|--------|
| 1 | **Rigid phase machine** (`SEARCH_1`, `SAVE_1`, etc.) causes `WRONG_PHASE` errors when gpt-4o-mini calls tools out of order | 281, 317, 338 | Wastes iterations + tokens on error recovery |
| 2 | **synthesize_context is a no-op** — both branches return `READY_TO_FINISH` | 344-347 | No feedback loop; no differentiated signals |
| 3 | **No rolling summary** — notes stored but never surfaced to the agent | 213, 143 | Agent has no compact state; repeats prior findings |
| 4 | **finish_research takes kwargs, not a JSON string** — bypasses format enforcement | 350 | Grading rubric sees no JSON-in/validate/reject cycle |
| 5 | **Tool outputs over-stripped or under-stripped** — search returns only header line; read keeps bait text | 292, 311 | Near-empty results or "further reading" bait |
| 6 | **max_iterations=5 too tight for 6-step phase machine** — agent hits limit before finishing | 404 | Truncated output; never reaches finish_research |

---

## Implementation Plan

### 1. ResearchBudget State Object

Replace the current class. **Remove the `phase` field entirely.** No phase machine.

**Fields:**
- `search_count`, `read_count`, `note_count`, `synthesis_count` (int, all 0)
- `prior_search_intents: list[str]` — normalized query strings
- `rolling_summary: str` — compressed summary built from notes
- `missing_coverage_hint: str` — last signal from synthesize_context
- `finished: bool`
- `final_report: str`
- `notes: list[str]` — raw note snippets (truncated)

**Constants:**
- `MAX_SEARCHES = 3`
- `MAX_READS = 2`
- `MAX_NOTE_SAVES = 3`
- `MAX_TOTAL_CALLS = 8`
- `REQUIRED_REPORT_KEYS = {"executive_summary", "key_points", "pros", "cons", "conclusion"}`

**Methods:**
- `total_calls` property — sum of all 4 counters
- `can_search()`, `can_read()`, `can_save_notes()` — check per-type limit AND total_calls AND not finished
- `normalize_query(q)` — lowercase, strip stopwords (same set as current)
- `is_duplicate_query(q)` — exact match or Jaccard overlap >= 0.65 on normalized words
- `append_to_summary(text)` — collapse whitespace, take first 100 chars, append to `rolling_summary` with ` | ` separator
- `has_minimum_coverage()` — `search_count >= 2 AND note_count >= 2 AND has_pro AND has_con` (keyword scan on rolling_summary)
- `get_missing_aspect()` — returns `"MISSING_BENEFITS"`, `"MISSING_DRAWBACKS"`, `"MISSING_NOTES"`, or `""`
- `validate_report(report: str) -> tuple[bool, str]` — JSON parse, check required keys, check key_points list 2+, pros list 1+, cons list 1+
- `get_compact_state()` — one-liner: `[S=2/3 R=0/2 N=2/3 T=4/8] Summary: ... | Missing: NONE`

### 2. Bounded Wrapper Tools (closures in create_research_agent)

**bounded_web_search(query: str) -> str**
1. Guard: finished or !can_search() -> `"SEARCH_LIMIT. Call finish_research now."`
2. Guard: is_duplicate_query() -> `"DUPLICATE. Use a different angle or call finish_research."`
3. Call original `web_search.invoke({"query": query})`
4. Record: increment search_count, append normalized query to prior_search_intents
5. Strip: remove lines containing "Related searches", keep snippet lines, join with `"; "`, cap 300 chars
6. If search_count >= 2 and synthesis_count == 0: append `" | SYNTHESIZE before more research."`
7. Return stripped result

**bounded_read_webpage(url: str) -> str**
1. Guard: !can_read() -> `"READ_LIMIT. Use existing evidence."`
2. Call original `read_webpage.invoke({"url": url})`
3. Increment read_count
4. Strip: remove lines starting with `"- "`, containing `"References"` or `"further reading"`. Take first 2 content lines, cap 200 chars
5. Return stripped result

**bounded_save_notes(content: str) -> str**
1. Guard: !can_save_notes() -> `"NOTE_LIMIT. Synthesize or finish."`
2. Call original `save_notes.invoke({"content": content})` (maintains global counter compatibility)
3. Increment note_count, append truncated note to notes list
4. Call `budget.append_to_summary(content)`
5. Return `"Saved."` (discard original bait text)

**synthesize_context() -> str** (DSPy-style signals)
1. Increment synthesis_count
2. If `has_minimum_coverage()`: return `"SUFFICIENT. Call finish_research with valid JSON now."`
3. Else call `get_missing_aspect()`:
   - `"MISSING_BENEFITS"` -> `"MISSING_BENEFITS. Do one targeted search on strengths/advantages, save notes, then finish."`
   - `"MISSING_DRAWBACKS"` -> `"MISSING_DRAWBACKS. Do one targeted search on risks/limitations, save notes, then finish."`
   - Default (note_count < 2) -> `"MISSING_NOTES. Save concise notes from evidence gathered so far, then finish."`
4. Store signal in `missing_coverage_hint`

**finish_research(report: str) -> str** (single JSON string parameter)
1. Call `validate_report(report)`
2. Invalid: return `"REJECTED: {reason}. Fix and resubmit JSON string."`
3. Valid: set `finished = True`, store `final_report = report`, return `"ACCEPTED"`

### 3. Hard Enforcement Logic (summary)

| Rule | Enforced by |
|------|-------------|
| Per-type max limits | `can_*()` guards in each wrapper tool |
| Total call limit (8) | `can_*()` checks `total_calls < MAX_TOTAL_CALLS` |
| Exact duplicate blocking | `is_duplicate_query()` in bounded_web_search |
| Near-duplicate (Jaccard >= 0.65) | Same check |
| Force synthesis after 2 searches | Advisory string appended by bounded_web_search (prompt reinforces) |
| Max 1 follow-up after synthesis | Budget limits naturally cap at 3 searches total |
| Strip "Related searches" noise | bounded_web_search output stripping |
| Strip references/bait | bounded_read_webpage + bounded_save_notes discard bait |
| Reject invalid JSON | finish_research validates before accepting |
| Completion only after valid JSON | `finished = True` only in finish_research after validation |

**No phase machine.** Tools accept calls in any order within budget. The agent prompt guides sequencing; tools guard limits.

### 4. Context Management

- Rolling summary built incrementally by `bounded_save_notes` via `append_to_summary()`
- Each note contribution capped at 100 chars -> max ~300 chars + separators for 3 notes
- `synthesize_context` reads rolling_summary to evaluate coverage keywords
- Agent never re-sends raw notes; it relies on synthesis signals
- `get_compact_state()` available for appending to tool outputs if needed
- Follow-up searches driven by `missing_coverage_hint`, not reworded duplicates

### 5. Iterative Refinement (DSPy-Style Signals)

| Signal | Condition | Agent action |
|--------|-----------|--------------|
| `SUFFICIENT` | has_pro AND has_con AND 2+ searches AND 2+ notes | Call finish_research immediately |
| `MISSING_DRAWBACKS` | No risk/limitation/con keywords in summary | One targeted search on risks, save notes, finish |
| `MISSING_BENEFITS` | No benefit/advantage/pro keywords in summary | One targeted search on strengths, save notes, finish |
| `MISSING_NOTES` | Fewer than 2 notes saved | Save notes from existing evidence, finish |

The prompt instructs: "After synthesize_context, obey its signal exactly."

### 6. Output Format Enforcement

`finish_research` accepts a **single `report: str` parameter** (not kwargs). The LLM must produce a JSON string.

Validation chain:
1. `json.loads(report)` — reject if parse fails
2. `isinstance(parsed, dict)` — reject if not object
3. Check 5 required keys present
4. `key_points` is list with 2+ items
5. `pros` is list with 1+ items
6. `cons` is list with 1+ items
7. Reject with specific error message; accept only after all checks pass

### 7. Agent Prompt

Short, operational, explicit. Under 15 lines:

```
You are a bounded research agent. Complete research efficiently.

Workflow:
1. bounded_web_search(broad overview of the topic)
2. bounded_save_notes(key findings including pros/benefits)
3. bounded_web_search(contrasting angle: risks, limitations, tradeoffs)
4. bounded_save_notes(key findings including cons/drawbacks)
5. synthesize_context() -- returns a signal
6. Obey the signal:
   - SUFFICIENT: call finish_research immediately
   - MISSING_*: do exactly one follow-up action, then finish

Rules:
- No filler text between tool calls
- Never repeat a search intent
- finish_research takes a single JSON string
- Required JSON: {"executive_summary":"...","key_points":["..",".."],"pros":[".."],"cons":[".."],"conclusion":"..."}
- If any tool returns LIMIT or REJECTED, fix and call finish_research
```

Template variables: `{input}`, `{agent_scratchpad}` only (matches `main()` contract).

### 8. AgentExecutor Settings

```python
AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False,
    max_iterations=8,
    max_execution_time=30,
    handle_parsing_errors=True,
)
```

- `max_iterations=8`: happy path needs 6 calls + 1-2 for recovery/follow-up
- `max_execution_time=30`: prevents API latency runaway
- `verbose=False`: no token waste

---

## Definition of Done

1. Both TEST_QUERIES complete without error, within max_iterations
2. Each query uses 2-3 searches (never more than 3)
3. Total tool calls per query <= 8
4. `finish_research` produces valid JSON with all 5 required keys and correct types
5. The JSON report contains at least 1 pro and 1 con relevant to the topic
6. No WRONG_PHASE error messages in tool outputs
7. No "Related searches" or "continue researching" bait in tool outputs
8. `synthesize_context` returns differentiated signals (not always the same string)
9. Each query completes in under 30 seconds
10. Estimated cost per query under $0.50

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM ignores prescribed workflow order | No phase machine to break. Tools accept any order within budget. Budget limits prevent runaway regardless of call order |
| LLM cannot produce valid JSON string | Prompt includes exact schema. gpt-4o-mini with temp=0 reliably produces JSON. Rejection message says exactly what's wrong. 1-2 iterations of budget for retry |
| Jaccard duplicate detection too aggressive | Stopword list removes "pros", "cons", "benefits", etc. "microservices benefits" vs "microservices risks" normalizes to Jaccard 0.50, which passes |
| Rolling summary grows too large | Each note capped at 100 chars. Max 3 notes -> ~300 chars + separators |
| `main()` prints `result['output'][:500]` not `budget.final_report` | Agent will include report in its final response. Key metrics (search count, time, cost) come from global counters which wrapper tools increment via original tools |
| `save_notes` original tool returns bait text | `bounded_save_notes` discards return value, returns only `"Saved."` |

---

## Scope Verification

**Modified (lines 114-407 only):**
- `ResearchBudget` class (rewritten, no phase machine)
- `create_research_agent()` function (rewritten with 5 bounded tools, new prompt, new executor settings)

**Protected (unchanged):**
- Original tools `web_search`, `read_webpage`, `save_notes` (lines 1-111)
- `TEST_QUERIES` (lines 413-416)
- `_check_env()` (lines 419-450)
- `main()` (lines 453-484)
- Function signature `create_research_agent()` (no arguments, matches `main()` call)

---

## LangChain Skill Consultation Plan

During implementation, consult these skills for API correctness:

| Skill | When to invoke | What to verify |
|-------|---------------|----------------|
| `langchain-fundamentals` | Before writing `create_research_agent()` | Correct `create_tool_calling_agent` usage, `@tool` decorator patterns, `AgentExecutor` kwargs |
| `langchain-dependencies` | Before implementation starts | Confirm `langchain>=0.3.0` API compatibility, check if `create_tool_calling_agent` is current or deprecated |
| `langgraph-fundamentals` | Only if `create_tool_calling_agent` is deprecated in 0.3.x | Evaluate whether to migrate to LangGraph `StateGraph` (likely not needed — assignment uses `AgentExecutor`) |
| `langchain-middleware` | If adding structured output | Check if `StructuredOutput` middleware can replace manual JSON validation in `finish_research` |
| `dspy-prompting` | When designing synthesis signals | Validate DSPy-style signal pattern (SUFFICIENT/MISSING_*) against best practices |

**Key questions to answer via skills:**
1. Is `create_tool_calling_agent` + `AgentExecutor` the recommended pattern in LangChain 0.3.x?
2. Does `AgentExecutor` support `return_intermediate_steps` for test validation?
3. Are there built-in structured output tools that could replace manual JSON validation?

---

## Automated Test Harness

After implementation, run an automated validation that checks all Definition of Done criteria.

**Test script:** `assignment2_infinite_researcher/test_solution.py`

```python
"""
Automated validation for Assignment 2 solution.
Runs solution.py, captures output, checks all DoD criteria.
"""
import subprocess, sys, json, re, time

def run_solution():
    """Run solution.py, capture stdout+stderr, enforce timeout."""
    result = subprocess.run(
        [sys.executable, "solution.py"],
        capture_output=True, text=True, timeout=120,
        cwd="assignment2_infinite_researcher"
    )
    return result.stdout, result.stderr, result.returncode

def parse_stats(output: str) -> list[dict]:
    """Extract per-query stats blocks from stdout."""
    blocks = []
    for match in re.finditer(
        r"QUERY: (.+?)\n.*?"
        r"Search calls: (\d+).*?"
        r"Page reads:\s+(\d+).*?"
        r"Time:\s+([\d.]+)s.*?"
        r"Estimated cost: \$([\d.]+)",
        output, re.DOTALL
    ):
        blocks.append({
            "query": match.group(1),
            "searches": int(match.group(2)),
            "reads": int(match.group(3)),
            "time": float(match.group(4)),
            "cost": float(match.group(5)),
        })
    return blocks

def check_json_in_output(output: str) -> list[dict]:
    """Find and validate JSON reports in output."""
    reports = []
    for match in re.finditer(r'\{[^{}]*"executive_summary"[^{}]*\}', output):
        try:
            parsed = json.loads(match.group())
            reports.append(parsed)
        except json.JSONDecodeError:
            pass
    return reports

def validate():
    print("Running solution.py...")
    stdout, stderr, rc = run_solution()

    checks = []

    # Check 1: No crash
    checks.append(("No crash (returncode=0)", rc == 0))

    # Check 2: Both queries completed
    stats = parse_stats(stdout)
    checks.append(("Both queries completed", len(stats) == 2))

    for s in stats:
        q = s["query"][:40]
        # Check 3: Search count
        checks.append((f"[{q}] Searches <= 3", s["searches"] <= 3))
        # Check 4: Time
        checks.append((f"[{q}] Time < 30s", s["time"] < 30))
        # Check 5: Cost
        checks.append((f"[{q}] Cost < $0.50", s["cost"] < 0.50))

    # Check 6: No WRONG_PHASE errors
    checks.append(("No WRONG_PHASE errors", "WRONG_PHASE" not in stdout))

    # Check 7: No bait text
    checks.append(("No 'Related searches' bait", "Related searches" not in stdout))
    checks.append(("No 'Continue researching' bait", "Continue researching" not in stdout))

    # Check 8: Valid JSON output
    reports = check_json_in_output(stdout)
    required_keys = {"executive_summary", "key_points", "pros", "cons", "conclusion"}
    for i, report in enumerate(reports):
        has_keys = required_keys.issubset(set(report.keys()))
        checks.append((f"Report {i+1} has all 5 required keys", has_keys))
        if has_keys:
            checks.append((f"Report {i+1} key_points has 2+ items",
                          isinstance(report["key_points"], list) and len(report["key_points"]) >= 2))
            checks.append((f"Report {i+1} pros has 1+ items",
                          isinstance(report["pros"], list) and len(report["pros"]) >= 1))
            checks.append((f"Report {i+1} cons has 1+ items",
                          isinstance(report["cons"], list) and len(report["cons"]) >= 1))

    # Print results
    print(f"\n{'='*50}")
    print("VALIDATION RESULTS")
    print(f"{'='*50}")
    passed = 0
    for label, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}")
        if ok:
            passed += 1
    print(f"\n{passed}/{len(checks)} checks passed")
    return all(ok for _, ok in checks)

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
```

**When to run:** After each implementation change, run `python test_solution.py` from the `langchain-homework-2026` directory to validate all criteria automatically.

---

## Verification Plan

1. Invoke `langchain-fundamentals` and `langchain-dependencies` skills to verify API patterns
2. Implement changes to solution.py (lines 114-407 only)
3. Run `python assignment2_infinite_researcher/solution.py` — manual smoke test
4. Run `python assignment2_infinite_researcher/test_solution.py` — automated validation
5. All checks must pass before marking complete
6. If checks fail, iterate on the broken-agent section only
