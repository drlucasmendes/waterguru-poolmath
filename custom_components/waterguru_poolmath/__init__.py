"""WaterGuru to PoolMath integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PoolMathClient
from .const import CONF_AUTHORIZATION, CONF_POOL_ID, PLATFORMS
from .manager import WaterGuruPoolMathManager


@dataclass(slots=True)
class RuntimeData:
    """Runtime data for a config entry."""

    manager: WaterGuruPoolMathManager


type WaterGuruPoolMathConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
) -> bool:
    """Set up WaterGuru to PoolMath from a config entry."""
    client = PoolMathClient(
        async_get_clientsession(hass),
        entry.data[CONF_AUTHORIZATION],
        entry.data[CONF_POOL_ID],
    )
    manager = WaterGuruPoolMathManager(hass, entry, client)
    entry.runtime_data = RuntimeData(manager=manager)

    await manager.async_initialize()
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
