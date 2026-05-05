from datetime import datetime
from unittest.mock import MagicMock

from pydantic import ValidationError

from openclaw_agent.classifier import IntentClassifier
from openclaw_agent.models import ClassificationResult, Email, Intent


def _email(subject: str, body: str) -> Email:
    return Email(
        id="e", sender="x@y.com", subject=subject, body=body,
        unread=True, received_at=datetime.now(),
    )


def test_classifier_returns_chain_output_when_confident():
    chain = MagicMock()
    chain.invoke.return_value = ClassificationResult(
        intent=Intent.MEETING, confidence=0.9, reasoning="meeting"
    )
    clf = IntentClassifier(chain=chain)

    result = clf.classify(_email("Schedule a sync", "30 min Tuesday"))

    assert result.intent is Intent.MEETING
    chain.invoke.assert_called_once()
    args = chain.invoke.call_args[0][0]
    # LLM must NOT see sender or id
    assert "x@y.com" not in str(args)


def test_classifier_falls_back_to_none_on_low_confidence():
    chain = MagicMock()
    chain.invoke.return_value = ClassificationResult(
        intent=Intent.MEETING, confidence=0.2, reasoning="unsure"
    )
    clf = IntentClassifier(chain=chain, min_confidence=0.4)

    result = clf.classify(_email("?", "?"))

    assert result.intent is Intent.NONE


def test_classifier_falls_back_to_none_on_validation_error():
    chain = MagicMock()
    chain.invoke.side_effect = ValidationError.from_exception_data(
        "ClassificationResult", []
    )
    clf = IntentClassifier(chain=chain)

    result = clf.classify(_email("x", "y"))

    assert result.intent is Intent.NONE
    assert "fallback" in result.reasoning.lower()


def test_classifier_falls_back_to_none_on_unexpected_exception():
    chain = MagicMock()
    chain.invoke.side_effect = RuntimeError("network down")
    clf = IntentClassifier(chain=chain)

    result = clf.classify(_email("x", "y"))

    assert result.intent is Intent.NONE
