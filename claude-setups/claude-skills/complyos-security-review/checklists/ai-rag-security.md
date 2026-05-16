# AI / RAG / Agent Security Checklist (operational)

Run if Phase 0 declared AI/RAG presence. This is the operational counterpart to `owasp-llm-security.md` — focused on the multi-tenant compliance product threat model.

## Tenant scope (CRITICAL)

- [ ] Vector / embedding store partitioned per tenant. Cite the schema (collection-per-tenant, namespace-per-tenant, OR `tenant_id` column with RLS).
- [ ] Every kNN query carries `WHERE tenant_id = current_tenant_id()` OR queries the per-tenant collection.
- [ ] Embedding ingest writes go through `withTenantContext` and write to the tenant's namespace.
- [ ] Agent state checkpoints (LangGraph / CrewAI / custom) keyed on `(tenant_id, thread_id)` composite. Resume verifies binding.
- [ ] Agent tool calls inherit tenant context; tools that hit DB go through `withTenantContext`.
- [ ] Cross-tenant retrieval is impossible by construction, not by application-layer filter on shared corpus.

## Prompt injection defense

- [ ] System prompt boundary clear; user content fenced.
- [ ] RAG-retrieved content wrapped in untrusted-content delimiters before insertion into prompt.
- [ ] Tool-call output wrapped likewise.
- [ ] OCR / document-parser output wrapped likewise.
- [ ] Input guardrail (regex / classifier / LLM-judge) at request entry. Document threshold + tier.
- [ ] Output guardrail validates shape + framework lock + PII scrub before returning.
- [ ] NFKC unicode normalization + zero-width-char strip before guardrail scoring.
- [ ] Multi-turn injection: prior assistant turns from poisoned context cannot pivot future tool calls.

## Tool authorization

- [ ] Tool inventory minimal and justified.
- [ ] Tools that mutate state require HITL approval token bound to (tenant, thread, action).
- [ ] Tools that touch external URLs validated against SSRF rules (per `owasp-api-security.md` API7).
- [ ] No "create_admin_user" / "elevate_role" / "delete_evidence" tool exposed to general agent.
- [ ] Tool-call args validated against per-tool schema before execution.
- [ ] Tool-call recursion budget capped (`recursion_limit` on LangGraph; explicit max-iter on custom loops).

## Cost and resource control

- [ ] Per-tenant daily/hourly LLM cost cap. Enforced at REQUEST ENTRY, not just observed in trace.
- [ ] Per-request token cap.
- [ ] Per-request wall-clock cap (timeout).
- [ ] Per-tenant concurrent-agent-run cap (semaphore).
- [ ] Idempotency-Key header on agent-start to defeat retry-storm cost amplification.
- [ ] Streaming endpoints (SSE/WS) per-tenant connection cap + lifetime cap.
- [ ] Cost ledger writes are tenant-scoped + audit-trailed.

## Output handling

- [ ] LLM output rendered in browser sanitized via DOMPurify (NOT raw HTML render).
- [ ] LLM output that becomes SQL / shell / template / URL validated/escaped per sink.
- [ ] LLM-suggested URLs that the UI renders as `<a href>` validated for scheme.
- [ ] LLM output that triggers state mutation goes through HITL approval for sensitive flows.
- [ ] PII redaction on output: regex + Presidio (or equivalent) scrub before logging to LangFuse / Sentry.

## Observability and tracing

- [ ] LangFuse / Phoenix / equivalent traces exclude PII, tokens, secrets at ingest.
- [ ] Trace tags: tenant_id (hashed), request_id, llm_provider, llm_model_id, agent_run_id, node_name.
- [ ] Trace retention bounded.
- [ ] No customer prompt content logged at INFO or higher; only at DEBUG with explicit redaction.

## Sensitive flows (HITL)

- [ ] Document publish: requires HITL approval before agent can commit.
- [ ] Evidence delete: HITL.
- [ ] Role grant: HITL.
- [ ] Vendor add: HITL where applicable.
- [ ] Workflow segregation of duties: same actor cannot author + approve + publish via agent.

## Caller binding (agent runtime entry)

- [ ] Agent runtime cross-checks caller-asserted tenant against signature-bound claim, not just `x-tenant-id` header.
- [ ] If only one upstream caller is allowlisted, document the trust boundary explicitly + log every (caller, tenant) tuple at INFO.
- [ ] Plan signed tenant-claim path before adding any second SA to the allowlist.

## RAG ingest provenance

- [ ] Source provenance recorded per chunk (source_doc_id, source_type, ingest_actor, ingest_timestamp).
- [ ] Tenant-uploaded documents indexed into the tenant namespace, NOT a global corpus.
- [ ] Auto-update / re-embed of system prompts and few-shots gated by review.

## Tests required

- Cross-tenant RAG retrieval attempt (verify denied / empty).
- Cross-tenant agent thread resume (verify rejected).
- Prompt injection: direct (in user message), indirect (via RAG content), multimodal (via OCR text).
- Tool-call argument fuzzing (per-tool schema rejects malformed).
- Cost-cap rejection: simulate >cap and verify 402/429 at entry.
- Recursion-limit hit (verify safe halt).
- HITL gate bypass attempt: agent attempts publish without approval token.
- Output sanitization: LLM emits `<script>` and verify browser renders inert.
- LangFuse trace inspection: confirm PII scrubbed.
