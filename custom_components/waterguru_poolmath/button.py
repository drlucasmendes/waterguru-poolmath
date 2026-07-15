"""Manual submission buttons for WaterGuru to PoolMath."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WaterGuruPoolMathConfigEntry
from .entity import WaterGuruPoolMathEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up manual submission buttons."""
    manager = entry.runtime_data.manager
    async_add_entities(
        [
            SubmitNowButton(entry, manager),
            ResubmitLastTestButton(entry, manager),
        ]
    )


class SubmitNowButton(WaterGuruPoolMathEntity, ButtonEntity):
    """Read the currently selected entities and submit them immediately."""

    _attr_name = "Submit current values"
    _attr_icon = "mdi:cloud-upload-outline"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_submit_now"

    async def async_press(self) -> None:
        """Submit current values even if their signature matches the previous one."""
        await self._manager.async_submit(force=True)


class ResubmitLastTestButton(WaterGuruPoolMathEntity, ButtonEntity):
    """Force-resubmit the exact last successfully captured test."""

    _attr_name = "Force resync last test"
    _attr_icon = "mdi:sync-alert"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_resubmit_last_test"

    async def async_press(self) -> None:
        """Upload the persisted last test again with its original test timestamp."""
        await self._manager.async_resubmit_last_test()
