"""Release Radar CLI — batch-mode orchestrator."""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from guardrails.base import GuardrailError
from guardrails.chain import GuardrailChain
from guardrails.citation import CitationGuardrail
from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail
from scripts.gh_adapter import GitHubAdapter

# Load .env from release-radar/ or parent claude-code-homework/
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env")

SKILL_PROMPTS_DIR = Path(__file__).parent.parent / "claude_skills"


def build_chain() -> GuardrailChain:
    return GuardrailChain(
        pre_guardrails=[
            InsufficientContextGuardrail(),
            PIIRedactionGuardrail(),
        ],
        post_guardrails=[
            SchemaValidationGuardrail(),
            CitationGuardrail(),
            UncertaintyGuardrail(),
            PIIRedactionGuardrail(),
        ],
    )


def load_skill_prompt(skill_name: str) -> str:
    path = SKILL_PROMPTS_DIR / skill_name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text()


def call_claude(skill_name: str, input_data: dict, client: anthropic.Anthropic) -> dict:
    """Call Claude API with skill prompt and input data."""
    skill_prompt = load_skill_prompt(skill_name)
    user_message = (
        f"Process this input and return JSON output:\n\n"
        f"```json\n{json.dumps(input_data, indent=2)}\n```"
    )

    # Use streaming to support DataExpert proxy which returns SSE
    text = ""
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=skill_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)


def process_skill(
    skill_name: str,
    input_data: dict,
    chain: GuardrailChain,
    client: anthropic.Anthropic,
) -> dict:
    """Run guardrails, call Claude, run post-guardrails."""
    try:
        checked_input = chain.run_pre(input_data, skill=skill_name)
    except GuardrailError as e:
        if e.details.get("status") == "insufficient_context":
            return e.details
        return {"error": str(e)}

    output = call_claude(skill_name, checked_input, client)

    try:
        checked_output = chain.run_post(output, skill=skill_name, input_data=checked_input)
    except GuardrailError as e:
        print(
            f"Warning: Post-guardrail '{e.guardrail_name}' failed: {e.message}",
            file=sys.stderr,
        )
        return output

    return checked_output


def cmd_triage(args, chain, client):
    with open(args.input) as f:
        issues = json.load(f)
    results = []
    for issue in issues:
        result = process_skill("triage-issue", issue, chain, client)
        results.append({"issue_id": issue.get("id"), "result": result})
    json.dump(results, sys.stdout, indent=2)
    print()


def cmd_summarize(args, chain, client):
    with open(args.input) as f:
        prs = json.load(f)
    results = []
    for pr in prs:
        result = process_skill("summarize-pr", pr, chain, client)
        results.append({"pr_id": pr.get("id"), "result": result})
    json.dump(results, sys.stdout, indent=2)
    print()


def cmd_digest(args, chain, client):
    with open(args.input) as f:
        data = json.load(f)
    if isinstance(data, list):
        data = {"commits": data, "date_range": {"start": "unknown", "end": "unknown"}}
    result = process_skill("digest-commits", data, chain, client)
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_email(args, chain, client):
    with open(args.input) as f:
        commits_data = json.load(f)
    if isinstance(commits_data, list):
        commits_data = {"commits": commits_data}

    digest = process_skill("digest-commits", commits_data, chain, client)

    pr_summaries = []
    if args.prs:
        with open(args.prs) as f:
            prs = json.load(f)
        for pr in prs[:5]:
            summary = process_skill("summarize-pr", pr, chain, client)
            pr_summaries.append(summary)

    email_input = {
        "digest": digest,
        "pr_summaries": pr_summaries,
        "recipient_context": "engineering leadership and non-technical stakeholders",
        "week": (
            f"{commits_data.get('date_range', {}).get('start', 'unknown')} to "
            f"{commits_data.get('date_range', {}).get('end', 'unknown')}"
        ),
    }
    result = process_skill("draft-email", email_input, chain, client)
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_weekly(args, chain, client):
    github_token = args.token or os.getenv("GITHUB_PAT_TOKEN") or os.getenv("GITHUB_TOKEN")
    adapter = GitHubAdapter(mock=not args.live, token=github_token)
    repo = args.repo or "mock/repo"

    print("=== Release Radar Weekly Report ===", file=sys.stderr)

    issues = adapter.get_issues(repo=repo, since=args.since)
    prs = adapter.get_pull_requests(repo=repo, since=args.since)
    commits_raw = adapter.get_commits(repo=repo, since=args.since)

    print(
        f"Loaded: {len(issues)} issues, {len(prs)} PRs, {len(commits_raw)} commits",
        file=sys.stderr,
    )

    print("Triaging issues...", file=sys.stderr)
    triage_results = []
    for issue in issues:
        result = process_skill("triage-issue", issue, chain, client)
        triage_results.append({"issue_id": issue.get("id"), "result": result})

    print("Summarizing PRs...", file=sys.stderr)
    pr_summaries = []
    for pr in prs[:10]:
        result = process_skill("summarize-pr", pr, chain, client)
        pr_summaries.append(result)

    print("Digesting commits...", file=sys.stderr)
    commits_input = {
        "commits": commits_raw,
        "date_range": {
            "start": args.since or "unknown",
            "end": args.until or "unknown",
        },
    }
    digest = process_skill("digest-commits", commits_input, chain, client)

    print("Drafting email...", file=sys.stderr)
    email_input = {
        "digest": digest,
        "pr_summaries": pr_summaries,
        "recipient_context": "engineering leadership and non-technical stakeholders",
        "week": f"{args.since or 'past week'} to {args.until or 'now'}",
    }
    email = process_skill("draft-email", email_input, chain, client)

    report = {
        "triage": triage_results,
        "pr_summaries": pr_summaries,
        "digest": digest,
        "email": email,
    }
    json.dump(report, sys.stdout, indent=2)
    print()


def main():
    parser = argparse.ArgumentParser(description="Release Radar — GitHub activity summarizer")
    subparsers = parser.add_subparsers(dest="command")

    p_triage = subparsers.add_parser("triage", help="Triage GitHub issues")
    p_triage.add_argument("--input", required=True, help="Path to issues JSON")

    p_summarize = subparsers.add_parser("summarize", help="Summarize pull requests")
    p_summarize.add_argument("--input", required=True, help="Path to PRs JSON")

    p_digest = subparsers.add_parser("digest", help="Digest commits")
    p_digest.add_argument("--input", required=True, help="Path to commits JSON")

    p_email = subparsers.add_parser("email", help="Draft stakeholder email")
    p_email.add_argument("--input", required=True, help="Path to commits JSON")
    p_email.add_argument("--prs", help="Path to PRs JSON (optional)")

    parser.add_argument("--weekly", action="store_true", help="Run full weekly report")
    parser.add_argument("--repo", help="GitHub repo (owner/name)")
    parser.add_argument("--live", action="store_true", help="Use live GitHub API")
    parser.add_argument("--since", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", help="End date (YYYY-MM-DD)")
    parser.add_argument("--token", help="GitHub token (overrides .env)")

    args = parser.parse_args()
    session_id = str(uuid.uuid4())
    client = anthropic.Anthropic(
        default_headers={"X-Session-ID": session_id},
    )
    chain = build_chain()

    if args.weekly:
        cmd_weekly(args, chain, client)
    elif args.command == "triage":
        cmd_triage(args, chain, client)
    elif args.command == "summarize":
        cmd_summarize(args, chain, client)
    elif args.command == "digest":
        cmd_digest(args, chain, client)
    elif args.command == "email":
        cmd_email(args, chain, client)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
