"""Shared fixtures for ClubLog HA Bridge tests.

These tests are designed to run without Home Assistant installed.
HA-dependent integration tests run in CI (GitHub Actions with Python 3.12+).
"""

import pytest


@pytest.fixture
def sample_matrix():
    """Realistic DXCC matrix response from ClubLog API.

    Status values: 1=confirmed, 2=worked, 3=verified (LoTW).
    """
    return {
        "1": {"20m": 1, "40m": 2},      # confirmed + worked
        "100": {"20m": 3, "15m": 1},     # verified + confirmed
        "200": {"10m": 2},               # worked only
        "291": {"20m": 1, "40m": 1, "80m": 3},  # confirmed + verified
    }


@pytest.fixture
def sample_watch():
    """Realistic watch/monitor response."""
    return {
        "clublog_user": True,
        "is_expedition": False,
        "has_oqrs": True,
        "clublog_info": {
            "total_qsos": 15234,
            "last_upload": "2026-02-01 14:30:00",
            "first_qso": "2005-03-15",
            "last_qso": "2026-01-31",
        },
    }


@pytest.fixture
def sample_most_wanted():
    """Realistic most wanted response (rank: ADIF)."""
    return {str(i): str(100 + i) for i in range(1, 341)}


@pytest.fixture
def sample_expeditions():
    """Realistic expeditions response."""
    return [
        ["3Y0K", "2026-01-15", 45000],
        ["VP8PJ", "2026-02-01", 12000],
        ["TX7L", "2026-01-20", 8500],
    ]


@pytest.fixture
def sample_livestreams():
    """Realistic livestreams response."""
    return [
        ["3Y0K", "199", "2026-01-15", "https://clublog.org/livestream/3Y0K"],
        ["VP8PJ", "141", "2026-02-01", "https://clublog.org/livestream/VP8PJ"],
    ]


@pytest.fixture
def sample_activity():
    """Realistic band activity response."""
    return {
        "20m": [10, 20, 30, 15, 0, 0, 5, 10, 25, 30, 20, 10,
                5, 0, 0, 0, 10, 15, 20, 25, 30, 15, 10, 5],
        "40m": [5, 10, 15, 20, 25, 30, 20, 15, 10, 5, 0, 0,
                0, 5, 10, 15, 20, 25, 30, 20, 15, 10, 5, 0],
        "15m": [0, 0, 0, 5, 10, 15, 20, 25, 30, 25, 20, 15,
                10, 5, 0, 0, 0, 0, 5, 10, 15, 20, 15, 10],
    }
