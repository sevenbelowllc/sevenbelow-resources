# OWASP LLM Top 10:2025 + Agentic Security Checklist

Run this checklist if Phase 0 declared AI/RAG/agent code paths in scope. Skip otherwise (and note skip in `08-ai-rag-security-review.md`).

## LLM01:2025 — Prompt Injection

- [ ] Direct prompt injection: user message content never trusted as instruction. Cite the system-prompt boundary or guardrail node.
- [ ] Indirect prompt injection: RAG-retrieved content, tool-call output, document attachments treated as data, not instruction. Cite sanitization or "untrusted-content" wrapping.
- [ ] Multi-turn injection: prior assistant turns from poisoned context cannot pivot future tool calls.
- [ ] Multimodal injection: image OCR / document OCR text NOT fed back as instruction without sanitization.
- [ ] Regex-only guardrails recognized as defense-in-depth, not primary control. Cite LLM-second-tier guard if claimed.
- [ ] Prompt-injection guard handles unicode lookalikes, zero-width splitters, encoding obfuscation.

## LLM02:2025 — Sensitive Information Disclosure

- [ ] System prompts do not contain secrets, internal hostnames, or tenant identifiers.
- [ ] Few-shot examples scrubbed of customer data.
- [ ] LLM output PII-redacted before downstream consumption (response body, trace store, logs).
- [ ] LangFuse / observability traces scrub PII, tokens, secrets.
- [ ] Model fine-tuning data (if any) PII-controlled and tenant-segregated.

## LLM03:2025 — Supply Chain

- [ ] Model providers pinned by version (no implicit upgrades).
- [ ] Open-weight models (if used) verified by hash + signature.
- [ ] Model-router / proxy services (LiteLLM, OpenRouter, DataExpert proxy) auth + TLS verified.
- [ ] LangChain / LangGraph / MCP server packages locked + scanned (these are high-churn supply-chain surfaces).
- [ ] No `latest` tag on model IDs in deployed config.

## LLM04:2025 — Data and Model Poisoning

- [ ] RAG ingest path validates source provenance.
- [ ] Tenant-uploaded documents indexed into a tenant-scoped namespace, not a shared corpus.
- [ ] Vector DB writes from agent code go through `withTenantContext`.
- [ ] Auto-update of system prompts / few-shots gated by review.

## LLM05:2025 — Improper Output Handling

- [ ] LLM output rendered in browser is sanitized via DOMPurify (NOT raw HTML render).
- [ ] LLM output that becomes SQL / shell / template / URL is validated/escaped per sink.
- [ ] LLM-suggested URLs that the UI renders as `<a href>` validated for scheme.
- [ ] LLM tool-call args validated against per-tool schema before execution.
- [ ] LLM output that triggers state mutation goes through HITL approval for sensitive flows.

## LLM06:2025 — Excessive Agency

- [ ] Tool inventory minimal: each tool justified, scoped, audited.
- [ ] Tools that mutate state require HITL approval token bound to (tenant, thread, action).
- [ ] Tools cannot self-elevate (no "create_admin_user" tool exposed to general agent).
- [ ] Tool-call recursion budget capped (max iterations per agent run).
- [ ] Agent cannot spawn child agents that bypass parent's tenant scope.

## LLM07:2025 — System Prompt Leakage

- [ ] System prompts assume disclosure (treat as semi-public).
- [ ] No secrets, no internal hostnames, no tenant lists in system prompt.
- [ ] Test that probes for system-prompt extraction exists.

## LLM08:2025 — Vector and Embedding Weaknesses

- [ ] Embedding namespace per tenant (collection, schema, or `WHERE tenant_id = $1` on every kNN query).
- [ ] kNN queries bounded by `top_k` cap.
- [ ] Embedding ingest authenticated + tenant-bound.
- [ ] Embedding DB credentials separate from app DB credentials where data classification warrants.

## LLM09:2025 — Misinformation

- [ ] LLM output marked as AI-generated in UI.
- [ ] Compliance-critical output (control mapping, framework citation) cross-checked against canonical source before persist.
- [ ] HITL approval gate before LLM output becomes audit evidence.

## LLM10:2025 — Unbounded Consumption

- [ ] Per-tenant daily/hourly LLM cost cap enforced AT REQUEST ENTRY (reject 402/429 above cap), not just observed in trace.
- [ ] Per-request token cap.
- [ ] Per-request wall-clock cap (`asyncio.wait_for` / equivalent).
- [ ] Per-tenant concurrent-agent-run cap (semaphore).
- [ ] Idempotency-Key on agent-start to defeat retry-storm cost amplification.
- [ ] LangGraph `recursion_limit` set explicitly.
- [ ] Streaming endpoints (SSE/WS) per-tenant connection cap + lifetime cap.

## Agentic-specific (OWASP Agentic AI 2026 preview)

- [ ] Tenant-claim binding: agent runtime cross-checks caller-asserted tenant against signature-bound claim, not just header trust.
- [ ] Thread/checkpoint ownership: every `thread_id` access verifies `(thread_id, tenant_id)` binding.
- [ ] Tool authorization: tools that touch DB go through `withTenantContext`; tools that touch external APIs validated per API7 SSRF rules.
- [ ] Sensitive-action HITL: publish, delete-evidence, role-change, billing-change require human approval token before agent can execute.
- [ ] Agent-to-agent calls (if any) propagate tenant context AND restrict to declared sub-agent allowlist.
- [ ] Agent observability does not log raw user PII to LangFuse / Sentry (regex + Presidio scrub at trace boundary).
