---
name: handoff
description: Use at the end of any work session to create a structured handoff document that enables the next session (human or AI) to resume without context loss. Invoke before closing a session, when switching tasks, or when the user says "handoff", "wrap up", or "save state".
---

# Handoff — Session State Capture

Create a structured handoff document that captures everything the next session needs to resume work without re-discovery.

## When to Use

- End of a work session
- Before switching to a different task or project
- When the user says "handoff", "wrap up", "save state", "checkpoint"
- Before any context window is likely to expire

## The Process

### Step 1: Gather Session State

Collect the following by reviewing the conversation, recent tool calls, and project state:

1. **What was accomplished** — concrete deliverables, not intentions
2. **What changed** — files modified, created, deleted (use `git diff` and `git status`)
3. **What's next** — specific next actions, not vague goals
4. **Open decisions** — unresolved questions that block progress
5. **Key context** — non-obvious information the next session needs (error messages, gotchas, constraints discovered)
6. **Memory updates** — what was saved to Claude memory this session

### Step 2: Write the Handoff Document

Write to **`memory/HANDOFF.md`** (this project's canonical handoff location).
Do NOT use `docs/superpowers/checkpoints/` — that path is the skill default but this project
keeps all session state under `memory/` per the documentation rationale.

Use this structure:

```markdown
# <Topic> — Session Handoff

> **Session Date:** YYYY-MM-DD-HH-MM-SS
> **Status:** <current state in one line>
> **Next Session:** <what to do first>

---

## 1. What Was Accomplished

<Concrete deliverables with specifics. Not "worked on X" but "implemented X in file Y, tested with Z.">

## 2. What Changed

<Files modified/created/deleted. Include paths. For large changesets, summarize by area.>

### Git State
<Output of git status and summary of uncommitted work, if any.>

## 3. What's Next

<Ordered list of specific next actions. The first item is what the next session should do immediately.>

1. ...
2. ...
3. ...

## 4. Open Decisions

| # | Question | Options | Impact |
|---|----------|---------|--------|
| 1 | ... | ... | ... |

<If no open decisions, state "None — all decisions resolved this session.">

## 5. Key Context

<Non-obvious information. Error messages encountered, constraints discovered, things that almost worked but didn't and why. The stuff that saves the next session from repeating your mistakes.>

## 6. Memory Updates

| Memory File | Type | What Was Saved |
|------------|------|---------------|
| ... | ... | ... |

<If no memory updates, state "None this session.">

---

## Session Metadata

- **Model:** <model name>
- **Working directory:** <path>
- **Active skills/plugins:** <what was in use>
```

### Step 3: Update Memory

Save a project-type memory pointing to the handoff file:

```markdown
---
name: <Topic> Session Handoff
description: <one-line summary of session state and resume point>
type: project
---
Handoff file: `<path to handoff document>`

**Resume point:** <what to do first next session>

**Key decisions:** <bullet list of decisions made>

**How to apply:** Next session should read the handoff file, then execute the first item in "What's Next".
```

### Step 4: Confirm with User

After writing the handoff document and memory:

> "Handoff written to `<path>`. Memory updated. The next session should start by reading that file. Anything you want to add or change before we wrap?"

Wait for user confirmation.

## Quality Gates

- **No vague actions.** "Continue working on X" is not a valid next action. "Run `npm test` in compliance-core to verify the auth fix, then move to control mapping resolver" is.
- **No assumed context.** Write as if the next reader has never seen this conversation.
- **No stale state.** Run `git status` and `git diff` fresh — don't rely on earlier observations.
- **Paths must be absolute or repo-relative.** No ambiguous references.
- **Decisions must include rationale.** Not just "we chose X" but "we chose X because Y."

## Key Principles

- **Capture state, not narrative.** This is a resume point, not a session log.
- **Be specific.** File paths, line numbers, command outputs, error messages.
- **Assume amnesia.** The next session has zero memory of this one beyond what you write down.
- **Err on the side of too much context.** A redundant detail costs nothing. A missing one costs a full re-discovery cycle.
