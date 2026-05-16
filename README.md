# SevenBelow Resources

<p align="center">
  <img src="assets/logo.png" alt="SevenBelow Logo" width="200">
</p>

<p align="center">
  <strong>Public Resources from SevenBelow — Compliance OS</strong>
</p>

<p align="center">
  <a href="https://sevenbelow.com">🌐 SevenBelow</a> •
  <a href="https://www.linkedin.com/in/davidkramer13/">💼 LinkedIn</a>
</p>

---

Public showcase repo for SevenBelow work: production Claude Code framework, AI-engineering bootcamp solutions, and legacy GSD tooling. Each top-level directory ships its own README with deeper detail.

---

## 📂 What's Inside

### 🏛️ [`claude-setups/compliance-os-project-v1/`](./claude-setups/compliance-os-project-v1/)

**Production-grade Claude Code framework — v1.** Foundation of the SevenBelow Compliance OS MVP.

Highlights:
- **Three-repo governance pattern** — Authority (`compliance-os-goldmaster-prds`), Orchestration (`sevenbelow-orchestrator`), Execution (`compliance-core`, `compliance-ui`)
- **GSD (Get Shit Done) protocol** — disciplined plan → execute → verify loop
- **CARL (Context-Aware Rule Layer)** — governance rules layered across repos
- **Claude Skills system** — composable, reusable skill modules
- **Operating contracts** — strict CLAUDE.md per repo enforcing scope and boundaries
- **`global/`** — shared settings, hooks, agents, commands across all v1 repos

Includes the original mentor shoutout (Charles Dove / CC Strategic AI, James Goldbach / Agent Architects) and the full architecture deep-dive with mermaid diagrams.

> Status: v1 — superseded by an in-progress v2 architecture. Published as the reference implementation it grew out of.

---

### 🎓 [`dataexpertio-2026-AI-Eng-Bootcamp/`](./dataexpertio-2026-AI-Eng-Bootcamp/)

<p align="center">
  <a href="https://www.dataexpert.io/">
    <img src="assets/dataexpert-logo.png" alt="DataExpert.io" width="200">
  </a>
</p>

**DataExpert.io 2026 AI Engineering Bootcamp homework solutions.** Each subdir has its own README; original problem statements and solutions are not reproduced.

#### About DataExpert.io & Zach Wilson

[**DataExpert.io**](https://www.dataexpert.io/) is the data and AI engineering education platform founded by **[Zach Wilson](https://www.linkedin.com/in/eczachly/)** — ex-Airbnb / Netflix / Facebook data engineer and one of the most-followed voices in data on LinkedIn / YouTube. The platform runs structured, cohort-based bootcamps (Data Engineering, AI Engineering, Analytics) that pair production-grade curriculum with weekly homework graded against real systems. The 2026 AI Engineering track covered Claude Code agent design, LangChain / LangGraph, OpenClaw agent debugging and token-efficiency, observability with Langfuse, and LangSmith evaluation — every solution in this directory shipped against that curriculum.

> Big thanks to **Zach Wilson** and the DataExpert.io team for building one of the few bootcamps where you actually have to ship working systems to pass. Highly recommended — [dataexpert.io](https://www.dataexpert.io/).

Highlights:
- **[`claude-code-homework/`](./dataexpertio-2026-AI-Eng-Bootcamp/claude-code-homework/)** — *Release Radar*: GitHub-activity tool (issue triage, PR summaries, commit digests, stakeholder emails) built as Claude Code skills + CLI batch mode, with a guardrail chain (PII redaction, citation, schema validation, uncertainty/insufficient-context handling)
- **[`langchain-homework-2026/`](./dataexpertio-2026-AI-Eng-Bootcamp/langchain-homework-2026/)** — three LangChain/LangGraph assignments: context-overflow management, bounded infinite-researcher loop, MCP middleware. Includes per-assignment runtime logs, writeups, and an aggregate token-report tool
- **[`openclaw-week-3-homework/`](./dataexpertio-2026-AI-Eng-Bootcamp/openclaw-week-3-homework/)** — token-efficiency optimization on an OpenClaw Alfred workflow. Self-hosted Langfuse for trace capture, before/after metrics extraction, evidence collected on both live and simulated runs
- **[`openclaw-week-4-homework/`](./dataexpertio-2026-AI-Eng-Bootcamp/openclaw-week-4-homework/)** — debug-and-harden on a broken OpenClaw agent. Packaged `openclaw_agent` module, LangSmith evals, safety/tool/model/classifier test suites, before/after metrics, preflight check

---

### 🛠️ [`gsd-skills/checkpoint/`](./gsd-skills/checkpoint/)

**GSD Checkpoint Skill — historical showcase.** Lightweight state-preservation skill for Claude Code sessions running the GSD protocol. Captures session state to prevent context loss across compaction events.

> Status: superseded by GSD v2. Kept here as a reference for what a self-contained, installable Claude Code skill looks like end-to-end (`SKILL.md` body, install script, state-verification helper).

---

## 🧭 Navigation

| If you want… | Go to |
|---|---|
| Production Claude Code framework + GSD/CARL deep dive | [`claude-setups/compliance-os-project-v1/`](./claude-setups/compliance-os-project-v1/) |
| Bootcamp solutions (Claude Code, LangChain, OpenClaw) | [`dataexpertio-2026-AI-Eng-Bootcamp/`](./dataexpertio-2026-AI-Eng-Bootcamp/) |
| Example installable Claude Code skill | [`gsd-skills/checkpoint/`](./gsd-skills/checkpoint/) |

---

## 📜 License

See [LICENSE](./LICENSE).
