"""Tests for PII redaction guardrail."""

from guardrails.pii_redaction import PIIRedactionGuardrail


class TestPIIRedactionGuardrail:
    def setup_method(self):
        self.guardrail = PIIRedactionGuardrail()

    # --- Email ---
    def test_email_redacted(self):
        result = self.guardrail.redact_text("Contact us at user@example.com for support.")
        assert "user@example.com" not in result
        assert "[REDACTED-EMAIL]" in result

    def test_non_email_at_sign_preserved(self):
        result = self.guardrail.redact_text("Follow us @twitter for updates.")
        assert "@twitter" in result

    # --- Phone ---
    def test_us_phone_redacted(self):
        result = self.guardrail.redact_text("Call us at 555-867-5309.")
        assert "555-867-5309" not in result
        assert "[REDACTED-PHONE]" in result

    def test_international_phone_redacted(self):
        result = self.guardrail.redact_text("International: +1 800 555 1234")
        assert "+1 800 555 1234" not in result
        assert "[REDACTED-PHONE]" in result

    # --- SSN ---
    def test_ssn_redacted(self):
        result = self.guardrail.redact_text("SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "[REDACTED-SSN]" in result

    # --- Credit Card ---
    def test_credit_card_redacted(self):
        result = self.guardrail.redact_text("Card: 4111 1111 1111 1111")
        assert "4111 1111 1111 1111" not in result
        assert "[REDACTED-CC]" in result

    def test_non_cc_numbers_preserved(self):
        result = self.guardrail.redact_text("Order ID: 12345678")
        assert "12345678" in result

    # --- IPv4 ---
    def test_ipv4_redacted(self):
        result = self.guardrail.redact_text("Server at 192.168.1.100 is down.")
        assert "192.168.1.100" not in result
        assert "[REDACTED-IP]" in result

    # --- API Keys ---
    def test_anthropic_api_key_redacted(self):
        result = self.guardrail.redact_text("Key: sk-ant-api03-abc123xyz")
        assert "sk-ant-api03-abc123xyz" not in result
        assert "[REDACTED-KEY]" in result

    def test_github_token_redacted(self):
        result = self.guardrail.redact_text("Token: ghp_abcdefg1234567890")
        assert "ghp_abcdefg1234567890" not in result
        assert "[REDACTED-KEY]" in result

    def test_github_pat_redacted(self):
        result = self.guardrail.redact_text("PAT: github_pat_abc123XYZ")
        assert "github_pat_abc123XYZ" not in result
        assert "[REDACTED-KEY]" in result

    def test_slack_bot_token_redacted(self):
        result = self.guardrail.redact_text("Slack: xoxb-1234-5678-abcdef")
        assert "xoxb-1234-5678-abcdef" not in result
        assert "[REDACTED-KEY]" in result

    def test_slack_user_token_redacted(self):
        result = self.guardrail.redact_text("Slack user: xoxp-1234-5678-abcdef")
        assert "xoxp-1234-5678-abcdef" not in result
        assert "[REDACTED-KEY]" in result

    def test_slack_workspace_token_redacted(self):
        result = self.guardrail.redact_text("Slack ws: xoxs-1234-5678-abcdef")
        assert "xoxs-1234-5678-abcdef" not in result
        assert "[REDACTED-KEY]" in result

    def test_aws_access_key_redacted(self):
        result = self.guardrail.redact_text("AWS: AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED-KEY]" in result

    # --- Private Keys ---
    def test_private_key_block_redacted(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
        result = self.guardrail.redact_text(text)
        assert "BEGIN RSA PRIVATE KEY" not in result
        assert "[REDACTED-PRIVATE-KEY]" in result

    # --- Connection Strings ---
    def test_postgres_connection_string_redacted(self):
        result = self.guardrail.redact_text("DB: postgres://user:pass@db.internal:5432/mydb")
        assert "postgres://user:pass@db.internal:5432/mydb" not in result
        assert "[REDACTED-CONNECTION-STRING]" in result

    def test_mongodb_connection_string_redacted(self):
        result = self.guardrail.redact_text("Mongo: mongodb://admin:secret@mongo.corp/db")
        assert "mongodb://admin:secret@mongo.corp/db" not in result
        assert "[REDACTED-CONNECTION-STRING]" in result

    # --- Internal URLs ---
    def test_internal_url_redacted(self):
        result = self.guardrail.redact_text("See http://dashboard.internal/admin for details.")
        assert "dashboard.internal" not in result
        assert "[REDACTED-URL]" in result

    def test_corp_url_redacted(self):
        result = self.guardrail.redact_text("Access https://api.corp/v1/users")
        assert "api.corp" not in result
        assert "[REDACTED-URL]" in result

    def test_local_url_redacted(self):
        result = self.guardrail.redact_text("Visit https://service.local/health")
        assert "service.local" not in result
        assert "[REDACTED-URL]" in result

    # --- Mixed PII ---
    def test_mixed_pii_all_redacted(self):
        text = (
            "User john.doe@example.com called from 555-123-4567. "
            "SSN: 987-65-4321. IP: 10.0.0.1. "
            "Card: 4111 1111 1111 1111. "
            "Key: sk-ant-secret123 and ghp_token456. "
            "DB: postgres://user:pass@localhost/db. "
            "Dashboard: https://ops.internal/metrics"
        )
        result = self.guardrail.redact_text(text)
        assert "john.doe@example.com" not in result
        assert "555-123-4567" not in result
        assert "987-65-4321" not in result
        assert "10.0.0.1" not in result
        assert "4111 1111 1111 1111" not in result
        assert "sk-ant-secret123" not in result
        assert "ghp_token456" not in result
        assert "postgres://user:pass@localhost/db" not in result
        assert "ops.internal" not in result

    # --- No PII passes unchanged ---
    def test_clean_text_passes_unchanged(self):
        text = "The release was deployed successfully to production."
        result = self.guardrail.redact_text(text)
        assert result == text

    # --- check_input dict redaction ---
    def test_check_input_redacts_dict_values(self):
        data = {
            "user": "admin@company.com",
            "note": "Call 555-867-5309",
        }
        result = self.guardrail.check_input(data)
        assert "[REDACTED-EMAIL]" in result["user"]
        assert "[REDACTED-PHONE]" in result["note"]
        assert "admin@company.com" not in result["user"]

    def test_check_input_redacts_nested_dict(self):
        data = {
            "top": "clean text",
            "nested": {
                "email": "user@example.org",
                "inner": {"key": "sk-ant-nested-key"},
            },
        }
        result = self.guardrail.check_input(data)
        assert "user@example.org" not in result["nested"]["email"]
        assert "sk-ant-nested-key" not in result["nested"]["inner"]["key"]

    def test_check_input_redacts_list_values(self):
        data = {"emails": ["a@b.com", "c@d.org", "no-pii-here"]}
        result = self.guardrail.check_input(data)
        for item in result["emails"]:
            assert "@" not in item or "[REDACTED" in item

    # --- check_output dict redaction ---
    def test_check_output_redacts_dict_values(self):
        data = {
            "report": "Issue from 192.168.0.1 with card 4111 1111 1111 1111",
        }
        result = self.guardrail.check_output(data)
        assert "192.168.0.1" not in result["report"]
        assert "4111 1111 1111 1111" not in result["report"]

    def test_check_output_redacts_nested_dict(self):
        data = {
            "summary": "ok",
            "details": {
                "connection": "postgres://root:pass@db.corp/prod",
            },
        }
        result = self.guardrail.check_output(data)
        assert "postgres://root:pass@db.corp/prod" not in result["details"]["connection"]
        assert "[REDACTED-CONNECTION-STRING]" in result["details"]["connection"]
