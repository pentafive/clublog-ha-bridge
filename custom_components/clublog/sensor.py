"""Sensor platform for ClubLog HA Bridge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_CALLSIGN, DOMAIN, VERSION
from .coordinator import ClubLogCoordinator, ClubLogData


@dataclass(frozen=True, kw_only=True)
class ClubLogSensorEntityDescription(SensorEntityDescription):
    """Describe a ClubLog sensor entity."""

    value_fn: Callable[[ClubLogData], Any] = lambda _: None
    attr_fn: Callable[[ClubLogData], dict[str, Any] | None] = lambda _: None


SENSOR_DESCRIPTIONS: tuple[ClubLogSensorEntityDescription, ...] = (
    # --- DXCC Matrix ---
    ClubLogSensorEntityDescription(
        key="dxcc_worked_total",
        translation_key="dxcc_worked_total",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="entities",
        icon="mdi:earth",
        value_fn=lambda data: data.dxcc_worked_total,
    ),
    ClubLogSensorEntityDescription(
        key="dxcc_confirmed_total",
        translation_key="dxcc_confirmed_total",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="entities",
        icon="mdi:earth-plus",
        value_fn=lambda data: data.dxcc_confirmed_total,
    ),
    ClubLogSensorEntityDescription(
        key="dxcc_verified_total",
        translation_key="dxcc_verified_total",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="entities",
        icon="mdi:earth-arrow-right",
        value_fn=lambda data: data.dxcc_verified_total,
    ),
    # --- Expeditions ---
    ClubLogSensorEntityDescription(
        key="active_expeditions",
        translation_key="active_expeditions",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="expeditions",
        icon="mdi:airplane",
        value_fn=lambda data: len(data.expeditions),
        attr_fn=lambda data: {
            "expeditions": [
                {"call": e[0], "date": e[1], "qso_count": e[2]}
                for e in data.expeditions[:20]
            ]
            if data.expeditions
            else []
        },
    ),
    # --- Most Wanted ---
    ClubLogSensorEntityDescription(
        key="most_wanted_count",
        translation_key="most_wanted_count",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="entities",
        icon="mdi:star",
        value_fn=lambda data: len(data.most_wanted),
        attr_fn=lambda data: {
            "top_10": dict(list(data.most_wanted.items())[:10])
        }
        if data.most_wanted
        else None,
    ),
    # --- Watch Data ---
    ClubLogSensorEntityDescription(
        key="watch_total_qsos",
        translation_key="watch_total_qsos",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="QSOs",
        icon="mdi:radio-tower",
        value_fn=lambda data: (
            data.watch.get("clublog_info", {}).get("total_qsos")
            if data.watch
            else None
        ),
    ),
    ClubLogSensorEntityDescription(
        key="watch_is_expedition",
        translation_key="watch_is_expedition",
        icon="mdi:airplane-takeoff",
        value_fn=lambda data: (
            "Yes" if data.watch.get("is_expedition") else "No"
        )
        if data.watch
        else None,
    ),
    ClubLogSensorEntityDescription(
        key="watch_has_oqrs",
        translation_key="watch_has_oqrs",
        icon="mdi:email-check",
        value_fn=lambda data: (
            "Yes" if data.watch.get("has_oqrs") else "No"
        )
        if data.watch
        else None,
    ),
    ClubLogSensorEntityDescription(
        key="watch_last_upload",
        translation_key="watch_last_upload",
        icon="mdi:cloud-upload",
        value_fn=lambda data: (
            data.watch.get("clublog_info", {}).get("last_clublog_upload")
            if data.watch
            else None
        ),
    ),
    # --- Livestreams ---
    ClubLogSensorEntityDescription(
        key="active_livestreams",
        translation_key="active_livestreams",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="streams",
        icon="mdi:broadcast",
        value_fn=lambda data: len(data.livestreams),
        attr_fn=lambda data: {
            "livestreams": [
                {"call": s[0], "dxcc": s[1], "url": s[3]}
                for s in data.livestreams[:20]
            ]
            if data.livestreams
            else []
        },
    ),
    # --- Band Activity ---
    ClubLogSensorEntityDescription(
        key="band_activity",
        translation_key="band_activity",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="bands",
        icon="mdi:sine-wave",
        value_fn=lambda data: len(data.activity) if data.activity else 0,
        attr_fn=lambda data: {
            f"band_{band}": sum(hours) if isinstance(hours, list) else hours
            for band, hours in data.activity.items()
        }
        if data.activity
        else None,
    ),
    # --- Diagnostics ---
    ClubLogSensorEntityDescription(
        key="api_consecutive_errors",
        translation_key="api_consecutive_errors",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="errors",
        icon="mdi:alert-circle",
        entity_registry_enabled_default=False,
        value_fn=lambda data: sum(data.consecutive_errors.values()),
        attr_fn=lambda data: {
            f"{ep}_errors": count
            for ep, count in data.consecutive_errors.items()
            if count > 0
        }
        or None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ClubLog sensor entities."""
    coordinator: ClubLogCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ClubLogSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class ClubLogSensor(CoordinatorEntity[ClubLogCoordinator], SensorEntity):
    """Representation of a ClubLog sensor."""

    entity_description: ClubLogSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: ClubLogCoordinator,
        description: ClubLogSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group all sensors under one device."""
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
