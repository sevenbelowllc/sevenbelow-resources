"""JSON schemas for all skill outputs."""

CITATION_SCHEMA = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "source": {"type": "string"},
    },
    "required": ["claim", "source"],
    "additionalProperties": True,
}

RISK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "risk": {"type": "string"},
        "severity": {"type": "string"},
        "mitigation": {"type": "string"},
    },
    "required": ["risk", "severity", "mitigation"],
    "additionalProperties": True,
}

CONFIDENCE_ENUM = {"type": "string", "enum": ["high", "medium", "low"]}

TRIAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "severity": {"type": "string"},
        "priority": {"type": "string"},
        "labels": {"type": "array", "items": {"type": "string"}},
        "recommended_owner": {"type": "string"},
        "confidence": CONFIDENCE_ENUM,
        "uncertainty_flags": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": CITATION_SCHEMA},
        "reasoning": {"type": "string"},
    },
    "required": [
        "status",
        "severity",
        "priority",
        "labels",
        "recommended_owner",
        "confidence",
        "uncertainty_flags",
        "citations",
        "reasoning",
    ],
    "additionalProperties": True,
}

SUMMARIZE_PR_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "summary": {"type": "string"},
        "risk_checklist": {"type": "array", "items": RISK_ITEM_SCHEMA},
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "required": ["status", "summary", "risk_checklist", "confidence", "citations"],
    "additionalProperties": True,
}

DIGEST_COMMITS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "sections": {
            "type": "object",
            "properties": {
                "what_changed": {"type": "string"},
                "risk_impact": {"type": "string"},
                "action_needed": {"type": "string"},
            },
            "required": ["what_changed", "risk_impact", "action_needed"],
            "additionalProperties": True,
        },
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "required": ["status", "sections", "confidence", "citations"],
    "additionalProperties": True,
}

DRAFT_EMAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "pii_redacted": {"type": "boolean"},
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "required": ["status", "subject", "body", "pii_redacted", "confidence", "citations"],
    "additionalProperties": True,
}

INSUFFICIENT_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["insufficient_context"]},
        "missing": {"type": "array", "items": {"type": "string"}},
        "suggestion": {"type": "string"},
    },
    "required": ["status", "missing", "suggestion"],
    "additionalProperties": True,
}

SKILL_SCHEMAS: dict[str, list[dict]] = {
    "triage-issue": [TRIAGE_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "summarize-pr": [SUMMARIZE_PR_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "digest-commits": [DIGEST_COMMITS_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "draft-email": [DRAFT_EMAIL_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
}
