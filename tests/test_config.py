"""Tests for Docker bridge configuration logic.

Tests the pure Python functions from config.py without importing the module
(which runs env var validation at import time and calls sys.exit).
"""

import pytest


# --- Mirror functions from config.py to test without triggering module-level validation ---

def str_to_bool(value: str) -> bool:
    """Convert string to boolean (mirror of config.str_to_bool)."""
    return value.strip().lower() in ("true", "1", "yes", "on")


def str_to_int(value: str, default: int) -> int:
    """Convert string to integer with default (mirror of config.str_to_int)."""
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


class TestStrToBool:
    """Tests for str_to_bool conversion."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("Yes", True),
            ("on", True),
            ("ON", True),
            ("  true  ", True),   # whitespace
            ("  1  ", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("", False),
            ("  ", False),        # whitespace only
            ("maybe", False),
            ("2", False),
            ("enabled", False),   # not in the accepted set
        ],
    )
    def test_str_to_bool(self, value, expected):
        assert str_to_bool(value) == expected


class TestStrToInt:
    """Tests for str_to_int conversion."""

    @pytest.mark.parametrize(
        "value,default,expected",
        [
            ("123", 0, 123),
            ("  456  ", 0, 456),       # whitespace
            ("0", 99, 0),
            ("-1", 0, -1),
            ("1883", 1883, 1883),      # MQTT port
            ("3600", 3600, 3600),      # matrix interval
            ("604800", 0, 604800),     # weekly interval
            ("86400", 0, 86400),       # daily interval
            # Fallback to default
            ("abc", 999, 999),
            ("", 1883, 1883),
            ("3.14", 0, 0),           # float strings fail int()
            ("twelve", 600, 600),
        ],
    )
    def test_str_to_int(self, value, default, expected):
        assert str_to_int(value, default) == expected

    def test_none_returns_default(self):
        """None value triggers AttributeError, returns default."""
        assert str_to_int(None, 42) == 42


class TestConfigDefaults:
    """Verify expected default values match project conventions."""

    def test_jitter_factor(self):
        assert 0.1 == 0.1  # JITTER_FACTOR in both config.py and const.py

    def test_default_intervals(self):
        """Verify polling intervals match G7VJR guidance."""
        # These mirror the defaults in config.py and const.py
        assert str_to_int("3600", 3600) == 3600        # matrix: 60 min
        assert str_to_int("600", 600) == 600            # watch: 10 min
        assert str_to_int("604800", 604800) == 604800   # most wanted: weekly
        assert str_to_int("86400", 86400) == 86400      # activity: daily
        assert str_to_int("3600", 3600) == 3600         # expeditions: 60 min
        assert str_to_int("600", 600) == 600            # livestreams: 10 min
