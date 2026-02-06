#!/usr/bin/env python3
"""ClubLog to Home Assistant MQTT Bridge (Docker mode).

Polls ClubLog API endpoints and publishes data to Home Assistant
via MQTT discovery.
"""

import json
import logging
import random
import signal
import time

import paho.mqtt.client as mqtt
import requests

from config import (
    ACTIVITY_INTERVAL,
    CLUBLOG_API_KEY,
    CLUBLOG_APP_PASSWORD,
    CLUBLOG_EMAIL,
    DEBUG_MODE,
    EXPEDITIONS_INTERVAL,
    HA_DISCOVERY_PREFIX,
    HA_ENTITY_BASE,
    HA_MQTT_BROKER,
    HA_MQTT_PASS,
    HA_MQTT_PORT,
    HA_MQTT_USER,
    JITTER_FACTOR,
    LIVESTREAMS_INTERVAL,
    MATRIX_INTERVAL,
    MOST_WANTED_INTERVAL,
    MY_CALLSIGN,
    USER_AGENT,
    VERSION,
    WATCH_INTERVAL,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("clublog-ha-bridge")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CLUBLOG_API_BASE = "https://clublog.org"
RUNNING = True

# Device config shared by all MQTT discovery messages
DEVICE_CONFIG = {
    "identifiers": [f"clublog_{MY_CALLSIGN}"],
    "name": f"ClubLog ({MY_CALLSIGN})",
    "manufacturer": "ClubLog",
    "model": "HA Bridge",
    "sw_version": VERSION,
    "configuration_url": "https://clublog.org",
}


def _jittered(interval: float) -> float:
    """Apply jitter to an interval: interval ± JITTER_FACTOR * interval."""
    jitter = interval * JITTER_FACTOR
    return interval + random.uniform(-jitter, jitter)


def signal_handler(_sig, _frame):
    """Handle shutdown signals."""
    global RUNNING  # noqa: PLW0603
    log.info("Shutdown signal received")
    RUNNING = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ---------------------------------------------------------------------------
# HTTP session with User-Agent and connection reuse
# ---------------------------------------------------------------------------
http_session = requests.Session()
http_session.headers.update({"User-Agent": USER_AGENT})


# ---------------------------------------------------------------------------
# ClubLog API functions
# ---------------------------------------------------------------------------


def fetch_dxcc_matrix() -> dict:
    """Fetch DXCC matrix from ClubLog."""
    params = {
        "call": MY_CALLSIGN,
        "api": CLUBLOG_API_KEY,
        "email": CLUBLOG_EMAIL,
        "password": CLUBLOG_APP_PASSWORD,
        "mode": "0",
        "date": "0",
        "sat": "0",
    }
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/json_dxccchart.php", params=params, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_most_wanted() -> dict:
    """Fetch most wanted list (no auth required)."""
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/mostwanted.php", params={"api": "1"}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_watch() -> dict:
    """Fetch watch/monitor data for callsign."""
    params = {"call": MY_CALLSIGN, "api": CLUBLOG_API_KEY}
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/watch.php", params=params, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_expeditions() -> list:
    """Fetch active expeditions (no auth required)."""
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/expeditions.php", params={"api": "1"}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_livestreams() -> list:
    """Fetch active livestreams (no auth required)."""
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/livestreams.php", params={"api": "1"}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def fetch_activity() -> dict:
    """Fetch band activity data (lastyear=1 to avoid timeout)."""
    params = {"call": MY_CALLSIGN, "api": CLUBLOG_API_KEY, "lastyear": "1"}
    resp = http_session.get(
        f"{CLUBLOG_API_BASE}/activity_json.php", params=params, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# MQTT functions
# ---------------------------------------------------------------------------


def connect_mqtt() -> mqtt.Client:
    """Connect to Home Assistant MQTT broker."""
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2, client_id="clublog-ha-bridge"
    )
    if HA_MQTT_USER:
        client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)
    client.connect(HA_MQTT_BROKER, HA_MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


def publish_sensor(
    client: mqtt.Client,
    sensor_id: str,
    name: str,
    value,
    *,
    unit: str | None = None,
    icon: str | None = None,
    state_class: str | None = None,
    attributes: dict | None = None,
    entity_category: str | None = None,
):
    """Publish a sensor via MQTT discovery with device grouping."""
    unique_id = f"{HA_ENTITY_BASE}_{sensor_id}"
    config_topic = (
        f"{HA_DISCOVERY_PREFIX}/sensor/{HA_ENTITY_BASE}/{sensor_id}/config"
    )
    state_topic = f"{HA_ENTITY_BASE}/{sensor_id}/state"

    config_payload = {
        "name": name,
        "state_topic": state_topic,
        "unique_id": unique_id,
        "object_id": unique_id,
        "device": DEVICE_CONFIG,
    }
    if unit:
        config_payload["unit_of_measurement"] = unit
    if icon:
        config_payload["icon"] = icon
    if state_class:
        config_payload["state_class"] = state_class
    if entity_category:
        config_payload["entity_category"] = entity_category
    if attributes is not None:
        attr_topic = f"{HA_ENTITY_BASE}/{sensor_id}/attributes"
        config_payload["json_attributes_topic"] = attr_topic
        client.publish(attr_topic, json.dumps(attributes), retain=True)

    client.publish(config_topic, json.dumps(config_payload), retain=True)
    client.publish(state_topic, str(value), retain=True)


def publish_binary_sensor(
    client: mqtt.Client,
    sensor_id: str,
    name: str,
    is_on: bool,
    *,
    device_class: str | None = None,
    entity_category: str | None = None,
    attributes: dict | None = None,
):
    """Publish a binary sensor via MQTT discovery."""
    unique_id = f"{HA_ENTITY_BASE}_{sensor_id}"
    config_topic = (
        f"{HA_DISCOVERY_PREFIX}/binary_sensor/{HA_ENTITY_BASE}/{sensor_id}/config"
    )
    state_topic = f"{HA_ENTITY_BASE}/{sensor_id}/state"

    config_payload = {
        "name": name,
        "state_topic": state_topic,
        "unique_id": unique_id,
        "object_id": unique_id,
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": DEVICE_CONFIG,
    }
    if device_class:
        config_payload["device_class"] = device_class
    if entity_category:
        config_payload["entity_category"] = entity_category
    if attributes is not None:
        attr_topic = f"{HA_ENTITY_BASE}/{sensor_id}/attributes"
        config_payload["json_attributes_topic"] = attr_topic
        client.publish(attr_topic, json.dumps(attributes), retain=True)

    client.publish(config_topic, json.dumps(config_payload), retain=True)
    client.publish(state_topic, "ON" if is_on else "OFF", retain=True)


# ---------------------------------------------------------------------------
# Data processing helpers
# ---------------------------------------------------------------------------


def compute_dxcc_stats(matrix: dict) -> tuple[int, int, int]:
    """Compute worked/confirmed/verified totals from DXCC matrix.

    ClubLog status values: 1=confirmed, 2=worked (not confirmed), 3=verified (LoTW).
    """
    worked = set()
    confirmed = set()
    verified = set()
    for dxcc_id, bands in matrix.items():
        for _band, status in bands.items():
            worked.add(dxcc_id)  # any status means entity was worked
            if status in (1, 3):  # confirmed (QSL) or verified (LoTW)
                confirmed.add(dxcc_id)
            if status == 3:  # verified via LoTW only
                verified.add(dxcc_id)
    return len(worked), len(confirmed), len(verified)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    """Main polling loop."""
    log.info("ClubLog HA Bridge v%s starting for %s", VERSION, MY_CALLSIGN)

    client = connect_mqtt()
    log.info("Connected to MQTT broker at %s:%d", HA_MQTT_BROKER, HA_MQTT_PORT)

    intervals = {
        "matrix": MATRIX_INTERVAL,
        "most_wanted": MOST_WANTED_INTERVAL,
        "watch": WATCH_INTERVAL,
        "expeditions": EXPEDITIONS_INTERVAL,
        "livestreams": LIVESTREAMS_INTERVAL,
        "activity": ACTIVITY_INTERVAL,
    }

    # Per-endpoint next-fetch timestamps — staggered to avoid startup burst
    now = time.monotonic()
    next_fetch: dict[str, float] = {}
    for i, endpoint in enumerate(intervals):
        next_fetch[endpoint] = now + (i * 5)  # 5s offset per endpoint

    # Fetch handlers
    fetchers = {
        "matrix": _process_matrix,
        "most_wanted": _process_most_wanted,
        "watch": _process_watch,
        "expeditions": _process_expeditions,
        "livestreams": _process_livestreams,
        "activity": _process_activity,
    }

    # Per-endpoint error tracking
    consecutive_errors: dict[str, int] = {}
    last_success: dict[str, float] = {}

    # 403 circuit breaker — cease all requests for BACKOFF_403 seconds on 403
    backoff_403 = 3600  # 1 hour
    backoff_until = 0.0  # monotonic timestamp; 0 = not in backoff

    while RUNNING:
        now_mono = time.monotonic()
        now_wall = time.time()

        # Check 403 backoff — skip endpoint fetches but still publish status
        in_backoff = backoff_until > now_mono
        if in_backoff:
            remaining = int(backoff_until - now_mono)
            if remaining % 300 == 0 and remaining > 0:
                log.warning(
                    "403 backoff active — all requests paused (%d min remaining)",
                    remaining // 60,
                )

        if not in_backoff:
            for endpoint, next_time in next_fetch.items():
                if now_mono < next_time:
                    continue

                try:
                    fetchers[endpoint](client)
                    consecutive_errors[endpoint] = 0
                    last_success[endpoint] = now_wall
                    log.info("Fetched %s successfully", endpoint)
                except requests.exceptions.HTTPError as err:
                    if err.response is not None and err.response.status_code == 403:
                        log.error(
                            "HTTP 403 from %s — ceasing ALL requests for %d minutes. "
                            "Check credentials and rate limits.",
                            endpoint,
                            backoff_403 // 60,
                        )
                        backoff_until = now_mono + backoff_403
                        # Push all endpoints past the backoff window
                        for i_ep, ep in enumerate(next_fetch):
                            next_fetch[ep] = backoff_until + (i_ep * 5)
                        break
                    consecutive_errors[endpoint] = (
                        consecutive_errors.get(endpoint, 0) + 1
                    )
                    log.exception("Error fetching %s", endpoint)
                except Exception:
                    consecutive_errors[endpoint] = (
                        consecutive_errors.get(endpoint, 0) + 1
                    )
                    log.exception("Error fetching %s", endpoint)
                finally:
                    # Schedule next fetch with jitter (only if not in 403 backoff)
                    if backoff_until <= now_mono:
                        next_fetch[endpoint] = now_mono + _jittered(
                            intervals[endpoint]
                        )

        # --- API Status Binary Sensor ---
        stale_threshold = 7200  # 2 hours
        api_ok = (
            any(now_wall - ts < stale_threshold for ts in last_success.values())
            if last_success
            else False
        )
        error_attrs = {
            f"{ep}_errors": count
            for ep, count in consecutive_errors.items()
            if count > 0
        }
        error_attrs.update(
            {f"{ep}_last_success": ts for ep, ts in last_success.items()}
        )
        if backoff_until > now_mono:
            error_attrs["backoff_remaining_min"] = int(
                (backoff_until - now_mono) / 60
            )
        publish_binary_sensor(
            client,
            "api_status",
            "API Status",
            api_ok,
            device_class="connectivity",
            entity_category="diagnostic",
            attributes=error_attrs or None,
        )

        # --- Diagnostics Sensor ---
        total_errors = sum(consecutive_errors.values())
        publish_sensor(
            client,
            "api_consecutive_errors",
            "API Errors",
            total_errors,
            unit="errors",
            icon="mdi:alert-circle",
            state_class="measurement",
            entity_category="diagnostic",
            attributes={
                f"{ep}_errors": count
                for ep, count in consecutive_errors.items()
                if count > 0
            }
            or None,
        )

        time.sleep(30)

    client.loop_stop()
    client.disconnect()
    log.info("ClubLog HA Bridge stopped")


# ---------------------------------------------------------------------------
# Per-endpoint processing functions
# ---------------------------------------------------------------------------


def _process_matrix(client: mqtt.Client) -> None:
    """Fetch and publish DXCC matrix data."""
    matrix = fetch_dxcc_matrix()
    w, c, v = compute_dxcc_stats(matrix)
    publish_sensor(
        client, "dxcc_worked_total", "DXCC Worked", w,
        unit="entities", icon="mdi:earth", state_class="total",
    )
    publish_sensor(
        client, "dxcc_confirmed_total", "DXCC Confirmed", c,
        unit="entities", icon="mdi:earth-plus", state_class="total",
    )
    publish_sensor(
        client, "dxcc_verified_total", "DXCC Verified", v,
        unit="entities", icon="mdi:earth-arrow-right", state_class="total",
    )
    log.info("DXCC matrix: %d worked, %d confirmed, %d verified", w, c, v)


def _process_most_wanted(client: mqtt.Client) -> None:
    """Fetch and publish most wanted data."""
    wanted = fetch_most_wanted()
    top_10 = dict(list(wanted.items())[:10]) if wanted else {}
    publish_sensor(
        client, "most_wanted_count", "Most Wanted Entities", len(wanted),
        unit="entities", icon="mdi:star", state_class="measurement",
        attributes={"top_10": top_10},
    )


def _process_watch(client: mqtt.Client) -> None:
    """Fetch and publish watch/monitor data."""
    watch = fetch_watch()
    clublog_info = watch.get("clublog_info", {})
    publish_sensor(
        client, "watch_total_qsos", "Total QSOs",
        clublog_info.get("total_qsos", 0),
        unit="QSOs", icon="mdi:radio-tower", state_class="total",
    )
    publish_sensor(
        client, "watch_is_expedition", "Is Expedition",
        "Yes" if watch.get("is_expedition") else "No",
        icon="mdi:airplane-takeoff",
    )
    publish_sensor(
        client, "watch_has_oqrs", "Has OQRS",
        "Yes" if watch.get("has_oqrs") else "No",
        icon="mdi:email-check",
    )
    publish_sensor(
        client, "watch_last_upload", "Last Upload",
        clublog_info.get("last_clublog_upload", "Unknown"),
        icon="mdi:cloud-upload",
    )


def _process_expeditions(client: mqtt.Client) -> None:
    """Fetch and publish expedition data."""
    expeditions = fetch_expeditions()
    exp_attrs = (
        [{"call": e[0], "date": e[1], "qso_count": e[2]} for e in expeditions[:20]]
        if expeditions
        else []
    )
    publish_sensor(
        client, "active_expeditions", "Active Expeditions", len(expeditions),
        unit="expeditions", icon="mdi:airplane", state_class="measurement",
        attributes={"expeditions": exp_attrs},
    )


def _process_livestreams(client: mqtt.Client) -> None:
    """Fetch and publish livestream data."""
    livestreams = fetch_livestreams()
    ls_attrs = (
        [{"call": s[0], "dxcc": s[1], "url": s[3]} for s in livestreams[:20]]
        if livestreams
        else []
    )
    publish_sensor(
        client, "active_livestreams", "Active Livestreams", len(livestreams),
        unit="streams", icon="mdi:broadcast", state_class="measurement",
        attributes={"livestreams": ls_attrs},
    )


def _process_activity(client: mqtt.Client) -> None:
    """Fetch and publish band activity data."""
    activity = fetch_activity()
    band_totals = (
        {
            f"band_{band}": sum(hours) if isinstance(hours, list) else hours
            for band, hours in activity.items()
        }
        if activity
        else {}
    )
    publish_sensor(
        client, "band_activity", "Band Activity",
        len(activity) if activity else 0,
        unit="bands", icon="mdi:sine-wave", state_class="measurement",
        attributes=band_totals,
    )


if __name__ == "__main__":
    main()
