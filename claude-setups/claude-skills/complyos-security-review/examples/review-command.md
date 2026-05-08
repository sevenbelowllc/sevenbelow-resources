# Review Command Reference

Operational invocations for common review scopes.

## Full review

```
/complyos-security-review
  scope: <repo-list>
  authority: <spec-index-path>
  auth_provider: <provider>
  api: <REST|GraphQL|both>
  db: <engine + tenancy model>
  cloud: <provider + iac>
  ai_rag: <yes|no>
  envs_in_scope: <env labels with deployed/internet-reachable flags>
  runtime_authz: <NONE|env-name>
  output: <output-root>
```

## Phase-targeted re-run

After a fix lands, re-run a specific phase to verify:

```
/complyos-security-review --phase 5
  scope: <api-service>
  reason: "verify withTenantContext lint rule lands; re-confirm FINDING-001..003 closed"
  output: docs/security-review/
```

Phases: 0..14 (or `0,3,5` for a multi-phase subset).

## Single-finding verification

```
/complyos-security-review --verify FINDING-001
  scope: <api-service>
  branch: fix/finding-001-tenant-context
  output: docs/security-review/verifications/
```

Produces a one-paragraph verdict (CLOSED / OPEN / REGRESSED) with file evidence.

## Diff-scoped review

For a PR-sized review:

```
/complyos-security-review --diff main..HEAD
  scope: <api-service>
  reason: "PR review — security-only pass on the diff"
  output: <pr-comment>
```

Emits findings inline + a summary; safe to attach as a PR review comment.

## AI/RAG-only sub-review

```
/complyos-security-review --phase 8
  scope: <agent-service>
  ai_rag: yes
  authority: docs/specs/agent-runtime.md
  reason: "post-D14 AI hardening pass before stretch wave"
  output: docs/security-review/agent-only/
```

## Scope-gap-only run

When inputs are missing and the user wants the gap list before authorizing the full review:

```
/complyos-security-review --phase 0
  scope: <whatever-is-known>
  reason: "produce 00-scope.md gaps; halt before Phase 1"
```

## Output discipline (every invocation)

- Every artifact written under `<output-root>/security-review/`.
- Findings register kept current across phase re-runs (don't replace; update by ID).
- Verifications append to `verifications/<date>/<finding-id>.md`, leaving the original finding's status unchanged in the register until the user explicitly closes it.

## Refuse to proceed if

- `runtime_authz` is set to a deployed env without a signed authorization line in `00-scope.md`.
- Required scope inputs are missing AND no `--phase 0` flag was set.
- Output root is inside a deprecated/archive path.
- Output root would overwrite an existing report without `--overwrite`.
