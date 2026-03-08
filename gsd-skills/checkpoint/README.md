# GSD Checkpoint Skill

<p align="center">
  <img src="../../assets/logo.png" alt="[YOUR PRODUCT] Logo" width="150">
</p>

<p align="center">
  <strong>Lightweight State Preservation for GSD Workflows</strong>
</p>

<p align="center">
  <a href="https://github.com/[YOUR-GITHUB-ORG]/sevenbelow-resources">🏠 Main Repo</a> •
  <a href="#installation">⚡ Quick Install</a> •
  <a href="#usage">📖 Usage</a>
</p>

---

A fast checkpointing system for the GSD (Get Shit Done) framework that prevents context loss during Claude Code sessions.

---

## Table of Contents

- [What This Skill Does](#what-this-skill-does)
  - [Why Checkpoints Matter](#why-checkpoints-matter)
- [Installation](#installation)
  - [Quick Install](#quick-install)
  - [What Gets Installed](#what-gets-installed)
  - [Manual Installation](#manual-installation)
- [Supported Platforms](#supported-platforms)
  - [Requirements](#requirements)
- [Usage](#usage)
  - [Running a Checkpoint](#running-a-checkpoint)
  - [When to Checkpoint](#when-to-checkpoint)
  - [Checkpoint Output](#checkpoint-output)
  - [Where Checkpoints Are Stored](#where-checkpoints-are-stored)
- [The Verification Script](#the-verification-script)
  - [What It Checks](#what-it-checks)
  - [Sample Output](#sample-output)
- [Integration with GSD Workflow](#integration-with-gsd-workflow)
- [Configuration](#configuration)
  - [Checkpoint File Location](#checkpoint-file-location)
  - [Auto-Commit Behavior](#auto-commit-behavior)
- [Troubleshooting](#troubleshooting)
- [Related Resources](#related-resources)
- [License](#license)

---

## What This Skill Does

The GSD Checkpoint Skill provides **rapid state serialization** to preserve your work context before it gets lost to context window compression. It captures:

- **Current Position**: Which phase, plan, and task you're actively working on
- **Completed Work**: What you've just finished (specific, actionable details)
- **In-Progress Items**: What's currently being worked on
- **Next Steps**: What comes after your current work
- **Key Decisions**: Important decisions made during the session
- **File Status**: Uncommitted changes and their state
- **Artifact Status**: Health of PLAN.md, SUMMARY.md, and STATE.md files

### Why Checkpoints Matter

Claude Code has a finite context window. As conversations grow, older context gets compressed and eventually lost. Without checkpoints:
- You forget where you left off
- Decisions made 20 minutes ago vanish
- File changes get lost in the noise
- Phase progress becomes unclear

**Checkpoints solve this by writing state to disk** — making it recoverable across sessions and immune to context compaction.

---

## Installation

### Quick Install

```bash
# Navigate to the checkpoint directory
cd gsd-skills/checkpoint

# Run the install script
./install-checkpoint.sh
```

### What Gets Installed

| File | Destination | Purpose |
|------|-------------|---------|
| `checkpoint.md` | `~/.claude/commands/gsd/checkpoint.md` | The checkpoint command for Claude Code |
| `verify-gsd-state.js` | `~/.claude/get-shit-done/scripts/verify-gsd-state.js` | State verification script |

### Manual Installation

If you prefer to install manually:

```bash
# Create directories
mkdir -p ~/.claude/commands/gsd
mkdir -p ~/.claude/get-shit-done/scripts

# Copy files
cp checkpoint.md ~/.claude/commands/gsd/
cp verify-gsd-state.js ~/.claude/get-shit-done/scripts/
```

---

## Supported Platforms

This skill works across all platforms supported by Claude Code:

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Fully Supported | Tested on macOS 13+ (Intel & Apple Silicon) |
| **Linux** | ✅ Fully Supported | Tested on Ubuntu 20.04+, Debian, Fedora |
| **Windows** | ✅ Fully Supported | Works via WSL2 or native Node.js |

### Requirements

- **Claude Code** installed and configured
- **Node.js** 14+ (for the verification script)
- **Git** (for checkpoint commits)
- **Bash** (for the install script)

---

## Usage

### Running a Checkpoint

Once installed, use the checkpoint command in Claude Code:

```
/gsd:checkpoint
```

### When to Checkpoint

Run checkpoints frequently — they're designed to be fast (< 30 seconds):

| Trigger | Why |
|---------|-----|
| **After completing a task** | Capture what was done before moving on |
| **Before starting complex work** | Establish a baseline before diving deep |
| **When context compacts** | If Claude says "Let me summarize..." — checkpoint NOW |
| **Before spawning subagents** | Preserve state before parallel execution |
| **Every 10-15 minutes** | During long sessions, checkpoint regularly |
| **Before ending a session** | Always checkpoint before walking away |

### Checkpoint Output

After running, you'll see:

```
✓ Checkpoint saved [2026-03-07 14:30]
  Phase: 08-user-authentication
  Status: in-progress
  Artifacts: ✓ ok
```

### Where Checkpoints Are Stored

Checkpoints are written to `.planning/CHECKPOINT.md` in your project root. This file:
- Is git-tracked (automatically committed)
- Can be read to resume work
- Survives context window compression
- Can be referenced across sessions

---

## The Verification Script

The `verify-gsd-state.js` script provides artifact health checks:

```bash
# Run manually
node ~/.claude/get-shit-done/scripts/verify-gsd-state.js

# Or let the checkpoint command run it automatically
```

### What It Checks

1. **STATE.md exists** — The master state file
2. **Phase directories** — Each phase has required artifacts
3. **PLAN vs SUMMARY** — Plans without summaries indicate incomplete work
4. **Overall consistency** — Flags issues before they become problems

### Sample Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD State Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ STATE.md exists (modified: 2026-03-07 14:30)

Phase Directory Status:
─────────────────────────────────────────────────────
✅ 07-database-setup: 2 plan(s), 2 summary(s)
✅ 08-user-authentication: 1 plan(s), 0 summary(s)
⚠️  09-api-endpoints: PLAN exists but NO SUMMARY (incomplete execution)

─────────────────────────────────────────────────────
❌ Found 1 issue(s). GSD state needs attention.

To fix empty phases, run:
  /gsd:plan-phase 9
  /gsd:execute-phase 9
```

---

## Integration with GSD Workflow

The checkpoint skill integrates seamlessly with the full GSD workflow:

```mermaid
flowchart LR
    A[Start Session] --> B{/gsd:checkpoint}
    B --> C[Do Work]
    C --> D{Task Complete?}
    D -->|Yes| E[/gsd:checkpoint]
    D -->|No| F{Context Compacting?}
    F -->|Yes| B
    F -->|No| C
    E --> G[/gsd:execute-phase]
    G --> H[End Session]
    H --> I{/gsd:checkpoint}
```

---

## Configuration

No configuration required — checkpoint works out of the box. However, you can customize:

### Checkpoint File Location

By default: `.planning/CHECKPOINT.md`

To change, modify the `checkpoint.md` command file after installation.

### Auto-Commit Behavior

Checkpoints auto-commit by default. To disable:

```bash
# In checkpoint.md, comment out the commit step
# Or set NO_AUTO_COMMIT=1 in your environment
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Command not found" | Ensure files are in `~/.claude/commands/gsd/` and restart Claude Code |
| "Permission denied" on install | Run `chmod +x install-checkpoint.sh` before executing |
| Verification script fails | Ensure Node.js 14+ is installed: `node --version` |
| Checkpoints not committing | Check git is initialized: `git status` |
| Windows path issues | Use WSL2 or update paths in the checkpoint.md file |

---

## Related Resources

- **GSD Framework**: [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
- **Claude Code Documentation**: [https://docs.anthropic.com/en/docs/agents-and-tools/claude-code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code)
- **Session Continuity Guide**: Part of the GSD documentation

---

## License

MIT — See [LICENSE](../../LICENSE) for details.

---

*Part of the [YOUR PRODUCT] GSD Skills Collection. Built for developers who ship.*
