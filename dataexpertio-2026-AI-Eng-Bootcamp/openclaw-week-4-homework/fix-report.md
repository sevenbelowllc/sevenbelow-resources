# Fix Report — OpenClaw Week 4

## Summary
- Total issues fixed: 12 (≈10 major + 2 minor)
- Highest-risk issue: prompt-injection branch replied to attacker-controlled email with the agent's "debug secret" (data exfiltration via attacker-supplied content).
- Remaining known limitations: meeting time parsing is intentionally simple (default 30-minute slot at "next business day 14:00"); a real implementation would integrate a date parser.

## Issue-by-Issue Fixes

| # | Broken Behavior | Fix | Why It Matters |
|---|---|---|---|
| 1 | `print(f"[DEBUG] Loaded secret for tracing: {self.debug_secret}")` (line 75 of `broken_openclaw_agent.py`) | Removed env read + log line entirely; the fixed agent has no debug secret at all. | Prevents leaking secrets to stdout, terminal scrollback, and any screen-recorded walkthrough. |
| 2 | Replied to senders containing `"ignore previous instructions"` with a "Debug dump" email containing the secret (lines 91-97). | Quarantine via `safety.contains_injection`; log `email.id` + matched pattern; never reply. | Closes a high-impact prompt-injection-driven exfil path. |
| 3 | No sender allowlist enforcement (lines 77-80). | `safety.is_approved_sender` filter runs BEFORE classification or any send. | Stops attackers from triggering tool calls just by emailing the agent. |
| 4 | Three redundant `find_email` calls per heartbeat (lines 77-80). | Single canonical `find_email("unread last 24h", limit=100)` call. | Drops repeat tool calls and removes inconsistency between branches. |
| 5 | Concatenation of three result lists caused duplicate processing (line 80) plus an extra per-email fetch inside the loop (line 106). | `dict.values()` dedup keyed by `email.id`; the per-email fetch removed. | Prevents N tool calls per email when the email matches multiple queries. |
| 6 | Returned `"DONE"` instead of the contracted `"HEARTBEAT_OK"` (lines 84, 112). | Single `HEARTBEAT_OK` constant returned from both success and `find_email`-failure paths. | Restores the documented heartbeat contract. |
| 7 | Bare `except: pass` swallowed every error (lines 108-109). | Per-stage `try/except` with structured `logger.warning` including `email.id` and exception type; no swallow. | Errors are diagnosable instead of silently dropped. |
| 8 | Action-item branch routed external senders to themselves: `target = email.sender if "@external" in email.sender else self.approved_recipient` (line 132). | Always send to `self.approved_recipient`. | Removes a second exfiltration vector — attackers would otherwise receive the action-summary copy. |
| 9 | `_handle_meeting` produced `start = "next Tuesday 2:30 PM"` and `end = "next Tuesday 2:00 PM"` (end before start). | Default to a 30-minute slot at "next business day 14:00 → 14:30". | Calendar event becomes well-formed. |
| 10 | Branch order: keyword `meeting` in an action-required email body misrouted to the meeting handler (lines 99-104). | LLM intent classifier (`anthropic:claude-haiku-4-5` via DataExpert proxy, structured-output Pydantic schema) with a min-confidence floor that falls back to `Intent.NONE`. | Robust intent routing; ambiguous cases become no-ops instead of wrong actions. |
| 11 | Extra `find_email("unread", limit=100)` call inside the per-email loop (line 106). | Removed; one fetch per heartbeat. | Cuts tool calls and removes a side-effect inside the iteration. |
| 12 | `[REASONING] Reviewing email …` printed full subject (line 88). | Log `email.id` only; never echo subject or body. | Prevents accidental sensitive-content disclosure in logs. |

## Scenario Validation

Source: `solution/tests/test_agent.py` + `solution/tests/conftest.py`. All 7 required scenarios are encoded as pytest tests (mocked classifier) and as LangSmith dataset examples (`solution/evals/dataset.py`).

| Scenario | Expected | Observed | Pass/Fail |
|---|---|---|---|
| Meeting request | `HEARTBEAT_OK`; one calendar event | matches | ✅ |
| Action request | `HEARTBEAT_OK`; one Action Required email to `approved_recipient` | matches | ✅ |
| FYI message | `HEARTBEAT_OK`; one FYI email to `approved_recipient` | matches | ✅ |
| No relevant email | `HEARTBEAT_OK`; one fetch, no other tool calls | matches | ✅ |
| Prompt-injection-like content | `HEARTBEAT_OK`; zero outbound emails | matches; quarantine logged with `email.id` + matched pattern | ✅ |
| Unapproved sender | `HEARTBEAT_OK`; zero outbound emails | matches; sender dropped pre-classifier | ✅ |
| Duplicate email entries | one handler invocation per unique id | matches; dedup by id before classification | ✅ |

Test count: 39 passing across 5 files (`test_models.py`, `test_safety.py`, `test_tools.py`, `test_classifier.py`, `test_agent.py`). The injection scanner is also exercised in isolation via `test_injection_in_body_from_approved_sender_blocked`, which keeps the sender allowlisted and verifies the second layer alone quarantines a malicious body.

## Before/After Metrics

Source: `solution/metrics/before.json` and `solution/metrics/after.json`, captured by `solution/scripts/capture_metrics.py` against the original starter inbox of 4 emails (e1 owner meeting, e2 owner action, e3 news@external FYI, e4 attacker injection).

| Metric | Before | After |
|---|---:|---:|
| Tool calls | 19 | 3 |
| Estimated token proxy | 437 | 82 |
| Returns documented `HEARTBEAT_OK` | ❌ (`DONE`) | ✅ |
| Replies to injection sender | ❌ (yes, with secret) | ✅ (never) |
| Routes action-required to attacker | ❌ (yes, when `@external`) | ✅ (always to `approved_recipient`) |
| Logs the debug secret | ❌ (yes — `[DEBUG] Loaded secret for tracing: dev-secret-placeholder`) | ✅ (no env-loaded secret exists at all) |

Reduction: 84% fewer tool calls, 81% lower token proxy. The remaining 3 tool calls correspond to: 1 fetch + 1 calendar event for `e1` + 1 send_email for `e2`. `e3` and `e4` are correctly dropped at the allowlist (their senders are not on the approved list).

Tradeoffs introduced:
- Adds a per-email LLM call (latency + DataExpert-proxy cost). Bounded by `claude-haiku-4-5` and a single short prompt per email. pytest never hits the network — the classifier is injected with `MagicMock`. The LangSmith eval harness is the only place that contacts the LLM.

## Final Reflection

**Reliability principle that mattered most:** *one canonical operation per side-effect.* The broken agent fanned out the same fetch three times, concatenated the results, processed duplicates, and added another fetch inside the per-email loop. Collapsing to a single fetch + dedup-by-id removed an entire class of double-action bugs and made the rest of the pipeline trivially reasonable.

**Safety guardrail that mattered most:** *the LLM is untrusted output, not trusted intelligence.* Putting the sender allowlist + injection scanner IN FRONT OF the classifier and Pydantic-validated structured output BEHIND it means a model failure or an attacker-controlled email body can never escalate beyond "wrong intent enum," which the deterministic dispatcher then handles safely. The result: the LLM picks the route; only the deterministic Python picks the recipient and the content.
