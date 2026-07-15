"""Manual submission button for WaterGuru to PoolMath."""

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
    """Set up the manual-submit button."""
    async_add_entities(
        [SubmitNowButton(entry, entry.runtime_data.manager)]
    )


class SubmitNowButton(WaterGuruPoolMathEntity, ButtonEntity):
    """Submit current WaterGuru values immediately."""

    _attr_name = "Submit now"
    _attr_icon = "mdi:cloud-upload-outline"

    def __init__(self, entry, manager) -> None:
        super().__init__(entry, manager)
        self._attr_unique_id = f"{entry.entry_id}_submit_now"

    async def async_press(self) -> None:
        """Submit even if the reading matches the previous signature."""
        await self._manager.async_submit(force=True)
