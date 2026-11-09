"""Config flow for Grid Connect."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv

from .pytuya_gridconnect import GridConnectCloud, GridConnectError, REGIONS
from .const import (
    CONF_COUNTRY,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    DEFAULT_COUNTRY,
    DEFAULT_REGION,
    DOMAIN,
)


class GridConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Grid Connect config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            cloud = GridConnectCloud(
                country_code=user_input[CONF_COUNTRY],
                region=user_input[CONF_REGION],
            )
            try:
                await self.hass.async_add_executor_job(
                    cloud.login_email,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
            except GridConnectError:
                errors["base"] = "invalid_auth"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_COUNTRY, default=DEFAULT_COUNTRY): cv.string,
                vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(
                    sorted(REGIONS)
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
