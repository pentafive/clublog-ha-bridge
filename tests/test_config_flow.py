"""Tests for ClubLog config flow validation logic.

Tests callsign regex and field validation without requiring Home Assistant.
"""

import re

import pytest

# Mirror the regex from config_flow.py
CALLSIGN_REGEX = re.compile(r"^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}$", re.IGNORECASE)


class TestCallsignValidation:
    """Test callsign regex used in config_flow.py."""

    @pytest.mark.parametrize(
        "callsign",
        [
            "KD5QLM",   # US 2x3
            "W1AW",     # US 1x2 (ARRL HQ)
            "N5N",      # US 1x1
            "AA1A",     # US 2x1
            "VK3GA",    # Australia
            "G7VJR",    # UK
            "JA1ABC",   # Japan
            "5B4AHJ",   # Cyprus (starts with digit)
            "3Y0K",     # Bouvet expedition
            "VP8PJ",    # Falklands
            "TX7L",     # Marquesas expedition
            "kd5qlm",   # lowercase (IGNORECASE)
            "K5",       # minimal valid
            "A25A",     # Botswana
        ],
    )
    def test_valid_callsigns(self, callsign):
        assert CALLSIGN_REGEX.match(callsign), f"{callsign} should be valid"

    @pytest.mark.parametrize(
        "callsign",
        [
            "",            # empty
            "ABCD1EFGH",   # too long
            "TOOLONG1X",   # prefix >3 + digit + suffix >4
            "A",           # no digit
            "ABCD",        # no digit at all
            "AB-1CD",      # contains hyphen
            "KD5 QLM",    # contains space
            "KD5/QLM",    # contains slash (portable indicator)
        ],
    )
    def test_invalid_callsigns(self, callsign):
        assert not CALLSIGN_REGEX.match(callsign), f"{callsign} should be invalid"


class TestFieldValidation:
    """Test field presence validation logic from config_flow.py."""

    def _validate(self, user_input):
        """Mirror the validation logic from async_step_user."""
        errors = {}
        callsign = user_input.get("callsign", "").strip().upper()

        if not CALLSIGN_REGEX.match(callsign):
            errors["base"] = "invalid_callsign"
        elif not user_input.get("api_key"):
            errors["base"] = "api_key_required"
        elif not user_input.get("email"):
            errors["base"] = "email_required"
        elif not user_input.get("app_password"):
            errors["base"] = "app_password_required"
        return errors

    def test_valid_input(self):
        result = self._validate({
            "callsign": "KD5QLM",
            "api_key": "test-key",
            "email": "test@example.com",
            "app_password": "test-pass",
        })
        assert result == {}

    def test_invalid_callsign(self):
        result = self._validate({
            "callsign": "!!!",
            "api_key": "test-key",
            "email": "test@example.com",
            "app_password": "test-pass",
        })
        assert result == {"base": "invalid_callsign"}

    def test_empty_callsign(self):
        result = self._validate({
            "callsign": "",
            "api_key": "test-key",
            "email": "test@example.com",
            "app_password": "test-pass",
        })
        assert result == {"base": "invalid_callsign"}

    def test_missing_api_key(self):
        result = self._validate({
            "callsign": "KD5QLM",
            "api_key": "",
            "email": "test@example.com",
            "app_password": "test-pass",
        })
        assert result == {"base": "api_key_required"}

    def test_missing_email(self):
        result = self._validate({
            "callsign": "KD5QLM",
            "api_key": "test-key",
            "email": "",
            "app_password": "test-pass",
        })
        assert result == {"base": "email_required"}

    def test_missing_app_password(self):
        result = self._validate({
            "callsign": "KD5QLM",
            "api_key": "test-key",
            "email": "test@example.com",
            "app_password": "",
        })
        assert result == {"base": "app_password_required"}

    def test_callsign_uppercased(self):
        """Callsign should be uppercased before validation."""
        result = self._validate({
            "callsign": "  kd5qlm  ",
            "api_key": "test-key",
            "email": "test@example.com",
            "app_password": "test-pass",
        })
        assert result == {}

    def test_validation_order(self):
        """Errors should be reported in priority order: callsign > api_key > email > password."""
        # All missing — should report callsign first
        result = self._validate({
            "callsign": "",
            "api_key": "",
            "email": "",
            "app_password": "",
        })
        assert result["base"] == "invalid_callsign"
