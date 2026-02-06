"""Binary sensor platform for ClubLog HA Bridge."""

from __future__ import annotations

import time
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_CALLSIGN, DOMAIN, VERSION
from .coordinator import ClubLogCoordinator

# Consider API "recently succeeded" if any endpoint succeeded in the last 2 hours
_STALE_THRESHOLD = 7200


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ClubLog binary sensor entities."""
    coordinator: ClubLogCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ClubLogApiStatusSensor(coordinator)])


class ClubLogApiStatusSensor(CoordinatorEntity[ClubLogCoordinator], BinarySensorEntity):
    """Binary sensor indicating ClubLog API connectivity."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "api_status"
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: ClubLogCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_api_status"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group under the same device as sensors."""
        callsign = self.coordinator.entry.data[CONF_CALLSIGN]
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=f"ClubLog ({callsign})",
            manufacturer="ClubLog",
            model="HA Bridge",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://clublog.org",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if at least one endpoint succeeded recently."""
        if self.coordinator.data is None:
            return None
        fetches = self.coordinator.data.last_successful_fetch
        if not fetches:
            return False
        now = time.time()
        return any(now - ts < _STALE_THRESHOLD for ts in fetches.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return per-endpoint status details."""
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data
        attrs: dict[str, Any] = {}
        for endpoint, ts in data.last_successful_fetch.items():
            attrs[f"{endpoint}_last_success"] = ts
        for endpoint, count in data.consecutive_errors.items():
            if count > 0:
                attrs[f"{endpoint}_errors"] = count
        for endpoint, err in data.last_error.items():
            attrs[f"{endpoint}_last_error"] = err
        return attrs or None
