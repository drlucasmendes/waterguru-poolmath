"""Config flow for WaterGuru to PoolMath."""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AUTHORIZATION,
    CONF_BOR_ENTITY,
    CONF_CC_ENTITY,
    CONF_CH_ENTITY,
    CONF_COPPER_ENTITY,
    CONF_CSI_ENTITY,
    CONF_CYA_ENTITY,
    CONF_FC_ENTITY,
    CONF_IRON_ENTITY,
    CONF_PH_ENTITY,
    CONF_PHOSPHATE_ENTITY,
    CONF_POOL_ID,
    CONF_SALT_ENTITY,
    CONF_TA_ENTITY,
    CONF_TDS_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_TOTAL_HARDNESS_ENTITY,
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
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))


class WaterGuruPoolMathConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            authorization = user_input[CONF_AUTHORIZATION].strip()
            pool_id = user_input[CONF_POOL_ID].strip()

            if not authorization.lower().startswith("basic "):
                errors[CONF_AUTHORIZATION] = "authorization_format"
            elif len(pool_id) < 20:
                errors[CONF_POOL_ID] = "invalid_pool_id"
            else:
                await self.async_set_unique_id(pool_id)
                self._abort_if_unique_id_configured()
                user_input[CONF_AUTHORIZATION] = authorization
                user_input[CONF_POOL_ID] = pool_id
                return self.async_create_entry(
                    title="WaterGuru → PoolMath",
                    data=user_input,
                    options={
                        OPT_AUTO_SUBMIT: DEFAULT_AUTO_SUBMIT,
                        OPT_SUBMIT_TIME: DEFAULT_SUBMIT_TIME,
                        OPT_TIME_ZONE: self.hass.config.time_zone,
                        OPT_MAX_READING_AGE_HOURS: DEFAULT_MAX_READING_AGE_HOURS,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_AUTHORIZATION): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_POOL_ID): str,
                vol.Required(CONF_FC_ENTITY): _entity_selector(),
                vol.Required(CONF_PH_ENTITY): _entity_selector(),
                vol.Required(CONF_TEMPERATURE_ENTITY): _entity_selector(),
                vol.Optional(CONF_CC_ENTITY): _entity_selector(),
                vol.Optional(CONF_CYA_ENTITY): _entity_selector(),
                vol.Optional(CONF_CH_ENTITY): _entity_selector(),
                vol.Optional(CONF_TA_ENTITY): _entity_selector(),
                vol.Optional(CONF_SALT_ENTITY): _entity_selector(),
                vol.Optional(CONF_BOR_ENTITY): _entity_selector(),
                vol.Optional(CONF_TDS_ENTITY): _entity_selector(),
                vol.Optional(CONF_CSI_ENTITY): _entity_selector(),
                vol.Optional(CONF_TOTAL_HARDNESS_ENTITY): _entity_selector(),
                vol.Optional(CONF_PHOSPHATE_ENTITY): _entity_selector(),
                vol.Optional(CONF_COPPER_ENTITY): _entity_selector(),
                vol.Optional(CONF_IRON_ENTITY): _entity_selector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Accept a replacement authorization header."""
        errors: dict[str, str] = {}
        if user_input is not None:
            authorization = user_input[CONF_AUTHORIZATION].strip()
            if not authorization.lower().startswith("basic "):
                errors[CONF_AUTHORIZATION] = "authorization_format"
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data_updates={CONF_AUTHORIZATION: authorization},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return WaterGuruPoolMathOptionsFlow()


class WaterGuruPoolMathOptionsFlow(config_entries.OptionsFlow):
    """Handle integration options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                ZoneInfo(user_input[OPT_TIME_ZONE])
            except ZoneInfoNotFoundError:
                errors[OPT_TIME_ZONE] = "invalid_time_zone"
            else:
                return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        default_zone = options.get(OPT_TIME_ZONE, self.hass.config.time_zone)
        zone_options = sorted(available_timezones())
        schema = vol.Schema(
            {
                vol.Required(
                    OPT_AUTO_SUBMIT,
                    default=options.get(OPT_AUTO_SUBMIT, DEFAULT_AUTO_SUBMIT),
                ): bool,
                vol.Required(
                    OPT_SUBMIT_TIME,
                    default=options.get(OPT_SUBMIT_TIME, DEFAULT_SUBMIT_TIME),
                ): selector.TimeSelector(),
                vol.Required(
                    OPT_TIME_ZONE,
                    default=default_zone,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=zone_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                ),
                vol.Required(
                    OPT_MAX_READING_AGE_HOURS,
                    default=options.get(
                        OPT_MAX_READING_AGE_HOURS,
                        DEFAULT_MAX_READING_AGE_HOURS,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=8760)),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
