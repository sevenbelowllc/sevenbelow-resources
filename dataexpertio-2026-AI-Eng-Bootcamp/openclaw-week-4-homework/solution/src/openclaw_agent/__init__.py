"""Hardened OpenClaw Chief-of-Staff agent package."""

from .agent import HEARTBEAT_OK, ChiefOfStaffAgent
from .classifier import IntentClassifier, build_llm
from .models import ClassificationResult, Email, Intent
from .safety import contains_injection, is_approved_sender
from .tools import MockZapierTools

__all__ = [
    "ChiefOfStaffAgent",
    "ClassificationResult",
    "Email",
    "HEARTBEAT_OK",
    "Intent",
    "IntentClassifier",
    "MockZapierTools",
    "build_llm",
    "contains_injection",
    "is_approved_sender",
]
