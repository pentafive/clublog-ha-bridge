#!/usr/bin/env python3
"""ClubLog to Home Assistant MQTT Bridge (Docker mode).

Polls ClubLog API endpoints and publishes data to Home Assistant
via MQTT discovery.
"""

import json
import logging
import signal
import time

import paho.mqtt.client as mqtt
import requests

from config import (
    CLUBLOG_API_KEY,
    CLUBLOG_APP_PASSWORD,
    CLUBLOG_EMAIL,
    DEBUG_MODE,
    HA_DISCOVERY_PREFIX,
    HA_ENTITY_BASE,
    HA_MQTT_BROKER,
    HA_MQTT_PASS,
    HA_MQTT_PORT,
    HA_MQTT_USER,
    MATRIX_INTERVAL,
    MOST_WANTED_INTERVAL,
    MY_CALLSIGN,
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


def signal_handler(_sig, _frame):
    """Handle shutdown signals."""
    global RUNNING
    log.info("Shutdown signal received")
    RUNNING = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
        "mode": 0,
        "date": 0,
        "sat": 0,
    }
    resp = requests.get(f"{CLUBLOG_API_BASE}/json_dxccchart.php", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_most_wanted() -> list:
    """Fetch most wanted list (no auth required)."""
    resp = requests.get(f"{CLUBLOG_API_BASE}/mostwanted.php", params={"api": 1}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_watch() -> dict:
    """Fetch watch/monitor data for callsign."""
    params = {"callsign": MY_CALLSIGN, "api": CLUBLOG_API_KEY}
    resp = requests.get(f"{CLUBLOG_API_BASE}/watch.php", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# MQTT functions
# ---------------------------------------------------------------------------


def connect_mqtt() -> mqtt.Client:
    """Connect to Home Assistant MQTT broker."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="clublog-ha-bridge")
    if HA_MQTT_USER:
        client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)
    client.connect(HA_MQTT_BROKER, HA_MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


def publish_sensor(client: mqtt.Client, sensor_id: str, name: str, value, unit: str = None, icon: str = None):
    """Publish a sensor via MQTT discovery."""
    config_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{HA_ENTITY_BASE}/{sensor_id}/config"
    state_topic = f"{HA_ENTITY_BASE}/{sensor_id}/state"

    config_payload = {
        "name": name,
        "state_topic": state_topic,
        "unique_id": f"{HA_ENTITY_BASE}_{sensor_id}",
        "object_id": f"{HA_ENTITY_BASE}_{sensor_id}",
    }
    if unit:
        config_payload["unit_of_measurement"] = unit
    if icon:
        config_payload["icon"] = icon

    client.publish(config_topic, json.dumps(config_payload), retain=True)
    client.publish(state_topic, str(value), retain=True)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    """Main polling loop."""
    log.info("ClubLog HA Bridge starting for %s", MY_CALLSIGN)

    client = connect_mqtt()
    log.info("Connected to MQTT broker at %s:%d", HA_MQTT_BROKER, HA_MQTT_PORT)

    last_matrix = 0
    last_most_wanted = 0
    last_watch = 0

    while RUNNING:
        now = time.time()

        # Poll DXCC matrix
        if now - last_matrix >= MATRIX_INTERVAL:
            try:
                matrix = fetch_dxcc_matrix()
                worked = len(matrix)
                publish_sensor(client, "dxcc_worked", "DXCC Worked", worked, icon="mdi:earth")
                log.info("DXCC matrix updated: %d entities worked", worked)
                last_matrix = now
            except Exception:
                log.exception("Error fetching DXCC matrix")

        # Poll most wanted
        if now - last_most_wanted >= MOST_WANTED_INTERVAL:
            try:
                wanted = fetch_most_wanted()
                publish_sensor(client, "most_wanted_count", "Most Wanted Entities", len(wanted), icon="mdi:star")
                log.info("Most wanted updated: %d entities", len(wanted))
                last_most_wanted = now
            except Exception:
                log.exception("Error fetching most wanted")

        # Poll watch
        if now - last_watch >= WATCH_INTERVAL:
            try:
                watch = fetch_watch()
                publish_sensor(client, "watch_status", "Watch Status", json.dumps(watch), icon="mdi:eye")
                log.info("Watch data updated for %s", MY_CALLSIGN)
                last_watch = now
            except Exception:
                log.exception("Error fetching watch data")

        time.sleep(30)

    client.loop_stop()
    client.disconnect()
    log.info("ClubLog HA Bridge stopped")


if __name__ == "__main__":
    main()
