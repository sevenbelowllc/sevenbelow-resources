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
