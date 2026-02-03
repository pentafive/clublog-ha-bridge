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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClubLogCoordinator, ClubLogData


@dataclass(frozen=True, kw_only=True)
class ClubLogSensorEntityDescription(SensorEntityDescription):
    """Describe a ClubLog sensor entity."""

    value_fn: Callable[[ClubLogData], Any] = lambda _: None


SENSOR_DESCRIPTIONS: tuple[ClubLogSensorEntityDescription, ...] = (
    ClubLogSensorEntityDescription(
        key="dxcc_worked_total",
        translation_key="dxcc_worked_total",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.dxcc_worked_total,
    ),
    ClubLogSensorEntityDescription(
        key="dxcc_confirmed_total",
        translation_key="dxcc_confirmed_total",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.dxcc_confirmed_total,
    ),
    ClubLogSensorEntityDescription(
        key="dxcc_verified_total",
        translation_key="dxcc_verified_total",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.dxcc_verified_total,
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
