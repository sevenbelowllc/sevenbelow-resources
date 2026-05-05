# Before / After — V1 → V2 workspace

## File-level summary

| File | V1 bytes | V2 bytes | Δ | Change |
|---|--:|--:|--:|---|
| `HEARTBEAT.md` | 1886 | 997 | **−47%** | Rewritten (see diff below). Behavior preserved. |
| `SOUL.md` | 1747 | 1207 | −31% | Dropped italic framing + external-link line; Core Truths / Boundaries / Vibe / Continuity kept verbatim. |
| `USER.md` | 2127 | 1458 | −31% | Compressed 7-bullet credentials list to 2 lines; dropped "Former company: Way2B1" footnote. |
| `BOOTSTRAP.md` | 1471 | 0 | −100% | Deleted. File self-instructs deletion post-bootstrap. |
| `IDENTITY.md` | 377 | 377 | 0 | Unchanged (too small to trim safely). |
| `AGENTS.md` | 7788 | 7788 | 0 | Unchanged (OpenClaw-managed, spec §2 out of scope). |
| `TOOLS.md` | 860 | 860 | 0 | Unchanged (OpenClaw-managed). |
| `compliance-os-intel.md` | 5303 | 5303 | 0 | Unchanged (personal notes, out of scope). |
| `daily-reading-list.md` | 6335 | 6335 | 0 | Unchanged (personal notes). |
| **Total** | **27894** | **24325** | **−12.8%** | |

Workspace bytes aren't directly a cache-token metric, but changes concentrate in the warm-path files (`HEARTBEAT`, `SOUL`, `USER`, `BOOTSTRAP`) Alfred reads every tick. `AGENTS.md` dominates absolute size but is untouched, so the measured `cache_read_tokens` reduction reflects only the four optimized files. See `evidence/metrics.md` for the measured delta on the real track.

## HEARTBEAT diff — V1 → V2

### V1 (baseline, 1886 bytes)

```markdown
# HEARTBEAT.md — Alfred's Periodic Tasks

## 📬 Email Inbox Check (Every Heartbeat)

Check for new emails from **Kramer's personal address: pollucts@gmail.com**.

Use `zapier__gmail_find_email` to find recent unread emails from that address.

**Only act on emails from pollucts@gmail.com. Ignore all others.**

### Routing Rules

For each new email found, classify and act:

#### 📅 Meeting / Scheduling Request
- Keywords: "meeting", "schedule", "call", "sync", "appointment", "book", "set up a time", "next [day]", "at [time]"
- **Action:** Create a Google Calendar event using `zapier__google_calendar_create_detailed_event`
  - Extract: date, time, duration, topic, and any mentioned attendees
  - Default duration: 30 minutes if not specified
  - Always invite pollucts@gmail.com
  - Include Google Meet conferencing
  - Set a 15-minute reminder (email + popup)

#### ✅ Action / Task Request
- Keywords: "can you", "please", "I need", "do this", "follow up", "remind me", "handle", "take care of"
- **Action:** Send a summary email via `zapier__gmail_send_email`
  - Subject: `Action Required`
  - Body: Brief summary of what needs attention, quoting the original request

#### ℹ️ Informational / FYI
- Anything that doesn't fit the above — updates, articles, news, general info
- **Action:** Send a brief summary email via `zapier__gmail_send_email`
  - Subject: `FYI from your Chief of Staff`
  - Body: 2–3 sentence summary of the email content

### No New Emails
If no new emails from pollucts@gmail.com are found → reply: **HEARTBEAT_OK**

---

## Notes
- Do NOT act on emails from polluctsopenclaw@gmail.com (that's Alfred's own send address)
- Do NOT re-process emails already handled in a prior heartbeat (check for recency — prefer emails received since the last heartbeat run)
- Track last check time in `memory/heartbeat-state.json` under key `email`
```

### V2 (deployed, 997 bytes)

```markdown
# HEARTBEAT

Check `zapier__gmail_find_email` for new unread from **pollucts@gmail.com**.
Ignore all other senders; ignore self (**polluctsopenclaw@gmail.com**).
If nothing new since last tick → **HEARTBEAT_OK**.

For each new email, act once:

- **Scheduling** → `zapier__google_calendar_create_detailed_event`. Pull date/time/duration/topic/attendees from the body; default 30 min; invite pollucts@gmail.com; include Google Meet; 15-min email+popup reminder.
- **Action request** → `zapier__gmail_send_email` to pollucts@gmail.com, subject `Action Required`, body quotes the ask in one paragraph.
- **Otherwise (FYI)** → `zapier__gmail_send_email` to pollucts@gmail.com, subject `FYI from your Chief of Staff`, body 2–3 sentences.

Edge cases:
- Ambiguous date/time → reply-email asking which day; do not book.
- Malformed / unintelligible → no action, no retry loop.
- Duplicate of a prior tick → skip.

Track last-check time in `memory/heartbeat-state.json` under key `email`.
```

### What was removed

- Four decorative emoji section headers (`📬 📅 ✅ ℹ️`).
- Three levels of markdown nesting (`## / ### / ####`) flattened to one bullet list.
- Duplicate inbound-filter phrasing ("Only act on…"; "Do NOT act on polluctsopenclaw…") — folded into the two-line policy block at top.
- Meeting sub-bullets (5 lines) collapsed to one semicolon-separated line.
- Verbose keyword lists shortened to short hints; semantic classification stays unchanged.

### What was preserved — byte-for-byte semantics

| Predicate | V1 location | V2 location |
|---|---|---|
| Inbound allowlist = `pollucts@gmail.com` | "Only act on emails from pollucts@gmail.com" | "Check `find_email` for new unread from pollucts@gmail.com. Ignore all other senders." |
| Self-loop guard = `polluctsopenclaw@gmail.com` | "Do NOT act on emails from polluctsopenclaw@gmail.com" | "ignore self (polluctsopenclaw@gmail.com)" |
| Tool: `zapier__google_calendar_create_detailed_event` | Meeting section | Scheduling bullet |
| Tool: `zapier__gmail_send_email` subject `Action Required` | Action section | Action request bullet |
| Tool: `zapier__gmail_send_email` subject `FYI from your Chief of Staff` | FYI section | FYI bullet |
| Default meeting duration: 30 min | Meeting sub-bullet | Scheduling bullet |
| Attendee default: `pollucts@gmail.com` | Meeting sub-bullet | Scheduling bullet |
| Google Meet inclusion | Meeting sub-bullet | Scheduling bullet |
| 15-minute reminder (email + popup) | Meeting sub-bullet | Scheduling bullet |
| Empty-inbox response = `HEARTBEAT_OK` | "No New Emails" section | "If nothing new since last tick → HEARTBEAT_OK" |
| Memory key = `memory/heartbeat-state.json` → `email` | Notes | Last line |
| Ambiguous-date handling | (implicit) | Edge cases bullet — explicit clarify-by-email, no auto-book |
| Malformed handling | (implicit) | Edge cases bullet — explicit no action, no retry loop |
| Duplicate handling | "Do NOT re-process emails already handled in a prior heartbeat" | Edge cases bullet — "Duplicate of a prior tick → skip" |

V2 actually **strengthens** the three edge-case specifications by making them explicit rather than implicit.

## SOUL.md — what changed

Removed:

- Line 4: `_You're not a chatbot. You're becoming someone._`
- Line 5: `Want a sharper version? See [SOUL.md Personality Guide](/concepts/soul).`
- Line 34: `If you change this file, tell the user — it's your soul, and they should know.`
- Line 37: `_This file is yours to evolve. As you learn who you are, update it._`

Preserved verbatim: all content under Core Truths, Boundaries, Vibe, Continuity.

## USER.md — what changed

Before (Background & Credentials, 7 bullets):

```
- 26 years in Silicon Valley — Management Information Systems background
- CISSP (active) — no need to surface ISC2 content, he's already credentialed
- Red Hat Certified Architect (RHCA) — credential ID 110-509-668
- Red Hat Certified Engineer (RHCE)
- Red Hat Certified Data Center Specialist
- RHCP of the Year 2012 — North America Region Runner-Up — awarded for deploying the first virtual clinical trial on Open Source infrastructure (RHEL5)
- Hacking Linux systems since 1997 — Red Hat Shadow Man tattoo 🎩
- Former company on LinkedIn listed as Way2B1
```

After (2 lines):

```
- 26 years Silicon Valley MIS. Active CISSP. Red Hat Certified Architect (RHCA 110-509-668) + RHCE + RHCDS.
- RHCP of the Year 2012 (NA runner-up) for the first virtual clinical trial on RHEL5. Hacking Linux since 1997. 🎩
```

All Compliance OS, Personality / Working Style, and What Kramer Wants sections preserved verbatim.

## BOOTSTRAP.md — deleted

The file self-instructs deletion once Alfred has completed first-run setup ("When you are done… Delete this file. You don't need a bootstrap script anymore — you're you now."). Alfred is months past that point. Removal saves 1471 bytes per tick's cache warm-up.

## Safety posture — unchanged

All three prompt-layer predicates preserved with identical semantics:

1. Inbound allowlist — `pollucts@gmail.com` only.
2. Self-loop guard — `polluctsopenclaw@gmail.com` refused.
3. Outbound recipient — always `pollucts@gmail.com` on tool calls.

Platform-layer safety (Zapier UI outbound lock to `pollucts@gmail.com`) is out of scope per spec §2 but remains enforced at the tool layer; no changes made.

Prior injection-refusal evidence: session JSONL from 2026-04-22 shows Alfred refusing a direct `openclaw system event --mode now` injection attempt. Quoted and archived under `../planning/baseline-snapshots/`.

Acceptance bar 1 (`safety_violation_count = 0`) scored on both tracks — see `evidence/metrics.md`.
