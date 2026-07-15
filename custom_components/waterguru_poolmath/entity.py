"""Shared entity base for WaterGuru to PoolMath."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import WaterGuruPoolMathConfigEntry
from .const import DOMAIN
from .manager import WaterGuruPoolMathManager


class WaterGuruPoolMathEntity(Entity):
    """Base entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: WaterGuruPoolMathConfigEntry,
        manager: WaterGuruPoolMathManager,
    ) -> None:
        self._entry = entry
        self._manager = manager
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WaterGuru to PoolMath",
            manufacturer="Custom integration",
            model="PoolMath synchronization bridge",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager updates."""
        self.async_on_remove(
            self._manager.async_add_listener(self.async_write_ha_state)
        )
