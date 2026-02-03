"""DataUpdateCoordinator for ClubLog HA Bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CLUBLOG_API_BASE,
    CLUBLOG_EXPEDITIONS_ENDPOINT,
    CLUBLOG_MATRIX_ENDPOINT,
    CLUBLOG_MOST_WANTED_ENDPOINT,
    CLUBLOG_WATCH_ENDPOINT,
    CONF_API_KEY,
    CONF_APP_PASSWORD,
    CONF_CALLSIGN,
    CONF_EMAIL,
    DEFAULT_MATRIX_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class ClubLogData:
    """Data class for ClubLog coordinator."""

    # DXCC matrix: {dxcc_id: {band: status}}
    dxcc_matrix: dict[str, dict[str, int]] = field(default_factory=dict)

    # Watch data
    watch: dict[str, Any] = field(default_factory=dict)

    # Most wanted list
    most_wanted: list[dict[str, Any]] = field(default_factory=list)

    # Active expeditions
    expeditions: list[dict[str, Any]] = field(default_factory=list)

    # Computed stats
    dxcc_worked_total: int = 0
    dxcc_confirmed_total: int = 0
    dxcc_verified_total: int = 0


class ClubLogCoordinator(DataUpdateCoordinator[ClubLogData]):
    """Coordinator for ClubLog API polling."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_MATRIX_INTERVAL),
        )
        self.entry = entry
        self._callsign = entry.data[CONF_CALLSIGN]
        self._api_key = entry.data[CONF_API_KEY]
        self._email = entry.data[CONF_EMAIL]
        self._app_password = entry.data[CONF_APP_PASSWORD]

    async def _async_update_data(self) -> ClubLogData:
        """Fetch data from ClubLog API."""
        data = ClubLogData()

        try:
            async with aiohttp.ClientSession() as session:
                # Fetch DXCC matrix
                data.dxcc_matrix = await self._fetch_matrix(session)

                # Compute stats from matrix
                worked = set()
                confirmed = set()
                verified = set()
                for dxcc_id, bands in data.dxcc_matrix.items():
                    for _band, status in bands.items():
                        if status >= 1:
                            confirmed.add(dxcc_id)
                        if status >= 2:
                            worked.add(dxcc_id)
                        if status >= 3:
                            verified.add(dxcc_id)

                data.dxcc_worked_total = len(worked)
                data.dxcc_confirmed_total = len(confirmed)
                data.dxcc_verified_total = len(verified)

                # Fetch most wanted (no auth required)
                data.most_wanted = await self._fetch_most_wanted(session)

                # Fetch expeditions (no auth required)
                data.expeditions = await self._fetch_expeditions(session)

                # Fetch watch data
                data.watch = await self._fetch_watch(session)

        except aiohttp.ClientResponseError as err:
            if err.status == 403:
                _LOGGER.error(
                    "ClubLog API returned 403 - check credentials and rate limits"
                )
            raise UpdateFailed(f"ClubLog API error: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"ClubLog connection error: {err}") from err

        return data

    async def _fetch_matrix(self, session: aiohttp.ClientSession) -> dict:
        """Fetch DXCC matrix."""
        params = {
            "call": self._callsign,
            "api": self._api_key,
            "email": self._email,
            "password": self._app_password,
            "mode": 0,
            "date": 0,
            "sat": 0,
        }
        async with session.get(
            f"{CLUBLOG_API_BASE}{CLUBLOG_MATRIX_ENDPOINT}", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_most_wanted(self, session: aiohttp.ClientSession) -> list:
        """Fetch most wanted list (no auth required)."""
        async with session.get(
            f"{CLUBLOG_API_BASE}{CLUBLOG_MOST_WANTED_ENDPOINT}", params={"api": 1}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_expeditions(self, session: aiohttp.ClientSession) -> list:
        """Fetch active expeditions (no auth required)."""
        async with session.get(
            f"{CLUBLOG_API_BASE}{CLUBLOG_EXPEDITIONS_ENDPOINT}", params={"api": 1}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_watch(self, session: aiohttp.ClientSession) -> dict:
        """Fetch watch/monitor data."""
        params = {
            "callsign": self._callsign,
            "api": self._api_key,
        }
        async with session.get(
            f"{CLUBLOG_API_BASE}{CLUBLOG_WATCH_ENDPOINT}", params=params
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
