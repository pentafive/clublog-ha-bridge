"""Tests for ClubLog sensor value extraction and attribute logic.

Tests the data extraction patterns used by sensor value_fn and attr_fn
without requiring Home Assistant. Uses plain dicts/lists matching the
ClubLogData dataclass structure.
"""

import pytest


class _FakeData:
    """Lightweight stand-in for ClubLogData (avoids HA import)."""

    def __init__(self, **kwargs):
        self.dxcc_matrix = kwargs.get("dxcc_matrix", {})
        self.watch = kwargs.get("watch", {})
        self.most_wanted = kwargs.get("most_wanted", {})
        self.expeditions = kwargs.get("expeditions", [])
        self.livestreams = kwargs.get("livestreams", [])
        self.activity = kwargs.get("activity", {})
        self.dxcc_worked_total = kwargs.get("dxcc_worked_total", 0)
        self.dxcc_confirmed_total = kwargs.get("dxcc_confirmed_total", 0)
        self.dxcc_verified_total = kwargs.get("dxcc_verified_total", 0)
        self.last_successful_fetch = kwargs.get("last_successful_fetch", {})
        self.consecutive_errors = kwargs.get("consecutive_errors", {})
        self.last_error = kwargs.get("last_error", {})


# --- Mirror the value_fn and attr_fn lambdas from sensor.py ---
# This tests the extraction logic independent of HA's SensorEntity machinery.

SENSORS = {
    "dxcc_worked_total": {
        "value_fn": lambda data: data.dxcc_worked_total,
    },
    "dxcc_confirmed_total": {
        "value_fn": lambda data: data.dxcc_confirmed_total,
    },
    "dxcc_verified_total": {
        "value_fn": lambda data: data.dxcc_verified_total,
    },
    "active_expeditions": {
        "value_fn": lambda data: len(data.expeditions),
        "attr_fn": lambda data: {
            "expeditions": [
                {"call": e[0], "date": e[1], "qso_count": e[2]}
                for e in data.expeditions[:20]
            ]
            if data.expeditions
            else []
        },
    },
    "most_wanted_count": {
        "value_fn": lambda data: len(data.most_wanted),
        "attr_fn": lambda data: {
            "top_10": dict(list(data.most_wanted.items())[:10])
        }
        if data.most_wanted
        else None,
    },
    "watch_total_qsos": {
        "value_fn": lambda data: (
            data.watch.get("clublog_info", {}).get("total_qsos")
            if data.watch
            else None
        ),
    },
    "watch_is_expedition": {
        "value_fn": lambda data: (
            "Yes" if data.watch.get("is_expedition") else "No"
        )
        if data.watch
        else None,
    },
    "watch_has_oqrs": {
        "value_fn": lambda data: (
            "Yes" if data.watch.get("has_oqrs") else "No"
        )
        if data.watch
        else None,
    },
    "watch_last_upload": {
        "value_fn": lambda data: (
            data.watch.get("clublog_info", {}).get("last_upload")
            if data.watch
            else None
        ),
    },
    "active_livestreams": {
        "value_fn": lambda data: len(data.livestreams),
        "attr_fn": lambda data: {
            "livestreams": [
                {"call": s[0], "dxcc": s[1], "url": s[3]}
                for s in data.livestreams[:20]
            ]
            if data.livestreams
            else []
        },
    },
    "band_activity": {
        "value_fn": lambda data: len(data.activity) if data.activity else 0,
        "attr_fn": lambda data: {
            f"band_{band}": sum(hours) if isinstance(hours, list) else hours
            for band, hours in data.activity.items()
        }
        if data.activity
        else None,
    },
    "api_consecutive_errors": {
        "value_fn": lambda data: sum(data.consecutive_errors.values()),
        "attr_fn": lambda data: {
            f"{ep}_errors": count
            for ep, count in data.consecutive_errors.items()
            if count > 0
        }
        or None,
    },
}


def _val(key, data):
    return SENSORS[key]["value_fn"](data)


def _attr(key, data):
    return SENSORS[key].get("attr_fn", lambda _: None)(data)


class TestDxccSensors:
    """DXCC progress sensors."""

    def test_worked(self):
        data = _FakeData(dxcc_worked_total=4)
        assert _val("dxcc_worked_total", data) == 4

    def test_confirmed(self):
        data = _FakeData(dxcc_confirmed_total=3)
        assert _val("dxcc_confirmed_total", data) == 3

    def test_verified(self):
        data = _FakeData(dxcc_verified_total=2)
        assert _val("dxcc_verified_total", data) == 2

    def test_zeros_on_empty(self):
        data = _FakeData()
        assert _val("dxcc_worked_total", data) == 0
        assert _val("dxcc_confirmed_total", data) == 0
        assert _val("dxcc_verified_total", data) == 0


class TestExpeditionSensor:
    """Active expeditions sensor."""

    def test_count(self, sample_expeditions):
        data = _FakeData(expeditions=sample_expeditions)
        assert _val("active_expeditions", data) == 3

    def test_count_empty(self):
        data = _FakeData()
        assert _val("active_expeditions", data) == 0

    def test_attributes(self, sample_expeditions):
        data = _FakeData(expeditions=sample_expeditions)
        attrs = _attr("active_expeditions", data)
        assert len(attrs["expeditions"]) == 3
        assert attrs["expeditions"][0]["call"] == "3Y0K"
        assert attrs["expeditions"][0]["qso_count"] == 45000

    def test_attributes_empty(self):
        data = _FakeData()
        attrs = _attr("active_expeditions", data)
        assert attrs == {"expeditions": []}

    def test_attributes_cap_20(self):
        exps = [[f"CALL{i}", "2026-01-01", i * 100] for i in range(30)]
        data = _FakeData(expeditions=exps)
        attrs = _attr("active_expeditions", data)
        assert len(attrs["expeditions"]) == 20


class TestMostWantedSensor:
    """Most wanted sensor."""

    def test_count(self, sample_most_wanted):
        data = _FakeData(most_wanted=sample_most_wanted)
        assert _val("most_wanted_count", data) == 340

    def test_count_empty(self):
        data = _FakeData()
        assert _val("most_wanted_count", data) == 0

    def test_top_10(self, sample_most_wanted):
        data = _FakeData(most_wanted=sample_most_wanted)
        attrs = _attr("most_wanted_count", data)
        assert "top_10" in attrs
        assert len(attrs["top_10"]) == 10

    def test_less_than_10(self):
        data = _FakeData(most_wanted={"1": "100", "2": "200", "3": "300"})
        attrs = _attr("most_wanted_count", data)
        assert len(attrs["top_10"]) == 3

    def test_attrs_empty(self):
        data = _FakeData()
        attrs = _attr("most_wanted_count", data)
        assert attrs is None


class TestWatchSensors:
    """Callsign watch/monitor sensors."""

    def test_total_qsos(self, sample_watch):
        data = _FakeData(watch=sample_watch)
        assert _val("watch_total_qsos", data) == 15234

    def test_total_qsos_no_data(self):
        data = _FakeData()
        assert _val("watch_total_qsos", data) is None

    def test_is_expedition_false(self, sample_watch):
        data = _FakeData(watch=sample_watch)
        assert _val("watch_is_expedition", data) == "No"

    def test_is_expedition_true(self):
        data = _FakeData(watch={"is_expedition": True})
        assert _val("watch_is_expedition", data) == "Yes"

    def test_has_oqrs(self, sample_watch):
        data = _FakeData(watch=sample_watch)
        assert _val("watch_has_oqrs", data) == "Yes"

    def test_last_upload(self, sample_watch):
        data = _FakeData(watch=sample_watch)
        assert _val("watch_last_upload", data) == "2026-02-01 14:30:00"

    def test_last_upload_empty(self):
        data = _FakeData()
        assert _val("watch_last_upload", data) is None

    def test_missing_clublog_info(self):
        """Watch response without clublog_info → None for QSO count."""
        data = _FakeData(watch={"is_expedition": False})
        assert _val("watch_total_qsos", data) is None


class TestLivestreamSensor:
    """Livestream sensor."""

    def test_count(self, sample_livestreams):
        data = _FakeData(livestreams=sample_livestreams)
        assert _val("active_livestreams", data) == 2

    def test_count_empty(self):
        data = _FakeData()
        assert _val("active_livestreams", data) == 0

    def test_attributes(self, sample_livestreams):
        data = _FakeData(livestreams=sample_livestreams)
        attrs = _attr("active_livestreams", data)
        assert len(attrs["livestreams"]) == 2
        assert attrs["livestreams"][0]["call"] == "3Y0K"
        assert "url" in attrs["livestreams"][0]


class TestBandActivitySensor:
    """Band activity sensor."""

    def test_band_count(self, sample_activity):
        data = _FakeData(activity=sample_activity)
        assert _val("band_activity", data) == 3

    def test_band_count_empty(self):
        data = _FakeData()
        assert _val("band_activity", data) == 0

    def test_band_sum(self, sample_activity):
        data = _FakeData(activity=sample_activity)
        attrs = _attr("band_activity", data)
        assert attrs["band_20m"] == sum(sample_activity["20m"])
        assert attrs["band_40m"] == sum(sample_activity["40m"])

    def test_attrs_empty(self):
        data = _FakeData()
        attrs = _attr("band_activity", data)
        assert attrs is None

    def test_scalar_band_values(self):
        """Activity with scalar (non-list) values."""
        data = _FakeData(activity={"20m": 42, "40m": 10})
        attrs = _attr("band_activity", data)
        assert attrs["band_20m"] == 42
        assert attrs["band_40m"] == 10


class TestApiErrorsSensor:
    """API errors diagnostic sensor."""

    def test_no_errors(self):
        data = _FakeData()
        assert _val("api_consecutive_errors", data) == 0

    def test_sum_errors(self):
        data = _FakeData(consecutive_errors={"matrix": 3, "watch": 1})
        assert _val("api_consecutive_errors", data) == 4

    def test_error_attrs_only_nonzero(self):
        data = _FakeData(consecutive_errors={"matrix": 3, "watch": 0, "activity": 2})
        attrs = _attr("api_consecutive_errors", data)
        assert "matrix_errors" in attrs
        assert "activity_errors" in attrs
        assert "watch_errors" not in attrs

    def test_error_attrs_empty(self):
        data = _FakeData(consecutive_errors={})
        attrs = _attr("api_consecutive_errors", data)
        assert attrs is None


class TestSensorCompleteness:
    """Verify sensor suite completeness."""

    def test_12_sensors_defined(self):
        assert len(SENSORS) == 12

    def test_all_have_value_fn(self):
        for key, desc in SENSORS.items():
            assert "value_fn" in desc, f"{key} missing value_fn"
