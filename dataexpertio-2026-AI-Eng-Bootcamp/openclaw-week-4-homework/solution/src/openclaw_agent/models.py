from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    unread: bool
    received_at: datetime


class Intent(str, Enum):
    MEETING = "meeting"
    ACTION = "action"
    FYI = "fyi"
    NONE = "none"


class ClassificationResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
