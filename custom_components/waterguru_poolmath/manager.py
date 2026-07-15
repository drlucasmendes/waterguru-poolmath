"""Submission manager for WaterGuru to PoolMath."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import TemperatureConverter

from .api import PoolMathAuthError, PoolMathClient, PoolMathError
from .const import (
    ATTR_LAST_ERROR,
    ATTR_LAST_LOG_ID,
    ATTR_LAST_SIGNATURE,
    ATTR_LAST_UNMAPPED_VALUES,
    ATTR_LAST_VALUES,
    CONF_FC_ENTITY,
    CONF_MEASUREMENT_TIME_ENTITY,
    CONF_PH_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    DEFAULT_AUTO_SUBMIT,
    DEFAULT_MAX_READING_AGE_HOURS,
    DEFAULT_SUBMIT_TIME,
    OPT_AUTO_SUBMIT,
    OPT_MAX_READING_AGE_HOURS,
    OPT_SUBMIT_TIME,
    OPT_TIME_ZONE,
    POOLMATH_OPTIONAL_ENTITY_FIELDS,
    STATUS_AUTH_ERROR,
    STATUS_DUPLICATE,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_INVALID,
    STATUS_SUBMITTING,
    STATUS_SUCCESS,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    UNMAPPED_WATERGURU_ENTITY_FIELDS,
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
    last_measurement_timestamp: str | None = None
    last_values: dict[str, float] = field(default_factory=dict)
    last_unmapped_values: dict[str, float] = field(default_factory=dict)


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
        self._unsub_schedule: Callable[[], None] | None = None
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
            last_measurement_timestamp=saved.get("last_measurement_timestamp"),
            last_values=saved.get("last_values", {}),
            last_unmapped_values=saved.get("last_unmapped_values", {}),
        )
        self._schedule_next()

    @callback
    def async_shutdown(self) -> None:
        """Cancel the active schedule."""
        if self._unsub_schedule is not None:
            self._unsub_schedule()
            self._unsub_schedule = None

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
                "last_measurement_timestamp": self.state.last_measurement_timestamp,
                "last_values": self.state.last_values,
                "last_unmapped_values": self.state.last_unmapped_values,
            }
        )
        self._notify()

    def _selected_zone(self) -> ZoneInfo:
        zone_name = self.entry.options.get(OPT_TIME_ZONE, self.hass.config.time_zone)
        try:
            return ZoneInfo(zone_name)
        except ZoneInfoNotFoundError:
            _LOGGER.error(
                "Invalid time zone %s; using Home Assistant time zone %s",
                zone_name,
                self.hass.config.time_zone,
            )
            return ZoneInfo(self.hass.config.time_zone)

    def _next_run_utc(self) -> datetime:
        time_text = self.entry.options.get(OPT_SUBMIT_TIME, DEFAULT_SUBMIT_TIME)
        try:
            hour, minute, second = (int(part) for part in time_text.split(":"))
        except (TypeError, ValueError):
            _LOGGER.error("Invalid submission time %s; using %s", time_text, DEFAULT_SUBMIT_TIME)
            hour, minute, second = (10, 30, 0)

        zone = self._selected_zone()
        now_local = dt_util.utcnow().astimezone(zone)
        candidate = now_local.replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=0,
        )
        if candidate <= now_local:
            candidate += timedelta(days=1)
        return candidate.astimezone(dt_util.UTC)

    @callback
    def _schedule_next(self) -> None:
        if self._unsub_schedule is not None:
            self._unsub_schedule()
            self._unsub_schedule = None

        if not self.entry.options.get(OPT_AUTO_SUBMIT, DEFAULT_AUTO_SUBMIT):
            return

        async def scheduled_submission(now: datetime) -> None:
            self._unsub_schedule = None
            await self.async_submit(force=False)
            self._schedule_next()

        self._unsub_schedule = async_track_point_in_utc_time(
            self.hass,
            scheduled_submission,
            self._next_run_utc(),
        )

    def _read_number(
        self,
        entity_id: str,
        label: str,
    ) -> tuple[float, datetime | None, str | None]:
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


    def _read_measurement_timestamp(self) -> datetime:
        """Read the actual WaterGuru test timestamp."""
        entity_id = self.entry.data.get(CONF_MEASUREMENT_TIME_ENTITY)
        if not entity_id:
            raise ValueError(
                "WaterGuru last-measurement timestamp entity is not configured"
            )

        state = self.hass.states.get(entity_id)
        if state is None:
            raise ValueError(
                f"WaterGuru measurement-time entity {entity_id} does not exist"
            )
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, "", None):
            raise ValueError(
                f"WaterGuru measurement-time entity {entity_id} is {state.state}"
            )

        parsed = dt_util.parse_datetime(state.state)
        if parsed is None:
            raise ValueError(
                f"WaterGuru measurement-time entity {entity_id} is not a valid timestamp"
            )
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_util.UTC)
        return parsed.astimezone(dt_util.UTC)

    def _read_optional_entities(
        self,
        mapping: dict[str, str],
    ) -> tuple[dict[str, float], list[datetime]]:
        values: dict[str, float] = {}
        timestamps: list[datetime] = []
        for payload_name, config_key in mapping.items():
            entity_id = self.entry.data.get(config_key)
            if not entity_id:
                continue
            value, updated, _ = self._read_number(entity_id, payload_name)
            values[payload_name] = round(value, 3)
            if updated:
                timestamps.append(updated)
        return values, timestamps

    @staticmethod
    def _validate_ranges(values: dict[str, float]) -> None:
        checks = {
            "fc": (0, 40),
            "cc": (0, 20),
            "cya": (0, 300),
            "ch": (0, 2000),
            "ph": (6.0, 9.0),
            "ta": (0, 500),
            "salt": (0, 10000),
            "bor": (0, 200),
            "tds": (0, 20000),
            "csi": (-3, 3),
            "water_temp_f": (35, 110),
        }
        for key, value in values.items():
            if key not in checks:
                continue
            low, high = checks[key]
            if not low <= value <= high:
                raise ValueError(
                    f"{key} value {value} is outside the permitted range {low}–{high}"
                )

    async def async_submit(self, *, force: bool) -> bool:
        """Submit current WaterGuru values. Return True on success."""
        self.state.status = STATUS_SUBMITTING
        self.state.last_attempt = dt_util.utcnow().isoformat()
        self.state.last_error = None
        self._notify()

        try:
            fc, _, _ = self._read_number(
                self.entry.data[CONF_FC_ENTITY], "Free chlorine"
            )
            ph, _, _ = self._read_number(
                self.entry.data[CONF_PH_ENTITY], "pH"
            )
            temp, _, temp_unit = self._read_number(
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

            optional_values, _ = self._read_optional_entities(
                POOLMATH_OPTIONAL_ENTITY_FIELDS
            )
            unmapped_values, _ = self._read_optional_entities(
                UNMAPPED_WATERGURU_ENTITY_FIELDS
            )

            values = {
                "fc": round(fc, 3),
                "ph": round(ph, 3),
                "water_temp_f": round(temp, 2),
                **optional_values,
            }
            self._validate_ranges(values)

            measurement_time = self._read_measurement_timestamp()
            max_age_hours = self.entry.options.get(
                OPT_MAX_READING_AGE_HOURS, DEFAULT_MAX_READING_AGE_HOURS
            )
            age_hours = (
                dt_util.utcnow() - measurement_time
            ).total_seconds() / 3600
            if age_hours > max_age_hours:
                raise ValueError(
                    f"The WaterGuru test is {age_hours:.1f} hours old "
                    f"(limit: {max_age_hours} hours)"
                )
            if age_hours < -0.25:
                raise ValueError(
                    "The WaterGuru test timestamp is unexpectedly in the future"
                )

            signature_values = {**values, **unmapped_values}
            signature_body = "|".join(
                f"{key}={signature_values[key]}" for key in sorted(signature_values)
            )
            signature = f"{measurement_time.isoformat()}|{signature_body}"

            if not force and signature == self.state.last_signature:
                self.state.status = STATUS_DUPLICATE
                self.state.last_error = None
                await self._async_save()
                return False

            result = await self.client.async_submit_testlog(
                values=values,
                log_timestamp=measurement_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

            self.state.status = STATUS_SUCCESS
            self.state.last_submission = dt_util.utcnow().isoformat()
            self.state.last_http_status = result.status
            self.state.last_log_id = result.log_id
            self.state.last_signature = signature
            self.state.last_measurement_timestamp = measurement_time.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            self.state.last_values = values
            self.state.last_unmapped_values = unmapped_values
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


    async def async_resubmit_last_test(self) -> bool:
        """Force-upload the last successfully captured test values again."""
        self.state.status = STATUS_SUBMITTING
        self.state.last_attempt = dt_util.utcnow().isoformat()
        self.state.last_error = None
        self._notify()

        if not self.state.last_values or not self.state.last_measurement_timestamp:
            self.state.status = STATUS_INVALID
            self.state.last_error = (
                "No previous successful WaterGuru test is available to resubmit"
            )
            await self._async_save()
            return False

        try:
            result = await self.client.async_submit_testlog(
                values=dict(self.state.last_values),
                log_timestamp=self.state.last_measurement_timestamp,
            )
            self.state.status = STATUS_SUCCESS
            self.state.last_submission = dt_util.utcnow().isoformat()
            self.state.last_http_status = result.status
            self.state.last_log_id = result.log_id
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
        except PoolMathError as err:
            self.state.status = STATUS_ERROR
            self.state.last_error = str(err)
            await self._async_save()
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected last-test resubmission error")
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
            ATTR_LAST_UNMAPPED_VALUES: self.state.last_unmapped_values,
            ATTR_LAST_SIGNATURE: self.state.last_signature,
            "last_measurement_timestamp": self.state.last_measurement_timestamp,
            "last_attempt": self.state.last_attempt,
            "last_http_status": self.state.last_http_status,
            "automatic_submission_enabled": self.entry.options.get(
                OPT_AUTO_SUBMIT, DEFAULT_AUTO_SUBMIT
            ),
            "submission_time": self.entry.options.get(
                OPT_SUBMIT_TIME, DEFAULT_SUBMIT_TIME
            ),
            "submission_time_zone": self.entry.options.get(
                OPT_TIME_ZONE, self.hass.config.time_zone
            ),
            "next_scheduled_run_utc": (
                self._next_run_utc().isoformat()
                if self.entry.options.get(OPT_AUTO_SUBMIT, DEFAULT_AUTO_SUBMIT)
                else None
            ),
        }
