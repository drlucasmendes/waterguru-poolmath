"""Status sensors for WaterGuru to PoolMath."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WaterGuruPoolMathConfigEntry
from .entity import WaterGuruPoolMathEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up status sensors."""
    manager = entry.runtime_data.manager
    async_add_entities(
        [
            SubmissionStatusSensor(entry, manager),
            LastSubmissionSensor(entry, manager),
            LastHttpStatusSensor(entry, manager),
        ]
    )


class SubmissionStatusSensor(WaterGuruPoolMathEntity, SensorEntity):
    """Current synchronization status."""

    _attr_name = "Status"
    _attr_icon = "mdi:pool"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str:
        return self._manager.state.status

    @property
    def extra_state_attributes(self):
        return self._manager.extra_attributes


class LastSubmissionSensor(WaterGuruPoolMathEntity, SensorEntity):
    """Time of the last successful submission."""

    _attr_name = "Last submission"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_last_submission"

    @property
    def native_value(self) -> datetime | None:
        value = self._manager.state.last_submission
        return datetime.fromisoformat(value) if value else None


class LastHttpStatusSensor(WaterGuruPoolMathEntity, SensorEntity):
    """Last HTTP status returned by PoolMath."""

    _attr_name = "Last HTTP status"
    _attr_icon = "mdi:web-check"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_last_http_status"

    @property
    def native_value(self) -> int | None:
        return self._manager.state.last_http_status
