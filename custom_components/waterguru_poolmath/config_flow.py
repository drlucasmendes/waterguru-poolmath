"""Config flow for WaterGuru to PoolMath."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    PoolMathAuthError,
    PoolMathClient,
    PoolMathError,
    PoolMathNoPoolsError,
    PoolMathPool,
)
from .const import (
    AUTH_METHOD_BASIC,
    AUTH_METHOD_LOGIN,
    CONF_AUTH_METHOD,
    CONF_AUTHORIZATION,
    CONF_BOR_ENTITY,
    CONF_CC_ENTITY,
    CONF_CH_ENTITY,
    CONF_COPPER_ENTITY,
    CONF_CSI_ENTITY,
    CONF_CYA_ENTITY,
    CONF_EMAIL,
    CONF_FC_ENTITY,
    CONF_IRON_ENTITY,
    CONF_MEASUREMENT_TIME_ENTITY,
    CONF_PASSWORD,
    CONF_PH_ENTITY,
    CONF_PHOSPHATE_ENTITY,
    CONF_POOL_ID,
    CONF_POOL_NAME,
    CONF_SALT_ENTITY,
    CONF_TA_ENTITY,
    CONF_TDS_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TOTAL_HARDNESS_ENTITY,
    CONF_USER_ID,
    DEFAULT_AUTO_SUBMIT,
    DEFAULT_MAX_READING_AGE_HOURS,
    DEFAULT_SUBMIT_TIME,
    DOMAIN,
    OPT_AUTO_SUBMIT,
    OPT_MAX_READING_AGE_HOURS,
    OPT_SUBMIT_TIME,
    OPT_TIME_ZONE,
)


def _entity_selector() -> selector.EntitySelector:
    """Return a sensor entity selector."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )


class WaterGuruPoolMathConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle WaterGuru to PoolMath setup."""

    VERSION = 2
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._setup_data: dict[str, Any] = {}
        self._setup_options: dict[str, Any] = {}
        self._pools: list[PoolMathPool] = []
        self._default_pool_id: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None
        self._detected_entities: dict[str, str] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose authentication method."""
        if user_input is not None:
            if user_input[CONF_AUTH_METHOD] == AUTH_METHOD_LOGIN:
                return await self.async_step_login()
            return await self.async_step_basic()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AUTH_METHOD,
                        default=AUTH_METHOD_LOGIN,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": AUTH_METHOD_LOGIN,
                                    "label": "PoolMath username/email and password (recommended)",
                                },
                                {
                                    "value": AUTH_METHOD_BASIC,
                                    "label": "Existing Basic authorization (advanced)",
                                },
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )

    async def async_step_login(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Authenticate with PoolMath username/email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = PoolMathClient(async_get_clientsession(self.hass))
            try:
                login = await client.async_login(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
                pools = await client.async_get_pools(login.authorization)
            except PoolMathAuthError:
                errors["base"] = "invalid_auth"
            except PoolMathNoPoolsError:
                errors["base"] = "no_pools"
            except PoolMathError:
                errors["base"] = "cannot_connect"
            else:
                self._setup_data = {
                    CONF_AUTH_METHOD: AUTH_METHOD_LOGIN,
                    CONF_AUTHORIZATION: login.authorization,
                    CONF_USER_ID: login.user_id,
                }
                self._pools = pools
                self._default_pool_id = login.default_pool_id
                return await self.async_step_pool()

        return self.async_show_form(
            step_id="login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        )
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_basic(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Use an existing Basic authorization header."""
        errors: dict[str, str] = {}

        if user_input is not None:
            authorization = user_input[CONF_AUTHORIZATION].strip()
            if not authorization.lower().startswith("basic "):
                errors[CONF_AUTHORIZATION] = "authorization_format"
            else:
                client = PoolMathClient(async_get_clientsession(self.hass))
                try:
                    pools = await client.async_get_pools(authorization)
                except PoolMathAuthError:
                    errors["base"] = "invalid_auth"
                except PoolMathNoPoolsError:
                    errors["base"] = "no_pools"
                except PoolMathError:
                    errors["base"] = "cannot_connect"
                else:
                    self._setup_data = {
                        CONF_AUTH_METHOD: AUTH_METHOD_BASIC,
                        CONF_AUTHORIZATION: authorization,
                    }
                    self._pools = pools
                    return await self.async_step_pool()

        return self.async_show_form(
            step_id="basic",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AUTHORIZATION): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_pool(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select the destination PoolMath pool."""
        if user_input is not None:
            pool_id = user_input[CONF_POOL_ID]
            selected = next(
                pool for pool in self._pools if pool.pool_id == pool_id
            )
            self._setup_data.update(
                {
                    CONF_POOL_ID: selected.pool_id,
                    CONF_POOL_NAME: selected.name,
                }
            )
            await self.async_set_unique_id(selected.pool_id)
            self._abort_if_unique_id_configured()
            self._detected_entities = self._detect_waterguru_entities(
                selected.name
            )
            return await self.async_step_confirm_sensors()

        options = {
            pool.pool_id: pool.display_name
            for pool in self._pools
        }
        default = (
            self._default_pool_id
            if self._default_pool_id in options
            else self._pools[0].pool_id
        )
        return self.async_show_form(
            step_id="pool",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POOL_ID, default=default): vol.In(options)
                }
            ),
        )

    def _detect_waterguru_entities(self, pool_name: str) -> dict[str, str]:
        """Detect and map entities supplied by the WaterGuru integration."""
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)

        by_device: dict[str | None, list[er.RegistryEntry]] = defaultdict(list)
        for entry in entity_registry.entities.values():
            if entry.platform != "waterguru" or entry.domain != "sensor":
                continue
            if entry.disabled:
                continue
            by_device[entry.device_id].append(entry)

        if not by_device:
            return {}

        pool_words = {
            word for word in pool_name.lower().replace("_", " ").split() if word
        }

        def device_score(item: tuple[str | None, list[er.RegistryEntry]]) -> int:
            device_id, entries = item
            text_parts = [entry.entity_id for entry in entries]
            if device_id:
                device = device_registry.async_get(device_id)
                if device:
                    text_parts.extend(
                        value
                        for value in (
                            device.name,
                            device.name_by_user,
                            device.model,
                            device.manufacturer,
                        )
                        if value
                    )
            text = " ".join(text_parts).lower()
            score = sum(20 for word in pool_words if word in text)
            score += len(entries)
            return score

        _, entries = max(by_device.items(), key=device_score)

        def searchable_text(entry: er.RegistryEntry) -> str:
            state = self.hass.states.get(entry.entity_id)
            values = [
                entry.entity_id,
                entry.original_name or "",
                entry.translation_key or "",
                entry.unique_id or "",
                state.name if state else "",
            ]
            return " ".join(values).lower().replace("_", " ").replace("-", " ")

        aliases: dict[str, tuple[str, ...]] = {
            CONF_MEASUREMENT_TIME_ENTITY: (
                "last measurement",
                "latest measure time",
                "measurement time",
            ),
            CONF_FC_ENTITY: (
                "free chlorine",
                "freechlorine",
                " fc ",
                "fc ppm",
            ),
            CONF_PH_ENTITY: (
                " ph ",
                "pool ph",
            ),
            CONF_TA_ENTITY: (
                "total alkalinity",
                "alkalinity",
            ),
            CONF_CH_ENTITY: (
                "calcium hardness",
            ),
            CONF_CYA_ENTITY: (
                "cyanuric acid",
                "stabilizer",
                " cya ",
            ),
            CONF_TEMPERATURE_ENTITY: (
                "water temperature",
                "water temp",
            ),
            CONF_CC_ENTITY: (
                "combined chlorine",
            ),
            CONF_SALT_ENTITY: (
                "salt",
            ),
            CONF_BOR_ENTITY: (
                "borate",
                "borates",
            ),
            CONF_TDS_ENTITY: (
                "total dissolved solids",
                " tds ",
            ),
            CONF_CSI_ENTITY: (
                "calcite saturation index",
                " csi ",
            ),
            CONF_TOTAL_HARDNESS_ENTITY: (
                "total hardness",
            ),
            CONF_PHOSPHATE_ENTITY: (
                "phosphate",
                "phosphates",
            ),
            CONF_COPPER_ENTITY: (
                "copper",
            ),
            CONF_IRON_ENTITY: (
                "iron",
            ),
        }

        detected: dict[str, str] = {}
        for config_key, patterns in aliases.items():
            candidates: list[tuple[int, er.RegistryEntry]] = []
            for entry in entries:
                text = f" {searchable_text(entry)} "
                match_score = 0
                for pattern in patterns:
                    normalized = pattern.lower()
                    if normalized in text:
                        match_score = max(match_score, len(normalized))
                if match_score:
                    candidates.append((match_score, entry))
            if candidates:
                detected[config_key] = max(
                    candidates,
                    key=lambda item: item[0],
                )[1].entity_id

        return detected

    @staticmethod
    def _field(
        key: str,
        detected: dict[str, str],
        *,
        required: bool,
    ) -> vol.Marker:
        """Build a required or optional schema marker with a detected default."""
        default = detected.get(key)
        if required:
            if default:
                return vol.Required(key, default=default)
            return vol.Required(key)
        if default:
            return vol.Optional(key, default=default)
        return vol.Optional(key)

    async def async_step_confirm_sensors(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm automatically detected WaterGuru entities."""
        if user_input is not None:
            self._setup_data.update(
                {
                    key: value
                    for key, value in user_input.items()
                    if value
                }
            )
            return await self.async_step_schedule()

        detected = self._detected_entities
        schema = vol.Schema(
            {
                self._field(
                    CONF_MEASUREMENT_TIME_ENTITY,
                    detected,
                    required=True,
                ): _entity_selector(),
                self._field(
                    CONF_FC_ENTITY,
                    detected,
                    required=True,
                ): _entity_selector(),
                self._field(
                    CONF_PH_ENTITY,
                    detected,
                    required=True,
                ): _entity_selector(),
                self._field(
                    CONF_TA_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_CH_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_CYA_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_TEMPERATURE_ENTITY,
                    detected,
                    required=True,
                ): _entity_selector(),
                self._field(
                    CONF_CC_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_SALT_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_BOR_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_TDS_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_CSI_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_TOTAL_HARDNESS_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_PHOSPHATE_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_COPPER_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
                self._field(
                    CONF_IRON_ENTITY,
                    detected,
                    required=False,
                ): _entity_selector(),
            }
        )
        return self.async_show_form(
            step_id="confirm_sensors",
            data_schema=schema,
            description_placeholders={
                "detected_count": str(len(detected)),
            },
        )

    async def async_step_schedule(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure the initial daily schedule."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                ZoneInfo(user_input[OPT_TIME_ZONE])
            except ZoneInfoNotFoundError:
                errors[OPT_TIME_ZONE] = "invalid_time_zone"
            else:
                self._setup_options = dict(user_input)
                title = self._setup_data.get(
                    CONF_POOL_NAME,
                    "WaterGuru → PoolMath",
                )
                return self.async_create_entry(
                    title=title,
                    data=self._setup_data,
                    options=self._setup_options,
                )

        return self.async_show_form(
            step_id="schedule",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPT_AUTO_SUBMIT,
                        default=DEFAULT_AUTO_SUBMIT,
                    ): bool,
                    vol.Required(
                        OPT_SUBMIT_TIME,
                        default=DEFAULT_SUBMIT_TIME,
                    ): selector.TimeSelector(),
                    vol.Required(
                        OPT_TIME_ZONE,
                        default=self.hass.config.time_zone,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        )
                    ),
                    vol.Required(
                        OPT_MAX_READING_AGE_HOURS,
                        default=DEFAULT_MAX_READING_AGE_HOURS,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=8760),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_login()

    async def async_step_reauth_login(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Reauthenticate using PoolMath username/email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = PoolMathClient(async_get_clientsession(self.hass))
            try:
                login = await client.async_login(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
                pools = await client.async_get_pools(login.authorization)
            except PoolMathAuthError:
                errors["base"] = "invalid_auth"
            except PoolMathError:
                errors["base"] = "cannot_connect"
            else:
                assert self._reauth_entry is not None
                configured_pool_id = self._reauth_entry.data[CONF_POOL_ID]
                available_pool_ids = {pool.pool_id for pool in pools}
                if configured_pool_id not in available_pool_ids:
                    errors["base"] = "pool_not_found"
                else:
                    return self.async_update_reload_and_abort(
                        self._reauth_entry,
                        data_updates={
                            CONF_AUTH_METHOD: AUTH_METHOD_LOGIN,
                            CONF_AUTHORIZATION: login.authorization,
                            CONF_USER_ID: login.user_id,
                        },
                    )

        return self.async_show_form(
            step_id="reauth_login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        )
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return WaterGuruPoolMathOptionsFlow()


class WaterGuruPoolMathOptionsFlow(config_entries.OptionsFlow):
    """Handle schedule options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage integration options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                ZoneInfo(user_input[OPT_TIME_ZONE])
            except ZoneInfoNotFoundError:
                errors[OPT_TIME_ZONE] = "invalid_time_zone"
            else:
                return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPT_AUTO_SUBMIT,
                        default=options.get(
                            OPT_AUTO_SUBMIT,
                            DEFAULT_AUTO_SUBMIT,
                        ),
                    ): bool,
                    vol.Required(
                        OPT_SUBMIT_TIME,
                        default=options.get(
                            OPT_SUBMIT_TIME,
                            DEFAULT_SUBMIT_TIME,
                        ),
                    ): selector.TimeSelector(),
                    vol.Required(
                        OPT_TIME_ZONE,
                        default=options.get(
                            OPT_TIME_ZONE,
                            self.hass.config.time_zone,
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        )
                    ),
                    vol.Required(
                        OPT_MAX_READING_AGE_HOURS,
                        default=options.get(
                            OPT_MAX_READING_AGE_HOURS,
                            DEFAULT_MAX_READING_AGE_HOURS,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=8760),
                    ),
                }
            ),
            errors=errors,
        )
