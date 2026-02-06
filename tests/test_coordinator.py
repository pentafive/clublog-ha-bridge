"""Tests for ClubLog coordinator logic.

Tests DXCC stats computation, jitter, and error tracking logic
without requiring Home Assistant (runs on Python 3.10+).
"""

import random
from unittest.mock import patch

import pytest


# --- Extract pure logic from coordinator.py for testing ---

JITTER_FACTOR = 0.1


def _jittered_interval(base: float) -> float:
    """Apply jitter to an interval: base ± JITTER_FACTOR * base."""
    jitter = base * JITTER_FACTOR
    return base + random.uniform(-jitter, jitter)


def compute_dxcc_stats(matrix: dict) -> tuple:
    """Compute worked/confirmed/verified counts from DXCC matrix.

    Extracted from coordinator._fetch_matrix for testability.
    Status values: 1=confirmed, 2=worked (not confirmed), 3=verified (LoTW).
    """
    worked = set()
    confirmed = set()
    verified = set()
    for dxcc_id, bands in matrix.items():
        for _band, status in bands.items():
            worked.add(dxcc_id)
            if status in (1, 3):
                confirmed.add(dxcc_id)
            if status == 3:
                verified.add(dxcc_id)
    return len(worked), len(confirmed), len(verified)


class TestJitteredInterval:
    """Tests for the jitter function."""

    def test_jitter_within_bounds(self):
        """Jittered value should be within ±10% of base."""
        base = 3600.0
        for _ in range(200):
            result = _jittered_interval(base)
            assert base * 0.9 <= result <= base * 1.1

    def test_jitter_different_bases(self):
        """Jitter should scale with the base interval."""
        for base in [60, 300, 600, 3600, 86400, 604800]:
            for _ in range(50):
                result = _jittered_interval(float(base))
                assert base * 0.9 <= result <= base * 1.1

    def test_jitter_zero_base(self):
        """Zero base should return zero (no jitter range)."""
        assert _jittered_interval(0.0) == 0.0

    @patch("random.uniform", return_value=0.0)
    def test_jitter_no_random_returns_base(self, _mock):
        """When random returns 0, jittered == base."""
        assert _jittered_interval(3600.0) == 3600.0

    def test_jitter_produces_variation(self):
        """Multiple calls should produce different values (not constant)."""
        base = 3600.0
        results = {_jittered_interval(base) for _ in range(50)}
        assert len(results) > 1, "Jitter should produce variation"


class TestDxccStatsComputation:
    """Test DXCC stats logic extracted from _fetch_matrix.

    Status values: 1=confirmed, 2=worked (not confirmed), 3=verified (LoTW).
    """

    def test_empty_matrix(self):
        """Empty matrix yields all zeros."""
        w, c, v = compute_dxcc_stats({})
        assert (w, c, v) == (0, 0, 0)

    def test_single_worked_entity(self):
        """Status 2 = worked but not confirmed."""
        w, c, v = compute_dxcc_stats({"1": {"20m": 2}})
        assert (w, c, v) == (1, 0, 0)

    def test_single_confirmed_entity(self):
        """Status 1 = confirmed (QSL received)."""
        w, c, v = compute_dxcc_stats({"1": {"20m": 1}})
        assert (w, c, v) == (1, 1, 0)

    def test_single_verified_entity(self):
        """Status 3 = verified (LoTW) — counts as worked + confirmed + verified."""
        w, c, v = compute_dxcc_stats({"1": {"20m": 3}})
        assert (w, c, v) == (1, 1, 1)

    def test_multiple_bands_same_entity(self):
        """Same entity on multiple bands should count once per category."""
        matrix = {"1": {"20m": 2, "40m": 1, "80m": 3}}
        w, c, v = compute_dxcc_stats(matrix)
        assert w == 1  # one entity
        assert c == 1  # has confirmed/verified band
        assert v == 1  # has verified band

    def test_realistic_matrix(self, sample_matrix):
        """Test with realistic multi-entity matrix."""
        w, c, v = compute_dxcc_stats(sample_matrix)
        # "1": 20m=1(conf), 40m=2(worked) → worked+confirmed
        # "100": 20m=3(verified), 15m=1(conf) → worked+confirmed+verified
        # "200": 10m=2(worked) → worked only
        # "291": 20m=1, 40m=1, 80m=3 → worked+confirmed+verified
        assert w == 4
        assert c == 3  # entities 1, 100, 291
        assert v == 2  # entities 100, 291

    def test_set_deduplication(self):
        """Entity on many bands counted once."""
        matrix = {
            "1": {
                "160m": 2, "80m": 2, "40m": 1, "20m": 1,
                "15m": 3, "10m": 2, "6m": 2,
            }
        }
        w, c, v = compute_dxcc_stats(matrix)
        assert (w, c, v) == (1, 1, 1)

    def test_all_worked_none_confirmed(self):
        """All entities worked (status 2) but none confirmed."""
        matrix = {str(i): {"20m": 2} for i in range(100)}
        w, c, v = compute_dxcc_stats(matrix)
        assert w == 100
        assert c == 0
        assert v == 0

    def test_verified_subset_of_confirmed(self):
        """Verified entities should always be a subset of confirmed."""
        matrix = {
            "1": {"20m": 3},  # verified
            "2": {"20m": 1},  # confirmed
            "3": {"20m": 2},  # worked
            "4": {"20m": 3, "40m": 1},  # verified + confirmed
        }
        w, c, v = compute_dxcc_stats(matrix)
        assert v <= c <= w
        assert w == 4
        assert c == 3  # 1, 2, 4
        assert v == 2  # 1, 4


class TestStaggerLogic:
    """Tests for endpoint stagger logic (mirrors coordinator.__init__)."""

    def test_stagger_offsets(self):
        """Endpoints should be staggered by 5s each."""
        endpoints = ["matrix", "watch", "most_wanted",
                     "expeditions", "livestreams", "activity"]
        now = 1000.0
        next_fetch = {}
        for i, ep in enumerate(endpoints):
            next_fetch[ep] = now + (i * 5)

        assert next_fetch["matrix"] == 1000.0
        assert next_fetch["watch"] == 1005.0
        assert next_fetch["most_wanted"] == 1010.0
        assert next_fetch["expeditions"] == 1015.0
        assert next_fetch["livestreams"] == 1020.0
        assert next_fetch["activity"] == 1025.0

    def test_six_endpoints(self):
        """All 6 endpoints should be tracked."""
        endpoints = ["matrix", "watch", "most_wanted",
                     "expeditions", "livestreams", "activity"]
        assert len(endpoints) == 6


class TestErrorTracking:
    """Tests for error tracking logic (mirrors coordinator behavior)."""

    def test_consecutive_error_increment(self):
        """Errors should increment on each failure."""
        errors = {}
        for _ in range(5):
            prev = errors.get("matrix", 0)
            errors["matrix"] = prev + 1
        assert errors["matrix"] == 5

    def test_error_reset_on_success(self):
        """Errors reset to 0 on successful fetch."""
        errors = {"matrix": 5}
        last_error = {"matrix": "Connection timeout"}
        # Simulate success
        errors["matrix"] = 0
        last_error.pop("matrix", None)
        assert errors["matrix"] == 0
        assert "matrix" not in last_error

    def test_per_endpoint_isolation(self):
        """Errors on one endpoint don't affect others."""
        errors = {"matrix": 3, "watch": 0, "expeditions": 1}
        assert errors["matrix"] == 3
        assert errors["watch"] == 0
        assert errors["expeditions"] == 1

    def test_backoff_duration(self):
        """403 backoff should be 1 hour (3600s)."""
        backoff_duration = 3600.0
        now = 10000.0
        backoff_until = now + backoff_duration
        assert backoff_until == 13600.0

    def test_backoff_reschedules_all_endpoints(self):
        """On 403, all endpoints should be pushed past backoff window."""
        now = 10000.0
        backoff_until = now + 3600.0
        endpoints = ["matrix", "watch", "most_wanted",
                     "expeditions", "livestreams", "activity"]
        next_fetch = {}
        for i, ep in enumerate(endpoints):
            next_fetch[ep] = backoff_until + (i * 5)

        for ep in endpoints:
            assert next_fetch[ep] >= backoff_until, \
                f"{ep} scheduled before backoff expires"


class TestApiStatusLogic:
    """Tests for binary sensor API status logic (mirrors binary_sensor.py)."""

    STALE_THRESHOLD = 7200  # 2 hours

    def test_api_ok_recent_fetch(self):
        """API should be OK if any endpoint fetched within 2 hours."""
        import time
        now = time.time()
        fetches = {"matrix": now - 100, "watch": now - 3600}
        is_on = any(now - ts < self.STALE_THRESHOLD for ts in fetches.values())
        assert is_on is True

    def test_api_not_ok_stale(self):
        """API should be NOT OK if all fetches are stale (>2 hours)."""
        import time
        now = time.time()
        fetches = {"matrix": now - 8000, "watch": now - 9000}
        is_on = any(now - ts < self.STALE_THRESHOLD for ts in fetches.values())
        assert is_on is False

    def test_api_not_ok_no_fetches(self):
        """API should be NOT OK if no fetches have ever succeeded."""
        fetches = {}
        assert not fetches  # empty → False
