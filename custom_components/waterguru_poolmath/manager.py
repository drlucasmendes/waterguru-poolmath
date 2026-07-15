"""Submission manager for WaterGuru to PoolMath."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import TemperatureConverter

from .api import PoolMathAuthError, PoolMathClient, PoolMathError
from .const import (
    ATTR_LAST_ERROR,
    ATTR_LAST_LOG_ID,
    ATTR_LAST_SIGNATURE,
    ATTR_LAST_VALUES,
    CONF_FC_ENTITY,
    CONF_PH_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    DEFAULT_AUTO_SUBMIT,
    DEFAULT_MAX_READING_AGE_HOURS,
    DEFAULT_SUBMIT_TIME,
    OPT_AUTO_SUBMIT,
    OPT_MAX_READING_AGE_HOURS,
    OPT_SUBMIT_TIME,
    STATUS_AUTH_ERROR,
    STATUS_DUPLICATE,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_INVALID,
    STATUS_SUBMITTING,
    STATUS_SUCCESS,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeState:
    """In-memory and persisted integration status."""

    status: str = STATUS_IDLE
    last_submission: str | None = None
    last_attempt: str | None = None
    last_http_status: int | None = None
    last_error: str | None = None
    last_log_id: str | None = None
    last_signature: str | None = None
    last_values: dict[str, float] = field(default_factory=dict)


class WaterGuruPoolMathManager:
    """Read Home Assistant entities and submit a daily PoolMath test log."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: PoolMathClient,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.client = client
        self.state = RuntimeState()
        self._listeners: set[Callable[[], None]] = set()
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry.entry_id}",
        )

    async def async_initialize(self) -> None:
        """Restore state and create the daily scheduler."""
        saved = await self._store.async_load() or {}
        self.state = RuntimeState(
            status=saved.get("status", STATUS_IDLE),
            last_submission=saved.get("last_submission"),
            last_attempt=saved.get("last_attempt"),
            last_http_status=saved.get("last_http_status"),
            last_error=saved.get("last_error"),
            last_log_id=saved.get("last_log_id"),
            last_signature=saved.get("last_signature"),
            last_values=saved.get("last_values", {}),
        )
        self._schedule()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.add(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "status": self.state.status,
                "last_submission": self.state.last_submission,
                "last_attempt": self.state.last_attempt,
                "last_http_status": self.state.last_http_status,
                "last_error": self.state.last_error,
                "last_log_id": self.state.last_log_id,
                "last_signature": self.state.last_signature,
                "last_values": self.state.last_values,
            }
        )
        self._notify()

    def _schedule(self) -> None:
        if not self.entry.options.get(OPT_AUTO_SUBMIT, DEFAULT_AUTO_SUBMIT):
            return

        time_text = self.entry.options.get(OPT_SUBMIT_TIME, DEFAULT_SUBMIT_TIME)
        try:
            hour, minute, second = (int(part) for part in time_text.split(":"))
        except (TypeError, ValueError):
            _LOGGER.error("Invalid submission time %s; using %s", time_text, DEFAULT_SUBMIT_TIME)
            hour, minute, second = (10, 30, 0)

        async def scheduled_submission(now: datetime) -> None:
            await self.async_submit(force=False)

        unsubscribe = async_track_time_change(
            self.hass,
            scheduled_submission,
            hour=hour,
            minute=minute,
            second=second,
        )
        self.entry.async_on_unload(unsubscribe)

    def _read_number(self, entity_id: str, label: str) -> tuple[float, datetime | None, str | None]:
        state = self.hass.states.get(entity_id)
        if state is None:
            raise ValueError(f"{label} entity {entity_id} does not exist")
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, "", None):
            raise ValueError(f"{label} entity {entity_id} is {state.state}")

        try:
            value = float(state.state)
        except (TypeError, ValueError) as err:
            raise ValueError(f"{label} entity {entity_id} is not numeric") from err

        return value, state.last_updated, state.attributes.get("unit_of_measurement")

    @staticmethod
    def _validate_ranges(fc: float, ph: float, temperature_f: float) -> None:
        if not 0 <= fc <= 40:
            raise ValueError(f"Free chlorine {fc} is outside the permitted range 0–40 ppm")
        if not 6.0 <= ph <= 9.0:
            raise ValueError(f"pH {ph} is outside the permitted range 6.0–9.0")
        if not 35 <= temperature_f <= 110:
            raise ValueError(
                f"Water temperature {temperature_f} °F is outside the permitted range 35–110 °F"
            )

    async def async_submit(self, *, force: bool) -> bool:
        """Submit the current WaterGuru values. Return True on success."""
        self.state.status = STATUS_SUBMITTING
        self.state.last_attempt = dt_util.utcnow().isoformat()
        self.state.last_error = None
        self._notify()

        try:
            fc, fc_updated, _ = self._read_number(
                self.entry.data[CONF_FC_ENTITY], "Free chlorine"
            )
            ph, ph_updated, _ = self._read_number(
                self.entry.data[CONF_PH_ENTITY], "pH"
            )
            temp, temp_updated, temp_unit = self._read_number(
                self.entry.data[CONF_TEMPERATURE_ENTITY], "Water temperature"
            )

            if temp_unit == UnitOfTemperature.CELSIUS:
                temp = TemperatureConverter.convert(
                    temp,
                    UnitOfTemperature.CELSIUS,
                    UnitOfTemperature.FAHRENHEIT,
                )
            elif temp_unit not in (None, UnitOfTemperature.FAHRENHEIT):
                raise ValueError(f"Unsupported water-temperature unit: {temp_unit}")

            self._validate_ranges(fc, ph, temp)

            timestamps = [stamp for stamp in (fc_updated, ph_updated, temp_updated) if stamp]
            newest = max(timestamps) if timestamps else dt_util.utcnow()
            oldest = min(timestamps) if timestamps else newest
            max_age_hours = self.entry.options.get(
                OPT_MAX_READING_AGE_HOURS, DEFAULT_MAX_READING_AGE_HOURS
            )
            age_hours = (dt_util.utcnow() - oldest).total_seconds() / 3600
            if age_hours > max_age_hours:
                raise ValueError(
                    f"At least one WaterGuru reading is {age_hours:.1f} hours old "
                    f"(limit: {max_age_hours} hours)"
                )

            values = {
                "fc": round(fc, 3),
                "ph": round(ph, 3),
                "water_temp_f": round(temp, 2),
            }
            signature = (
                f"{newest.astimezone(dt_util.UTC).isoformat()}|"
                f"{values['fc']}|{values['ph']}|{values['water_temp_f']}"
            )

            if not force and signature == self.state.last_signature:
                self.state.status = STATUS_DUPLICATE
                self.state.last_error = None
                await self._async_save()
                return False

            result = await self.client.async_submit_testlog(
                fc=values["fc"],
                ph=values["ph"],
                water_temp_f=values["water_temp_f"],
                log_timestamp=newest.astimezone(dt_util.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

            self.state.status = STATUS_SUCCESS
            self.state.last_submission = dt_util.utcnow().isoformat()
            self.state.last_http_status = result.status
            self.state.last_log_id = result.log_id
            self.state.last_signature = signature
            self.state.last_values = values
            self.state.last_error = None
            await self._async_save()
            return True

        except PoolMathAuthError as err:
            self.state.status = STATUS_AUTH_ERROR
            self.state.last_http_status = 401
            self.state.last_error = str(err)
            await self._async_save()
            self.entry.async_start_reauth(self.hass)
            return False
        except ValueError as err:
            self.state.status = STATUS_INVALID
            self.state.last_error = str(err)
            await self._async_save()
            return False
        except PoolMathError as err:
            self.state.status = STATUS_ERROR
            self.state.last_error = str(err)
            await self._async_save()
            return False
        except Exception as err:  # Defensive boundary around an unofficial API.
            _LOGGER.exception("Unexpected WaterGuru-to-PoolMath submission error")
            self.state.status = STATUS_ERROR
            self.state.last_error = f"Unexpected error: {err}"
            await self._async_save()
            return False

    @property
    def extra_attributes(self) -> dict[str, Any]:
        """Common diagnostic attributes for entities."""
        return {
            ATTR_LAST_ERROR: self.state.last_error,
            ATTR_LAST_LOG_ID: self.state.last_log_id,
            ATTR_LAST_VALUES: self.state.last_values,
            ATTR_LAST_SIGNATURE: self.state.last_signature,
            "last_attempt": self.state.last_attempt,
            "last_http_status": self.state.last_http_status,
        }
