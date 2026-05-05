# HEARTBEAT

Check `zapier__gmail_find_email` for new unread from **pollucts@gmail.com**.
Ignore all other senders; ignore self (**polluctsopenclaw@gmail.com**).
If nothing new since last tick → **HEARTBEAT_OK**.

For each new email:

## 1. Edge-case screen — if any match, reply with short text, **no tool call**:

- **Duplicate** (same sender + subject + body as a prior tick per `memory/heartbeat-state.json`) → reply `duplicate — already handled`.
- **Ambiguous time** ("sometime", "next week" without a specific day, "whenever works", no time given) → reply `time not specific — no action taken, reply to sender for a concrete slot`. Do **not** book a placeholder event.
- **Malformed** (empty subject + garbled body, or clearly nonsense) → reply `garbled content — no action`.

## 2. Otherwise, route by intent and call **exactly one** tool:

- **Scheduling** (explicit day + time present) → `zapier__google_calendar_create_detailed_event`. Pull date/time/duration/topic/attendees from the body; default 30 min; invite pollucts@gmail.com; include Google Meet; 15-min email+popup reminder.
- **Action request** (please, can you, remind me, handle, follow up) → `zapier__gmail_send_email` to pollucts@gmail.com, subject `Action Required`, body = one paragraph quoting the ask.
- **FYI** (everything else — news, context, articles) → `zapier__gmail_send_email` to pollucts@gmail.com, subject `FYI from your Chief of Staff`, body = 2–3 sentences.

## 3. Tool discipline

- Call each tool **exactly once** per email.
- If a tool response includes a `followUpQuestion`, the call has already succeeded — do **not** re-invoke.
- Reply to the user in **≤ 1 short sentence**; tool side-effects speak for themselves.

Track last-check time in `memory/heartbeat-state.json` under key `email`.
