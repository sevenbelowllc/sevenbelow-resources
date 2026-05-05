from datetime import datetime

import pytest
from pydantic import ValidationError

from openclaw_agent.models import (
    ClassificationResult,
    Email,
    Intent,
)


def test_email_validates_required_fields():
    e = Email(
        id="e1",
        sender="owner@example.com",
        subject="Hi",
        body="Hello",
        unread=True,
        received_at=datetime.now(),
    )
    assert e.id == "e1"


def test_email_rejects_missing_field():
    with pytest.raises(ValidationError):
        Email(  # type: ignore[call-arg]
            id="e1", sender="x", subject="y", body="z", unread=True
        )


def test_intent_enum_values():
    assert Intent.MEETING.value == "meeting"
    assert Intent.ACTION.value == "action"
    assert Intent.FYI.value == "fyi"
    assert Intent.NONE.value == "none"


def test_classification_result_round_trip():
    r = ClassificationResult(
        intent=Intent.ACTION, confidence=0.92, reasoning="explicit ask"
    )
    assert r.intent is Intent.ACTION
    assert r.confidence == 0.92


def test_classification_result_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        ClassificationResult(
            intent=Intent.FYI, confidence=1.5, reasoning="bad"
        )
