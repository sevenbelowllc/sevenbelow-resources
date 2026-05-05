# Release Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Release Radar — a Claude Code skills-based tool that triages GitHub issues, summarizes PRs, digests commits, and drafts stakeholder emails, with 5 guardrails, dual-mode operation (interactive + batch), and HW2 documentation.

**Architecture:** 5 Claude Code skills backed by a shared Python guardrails library. A CLI orchestrator (`release_radar.py`) calls the Claude API and GitHub API for batch mode. Hooks wire guardrails into interactive mode. Mock + live GitHub data via a unified adapter.

**Tech Stack:** Python 3.11+, Anthropic SDK, GitHub REST API, jsonschema, ruff, mypy, pytest

**Spec:** `claude-code-homework/planning/specs/2026-04-11-release-radar-design.md`

**Working directory:** All paths below are relative to:
`/Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar/`

---

## Task 1: Project Scaffold + Config

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `guardrails/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`

- [ ] **Step 1: Create project directory structure**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
mkdir -p release-radar/{guardrails/hooks,scripts,tests/{unit,integration},claude_skills/{triage-issue,summarize-pr,digest-commits,draft-email,handoff},data/{mock,samples/{sample_1_triage,sample_2_insufficient,sample_3_email}},memory,docs,.claude}
```

- [ ] **Step 2: Create `.gitignore`**

```
# release-radar/.gitignore
.env
__pycache__/
*.pyc
.mypy_cache/
.pytest_cache/
.ruff_cache/
*.egg-info/
dist/
build/
.coverage
htmlcov/
```

- [ ] **Step 3: Create `.env.example`**

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
GITHUB_TOKEN=ghp_your-token-here
```

- [ ] **Step 4: Create `requirements.txt`**

```
# Core
anthropic>=0.40.0
requests>=2.31.0
python-dotenv>=1.0.0
jsonschema>=4.20.0

# Dev / Testing
pytest>=8.0.0
pytest-cov>=5.0.0
ruff>=0.4.0
mypy>=1.10.0
```

- [ ] **Step 5: Create `pyproject.toml`**

```toml
[project]
name = "release-radar"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: marks tests that call external APIs (deselect with '-m \"not integration\"')",
]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

- [ ] **Step 6: Create `__init__.py` files**

Create empty `__init__.py` in:
- `guardrails/__init__.py`
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`

- [ ] **Step 7: Create virtual environment and install dependencies**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 8: Verify linting runs clean on empty project**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
ruff check . && ruff format --check .
```

Expected: no errors (no Python files with content yet)

- [ ] **Step 9: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/
git commit -m "scaffold: Release Radar project structure, config, and dependencies"
```

---

## Task 2: Guardrail Base Class + Schemas

**Files:**
- Create: `guardrails/base.py`
- Create: `guardrails/schemas.py`
- Create: `tests/unit/test_schema_validation.py`
- Create: `guardrails/schema_validation.py`

- [ ] **Step 1: Write the failing test for schema validation**

Create `tests/unit/test_schema_validation.py`:

```python
"""Tests for schema validation guardrail."""

import pytest

from guardrails.base import Guardrail, GuardrailError
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.schemas import TRIAGE_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA


class TestSchemaValidationGuardrail:
    def setup_method(self):
        self.guardrail = SchemaValidationGuardrail()

    def test_valid_triage_output_passes(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug", "frontend"],
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "affects Safari", "source": "issue body"}],
            "reasoning": "Multiple users report 500 errors on Safari.",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert result == output

    def test_missing_required_field_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
            # missing priority, labels, etc.
        }
        with pytest.raises(GuardrailError, match="priority"):
            self.guardrail.check_output(output, skill="triage-issue")

    def test_wrong_field_type_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": "bug",  # should be array
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
        }
        with pytest.raises(GuardrailError, match="labels"):
            self.guardrail.check_output(output, skill="triage-issue")

    def test_extra_fields_allowed(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug"],
            "recommended_owner": "frontend-team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
            "extra_field": "should be fine",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert "extra_field" in result

    def test_insufficient_context_schema_valid(self):
        output = {
            "status": "insufficient_context",
            "missing": ["body", "reproduction steps"],
            "suggestion": "Please provide a detailed description.",
        }
        result = self.guardrail.check_output(output, skill="triage-issue")
        assert result["status"] == "insufficient_context"

    def test_invalid_confidence_value_raises(self):
        output = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug"],
            "recommended_owner": "frontend-team",
            "confidence": "very_high",  # invalid
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "test",
        }
        with pytest.raises(GuardrailError, match="confidence"):
            self.guardrail.check_output(output, skill="triage-issue")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python -m pytest tests/unit/test_schema_validation.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'guardrails.base'`

- [ ] **Step 3: Implement guardrail base class**

Create `guardrails/base.py`:

```python
"""Base class and exceptions for all guardrails."""


class GuardrailError(Exception):
    """Raised when a guardrail check fails."""

    def __init__(self, guardrail_name: str, message: str, details: dict | None = None):
        self.guardrail_name = guardrail_name
        self.message = message
        self.details = details or {}
        super().__init__(f"[{guardrail_name}] {message}")


class Guardrail:
    """Base class for all guardrails."""

    name: str = "base"

    def check_input(self, data: dict, skill: str = "") -> dict:
        """Pre-processing check. Returns modified data or raises GuardrailError."""
        return data

    def check_output(self, data: dict, skill: str = "") -> dict:
        """Post-processing check. Returns modified data or raises GuardrailError."""
        return data
```

- [ ] **Step 4: Implement output schemas**

Create `guardrails/schemas.py`:

```python
"""JSON schemas for all skill outputs."""

CITATION_SCHEMA = {
    "type": "object",
    "required": ["claim", "source"],
    "properties": {
        "claim": {"type": "string"},
        "source": {"type": "string"},
    },
}

RISK_ITEM_SCHEMA = {
    "type": "object",
    "required": ["risk", "severity", "mitigation"],
    "properties": {
        "risk": {"type": "string"},
        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
        "mitigation": {"type": "string"},
    },
}

CONFIDENCE_ENUM = {"type": "string", "enum": ["high", "medium", "low"]}

TRIAGE_OUTPUT_SCHEMA = {
    "type": "object",
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
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
        "priority": {"type": "string", "enum": ["p0", "p1", "p2", "p3"]},
        "labels": {"type": "array", "items": {"type": "string"}},
        "recommended_owner": {"type": "string"},
        "confidence": CONFIDENCE_ENUM,
        "uncertainty_flags": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": CITATION_SCHEMA},
        "reasoning": {"type": "string"},
    },
    "additionalProperties": True,
}

SUMMARIZE_PR_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["status", "summary", "risk_checklist", "confidence", "citations"],
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "summary": {"type": "string"},
        "risk_checklist": {"type": "array", "items": RISK_ITEM_SCHEMA},
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "additionalProperties": True,
}

DIGEST_COMMITS_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["status", "sections", "confidence", "citations"],
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "sections": {
            "type": "object",
            "required": ["what_changed", "risk_impact", "action_needed"],
            "properties": {
                "what_changed": {"type": "string"},
                "risk_impact": {"type": "string"},
                "action_needed": {"type": "string"},
            },
        },
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "additionalProperties": True,
}

DRAFT_EMAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["status", "subject", "body", "pii_redacted", "confidence", "citations"],
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "pii_redacted": {"type": "boolean"},
        "confidence": CONFIDENCE_ENUM,
        "citations": {"type": "array", "items": CITATION_SCHEMA},
    },
    "additionalProperties": True,
}

INSUFFICIENT_CONTEXT_SCHEMA = {
    "type": "object",
    "required": ["status", "missing", "suggestion"],
    "properties": {
        "status": {"type": "string", "enum": ["insufficient_context"]},
        "missing": {"type": "array", "items": {"type": "string"}},
        "suggestion": {"type": "string"},
    },
    "additionalProperties": True,
}

SKILL_SCHEMAS: dict[str, list[dict]] = {
    "triage-issue": [TRIAGE_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "summarize-pr": [SUMMARIZE_PR_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "digest-commits": [DIGEST_COMMITS_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
    "draft-email": [DRAFT_EMAIL_OUTPUT_SCHEMA, INSUFFICIENT_CONTEXT_SCHEMA],
}
```

- [ ] **Step 5: Implement schema validation guardrail**

Create `guardrails/schema_validation.py`:

```python
"""Schema validation guardrail using jsonschema."""

import jsonschema

from guardrails.base import Guardrail, GuardrailError
from guardrails.schemas import SKILL_SCHEMAS


class SchemaValidationGuardrail(Guardrail):
    """Validates skill output against JSON schemas."""

    name = "schema_validation"

    def check_output(self, data: dict, skill: str = "") -> dict:
        schemas = SKILL_SCHEMAS.get(skill)
        if not schemas:
            return data

        errors = []
        for schema in schemas:
            try:
                jsonschema.validate(instance=data, schema=schema)
                return data  # first matching schema passes
            except jsonschema.ValidationError as e:
                errors.append(str(e.message))

        raise GuardrailError(
            guardrail_name=self.name,
            message=f"Output does not match any valid schema for '{skill}': {errors[-1]}",
            details={"skill": skill, "errors": errors},
        )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python -m pytest tests/unit/test_schema_validation.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 7: Run linting**

```bash
ruff check guardrails/ tests/ && ruff format --check guardrails/ tests/
```

Expected: clean

- [ ] **Step 8: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/base.py release-radar/guardrails/schemas.py release-radar/guardrails/schema_validation.py release-radar/tests/unit/test_schema_validation.py
git commit -m "feat: guardrail base class, output schemas, and schema validation"
```

---

## Task 3: PII Redaction Guardrail

**Files:**
- Create: `guardrails/pii_redaction.py`
- Create: `tests/unit/test_pii_redaction.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_pii_redaction.py`:

```python
"""Tests for PII redaction guardrail."""

import pytest

from guardrails.pii_redaction import PIIRedactionGuardrail


class TestPIIRedactionPatterns:
    def setup_method(self):
        self.guardrail = PIIRedactionGuardrail()

    # --- Email ---
    def test_redacts_email(self):
        text = "Contact alice@example.com for details"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-EMAIL]" in result
        assert "alice@example.com" not in result

    def test_preserves_non_email_at_sign(self):
        text = "Use @mentions in GitHub"
        result = self.guardrail.redact_text(text)
        assert result == text

    # --- Phone ---
    def test_redacts_us_phone(self):
        text = "Call me at 555-123-4567"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-PHONE]" in result
        assert "555-123-4567" not in result

    def test_redacts_international_phone(self):
        text = "Phone: +1 (555) 123-4567"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-PHONE]" in result

    # --- SSN ---
    def test_redacts_ssn(self):
        text = "SSN: 123-45-6789"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-SSN]" in result
        assert "123-45-6789" not in result

    # --- Credit Card ---
    def test_redacts_credit_card(self):
        text = "Card: 4111 1111 1111 1111"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-CC]" in result

    def test_ignores_non_cc_numbers(self):
        text = "Issue #1234567890123456 filed"
        result = self.guardrail.redact_text(text)
        # Short numbers or numbers with # prefix should not be redacted as CC
        assert "[REDACTED-CC]" not in result

    # --- IP Address ---
    def test_redacts_ipv4(self):
        text = "Server at 192.168.1.100"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-IP]" in result

    # --- API Keys ---
    def test_redacts_anthropic_key(self):
        text = "key: sk-ant-api03-abcdef123456"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-KEY]" in result
        assert "sk-ant-" not in result

    def test_redacts_github_token(self):
        text = "token: ghp_abc123def456ghi789"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-KEY]" in result

    def test_redacts_github_pat(self):
        text = "pat: github_pat_abc123def456"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-KEY]" in result

    def test_redacts_slack_token(self):
        text = "token: xoxb-123-456-abc"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-KEY]" in result

    def test_redacts_aws_key(self):
        text = "aws_key: AKIAIOSFODNN7EXAMPLE"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-KEY]" in result

    # --- Private Keys ---
    def test_redacts_private_key(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-PRIVATE-KEY]" in result

    # --- Connection Strings ---
    def test_redacts_postgres_url(self):
        text = "db: postgres://user:pass@host:5432/db"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-CONNECTION-STRING]" in result

    def test_redacts_mongodb_url(self):
        text = "db: mongodb://user:pass@host:27017/db"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-CONNECTION-STRING]" in result

    # --- Internal URLs ---
    def test_redacts_internal_url(self):
        text = "Deploy to https://app.internal.corp.com"
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-URL]" in result

    # --- Mixed Content ---
    def test_mixed_pii_in_paragraph(self):
        text = (
            "Alice (alice@example.com, 555-123-4567) deployed to "
            "192.168.1.50 using key sk-ant-api03-secret123"
        )
        result = self.guardrail.redact_text(text)
        assert "[REDACTED-EMAIL]" in result
        assert "[REDACTED-PHONE]" in result
        assert "[REDACTED-IP]" in result
        assert "[REDACTED-KEY]" in result
        assert "alice@example.com" not in result

    def test_no_pii_passes_unchanged(self):
        text = "Fixed login timeout bug in Safari. PR #42 merged."
        result = self.guardrail.redact_text(text)
        assert result == text


class TestPIIGuardrailInterface:
    def setup_method(self):
        self.guardrail = PIIRedactionGuardrail()

    def test_check_input_redacts_body(self):
        data = {"title": "Bug report", "body": "Contact alice@example.com"}
        result = self.guardrail.check_input(data, skill="triage-issue")
        assert "alice@example.com" not in result["body"]
        assert "[REDACTED-EMAIL]" in result["body"]

    def test_check_output_redacts_reasoning(self):
        data = {
            "status": "ok",
            "severity": "high",
            "priority": "p0",
            "labels": ["bug"],
            "recommended_owner": "team",
            "confidence": "high",
            "uncertainty_flags": [],
            "citations": [{"claim": "x", "source": "y"}],
            "reasoning": "User alice@example.com reported this.",
        }
        result = self.guardrail.check_output(data, skill="triage-issue")
        assert "alice@example.com" not in result["reasoning"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python -m pytest tests/unit/test_pii_redaction.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'guardrails.pii_redaction'`

- [ ] **Step 3: Implement PII redaction guardrail**

Create `guardrails/pii_redaction.py`:

```python
"""PII redaction guardrail with 12+ pattern categories."""

import json
import re

from guardrails.base import Guardrail


# Compiled regex patterns for each PII category
PII_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # (tag, pattern, description)
    (
        "[REDACTED-EMAIL]",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "Email addresses",
    ),
    (
        "[REDACTED-SSN]",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "Social Security Numbers",
    ),
    (
        "[REDACTED-PHONE]",
        re.compile(
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "Phone numbers",
    ),
    (
        "[REDACTED-CC]",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "Credit card numbers",
    ),
    (
        "[REDACTED-IP]",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        "IPv4 addresses",
    ),
    (
        "[REDACTED-KEY]",
        re.compile(
            r"(?:sk-ant-[\w-]+|ghp_[\w]+|github_pat_[\w]+|xoxb-[\w-]+|xoxp-[\w-]+|xoxs-[\w-]+|AKIA[0-9A-Z]{16})"
        ),
        "API keys and tokens",
    ),
    (
        "[REDACTED-PRIVATE-KEY]",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?(?:PRIVATE KEY|CERTIFICATE)-----[\s\S]*?(?:-----END|$)"),
        "Private keys and certificates",
    ),
    (
        "[REDACTED-CONNECTION-STRING]",
        re.compile(
            r"(?:postgres(?:ql)?|mysql|mongodb|redis|amqp)://[^\s]+"
        ),
        "Database connection strings",
    ),
    (
        "[REDACTED-URL]",
        re.compile(
            r"https?://[^\s]*\.(?:internal|corp|local|lan)[^\s]*"
        ),
        "Internal URLs",
    ),
]


class PIIRedactionGuardrail(Guardrail):
    """Redacts PII from text using regex patterns."""

    name = "pii_redaction"

    def redact_text(self, text: str) -> str:
        """Apply all PII regex patterns to a string."""
        result = text
        for tag, pattern, _desc in PII_PATTERNS:
            result = pattern.sub(tag, result)
        return result

    def _redact_value(self, value: object) -> object:
        """Recursively redact PII from a value (str, list, or dict)."""
        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        return value

    def check_input(self, data: dict, skill: str = "") -> dict:
        """Redact PII from input data before sending to LLM."""
        return self._redact_value(data)

    def check_output(self, data: dict, skill: str = "") -> dict:
        """Redact any PII that leaked into output."""
        return self._redact_value(data)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python -m pytest tests/unit/test_pii_redaction.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Run linting**

```bash
ruff check guardrails/pii_redaction.py tests/unit/test_pii_redaction.py && ruff format --check guardrails/pii_redaction.py tests/unit/test_pii_redaction.py
```

- [ ] **Step 6: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/pii_redaction.py release-radar/tests/unit/test_pii_redaction.py
git commit -m "feat: PII redaction guardrail with 12+ pattern categories"
```

---

## Task 4: Uncertainty Guardrail

**Files:**
- Create: `guardrails/uncertainty.py`
- Create: `tests/unit/test_uncertainty.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_uncertainty.py`:

```python
"""Tests for uncertainty guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.uncertainty import UncertaintyGuardrail


class TestUncertaintyGuardrail:
    def setup_method(self):
        self.guardrail = UncertaintyGuardrail()

    def test_high_confidence_no_hedging_passes(self):
        data = {
            "status": "ok",
            "confidence": "high",
            "uncertainty_flags": [],
            "reasoning": "Clear evidence of a critical login bug.",
        }
        result = self.guardrail.check_output(data, skill="triage-issue")
        assert result == data

    def test_high_confidence_with_hedging_flagged(self):
        data = {
            "status": "ok",
            "confidence": "high",
            "uncertainty_flags": [],
            "reasoning": "This might be a critical bug, possibly affecting login.",
        }
        with pytest.raises(GuardrailError, match="hedging"):
            self.guardrail.check_output(data, skill="triage-issue")

    def test_low_confidence_empty_flags_flagged(self):
        data = {
            "status": "ok",
            "confidence": "low",
            "uncertainty_flags": [],
            "reasoning": "Not enough data.",
        }
        with pytest.raises(GuardrailError, match="uncertainty_flags"):
            self.guardrail.check_output(data, skill="triage-issue")

    def test_medium_confidence_with_flags_passes(self):
        data = {
            "status": "ok",
            "confidence": "medium",
            "uncertainty_flags": ["limited reproduction data"],
            "reasoning": "Some evidence suggests a medium-severity issue.",
        }
        result = self.guardrail.check_output(data, skill="triage-issue")
        assert result == data

    def test_invalid_confidence_value_raises(self):
        data = {
            "status": "ok",
            "confidence": "very_high",
            "uncertainty_flags": [],
            "reasoning": "test",
        }
        with pytest.raises(GuardrailError, match="confidence"):
            self.guardrail.check_output(data, skill="triage-issue")

    def test_missing_confidence_field_raises(self):
        data = {"status": "ok", "reasoning": "test"}
        with pytest.raises(GuardrailError, match="confidence"):
            self.guardrail.check_output(data, skill="triage-issue")

    def test_insufficient_context_skipped(self):
        data = {
            "status": "insufficient_context",
            "missing": ["body"],
            "suggestion": "Provide more details.",
        }
        result = self.guardrail.check_output(data, skill="triage-issue")
        assert result == data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_uncertainty.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement uncertainty guardrail**

Create `guardrails/uncertainty.py`:

```python
"""Uncertainty statements guardrail."""

import re

from guardrails.base import Guardrail, GuardrailError

HEDGING_WORDS = re.compile(
    r"\b(?:might|possibly|perhaps|unclear|uncertain|maybe|could be|not sure|"
    r"hard to say|difficult to determine|cannot confirm)\b",
    re.IGNORECASE,
)

VALID_CONFIDENCE = {"high", "medium", "low"}


class UncertaintyGuardrail(Guardrail):
    """Validates confidence field consistency with output content."""

    name = "uncertainty"

    def check_output(self, data: dict, skill: str = "") -> dict:
        if data.get("status") == "insufficient_context":
            return data

        confidence = data.get("confidence")
        if confidence is None:
            raise GuardrailError(
                guardrail_name=self.name,
                message="Missing 'confidence' field in output.",
            )

        if confidence not in VALID_CONFIDENCE:
            raise GuardrailError(
                guardrail_name=self.name,
                message=f"Invalid confidence value '{confidence}'. Must be one of: {VALID_CONFIDENCE}",
            )

        # Check for hedging language when confidence is high
        text_fields = [
            data.get("reasoning", ""),
            data.get("summary", ""),
            str(data.get("sections", "")),
            data.get("body", ""),
        ]
        combined_text = " ".join(text_fields)

        if confidence == "high" and HEDGING_WORDS.search(combined_text):
            raise GuardrailError(
                guardrail_name=self.name,
                message=(
                    "Confidence is 'high' but output contains hedging language. "
                    "Lower confidence or remove hedging."
                ),
            )

        # Non-high confidence should have uncertainty flags
        uncertainty_flags = data.get("uncertainty_flags")
        if confidence != "high" and isinstance(uncertainty_flags, list) and len(uncertainty_flags) == 0:
            raise GuardrailError(
                guardrail_name=self.name,
                message=(
                    f"Confidence is '{confidence}' but uncertainty_flags is empty. "
                    "Add flags explaining the uncertainty."
                ),
            )

        return data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_uncertainty.py -v
```

Expected: all 7 tests PASS

- [ ] **Step 5: Lint and commit**

```bash
ruff check guardrails/uncertainty.py tests/unit/test_uncertainty.py && ruff format --check guardrails/uncertainty.py tests/unit/test_uncertainty.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/uncertainty.py release-radar/tests/unit/test_uncertainty.py
git commit -m "feat: uncertainty guardrail with hedging detection"
```

---

## Task 5: Citation Guardrail

**Files:**
- Create: `guardrails/citation.py`
- Create: `tests/unit/test_citation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_citation.py`:

```python
"""Tests for citation guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.citation import CitationGuardrail


class TestCitationGuardrail:
    def setup_method(self):
        self.guardrail = CitationGuardrail()

    def test_valid_citations_pass(self):
        input_data = {
            "title": "Login bug",
            "body": "500 error on Safari",
            "comments": [],
        }
        output_data = {
            "status": "ok",
            "confidence": "high",
            "citations": [
                {"claim": "500 error on Safari", "source": "issue body: '500 error on Safari'"}
            ],
        }
        result = self.guardrail.check_output(
            output_data, skill="triage-issue", input_data=input_data
        )
        assert result == output_data

    def test_empty_citations_fails(self):
        output_data = {
            "status": "ok",
            "confidence": "high",
            "citations": [],
        }
        with pytest.raises(GuardrailError, match="citations"):
            self.guardrail.check_output(output_data, skill="triage-issue")

    def test_missing_citations_field_fails(self):
        output_data = {"status": "ok", "confidence": "high"}
        with pytest.raises(GuardrailError, match="citations"):
            self.guardrail.check_output(output_data, skill="triage-issue")

    def test_citation_missing_claim_fails(self):
        output_data = {
            "status": "ok",
            "citations": [{"source": "issue body"}],
        }
        with pytest.raises(GuardrailError, match="claim"):
            self.guardrail.check_output(output_data, skill="triage-issue")

    def test_citation_missing_source_fails(self):
        output_data = {
            "status": "ok",
            "citations": [{"claim": "something"}],
        }
        with pytest.raises(GuardrailError, match="source"):
            self.guardrail.check_output(output_data, skill="triage-issue")

    def test_insufficient_context_skipped(self):
        data = {
            "status": "insufficient_context",
            "missing": ["body"],
            "suggestion": "Provide details.",
        }
        result = self.guardrail.check_output(data, skill="triage-issue")
        assert result == data

    def test_commit_sha_citation_valid(self):
        input_data = {
            "commits": [{"sha": "abc1234", "message": "fix login"}],
        }
        output_data = {
            "status": "ok",
            "citations": [
                {"claim": "login fixed", "source": "commit abc1234: 'fix login'"}
            ],
        }
        result = self.guardrail.check_output(
            output_data, skill="digest-commits", input_data=input_data
        )
        assert result == output_data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_citation.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement citation guardrail**

Create `guardrails/citation.py`:

```python
"""Citation to source guardrail."""

from guardrails.base import Guardrail, GuardrailError


class CitationGuardrail(Guardrail):
    """Validates that output contains citations referencing input data."""

    name = "citation"

    def check_output(
        self, data: dict, skill: str = "", input_data: dict | None = None
    ) -> dict:
        if data.get("status") == "insufficient_context":
            return data

        citations = data.get("citations")

        if citations is None:
            raise GuardrailError(
                guardrail_name=self.name,
                message="Missing 'citations' field in output.",
            )

        if not isinstance(citations, list) or len(citations) == 0:
            raise GuardrailError(
                guardrail_name=self.name,
                message="Output must contain at least one citation.",
            )

        for i, citation in enumerate(citations):
            if not isinstance(citation, dict):
                raise GuardrailError(
                    guardrail_name=self.name,
                    message=f"Citation {i} is not an object.",
                )
            if "claim" not in citation:
                raise GuardrailError(
                    guardrail_name=self.name,
                    message=f"Citation {i} missing 'claim' field.",
                )
            if "source" not in citation:
                raise GuardrailError(
                    guardrail_name=self.name,
                    message=f"Citation {i} missing 'source' field.",
                )

        return data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_citation.py -v
```

Expected: all 7 tests PASS

- [ ] **Step 5: Lint and commit**

```bash
ruff check guardrails/citation.py tests/unit/test_citation.py && ruff format --check guardrails/citation.py tests/unit/test_citation.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/citation.py release-radar/tests/unit/test_citation.py
git commit -m "feat: citation guardrail with claim/source validation"
```

---

## Task 6: Insufficient Context Guardrail

**Files:**
- Create: `guardrails/insufficient_context.py`
- Create: `tests/unit/test_insufficient_context.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_insufficient_context.py`:

```python
"""Tests for insufficient context guardrail."""

import pytest

from guardrails.base import GuardrailError
from guardrails.insufficient_context import InsufficientContextGuardrail


class TestInsufficientContextGuardrail:
    def setup_method(self):
        self.guardrail = InsufficientContextGuardrail()

    # --- triage-issue ---
    def test_issue_with_title_only_triggers_fallback(self):
        data = {"title": "Bug"}
        with pytest.raises(GuardrailError) as exc_info:
            self.guardrail.check_input(data, skill="triage-issue")
        assert exc_info.value.details["status"] == "insufficient_context"
        assert "body" in exc_info.value.details["missing"]

    def test_issue_with_title_and_body_passes(self):
        data = {"title": "Bug", "body": "Login fails on Safari with 500 error."}
        result = self.guardrail.check_input(data, skill="triage-issue")
        assert result == data

    # --- summarize-pr ---
    def test_pr_with_no_diff_triggers_fallback(self):
        data = {"title": "Fix auth", "description": "Updated auth flow."}
        with pytest.raises(GuardrailError) as exc_info:
            self.guardrail.check_input(data, skill="summarize-pr")
        assert "diff_snippets" in exc_info.value.details["missing"]

    def test_pr_with_all_fields_passes(self):
        data = {
            "title": "Fix auth",
            "description": "Updated auth flow.",
            "diff_snippets": ["- old\n+ new"],
        }
        result = self.guardrail.check_input(data, skill="summarize-pr")
        assert result == data

    # --- digest-commits ---
    def test_empty_commits_triggers_fallback(self):
        data = {"commits": [], "date_range": {"start": "2026-04-01", "end": "2026-04-07"}}
        with pytest.raises(GuardrailError) as exc_info:
            self.guardrail.check_input(data, skill="digest-commits")
        assert "commits" in exc_info.value.details["missing"]

    def test_commits_with_data_passes(self):
        data = {
            "commits": [{"sha": "abc", "message": "fix", "author": "alice", "date": "2026-04-07"}],
            "date_range": {"start": "2026-04-01", "end": "2026-04-07"},
        }
        result = self.guardrail.check_input(data, skill="digest-commits")
        assert result == data

    # --- draft-email ---
    def test_email_missing_digest_triggers_fallback(self):
        data = {"pr_summaries": []}
        with pytest.raises(GuardrailError) as exc_info:
            self.guardrail.check_input(data, skill="draft-email")
        assert "digest" in exc_info.value.details["missing"]

    # --- unknown skill passes through ---
    def test_unknown_skill_passes(self):
        data = {"anything": "goes"}
        result = self.guardrail.check_input(data, skill="unknown-skill")
        assert result == data

    def test_missing_field_lists_exactly_whats_absent(self):
        data = {"title": "Bug"}  # missing body
        with pytest.raises(GuardrailError) as exc_info:
            self.guardrail.check_input(data, skill="triage-issue")
        missing = exc_info.value.details["missing"]
        assert isinstance(missing, list)
        assert "body" in missing
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_insufficient_context.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement insufficient context guardrail**

Create `guardrails/insufficient_context.py`:

```python
"""Insufficient context fallback guardrail."""

from guardrails.base import Guardrail, GuardrailError

# Per-skill minimum input requirements
# Each entry: (field_name, check_function)
# check_function takes the field value and returns True if sufficient
SKILL_REQUIREMENTS: dict[str, list[tuple[str, callable]]] = {
    "triage-issue": [
        ("title", lambda v: isinstance(v, str) and len(v.strip()) > 0),
        ("body", lambda v: isinstance(v, str) and len(v.strip()) > 0),
    ],
    "summarize-pr": [
        ("title", lambda v: isinstance(v, str) and len(v.strip()) > 0),
        ("diff_snippets", lambda v: isinstance(v, list) and len(v) > 0),
    ],
    "digest-commits": [
        ("commits", lambda v: isinstance(v, list) and len(v) > 0),
    ],
    "draft-email": [
        ("digest", lambda v: isinstance(v, dict) and len(v) > 0),
    ],
}


class InsufficientContextGuardrail(Guardrail):
    """Validates input has enough data before calling LLM."""

    name = "insufficient_context"

    def check_input(self, data: dict, skill: str = "") -> dict:
        requirements = SKILL_REQUIREMENTS.get(skill)
        if not requirements:
            return data

        missing = []
        for field_name, check_fn in requirements:
            value = data.get(field_name)
            if value is None or not check_fn(value):
                missing.append(field_name)

        if missing:
            suggestion = f"Please provide: {', '.join(missing)}"
            raise GuardrailError(
                guardrail_name=self.name,
                message=f"Insufficient context for '{skill}'. Missing: {missing}",
                details={
                    "status": "insufficient_context",
                    "missing": missing,
                    "suggestion": suggestion,
                },
            )

        return data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_insufficient_context.py -v
```

Expected: all 9 tests PASS

- [ ] **Step 5: Lint and commit**

```bash
ruff check guardrails/insufficient_context.py tests/unit/test_insufficient_context.py && ruff format --check guardrails/insufficient_context.py tests/unit/test_insufficient_context.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/insufficient_context.py release-radar/tests/unit/test_insufficient_context.py
git commit -m "feat: insufficient context guardrail with per-skill requirements"
```

---

## Task 7: Guardrail Chain + Shared Fixtures

**Files:**
- Create: `guardrails/chain.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/test_guardrail_chain.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/conftest.py`:

```python
"""Shared test fixtures for Release Radar."""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def mock_issues():
    with open(DATA_DIR / "mock" / "issues.json") as f:
        return json.load(f)


@pytest.fixture
def mock_pull_requests():
    with open(DATA_DIR / "mock" / "pull_requests.json") as f:
        return json.load(f)


@pytest.fixture
def mock_commits():
    with open(DATA_DIR / "mock" / "commits.json") as f:
        return json.load(f)


@pytest.fixture
def valid_triage_input():
    return {
        "title": "Login fails on Safari",
        "body": "Users report 500 errors when logging in on Safari 17.",
        "comments": ["I can reproduce on macOS Sonoma."],
        "labels_existing": ["bug", "frontend", "backend"],
    }


@pytest.fixture
def valid_triage_output():
    return {
        "status": "ok",
        "severity": "high",
        "priority": "p0",
        "labels": ["bug", "frontend"],
        "recommended_owner": "frontend-team",
        "confidence": "high",
        "uncertainty_flags": [],
        "citations": [
            {"claim": "500 errors on Safari", "source": "issue body: 'Users report 500 errors'"}
        ],
        "reasoning": "Multiple users confirm 500 errors on Safari 17.",
    }


@pytest.fixture
def sparse_triage_input():
    return {"title": "Bug"}
```

Create `tests/unit/test_guardrail_chain.py`:

```python
"""Tests for guardrail chain execution."""

import pytest

from guardrails.base import GuardrailError
from guardrails.chain import GuardrailChain
from guardrails.citation import CitationGuardrail
from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail


class TestGuardrailChain:
    def setup_method(self):
        self.chain = GuardrailChain(
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

    def test_pre_guardrails_execute_in_order(self, valid_triage_input):
        # Add PII to input — insufficient_context runs first (passes), then PII redaction
        valid_triage_input["body"] = "alice@example.com reports 500 errors"
        result = self.chain.run_pre(valid_triage_input, skill="triage-issue")
        assert "alice@example.com" not in result["body"]
        assert "[REDACTED-EMAIL]" in result["body"]

    def test_pre_guardrail_short_circuits_on_failure(self, sparse_triage_input):
        with pytest.raises(GuardrailError, match="insufficient_context"):
            self.chain.run_pre(sparse_triage_input, skill="triage-issue")

    def test_post_guardrails_execute_in_order(self, valid_triage_output):
        result = self.chain.run_post(
            valid_triage_output, skill="triage-issue"
        )
        assert result["status"] == "ok"

    def test_post_guardrail_fails_on_invalid_schema(self):
        bad_output = {"status": "ok", "severity": "high"}  # missing fields
        with pytest.raises(GuardrailError, match="schema_validation"):
            self.chain.run_post(bad_output, skill="triage-issue")

    def test_post_guardrail_fails_on_empty_citations(self, valid_triage_output):
        valid_triage_output["citations"] = []
        with pytest.raises(GuardrailError, match="citation"):
            self.chain.run_post(valid_triage_output, skill="triage-issue")

    def test_post_guardrail_redacts_pii_in_output(self, valid_triage_output):
        valid_triage_output["reasoning"] = "User alice@example.com confirmed the bug."
        result = self.chain.run_post(valid_triage_output, skill="triage-issue")
        assert "alice@example.com" not in result["reasoning"]
        assert "[REDACTED-EMAIL]" in result["reasoning"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_guardrail_chain.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'guardrails.chain'`

- [ ] **Step 3: Implement guardrail chain**

Create `guardrails/chain.py`:

```python
"""Guardrail chain for ordered pre/post processing."""

from guardrails.base import Guardrail, GuardrailError


class GuardrailChain:
    """Runs guardrails in sequence. Short-circuits on first failure."""

    def __init__(
        self,
        pre_guardrails: list[Guardrail] | None = None,
        post_guardrails: list[Guardrail] | None = None,
    ):
        self.pre_guardrails = pre_guardrails or []
        self.post_guardrails = post_guardrails or []

    def run_pre(self, data: dict, skill: str = "") -> dict:
        """Run pre-processing guardrails in order. Short-circuits on failure."""
        result = data
        for guardrail in self.pre_guardrails:
            result = guardrail.check_input(result, skill=skill)
        return result

    def run_post(
        self, data: dict, skill: str = "", input_data: dict | None = None
    ) -> dict:
        """Run post-processing guardrails in order. Short-circuits on failure."""
        result = data
        for guardrail in self.post_guardrails:
            if hasattr(guardrail.check_output, "__code__") and "input_data" in guardrail.check_output.__code__.co_varnames:
                result = guardrail.check_output(result, skill=skill, input_data=input_data)
            else:
                result = guardrail.check_output(result, skill=skill)
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_guardrail_chain.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 5: Run full unit test suite**

```bash
python -m pytest tests/unit/ -v
```

Expected: all tests across all guardrail modules PASS

- [ ] **Step 6: Lint and commit**

```bash
ruff check guardrails/ tests/ && ruff format --check guardrails/ tests/
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/chain.py release-radar/tests/conftest.py release-radar/tests/unit/test_guardrail_chain.py
git commit -m "feat: guardrail chain with pre/post ordering and short-circuit"
```

---

## Task 8: Mock Data

**Files:**
- Create: `data/mock/issues.json`
- Create: `data/mock/pull_requests.json`
- Create: `data/mock/commits.json`
- Create: `tests/unit/test_gh_adapter.py` (mock loading tests only)

- [ ] **Step 1: Create `data/mock/issues.json`**

Create 20 mock GitHub issues. Include:
- 5 high-severity bugs with full body + comments
- 5 medium-severity feature requests
- 4 low-severity documentation/chore issues
- 3 sparse issues (title only, no body) for insufficient-context testing
- 2 issues with embedded PII: one with `alice@company.internal` in body, one with `ghp_secrettoken123` in a code block
- 1 issue with hedging language in body ("might be related to...")

Each issue must follow this schema:

```json
{
  "id": 1,
  "title": "string",
  "body": "string or null",
  "comments": ["string"],
  "labels_existing": ["bug", "feature", "docs", "frontend", "backend", "urgent", "low-priority"],
  "author": "string",
  "created_at": "2026-04-XX"
}
```

Generate all 20 issues with realistic content about a fictional web application (user auth, payments, dashboard, API, notifications). The issues should feel like they come from a real engineering team.

- [ ] **Step 2: Create `data/mock/pull_requests.json`**

Create 20 mock PRs. Include:
- 6 feature PRs (large, with multiple files changed)
- 6 bug fix PRs (small, focused)
- 4 refactoring PRs (medium)
- 2 dependency update PRs
- 2 PRs with PII in diffs (hardcoded email in code, API key in config)

Each PR must follow this schema:

```json
{
  "id": 101,
  "title": "string",
  "description": "string",
  "diff_snippets": ["string"],
  "files_changed": ["path/to/file.py"],
  "additions": 100,
  "deletions": 50,
  "author": "string",
  "merged_at": "2026-04-XX",
  "state": "merged"
}
```

- [ ] **Step 3: Create `data/mock/commits.json`**

Create 60 mock commits spanning April 5-11, 2026. Include:
- 5-8 different authors
- Conventional commit format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- Distribution: ~20 fixes, ~15 features, ~10 chores, ~8 docs, ~5 refactors, ~2 tests
- Each commit references realistic file paths

Each commit must follow this schema:

```json
{
  "sha": "7-char hex string",
  "message": "type: description",
  "author": "string",
  "date": "2026-04-XX",
  "files": ["path/to/file.py"]
}
```

- [ ] **Step 4: Write test for mock data loading**

Create `tests/unit/test_gh_adapter.py` (mock-only tests for now):

```python
"""Tests for GitHub adapter — mock data loading."""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class TestMockDataLoading:
    def test_issues_json_loads(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        assert isinstance(issues, list)
        assert len(issues) >= 15

    def test_issues_have_required_fields(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        for issue in issues:
            assert "id" in issue
            assert "title" in issue
            # body can be null for sparse issues

    def test_pull_requests_json_loads(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            prs = json.load(f)
        assert isinstance(prs, list)
        assert len(prs) >= 15

    def test_pull_requests_have_required_fields(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            prs = json.load(f)
        for pr in prs:
            assert "id" in pr
            assert "title" in pr
            assert "diff_snippets" in pr

    def test_commits_json_loads(self):
        with open(DATA_DIR / "mock" / "commits.json") as f:
            commits = json.load(f)
        assert isinstance(commits, list)
        assert len(commits) >= 50

    def test_commits_have_required_fields(self):
        with open(DATA_DIR / "mock" / "commits.json") as f:
            commits = json.load(f)
        for commit in commits:
            assert "sha" in commit
            assert "message" in commit
            assert "author" in commit
            assert "date" in commit

    def test_issues_include_sparse_entries(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            issues = json.load(f)
        sparse = [i for i in issues if not i.get("body") or i["body"].strip() == ""]
        assert len(sparse) >= 3, "Need at least 3 sparse issues for insufficient-context testing"

    def test_issues_include_pii(self):
        with open(DATA_DIR / "mock" / "issues.json") as f:
            raw = f.read()
        assert "@" in raw, "At least one issue should contain an email for PII testing"

    def test_prs_include_pii_in_diffs(self):
        with open(DATA_DIR / "mock" / "pull_requests.json") as f:
            raw = f.read()
        has_pii = "@" in raw or "ghp_" in raw or "sk-" in raw
        assert has_pii, "At least one PR should contain PII in diffs"
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_gh_adapter.py -v
```

Expected: all 9 tests PASS

- [ ] **Step 6: Lint and commit**

```bash
ruff check tests/unit/test_gh_adapter.py && ruff format --check tests/unit/test_gh_adapter.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/data/mock/ release-radar/tests/unit/test_gh_adapter.py
git commit -m "feat: mock data (20 issues, 20 PRs, 60 commits) with PII and sparse entries"
```

---

## Task 9: GitHub Adapter

**Files:**
- Create: `scripts/gh_adapter.py`
- Modify: `tests/unit/test_gh_adapter.py` (add adapter class tests)

- [ ] **Step 1: Add failing tests for GitHubAdapter class**

Append to `tests/unit/test_gh_adapter.py`:

```python
from scripts.gh_adapter import GitHubAdapter


class TestGitHubAdapterMock:
    def setup_method(self):
        self.adapter = GitHubAdapter(mock=True)

    def test_get_issues_returns_list(self):
        issues = self.adapter.get_issues(repo="test/repo")
        assert isinstance(issues, list)
        assert len(issues) >= 15

    def test_get_pull_requests_returns_list(self):
        prs = self.adapter.get_pull_requests(repo="test/repo")
        assert isinstance(prs, list)
        assert len(prs) >= 15

    def test_get_commits_returns_list(self):
        commits = self.adapter.get_commits(repo="test/repo")
        assert isinstance(commits, list)
        assert len(commits) >= 50

    def test_get_commits_date_filter(self):
        commits = self.adapter.get_commits(repo="test/repo", since="2026-04-08")
        assert all(c["date"] >= "2026-04-08" for c in commits)

    def test_missing_mock_file_raises(self):
        adapter = GitHubAdapter(mock=True)
        # Temporarily break the path
        adapter.mock_dir = adapter.mock_dir / "nonexistent"
        with pytest.raises(FileNotFoundError):
            adapter.get_issues(repo="test/repo")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_gh_adapter.py::TestGitHubAdapterMock -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.gh_adapter'`

- [ ] **Step 3: Implement GitHub adapter**

Create `scripts/__init__.py` (empty) and `scripts/gh_adapter.py`:

```python
"""GitHub data adapter — unified interface for mock and live data."""

import json
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data"


class GitHubAdapter:
    """Loads GitHub data from mock files or the GitHub REST API."""

    def __init__(self, token: str | None = None, mock: bool = False):
        self.token = token
        self.mock = mock
        self.mock_dir = DATA_DIR / "mock"
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _load_mock(self, filename: str) -> list[dict]:
        path = self.mock_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Mock data file not found: {path}")
        with open(path) as f:
            return json.load(f)

    def get_issues(self, repo: str, since: str | None = None) -> list[dict]:
        if self.mock:
            issues = self._load_mock("issues.json")
            if since:
                issues = [i for i in issues if i.get("created_at", "") >= since]
            return issues

        url = f"{self.base_url}/repos/{repo}/issues"
        params = {"state": "open", "per_page": 100}
        if since:
            params["since"] = since
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_issues(resp.json())

    def get_pull_requests(
        self, repo: str, state: str = "closed", since: str | None = None
    ) -> list[dict]:
        if self.mock:
            prs = self._load_mock("pull_requests.json")
            if since:
                prs = [p for p in prs if p.get("merged_at", "") >= since]
            return prs

        url = f"{self.base_url}/repos/{repo}/pulls"
        params = {"state": state, "per_page": 100, "sort": "updated", "direction": "desc"}
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_prs(resp.json())

    def get_commits(self, repo: str, since: str | None = None) -> list[dict]:
        if self.mock:
            commits = self._load_mock("commits.json")
            if since:
                commits = [c for c in commits if c.get("date", "") >= since]
            return commits

        url = f"{self.base_url}/repos/{repo}/commits"
        params = {"per_page": 100}
        if since:
            params["since"] = since
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return self._normalize_commits(resp.json())

    def _normalize_issues(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": item["number"],
                "title": item["title"],
                "body": item.get("body"),
                "comments": [],
                "labels_existing": [l["name"] for l in item.get("labels", [])],
                "author": item["user"]["login"],
                "created_at": item["created_at"][:10],
            }
            for item in raw
            if "pull_request" not in item
        ]

    def _normalize_prs(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": item["number"],
                "title": item["title"],
                "description": item.get("body", ""),
                "diff_snippets": [],
                "files_changed": [],
                "additions": item.get("additions", 0),
                "deletions": item.get("deletions", 0),
                "author": item["user"]["login"],
                "merged_at": (item.get("merged_at") or "")[:10],
                "state": "merged" if item.get("merged_at") else item["state"],
            }
            for item in raw
        ]

    def _normalize_commits(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "sha": item["sha"][:7],
                "message": item["commit"]["message"].split("\n")[0],
                "author": item["commit"]["author"]["name"],
                "date": item["commit"]["author"]["date"][:10],
                "files": [],
            }
            for item in raw
        ]
```

- [ ] **Step 4: Create `scripts/__init__.py`**

Create empty `scripts/__init__.py`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/unit/test_gh_adapter.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Lint and commit**

```bash
ruff check scripts/ tests/unit/test_gh_adapter.py && ruff format --check scripts/ tests/unit/test_gh_adapter.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/scripts/ release-radar/tests/unit/test_gh_adapter.py
git commit -m "feat: GitHub adapter with mock/live data and normalization"
```

---

## Task 10: Claude Code Skills (SKILL.md files)

**Files:**
- Create: `claude_skills/triage-issue/SKILL.md`
- Create: `claude_skills/summarize-pr/SKILL.md`
- Create: `claude_skills/digest-commits/SKILL.md`
- Create: `claude_skills/draft-email/SKILL.md`
- Move: existing `handoff/SKILL.md` → `claude_skills/handoff/SKILL.md`

- [ ] **Step 1: Create `claude_skills/triage-issue/SKILL.md`**

```markdown
---
name: triage-issue
description: Classify a GitHub issue by severity, priority, labels, and recommended owner. Invoke when triaging issues, classifying bugs, or prioritizing a backlog.
---

# Triage Issue

You are a GitHub issue triage assistant. Analyze the provided issue and classify it.

## Input

You will receive a JSON object with:
- `title` (required): Issue title
- `body` (optional): Issue description
- `comments` (optional): Array of comment strings
- `labels_existing` (optional): Available labels to choose from

## Output

Return a JSON object with this exact structure:

```json
{
  "status": "ok",
  "severity": "high|medium|low",
  "priority": "p0|p1|p2|p3",
  "labels": ["selected", "labels"],
  "recommended_owner": "team-name",
  "confidence": "high|medium|low",
  "uncertainty_flags": ["list of things you're unsure about"],
  "citations": [{"claim": "what you concluded", "source": "where in the input you found evidence"}],
  "reasoning": "Brief explanation of your classification"
}
```

## Rules

1. **Every claim must cite its source.** Reference specific text from the issue title, body, or comments.
2. **Set confidence honestly.** If the issue is vague or lacks reproduction steps, use "medium" or "low".
3. **If confidence is not "high", you MUST include at least one uncertainty_flag.**
4. **Never use hedging language ("might", "possibly", "perhaps") when confidence is "high".**
5. **Never include PII** (emails, API keys, tokens, phone numbers) in your output.
6. **If the issue has no body or is too sparse to classify meaningfully**, return:

```json
{
  "status": "insufficient_context",
  "missing": ["body", "reproduction steps"],
  "suggestion": "Please provide a detailed description and steps to reproduce."
}
```

## Severity Guide

- **high**: Data loss, security vulnerability, service outage, blocks users
- **medium**: Degraded experience, workaround exists, affects subset of users
- **low**: Cosmetic, documentation, minor inconvenience

## Priority Guide

- **p0**: Fix immediately (production down, security breach)
- **p1**: Fix this sprint (major user impact)
- **p2**: Fix next sprint (important but not urgent)
- **p3**: Backlog (nice to have)
```

- [ ] **Step 2: Create `claude_skills/summarize-pr/SKILL.md`**

```markdown
---
name: summarize-pr
description: Generate a concise technical summary and risk checklist from a pull request. Invoke when reviewing PRs, creating release notes, or assessing merge risk.
---

# Summarize PR

You are a PR review assistant. Analyze the provided pull request and produce a technical summary with risk assessment.

## Input

You will receive a JSON object with:
- `title` (required): PR title
- `description` (optional): PR description/body
- `diff_snippets` (required): Array of code diff strings
- `files_changed` (optional): Array of file paths
- `additions` (optional): Number of lines added
- `deletions` (optional): Number of lines deleted

## Output

Return a JSON object with this exact structure:

```json
{
  "status": "ok",
  "summary": "2-4 sentence technical summary of what this PR does",
  "risk_checklist": [
    {"risk": "description of risk", "severity": "high|medium|low", "mitigation": "how to mitigate"}
  ],
  "confidence": "high|medium|low",
  "citations": [{"claim": "what you concluded", "source": "where in the diff/description you found evidence"}]
}
```

## Rules

1. **Every claim must cite its source.** Reference specific diff snippets, file names, or description text.
2. **Set confidence honestly.** If diffs are truncated or description is sparse, lower confidence.
3. **Never include PII** (emails, API keys, tokens) in your output. If you see them in diffs, note "PII found in diff" as a risk but do not reproduce the PII.
4. **If the PR lacks diff snippets**, return:

```json
{
  "status": "insufficient_context",
  "missing": ["diff_snippets"],
  "suggestion": "Please provide code diff snippets for analysis."
}
```

## Risk Severity Guide

- **high**: Breaking change, security implication, data migration, API change
- **medium**: New dependency, performance concern, complex logic
- **low**: Cosmetic, test-only, documentation
```

- [ ] **Step 3: Create `claude_skills/digest-commits/SKILL.md`**

```markdown
---
name: digest-commits
description: Organize a list of commits into a structured weekly digest with what_changed, risk_impact, and action_needed sections. Invoke for release notes or stakeholder updates.
---

# Digest Commits

You are an engineering digest writer. Organize the provided commits into a structured summary.

## Input

You will receive a JSON object with:
- `commits` (required): Array of commit objects, each with `sha`, `message`, `author`, `date`
- `date_range` (optional): Object with `start` and `end` date strings

## Output

Return a JSON object with this exact structure:

```json
{
  "status": "ok",
  "sections": {
    "what_changed": "Summary of changes grouped by category (features, fixes, chores)",
    "risk_impact": "Assessment of risk and user impact from these changes",
    "action_needed": "Specific actions for QA, stakeholders, or ops teams"
  },
  "confidence": "high|medium|low",
  "citations": [{"claim": "what you summarized", "source": "commit SHA: 'commit message'"}]
}
```

## Rules

1. **Cite specific commit SHAs.** Every claim in your summary must reference at least one commit.
2. **Group by type:** features, fixes, chores/refactors, docs. Use conventional commit prefixes when available.
3. **Set confidence honestly.** If commit messages are vague ("fix stuff"), lower confidence.
4. **Never include PII** in your output.
5. **If commits array is empty**, return:

```json
{
  "status": "insufficient_context",
  "missing": ["commits"],
  "suggestion": "No commits found in the specified date range."
}
```
```

- [ ] **Step 4: Create `claude_skills/draft-email/SKILL.md`**

```markdown
---
name: draft-email
description: Draft a polished stakeholder update email from commit digests and PR summaries. Invoke for weekly engineering updates or release communications.
---

# Draft Email

You are a technical communication specialist. Draft a stakeholder-ready email from engineering data.

## Input

You will receive a JSON object with:
- `digest` (required): Output from the digest-commits skill
- `pr_summaries` (optional): Array of outputs from summarize-pr skill
- `recipient_context` (optional): Who the email is for (e.g., "engineering leadership")
- `week` (optional): Date range string (e.g., "2026-04-05 to 2026-04-11")

## Output

Return a JSON object with this exact structure:

```json
{
  "status": "ok",
  "subject": "Engineering Update: Week of [date range]",
  "body": "Full email body in plain text with sections",
  "pii_redacted": true,
  "confidence": "high|medium|low",
  "citations": [{"claim": "what you referenced", "source": "which digest/PR summary data point"}]
}
```

## Rules

1. **Always set `pii_redacted` to true.** You must never include PII in the email body.
2. **Structure the email** with clear sections: What Shipped, Risk & Impact, Action Items.
3. **Write for the audience.** If recipient_context says "non-technical stakeholders", avoid jargon.
4. **Cite your sources.** Every claim in the email should trace back to digest or PR summary data.
5. **Set confidence honestly.** If the digest input is sparse, note that.
6. **If digest is missing or empty**, return:

```json
{
  "status": "insufficient_context",
  "missing": ["digest"],
  "suggestion": "Please provide a commit digest to generate the email."
}
```
```

- [ ] **Step 5: Move handoff skill**

```bash
cp /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/handoff/SKILL.md /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar/claude_skills/handoff/SKILL.md
```

- [ ] **Step 6: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/claude_skills/
git commit -m "feat: all 5 Claude Code skills (triage, summarize, digest, email, handoff)"
```

---

## Task 11: CLI Orchestrator

**Files:**
- Create: `scripts/release_radar.py`

- [ ] **Step 1: Implement CLI orchestrator**

Create `scripts/release_radar.py`:

```python
"""Release Radar CLI — batch-mode orchestrator."""

import argparse
import json
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from guardrails.chain import GuardrailChain
from guardrails.citation import CitationGuardrail
from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail
from scripts.gh_adapter import GitHubAdapter

load_dotenv()

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
    user_message = f"Process this input and return JSON output:\n\n```json\n{json.dumps(input_data, indent=2)}\n```"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=skill_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract JSON from response
    text = response.content[0].text
    # Try to find JSON in the response
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
    from guardrails.base import GuardrailError

    try:
        checked_input = chain.run_pre(input_data, skill=skill_name)
    except GuardrailError as e:
        return e.details if e.details.get("status") == "insufficient_context" else {"error": str(e)}

    output = call_claude(skill_name, checked_input, client)

    try:
        checked_output = chain.run_post(output, skill=skill_name, input_data=checked_input)
    except GuardrailError as e:
        print(f"Warning: Post-guardrail '{e.guardrail_name}' failed: {e.message}", file=sys.stderr)
        return output  # Return raw output with warning

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
        for pr in prs[:5]:  # Limit to 5 PRs for email
            summary = process_skill("summarize-pr", pr, chain, client)
            pr_summaries.append(summary)

    email_input = {
        "digest": digest,
        "pr_summaries": pr_summaries,
        "recipient_context": "engineering leadership and non-technical stakeholders",
        "week": f"{commits_data.get('date_range', {}).get('start', 'unknown')} to "
        f"{commits_data.get('date_range', {}).get('end', 'unknown')}",
    }
    result = process_skill("draft-email", email_input, chain, client)
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_weekly(args, chain, client):
    adapter = GitHubAdapter(mock=not args.live, token=args.token)
    repo = args.repo or "mock/repo"

    print("=== Release Radar Weekly Report ===", file=sys.stderr)

    # 1. Load data
    issues = adapter.get_issues(repo=repo, since=args.since)
    prs = adapter.get_pull_requests(repo=repo, since=args.since)
    commits_raw = adapter.get_commits(repo=repo, since=args.since)

    print(f"Loaded: {len(issues)} issues, {len(prs)} PRs, {len(commits_raw)} commits", file=sys.stderr)

    # 2. Triage issues
    print("Triaging issues...", file=sys.stderr)
    triage_results = []
    for issue in issues:
        result = process_skill("triage-issue", issue, chain, client)
        triage_results.append({"issue_id": issue.get("id"), "result": result})

    # 3. Summarize PRs
    print("Summarizing PRs...", file=sys.stderr)
    pr_summaries = []
    for pr in prs[:10]:  # Limit for cost
        result = process_skill("summarize-pr", pr, chain, client)
        pr_summaries.append(result)

    # 4. Digest commits
    print("Digesting commits...", file=sys.stderr)
    commits_input = {
        "commits": commits_raw,
        "date_range": {"start": args.since or "unknown", "end": args.until or "unknown"},
    }
    digest = process_skill("digest-commits", commits_input, chain, client)

    # 5. Draft email
    print("Drafting email...", file=sys.stderr)
    email_input = {
        "digest": digest,
        "pr_summaries": pr_summaries,
        "recipient_context": "engineering leadership and non-technical stakeholders",
        "week": f"{args.since or 'past week'} to {args.until or 'now'}",
    }
    email = process_skill("draft-email", email_input, chain, client)

    # 6. Output report
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

    # triage
    p_triage = subparsers.add_parser("triage", help="Triage GitHub issues")
    p_triage.add_argument("--input", required=True, help="Path to issues JSON")

    # summarize
    p_summarize = subparsers.add_parser("summarize", help="Summarize pull requests")
    p_summarize.add_argument("--input", required=True, help="Path to PRs JSON")

    # digest
    p_digest = subparsers.add_parser("digest", help="Digest commits")
    p_digest.add_argument("--input", required=True, help="Path to commits JSON")

    # email
    p_email = subparsers.add_parser("email", help="Draft stakeholder email")
    p_email.add_argument("--input", required=True, help="Path to commits JSON")
    p_email.add_argument("--prs", help="Path to PRs JSON (optional)")

    # weekly
    parser.add_argument("--weekly", action="store_true", help="Run full weekly report")
    parser.add_argument("--repo", help="GitHub repo (owner/name)")
    parser.add_argument("--live", action="store_true", help="Use live GitHub API")
    parser.add_argument("--since", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", help="End date (YYYY-MM-DD)")
    parser.add_argument("--token", help="GitHub token (overrides .env)")

    args = parser.parse_args()
    client = anthropic.Anthropic()
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
```

- [ ] **Step 2: Verify CLI help works**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python scripts/release_radar.py --help
```

Expected: shows help text with subcommands

- [ ] **Step 3: Lint and commit**

```bash
ruff check scripts/release_radar.py && ruff format --check scripts/release_radar.py
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/scripts/release_radar.py
git commit -m "feat: CLI orchestrator with triage/summarize/digest/email/weekly commands"
```

---

## Task 12: Guardrail Hooks

**Files:**
- Create: `guardrails/hooks/pre_tool_guardrail.py`
- Create: `guardrails/hooks/post_tool_guardrail.py`
- Create: `guardrails/hooks/__init__.py`
- Create: `.claude/settings.json`

- [ ] **Step 1: Create hook scripts**

Create `guardrails/hooks/__init__.py` (empty).

Create `guardrails/hooks/pre_tool_guardrail.py`:

```python
#!/usr/bin/env python3
"""Pre-tool guardrail hook for Claude Code.

Reads tool input from stdin, runs pre-processing guardrails,
outputs modified data to stdout.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from guardrails.insufficient_context import InsufficientContextGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.base import GuardrailError


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Map tool names to skill names
    skill_map = {
        "triage-issue": "triage-issue",
        "summarize-pr": "summarize-pr",
        "digest-commits": "digest-commits",
        "draft-email": "draft-email",
    }
    skill = skill_map.get(tool_name, "")
    if not skill:
        return

    guardrails = [InsufficientContextGuardrail(), PIIRedactionGuardrail()]

    try:
        result = tool_input
        for g in guardrails:
            result = g.check_input(result, skill=skill)
        output = {"tool_input": result}
        json.dump(output, sys.stdout)
    except GuardrailError as e:
        error_output = {
            "error": str(e),
            "details": e.details,
        }
        json.dump(error_output, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Create `guardrails/hooks/post_tool_guardrail.py`:

```python
#!/usr/bin/env python3
"""Post-tool guardrail hook for Claude Code.

Reads tool output from stdin, runs post-processing guardrails,
outputs modified data to stdout.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from guardrails.citation import CitationGuardrail
from guardrails.pii_redaction import PIIRedactionGuardrail
from guardrails.schema_validation import SchemaValidationGuardrail
from guardrails.uncertainty import UncertaintyGuardrail
from guardrails.base import GuardrailError


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = data.get("tool_name", "")
    tool_output = data.get("tool_output", {})

    skill_map = {
        "triage-issue": "triage-issue",
        "summarize-pr": "summarize-pr",
        "digest-commits": "digest-commits",
        "draft-email": "draft-email",
    }
    skill = skill_map.get(tool_name, "")
    if not skill:
        return

    guardrails = [
        SchemaValidationGuardrail(),
        CitationGuardrail(),
        UncertaintyGuardrail(),
        PIIRedactionGuardrail(),
    ]

    try:
        result = tool_output
        for g in guardrails:
            result = g.check_output(result, skill=skill)
        output = {"tool_output": result}
        json.dump(output, sys.stdout)
    except GuardrailError as e:
        error_output = {
            "error": str(e),
            "details": e.details,
        }
        json.dump(error_output, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `.claude/settings.json`**

```json
{
  "hooks": {
    "pre_tool_call": [
      {
        "command": "python guardrails/hooks/pre_tool_guardrail.py"
      }
    ],
    "post_tool_call": [
      {
        "command": "python guardrails/hooks/post_tool_guardrail.py"
      }
    ]
  }
}
```

> **Note:** Verify exact hook registration syntax against Claude Code docs at implementation time.

- [ ] **Step 3: Make hook scripts executable**

```bash
chmod +x release-radar/guardrails/hooks/pre_tool_guardrail.py
chmod +x release-radar/guardrails/hooks/post_tool_guardrail.py
```

- [ ] **Step 4: Lint and commit**

```bash
ruff check guardrails/hooks/ && ruff format --check guardrails/hooks/
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/guardrails/hooks/ release-radar/.claude/
git commit -m "feat: guardrail hooks for Claude Code interactive mode"
```

---

## Task 13: Integration Tests

**Files:**
- Create: `tests/integration/test_cli_triage.py`
- Create: `tests/integration/test_cli_summarize.py`
- Create: `tests/integration/test_cli_digest.py`
- Create: `tests/integration/test_cli_email.py`
- Create: `tests/integration/test_cli_weekly.py`
- Create: `tests/integration/test_guardrail_hooks.py`

- [ ] **Step 1: Create integration test for CLI triage**

Create `tests/integration/test_cli_triage.py`:

```python
"""Integration test for CLI triage command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_ISSUES = PROJECT_ROOT / "data" / "mock" / "issues.json"


@pytest.mark.integration
class TestCLITriage:
    def test_triage_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_triage_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_triage_results_have_structure(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "triage", "--input", str(MOCK_ISSUES)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        for item in data:
            assert "issue_id" in item
            assert "result" in item
```

- [ ] **Step 2: Create integration test for CLI summarize**

Create `tests/integration/test_cli_summarize.py`:

```python
"""Integration test for CLI summarize command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_PRS = PROJECT_ROOT / "data" / "mock" / "pull_requests.json"


@pytest.mark.integration
class TestCLISummarize:
    def test_summarize_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "summarize", "--input", str(MOCK_PRS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_summarize_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "summarize", "--input", str(MOCK_PRS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
```

- [ ] **Step 3: Create integration test for CLI digest**

Create `tests/integration/test_cli_digest.py`:

```python
"""Integration test for CLI digest command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_COMMITS = PROJECT_ROOT / "data" / "mock" / "commits.json"


@pytest.mark.integration
class TestCLIDigest:
    def test_digest_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "digest", "--input", str(MOCK_COMMITS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_digest_outputs_valid_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "digest", "--input", str(MOCK_COMMITS)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        if data.get("status") == "ok":
            assert "sections" in data
```

- [ ] **Step 4: Create integration test for CLI email**

Create `tests/integration/test_cli_email.py`:

```python
"""Integration test for CLI email command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"
MOCK_COMMITS = PROJECT_ROOT / "data" / "mock" / "commits.json"
MOCK_PRS = PROJECT_ROOT / "data" / "mock" / "pull_requests.json"


@pytest.mark.integration
class TestCLIEmail:
    def test_email_exits_zero(self):
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "email",
                "--input", str(MOCK_COMMITS),
                "--prs", str(MOCK_PRS),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_email_has_subject_and_body(self):
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "email",
                "--input", str(MOCK_COMMITS),
                "--prs", str(MOCK_PRS),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
        )
        data = json.loads(result.stdout)
        if data.get("status") == "ok":
            assert "subject" in data
            assert "body" in data
```

- [ ] **Step 5: Create integration test for CLI weekly**

Create `tests/integration/test_cli_weekly.py`:

```python
"""Integration test for CLI weekly report command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_radar.py"


@pytest.mark.integration
class TestCLIWeekly:
    def test_weekly_mock_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--weekly"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_weekly_outputs_full_report(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--weekly"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300,
        )
        data = json.loads(result.stdout)
        assert "triage" in data
        assert "pr_summaries" in data
        assert "digest" in data
        assert "email" in data
```

- [ ] **Step 6: Create integration test for guardrail hooks**

Create `tests/integration/test_guardrail_hooks.py`:

```python
"""Integration test for guardrail hook scripts."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
PRE_HOOK = PROJECT_ROOT / "guardrails" / "hooks" / "pre_tool_guardrail.py"
POST_HOOK = PROJECT_ROOT / "guardrails" / "hooks" / "post_tool_guardrail.py"


@pytest.mark.integration
class TestGuardrailHooks:
    def test_pre_hook_redacts_pii(self):
        input_data = {
            "tool_name": "triage-issue",
            "tool_input": {
                "title": "Bug report",
                "body": "Contact alice@example.com for details.",
            },
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "alice@example.com" not in json.dumps(output)

    def test_pre_hook_rejects_insufficient_context(self):
        input_data = {
            "tool_name": "triage-issue",
            "tool_input": {"title": "Bug"},
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert "error" in output

    def test_pre_hook_ignores_unknown_tool(self):
        input_data = {
            "tool_name": "unknown-tool",
            "tool_input": {"data": "test"},
        }
        result = subprocess.run(
            [sys.executable, str(PRE_HOOK)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        assert result.returncode == 0
```

- [ ] **Step 7: Run hook integration tests (these don't need API keys)**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
python -m pytest tests/integration/test_guardrail_hooks.py -v
```

Expected: all 3 tests PASS

- [ ] **Step 8: Lint and commit**

```bash
ruff check tests/integration/ && ruff format --check tests/integration/
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/tests/integration/
git commit -m "feat: integration tests for CLI commands and guardrail hooks"
```

---

## Task 14: Sample I/O Pairs

**Files:**
- Create: `data/samples/sample_1_triage/input.json`
- Create: `data/samples/sample_1_triage/output.json`
- Create: `data/samples/sample_2_insufficient/input.json`
- Create: `data/samples/sample_2_insufficient/output.json`
- Create: `data/samples/sample_3_email/input.json`
- Create: `data/samples/sample_3_email/output.json`

- [ ] **Step 1: Create sample 1 — full triage with guardrails**

Create `data/samples/sample_1_triage/input.json`:

```json
{
  "title": "Login fails on Safari 17 with 500 error",
  "body": "Multiple users (including alice@company.internal) report that login fails on Safari 17. The error is a 500 Internal Server Error. Reproduction steps: 1) Open Safari 17 on macOS Sonoma, 2) Navigate to login page, 3) Enter credentials, 4) Click submit. The server logs show a NullPointerException in AuthService.validate().",
  "comments": [
    "I can reproduce this on Safari 17.2 on macOS 14.1",
    "Same issue on iOS Safari. Might be a WebKit issue.",
    "Priority: this blocks our enterprise customers who mandate Safari."
  ],
  "labels_existing": ["bug", "frontend", "backend", "auth", "urgent", "low-priority"]
}
```

Create `data/samples/sample_1_triage/output.json`:

```json
{
  "status": "ok",
  "severity": "high",
  "priority": "p0",
  "labels": ["bug", "auth", "urgent"],
  "recommended_owner": "backend-team",
  "confidence": "high",
  "uncertainty_flags": [],
  "citations": [
    {"claim": "500 Internal Server Error on Safari 17", "source": "issue body: 'login fails on Safari 17. The error is a 500 Internal Server Error'"},
    {"claim": "NullPointerException in AuthService", "source": "issue body: 'server logs show a NullPointerException in AuthService.validate()'"},
    {"claim": "Blocks enterprise customers", "source": "comment: 'this blocks our enterprise customers who mandate Safari'"}
  ],
  "reasoning": "Critical authentication failure affecting Safari 17 users. Server-side NullPointerException in AuthService.validate() confirms this is a backend issue. Enterprise customers are blocked, warranting p0 priority. PII (email [REDACTED-EMAIL]) was redacted from input."
}
```

- [ ] **Step 2: Create sample 2 — insufficient context fallback**

Create `data/samples/sample_2_insufficient/input.json`:

```json
{
  "title": "Bug"
}
```

Create `data/samples/sample_2_insufficient/output.json`:

```json
{
  "status": "insufficient_context",
  "missing": ["body"],
  "suggestion": "Please provide: body"
}
```

- [ ] **Step 3: Create sample 3 — full email pipeline**

Create `data/samples/sample_3_email/input.json`:

```json
{
  "digest": {
    "status": "ok",
    "sections": {
      "what_changed": "12 commits this week: 4 bug fixes (login timeout, payment rounding, notification delivery, API rate limiting), 5 features (OAuth2 provider, dashboard charts, export CSV, search filters, dark mode), 3 chores (dependency updates, CI config, docs).",
      "risk_impact": "OAuth2 migration is a breaking change for existing session-based auth. Payment rounding fix affects financial calculations. Other changes are low-risk.",
      "action_needed": "QA should verify OAuth2 flow end-to-end before release. Finance team should validate payment calculations against test data."
    },
    "confidence": "high",
    "citations": [
      {"claim": "OAuth2 migration", "source": "commit def5678: 'feat: add OAuth2 provider'"},
      {"claim": "payment rounding fix", "source": "commit abc1234: 'fix: payment rounding error'"}
    ]
  },
  "pr_summaries": [
    {
      "status": "ok",
      "summary": "Migrates authentication from session-based to OAuth2. Adds new OAuth2 provider, updates auth middleware, and includes migration script for existing sessions.",
      "risk_checklist": [
        {"risk": "Breaking change for existing sessions", "severity": "high", "mitigation": "Migration script included"},
        {"risk": "New dependency on oauth-lib v2.1", "severity": "low", "mitigation": "Pinned version"}
      ],
      "confidence": "high",
      "citations": [{"claim": "migration script included", "source": "diff: auth/migrate.py added"}]
    }
  ],
  "recipient_context": "engineering leadership, non-technical stakeholders",
  "week": "2026-04-05 to 2026-04-11"
}
```

Create `data/samples/sample_3_email/output.json`:

```json
{
  "status": "ok",
  "subject": "Engineering Update: Week of April 5-11, 2026",
  "body": "Hi team,\n\nHere's what the engineering team shipped this week.\n\n## What Shipped\n\nWe merged 12 changes this week across bug fixes, new features, and maintenance:\n\n- **Authentication upgrade**: Migrated from session-based auth to OAuth2, providing better security and third-party integration support. A migration script handles existing sessions automatically.\n- **Bug fixes**: Resolved login timeout issues, corrected payment rounding calculations, fixed notification delivery reliability, and improved API rate limiting.\n- **New features**: Added dashboard charts, CSV export, search filters, and dark mode support.\n- **Maintenance**: Updated dependencies, improved CI configuration, and refreshed documentation.\n\n## Risk & Impact\n\n- **High**: The OAuth2 migration is a breaking change. Existing session-based auth will no longer work after deployment. A migration script is included, but QA must verify the full OAuth2 flow before release.\n- **Medium**: Payment rounding fix affects financial calculations. The finance team should validate against test data.\n- **Low**: All other changes are backward-compatible.\n\n## Action Items\n\n1. **QA**: Verify OAuth2 authentication flow end-to-end before release\n2. **Finance**: Validate payment calculations against test data set\n3. **Ops**: Plan deployment window for OAuth2 migration (requires brief downtime for session migration)\n\nReach out if you have questions.\n\nBest,\nRelease Radar",
  "pii_redacted": true,
  "confidence": "high",
  "citations": [
    {"claim": "OAuth2 migration", "source": "digest: commit def5678"},
    {"claim": "payment rounding fix", "source": "digest: commit abc1234"},
    {"claim": "migration script included", "source": "PR summary: diff auth/migrate.py added"}
  ]
}
```

- [ ] **Step 4: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/data/samples/
git commit -m "feat: 3 sample I/O pairs demonstrating triage, insufficient context, and email pipeline"
```

---

## Task 15: HW2 Documentation — CLAUDE.md

**Files:**
- Create: `CLAUDE.md` (in release-radar root)

- [ ] **Step 1: Write CLAUDE.md**

Create `CLAUDE.md` in `release-radar/`:

```markdown
# CLAUDE.md — Release Radar

## Project Overview

Release Radar is a lightweight internal tool that summarizes GitHub PR activity, triages issues, and drafts weekly stakeholder update emails. It operates in two modes:

1. **Interactive mode** — Claude Code skills invoked directly (e.g., `/triage-issue`)
2. **Batch mode** — CLI orchestrator (`scripts/release_radar.py`) calls Claude API + GitHub API

Built for the DataExpert Claude Code bootcamp, covering HW1 (GitHub Triage + Email Drafting) and HW2 (CLAUDE.md + HANDOFF.md).

## Build / Test / Lint Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all unit tests (no API calls)
pytest tests/unit/ -v

# Run integration tests (requires .env with API keys)
pytest tests/integration/ -v -m integration

# Run all tests
pytest -v

# Lint
ruff check .

# Format check
ruff format --check .

# Type check
mypy scripts/ guardrails/ --ignore-missing-imports

# Full validation
ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest -v
```

## Folder Map

```
release-radar/
  claude_skills/           # 5 Claude Code skills (SKILL.md files)
    triage-issue/          # Classify issues by severity/priority
    summarize-pr/          # Technical PR summary + risk checklist
    digest-commits/        # Weekly commit digest
    draft-email/           # Stakeholder email from digest data
    handoff/               # Session state capture
  guardrails/              # 5 guardrail implementations
    base.py                # Guardrail base class + GuardrailError
    schemas.py             # JSON schemas for all skill outputs
    chain.py               # Ordered pre/post guardrail chain
    pii_redaction.py       # 12+ PII pattern categories
    schema_validation.py   # JSON schema validation
    uncertainty.py         # Confidence/hedging consistency
    citation.py            # Source citation validation
    insufficient_context.py # Input completeness check
    hooks/                 # Claude Code hook wrappers
  scripts/
    release_radar.py       # CLI orchestrator (batch mode)
    gh_adapter.py          # GitHub API adapter (mock + live)
  tests/
    unit/                  # Unit tests (no API calls)
    integration/           # Integration tests (CLI + API)
  data/
    mock/                  # 20 issues, 20 PRs, 60 commits
    samples/               # 3 sample I/O pairs
  memory/
    HANDOFF.md             # Generated by handoff skill
  docs/                    # Design note + documentation rationale
```

## Coding Conventions

- **Python 3.11+** — use `dict` not `Dict`, `list` not `List`, `X | None` not `Optional[X]`
- **Line length**: 100 characters (configured in pyproject.toml)
- **Imports**: sorted by ruff (isort-compatible), stdlib → third-party → local
- **Guardrail interface**: all guardrails extend `Guardrail` base class with `check_input()` and `check_output()` methods
- **Skill format**: each skill is a `SKILL.md` file with YAML frontmatter (`name`, `description`) and markdown body
- **Output format**: all skills return JSON with `status`, `confidence`, and `citations` fields
- **Error format**: guardrail failures raise `GuardrailError(guardrail_name, message, details)`

## Deployment / Runtime Constraints

- **Python 3.11+** required
- **Claude Code** required for interactive mode (skills, hooks)
- **API keys** required in `.env` for batch mode:
  - `ANTHROPIC_API_KEY` — Claude API access
  - `GITHUB_TOKEN` — GitHub REST API access
- **Never commit `.env`** — use `.env.example` as template
- **Model**: batch mode uses `claude-sonnet-4-20250514` by default

## Security / Privacy Boundaries

- **PII redaction is mandatory.** All inputs and outputs pass through the PII redaction guardrail.
- **Never log, print, or store raw PII.** Use `[REDACTED-*]` tags.
- **`.env` is gitignored.** Never commit API keys or tokens.
- **Mock data contains intentional PII** for testing redaction — do not use mock data in production contexts.
- **The Claude API pass for contextual PII** is optional but recommended for production use.

## Do / Don't Instructions

### Do
- Run the full validation command before claiming any task is complete
- Add unit tests for any new guardrail patterns or skill schemas
- Use the `GuardrailChain` for ordered execution — don't call guardrails ad-hoc
- Keep skill SKILL.md prompts self-contained — they should work without external context
- Use mock data for development and testing
- Cite sources in all skill outputs

### Don't
- Don't skip guardrails for "quick tests" — they catch real issues
- Don't hardcode API keys anywhere — always use environment variables
- Don't modify output schemas without updating `guardrails/schemas.py` and tests
- Don't add new PII patterns without corresponding positive and negative tests
- Don't use `print()` for output in the CLI — use `json.dump()` to stdout and `print()` to stderr for status
- Don't commit `.env` files or any file containing secrets

## Common Pitfalls

- **GitHub API rate limits**: unauthenticated requests are limited to 60/hour. Always use `GITHUB_TOKEN`.
- **Mock vs live confusion**: `GitHubAdapter(mock=True)` loads from `data/mock/`. Forgetting `--live` flag uses mock data silently.
- **Schema drift**: if you change a skill's output format, update `guardrails/schemas.py` AND the skill's SKILL.md AND the tests. All three must agree.
- **JSON extraction from Claude**: the CLI parses JSON from Claude's response. If Claude wraps JSON in markdown code fences, the parser handles it. If Claude returns non-JSON, it will crash.
- **Hook stdin format**: hooks receive JSON on stdin with `tool_name` and `tool_input`/`tool_output` keys. Empty stdin means the hook should do nothing.

## Validation

**Required before any work is considered complete:**

1. `ruff check .` — linting must pass
2. `ruff format --check .` — formatting must pass
3. `mypy scripts/ guardrails/ --ignore-missing-imports` — type checking must pass
4. `pytest tests/unit/ -v` — all unit tests must pass
5. `pytest tests/integration/ -v` — integration tests must pass for modified CLI paths
6. New code must have corresponding unit tests — no untested code accepted
7. Full validation: `ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest -v`

**If any step fails, fix it before proceeding.** Do not claim a task is done without passing validation output.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/CLAUDE.md
git commit -m "docs: CLAUDE.md with project overview, conventions, guardrails, and validation"
```

---

## Task 16: README.md

**Files:**
- Create: `README.md` (in release-radar root)

- [ ] **Step 1: Write README.md**

Create `README.md` in `release-radar/`:

```markdown
# Release Radar

A lightweight internal tool that summarizes GitHub PR activity, triages issues, and drafts weekly stakeholder update emails. Built on the Claude Code ecosystem.

## Quick Start

```bash
# 1. Clone and enter the project
cd release-radar

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run with mock data
python scripts/release_radar.py --weekly
```

## Usage

### Interactive Mode (Claude Code Skills)

Invoke skills directly in Claude Code:
- `/triage-issue` — classify an issue
- `/summarize-pr` — summarize a PR
- `/digest-commits` — create a commit digest
- `/draft-email` — draft a stakeholder email
- `/handoff` — capture session state

### Batch Mode (CLI)

```bash
# Full weekly report (mock data)
python scripts/release_radar.py --weekly

# Full weekly report (live data)
python scripts/release_radar.py --weekly --repo owner/repo --live

# Individual commands
python scripts/release_radar.py triage --input data/mock/issues.json
python scripts/release_radar.py summarize --input data/mock/pull_requests.json
python scripts/release_radar.py digest --input data/mock/commits.json
python scripts/release_radar.py email --input data/mock/commits.json --prs data/mock/pull_requests.json
```

## Guardrails

All outputs pass through 5 guardrails:

1. **PII Redaction** — 12+ pattern categories (emails, keys, SSNs, etc.)
2. **Schema Validation** — JSON schema enforcement per skill
3. **Uncertainty Statements** — confidence/hedging consistency
4. **Citation to Source** — every claim references input data
5. **Insufficient Context** — rejects sparse inputs before calling the LLM

## Testing

```bash
# Unit tests (no API calls)
pytest tests/unit/ -v

# Integration tests (requires API keys)
pytest tests/integration/ -v

# Full validation
ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest -v
```

## Project Structure

See [CLAUDE.md](CLAUDE.md) for detailed folder map and coding conventions.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/README.md
git commit -m "docs: README.md with setup, usage, and testing instructions"
```

---

## Task 17: HW1 Design Note + HW2 Documentation Rationale

**Files:**
- Create: `docs/design-note.md`
- Create: `docs/documentation-rationale.md`

- [ ] **Step 1: Write design note (HW1)**

Create `docs/design-note.md`:

```markdown
# Release Radar — Design Note

## Prompt Strategy

Each skill uses a structured prompt pattern:

1. **Role assignment** — "You are a [role] assistant"
2. **Input specification** — exact JSON schema the skill receives
3. **Output specification** — exact JSON schema required in response
4. **Rules** — numbered constraints (cite sources, set confidence honestly, redact PII)
5. **Reference guides** — severity/priority/risk classification tables

This structure ensures consistent, parseable output regardless of input variation. The prompts are self-contained — each SKILL.md works independently without external context.

### Why structured JSON output?

Unstructured text output would require parsing heuristics. JSON output with enforced schemas enables:
- Programmatic guardrail validation (schema check, citation check)
- Composability (digest output feeds into email input)
- Reliable CLI pipeline (no regex extraction from prose)

## Error Handling

### Guardrail Chain

Errors are handled at two levels:

1. **Pre-processing guardrails** short-circuit before the LLM call. If `InsufficientContextGuardrail` rejects input, no API call is made — saving cost and returning immediately with a structured error.

2. **Post-processing guardrails** validate LLM output. If validation fails, the CLI logs a warning to stderr and returns the raw output. This "warn, don't crash" approach ensures partial results are still useful.

### API Failures

The CLI lets `anthropic` SDK exceptions propagate. This is intentional — retries and backoff belong in a production wrapper, not in a homework submission. The error messages from the SDK are already informative.

### Mock vs Live

The `GitHubAdapter` uses the same interface for both modes. Mock mode loads from JSON fixtures; live mode calls the GitHub REST API and normalizes responses to the same schema. This means all downstream code (skills, guardrails, CLI) works identically regardless of data source.

## Known Limitations

1. **Claude output parsing is fragile.** The CLI extracts JSON from Claude's response by looking for code fences. If Claude returns malformed JSON or wraps it in unexpected formatting, parsing fails.

2. **PII redaction is regex-based.** The regex patterns catch common formats but miss context-dependent PII (e.g., "John broke the deploy" — "John" is PII but not caught by patterns). The Claude API pass addresses this but adds latency and cost.

3. **No retry logic.** API rate limits or transient failures cause immediate failure. A production system would add exponential backoff.

4. **Mock data is static.** The mock fixtures don't change, so the same weekly report is generated every run. Live mode resolves this.

5. **Hook integration is illustrative.** The exact Claude Code hook API syntax may differ from what's implemented. The hook scripts demonstrate the pattern; wiring may need adjustment.

6. **Integration tests are expensive.** Each integration test makes Claude API calls. Running the full suite costs real money. Use `pytest tests/unit/ -v` for fast iteration.
```

- [ ] **Step 2: Write documentation rationale (HW2)**

Create `docs/documentation-rationale.md`:

```markdown
# Documentation Rationale

## Why Two Documents?

CLAUDE.md and HANDOFF.md serve different audiences with different needs:

| | CLAUDE.md | HANDOFF.md |
|---|---|---|
| **Audience** | AI agents (Claude Code, Copilot, etc.) | Humans (next developer, team lead) |
| **Purpose** | Enable correct autonomous operation | Enable fast onboarding and context transfer |
| **Lifespan** | Evolves with the codebase | Snapshot of a point in time |
| **Update trigger** | When conventions, structure, or tooling changes | At session end, task handoff, or milestone |

## CLAUDE.md Structure Choices

### Optimized for AI agent reload, not human browsing

The sections follow the order an AI agent needs context:
1. What is this project? (overview)
2. How do I build/test it? (commands)
3. Where is everything? (folder map)
4. What are the rules? (conventions, security, do/don't)
5. What breaks? (pitfalls)
6. How do I prove I'm done? (validation)

A human README puts "quick start" first. CLAUDE.md puts "project identity" first because an AI agent needs to understand *what it's working on* before *how to run it*.

### Validation section is prescriptive

The Validation section doesn't say "consider running tests." It says "run these exact commands, in this order, and do not claim completion without passing output." This is deliberate — AI agents follow explicit instructions better than suggestions.

### Do/Don't is behavioral

The Do/Don't section addresses specific mistakes an AI agent would make (skipping guardrails, using print instead of json.dump, modifying schemas without updating tests). These come from observed failure modes, not theoretical concerns.

## HANDOFF.md Structure Choices

### Generated by a skill, not hand-written

HANDOFF.md is produced by the `/handoff` skill. This is dogfooding — the project includes a skill for exactly this purpose, so using it demonstrates the tool's value. It also ensures consistency: every handoff follows the same structure regardless of who writes it.

### Lives in `memory/`, not project root

HANDOFF.md is a temporal artifact (session state), not a permanent project document. Placing it in `memory/` signals that it's expected to be overwritten at the next handoff, not preserved as documentation.

## Tradeoffs

### Included
- Exact commands (copy-paste ready, no interpretation needed)
- Folder map (AI agents need to know where to look)
- Security boundaries (prevent AI from committing secrets)
- Validation requirements (prevent AI from claiming false completion)

### Excluded
- Architectural decision records (too verbose for a control file; captured in HANDOFF.md decision log)
- API documentation (the skills are self-documenting via SKILL.md)
- Contribution guide (single-developer homework project)
- Changelog (git log serves this purpose)

### Depth vs Breadth
CLAUDE.md covers many topics briefly rather than few topics deeply. An AI agent needs to know *that* guardrails exist and *where* they live, not *how* PII regex patterns work. The code itself provides depth; CLAUDE.md provides the map.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/docs/
git commit -m "docs: HW1 design note and HW2 documentation rationale"
```

---

## Task 18: Generate HANDOFF.md

**Files:**
- Create: `memory/HANDOFF.md`

- [ ] **Step 1: Invoke the handoff skill**

After all previous tasks are complete, invoke `/handoff` in Claude Code to generate `memory/HANDOFF.md` for the Release Radar project. The handoff skill will:
1. Gather current project state
2. Write structured handoff document to `memory/HANDOFF.md`
3. Include decision log, next steps, and recovery procedures

- [ ] **Step 2: Review the generated HANDOFF.md**

Verify it covers all HW2 requirements:
- [ ] Current project status and milestone progress
- [ ] Completed vs. pending tasks
- [ ] Open issues/risks/blockers
- [ ] Decision log
- [ ] Next 7-day execution plan
- [ ] Ownership/contact map
- [ ] Recovery steps

- [ ] **Step 3: Commit**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/memory/HANDOFF.md
git commit -m "docs: HANDOFF.md generated by handoff skill"
```

---

## Task 19: Full Validation

**Files:** None — validation only

- [ ] **Step 1: Run linting**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework/release-radar
ruff check . && ruff format --check .
```

Expected: clean

- [ ] **Step 2: Run type checking**

```bash
mypy scripts/ guardrails/ --ignore-missing-imports
```

Expected: clean

- [ ] **Step 3: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass

- [ ] **Step 4: Run integration tests**

```bash
pytest tests/integration/ -v
```

Expected: all tests pass (requires `.env` with valid API keys)

- [ ] **Step 5: Run full validation command**

```bash
ruff check . && ruff format --check . && mypy scripts/ guardrails/ --ignore-missing-imports && pytest -v
```

Expected: exit code 0

- [ ] **Step 6: Verify CLI works end-to-end**

```bash
python scripts/release_radar.py triage --input data/mock/issues.json | head -20
python scripts/release_radar.py --weekly 2>/dev/null | python -m json.tool | head -30
```

Expected: valid JSON output

- [ ] **Step 7: Final commit if any fixes were needed**

```bash
cd /Users/pollucts/workdir/dataexpertio-bootcamp-allrepos/dataexpertio-bootcamp/claude-code-homework
git add release-radar/
git commit -m "fix: validation fixes from full test run"
```
