"""Diagnostics for WaterGuru to PoolMath."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import WaterGuruPoolMathConfigEntry
from .const import CONF_AUTHORIZATION, CONF_EMAIL, CONF_PASSWORD


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: WaterGuruPoolMathConfigEntry,
) -> dict[str, Any]:
    """Return redacted diagnostics."""
    return {
        "entry": async_redact_data(dict(entry.data), {CONF_AUTHORIZATION, CONF_EMAIL, CONF_PASSWORD}),
        "options": dict(entry.options),
        "measurement_time_entity": entry.data.get("measurement_time_entity"),
        "resolved_measurement_time_entity": entry.runtime_data.manager._find_last_measurement_entity(),
        "runtime": {
            "status": entry.runtime_data.manager.state.status,
            "last_submission": entry.runtime_data.manager.state.last_submission,
            "last_attempt": entry.runtime_data.manager.state.last_attempt,
            "last_http_status": entry.runtime_data.manager.state.last_http_status,
            "last_error": entry.runtime_data.manager.state.last_error,
            "last_log_id": entry.runtime_data.manager.state.last_log_id,
            "last_measurement_timestamp": entry.runtime_data.manager.state.last_measurement_timestamp,
            "last_values": entry.runtime_data.manager.state.last_values,
            "last_unmapped_values": entry.runtime_data.manager.state.last_unmapped_values,
        },
    }
