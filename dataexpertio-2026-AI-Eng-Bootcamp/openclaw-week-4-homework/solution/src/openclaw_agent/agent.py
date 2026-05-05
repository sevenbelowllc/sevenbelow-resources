from __future__ import annotations

import logging
from typing import Iterable

from langsmith import traceable

from .classifier import IntentClassifier
from .models import Email, Intent
from .safety import contains_injection, is_approved_sender
from .tools import MockZapierTools

logger = logging.getLogger(__name__)

HEARTBEAT_OK = "HEARTBEAT_OK"


class ChiefOfStaffAgent:
    def __init__(
        self,
        tools: MockZapierTools,
        approved_senders: Iterable[str] | str,
        approved_recipient: str,
        classifier: IntentClassifier,
    ) -> None:
        if isinstance(approved_senders, str):
            approved_senders = {approved_senders}
        self.tools = tools
        self.approved_senders = frozenset(s.strip().lower() for s in approved_senders)
        self.approved_recipient = approved_recipient
        self.classifier = classifier

    @traceable(name="heartbeat")
    def heartbeat(self) -> str:
        try:
            raw = self.tools.find_email("unread last 24h", limit=100)
        except Exception as exc:  # noqa: BLE001 — bounded tool boundary
            logger.warning("find_email failed (%s); returning HEARTBEAT_OK", type(exc).__name__)
            return HEARTBEAT_OK

        unique = list({e.id: e for e in raw}.values())

        for email in unique:
            if not is_approved_sender(email, self.approved_senders):
                logger.info("dropped unapproved sender for email %s", email.id)
                continue

            hit, pattern = contains_injection(email)
            if hit:
                logger.warning(
                    "quarantined email %s; matched injection pattern %r",
                    email.id, pattern,
                )
                continue

            try:
                result = self.classifier.classify(email)
            except Exception as exc:  # noqa: BLE001
                logger.warning("classify failed for %s (%s)", email.id, type(exc).__name__)
                continue

            try:
                self._dispatch(result.intent, email)
            except Exception as exc:  # noqa: BLE001 — bounded handler boundary
                logger.warning(
                    "handler %s failed for %s (%s)",
                    result.intent.value, email.id, type(exc).__name__,
                )

        return HEARTBEAT_OK

    def _dispatch(self, intent: Intent, email: Email) -> None:
        if intent is Intent.MEETING:
            self._handle_meeting(email)
        elif intent is Intent.ACTION:
            self._handle_action(email)
        elif intent is Intent.FYI:
            self._handle_fyi(email)
        else:  # Intent.NONE
            logger.info("no-op for email %s (intent=NONE)", email.id)

    def _handle_meeting(self, email: Email) -> None:
        # Conservative default: 30-min slot next business day at 14:00.
        # Real parsing is out of scope for this homework; the previous code
        # had end < start which is the bug we're fixing.
        start = "next business day 14:00"
        end = "next business day 14:30"
        title = f"Meeting requested: {email.subject[:60]}"
        self.tools.create_calendar_event(
            title=title, start=start, end=end, attendee=email.sender,
        )

    def _handle_action(self, email: Email) -> None:
        body = (
            "Action Required\n\n"
            f"From: {email.sender}\n"
            f"Subject: {email.subject}\n\n"
            f"Body:\n{email.body}\n"
        )
        self.tools.send_email(
            to=self.approved_recipient, subject="Action Required", body=body,
        )

    def _handle_fyi(self, email: Email) -> None:
        body = (
            "FYI\n\n"
            f"From: {email.sender}\n"
            f"Subject: {email.subject}\n\n"
            f"Summary: {email.body[:200]}"
        )
        self.tools.send_email(
            to=self.approved_recipient, subject="FYI", body=body,
        )
