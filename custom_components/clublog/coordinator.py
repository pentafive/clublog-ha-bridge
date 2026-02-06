"""DataUpdateCoordinator for ClubLog HA Bridge."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CLUBLOG_ACTIVITY_ENDPOINT,
    CLUBLOG_API_BASE,
    CLUBLOG_EXPEDITIONS_ENDPOINT,
    CLUBLOG_LIVESTREAMS_ENDPOINT,
    CLUBLOG_MATRIX_ENDPOINT,
    CLUBLOG_MOST_WANTED_ENDPOINT,
    CLUBLOG_WATCH_ENDPOINT,
    CONF_API_KEY,
    CONF_APP_PASSWORD,
    CONF_CALLSIGN,
    CONF_EMAIL,
    DEFAULT_ACTIVITY_INTERVAL,
    DEFAULT_EXPEDITIONS_INTERVAL,
    DEFAULT_LIVESTREAMS_INTERVAL,
    DEFAULT_MATRIX_INTERVAL,
    DEFAULT_MOST_WANTED_INTERVAL,
    DEFAULT_WATCH_INTERVAL,
    DOMAIN,
    JITTER_FACTOR,
    MIN_COORDINATOR_INTERVAL,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

# Endpoint names used as keys for tracking
ENDPOINT_MATRIX = "matrix"
ENDPOINT_WATCH = "watch"
ENDPOINT_MOST_WANTED = "most_wanted"
ENDPOINT_EXPEDITIONS = "expeditions"
ENDPOINT_LIVESTREAMS = "livestreams"
ENDPOINT_ACTIVITY = "activity"

# Map endpoint names to their configured intervals
ENDPOINT_INTERVALS = {
    ENDPOINT_MATRIX: DEFAULT_MATRIX_INTERVAL,
    ENDPOINT_WATCH: DEFAULT_WATCH_INTERVAL,
    ENDPOINT_MOST_WANTED: DEFAULT_MOST_WANTED_INTERVAL,
    ENDPOINT_EXPEDITIONS: DEFAULT_EXPEDITIONS_INTERVAL,
    ENDPOINT_LIVESTREAMS: DEFAULT_LIVESTREAMS_INTERVAL,
    ENDPOINT_ACTIVITY: DEFAULT_ACTIVITY_INTERVAL,
}


def _jittered_interval(base: float) -> float:
    """Apply jitter to an interval: base ± JITTER_FACTOR * base."""
    jitter = base * JITTER_FACTOR
    return base + random.uniform(-jitter, jitter)


@dataclass
class ClubLogData:
    """Data class for ClubLog coordinator."""

    # DXCC matrix: {dxcc_id: {band: status}}
    dxcc_matrix: dict[str, dict[str, int]] = field(default_factory=dict)

    # Watch data
    watch: dict[str, Any] = field(default_factory=dict)

    # Most wanted list: {rank: adif_id}
    most_wanted: dict[str, Any] = field(default_factory=dict)

    # Active expeditions: [[call, date, count], ...]
    expeditions: list[list[Any]] = field(default_factory=list)

    # Livestreams: [[call, dxcc, date, url], ...]
    livestreams: list[list[Any]] = field(default_factory=list)

    # Activity: {band: [hourly_counts]}
    activity: dict[str, Any] = field(default_factory=dict)

    # Computed DXCC stats
    dxcc_worked_total: int = 0
    dxcc_confirmed_total: int = 0
    dxcc_verified_total: int = 0

    # Health tracking
    last_successful_fetch: dict[str, float] = field(default_factory=dict)
    consecutive_errors: dict[str, int] = field(default_factory=dict)
    last_error: dict[str, str] = field(default_factory=dict)


class ClubLogCoordinator(DataUpdateCoordinator[ClubLogData]):
    """Coordinator for ClubLog API polling.

    Uses a single coordinator with MIN_COORDINATOR_INTERVAL wake cycle.
    Each endpoint has its own interval tracked via _next_fetch timestamps.
    Only endpoints whose interval has elapsed are fetched each cycle.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=MIN_COORDINATOR_INTERVAL),
        )
        self.entry = entry
        self._callsign = entry.data[CONF_CALLSIGN]
        self._api_key = entry.data[CONF_API_KEY]
        self._email = entry.data[CONF_EMAIL]
        self._app_password = entry.data[CONF_APP_PASSWORD]

        # Per-endpoint next-fetch timestamps (staggered to avoid burst)
        now = time.monotonic()
        self._next_fetch: dict[str, float] = {}
        for i, (endpoint, _interval) in enumerate(ENDPOINT_INTERVALS.items()):
            # Stagger initial fetches: first endpoint immediate, others offset
            stagger = i * 5  # 5 seconds between each endpoint on first run
            self._next_fetch[endpoint] = now + stagger

        # Persistent data across partial updates
        self._data = ClubLogData()

        # 403 circuit breaker — cease all requests on HTTP 403
        self._backoff_until: float = 0.0  # monotonic timestamp; 0 = not in backoff
        self._backoff_duration: float = 3600.0  # 1 hour

    async def _async_update_data(self) -> ClubLogData:
        """Fetch data from ClubLog API endpoints that are due."""
        now = time.monotonic()

        # 403 circuit breaker — skip all fetches during backoff
        if self._backoff_until > now:
            remaining = int((self._backoff_until - now) / 60)
            _LOGGER.warning(
                "403 backoff active — all requests paused (%d min remaining)",
                remaining,
            )
            return self._data

        session = async_get_clientsession(self.hass)
        headers = {"User-Agent": USER_AGENT}

        any_success = False
        any_attempted = False

        # Check each endpoint and fetch if due
        for endpoint, next_time in self._next_fetch.items():
            if now < next_time:
                continue

            any_attempted = True
            interval = ENDPOINT_INTERVALS[endpoint]

            try:
                await self._fetch_endpoint(session, headers, endpoint)
                self._data.last_successful_fetch[endpoint] = time.time()
                self._data.consecutive_errors[endpoint] = 0
                self._data.last_error.pop(endpoint, None)
                any_success = True
                _LOGGER.debug("Fetched %s successfully", endpoint)
            except ClientResponseError as err:
                if err.status == 403:
                    _LOGGER.error(
                        "HTTP 403 from %s — ceasing ALL requests for %d minutes. "
                        "Check credentials and rate limits.",
                        endpoint,
                        int(self._backoff_duration / 60),
                    )
                    self._backoff_until = now + self._backoff_duration
                    # Push all endpoints past the backoff window
                    for i, ep in enumerate(self._next_fetch):
                        self._next_fetch[ep] = self._backoff_until + (i * 5)
                    self._data.last_error[endpoint] = "HTTP 403 — requests paused"
                    break
                prev_errors = self._data.consecutive_errors.get(endpoint, 0)
                self._data.consecutive_errors[endpoint] = prev_errors + 1
                self._data.last_error[endpoint] = str(err)
                _LOGGER.warning(
                    "Error fetching %s (attempt %d): %s",
                    endpoint,
                    prev_errors + 1,
                    err,
                )
            except Exception as err:
                prev_errors = self._data.consecutive_errors.get(endpoint, 0)
                self._data.consecutive_errors[endpoint] = prev_errors + 1
                self._data.last_error[endpoint] = str(err)
                _LOGGER.warning(
                    "Error fetching %s (attempt %d): %s",
                    endpoint,
                    prev_errors + 1,
                    err,
                )

            # Schedule next fetch with jitter regardless of success/failure
            self._next_fetch[endpoint] = now + _jittered_interval(interval)

        # Only raise UpdateFailed if we attempted fetches and ALL failed
        if any_attempted and not any_success:
            # Check if we have any historical data at all
            if not self._data.last_successful_fetch:
                raise UpdateFailed(
                    "All ClubLog API endpoints failed — check credentials and connectivity"
                )
            _LOGGER.warning("All attempted endpoints failed this cycle, using cached data")

        return self._data

    async def _fetch_endpoint(
        self, session: Any, headers: dict[str, str], endpoint: str
    ) -> None:
        """Dispatch fetch to the appropriate endpoint handler."""
        handlers = {
            ENDPOINT_MATRIX: self._fetch_matrix,
            ENDPOINT_WATCH: self._fetch_watch,
            ENDPOINT_MOST_WANTED: self._fetch_most_wanted,
            ENDPOINT_EXPEDITIONS: self._fetch_expeditions,
            ENDPOINT_LIVESTREAMS: self._fetch_livestreams,
            ENDPOINT_ACTIVITY: self._fetch_activity,
        }
        await handlers[endpoint](session, headers)

    async def _fetch_matrix(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch DXCC matrix and compute stats."""
        params = {
            "call": self._callsign,
            "api": self._api_key,
            "email": self._email,
            "password": self._app_password,
            "mode": "0",
            "date": "0",
            "sat": "0",
        }
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_MATRIX_ENDPOINT}"
        async with session.get(url, params=params, headers=headers) as resp:
            resp.raise_for_status()
            matrix = await resp.json(content_type=None)

        self._data.dxcc_matrix = matrix

        # Compute stats from matrix
        # ClubLog status values: 1=confirmed, 2=worked (not confirmed), 3=verified (LoTW)
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

        self._data.dxcc_worked_total = len(worked)
        self._data.dxcc_confirmed_total = len(confirmed)
        self._data.dxcc_verified_total = len(verified)

    async def _fetch_watch(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch watch/monitor data."""
        params = {"call": self._callsign, "api": self._api_key}
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_WATCH_ENDPOINT}"
        async with session.get(url, params=params, headers=headers) as resp:
            resp.raise_for_status()
            self._data.watch = await resp.json(content_type=None)

    async def _fetch_most_wanted(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch most wanted list (no auth required)."""
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_MOST_WANTED_ENDPOINT}"
        async with session.get(url, params={"api": "1"}, headers=headers) as resp:
            resp.raise_for_status()
            self._data.most_wanted = await resp.json(content_type=None)

    async def _fetch_expeditions(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch active expeditions (no auth required)."""
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_EXPEDITIONS_ENDPOINT}"
        async with session.get(url, params={"api": "1"}, headers=headers) as resp:
            resp.raise_for_status()
            self._data.expeditions = await resp.json(content_type=None)

    async def _fetch_livestreams(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch active livestreams (no auth required)."""
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_LIVESTREAMS_ENDPOINT}"
        async with session.get(url, params={"api": "1"}, headers=headers) as resp:
            resp.raise_for_status()
            self._data.livestreams = await resp.json(content_type=None)

    async def _fetch_activity(self, session: Any, headers: dict[str, str]) -> None:
        """Fetch band activity data (lastyear=1 required to avoid timeout)."""
        params = {
            "call": self._callsign,
            "api": self._api_key,
            "lastyear": "1",
        }
        url = f"{CLUBLOG_API_BASE}{CLUBLOG_ACTIVITY_ENDPOINT}"
        async with session.get(url, params=params, headers=headers) as resp:
            resp.raise_for_status()
            self._data.activity = await resp.json(content_type=None)
