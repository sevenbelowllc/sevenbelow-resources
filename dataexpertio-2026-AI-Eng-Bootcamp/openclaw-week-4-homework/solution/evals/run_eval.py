"""Run the seven-scenario evaluation against the fixed agent."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "solution"))
sys.path.insert(0, str(ROOT / "solution" / "src"))

from openclaw_agent import (  # noqa: E402
    ChiefOfStaffAgent, Email, IntentClassifier, MockZapierTools,
)

from evals.dataset import DATASET_NAME, ensure_dataset  # noqa: E402
from evals.evaluators import ALL_EVALUATORS  # noqa: E402


APPROVED_SENDER = "owner@example.com"
APPROVED_RECIPIENT = "owner@example.com"


def _build_emails(inbox_dicts):
    return [
        Email(received_at=datetime.now(), **d) for d in inbox_dicts
    ]


def target(inputs: dict) -> dict:
    inbox = _build_emails(inputs["inbox"])
    tools = MockZapierTools(inbox=inbox)
    agent = ChiefOfStaffAgent(
        tools=tools,
        approved_senders={APPROVED_SENDER},
        approved_recipient=APPROVED_RECIPIENT,
        classifier=IntentClassifier(),
    )
    result = agent.heartbeat()
    return {
        "result": result,
        "calls": tools.calls,
        "tool_call_count": tools.tool_call_count,
    }


def preflight() -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        sys.exit("ANTHROPIC_API_KEY missing; populate .env from .env.example.")
    if "LANGSMITH_API_KEY" not in os.environ:
        sys.exit("LANGSMITH_API_KEY missing; cannot upload evaluation runs.")


def main() -> None:
    load_dotenv(ROOT / ".env")
    preflight()
    Client()  # raises if endpoint/key invalid
    ensure_dataset()

    experiment = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=ALL_EVALUATORS,
        experiment_prefix="openclaw-week4-after",
        metadata={"version": "after"},
    )
    # LangSmith already prints the experiment URL at the start of the run.
    # ExperimentResults exposes experiment_name (not experiment_url) in
    # current SDK versions; guard with getattr for compatibility.
    name = getattr(experiment, "experiment_name", None) or getattr(
        experiment, "experiment_id", "unknown"
    )
    print(f"\nExperiment: {name}")
    print("(URL printed at top of this run; copy it into SUBMISSION.md)")


if __name__ == "__main__":
    main()
