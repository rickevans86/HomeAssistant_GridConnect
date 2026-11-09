"""Config flow for Grid Connect."""

from __future__ import annotations

import logging
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

_LOGGER = logging.getLogger(__name__)


class GridConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Grid Connect config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            region = user_input[CONF_REGION]
            try:
                if region == "auto":
                    # Probe every data centre and keep the one that accepts the
                    # login; store the discovered region so later runs skip probing.
                    cloud = await self.hass.async_add_executor_job(
                        lambda: GridConnectCloud.login_autoregion(
                            user_input[CONF_EMAIL],
                            user_input[CONF_PASSWORD],
                            user_input[CONF_COUNTRY],
                        )
                    )
                    user_input[CONF_REGION] = cloud.region
                    _LOGGER.warning(
                        "Grid Connect auto-probe selected region %s", cloud.region
                    )
                else:
                    cloud = GridConnectCloud(
                        country_code=user_input[CONF_COUNTRY], region=region
                    )
                    await self.hass.async_add_executor_job(
                        cloud.login_email,
                        user_input[CONF_EMAIL],
                        user_input[CONF_PASSWORD],
                    )
            except GridConnectError as err:
                # Keep Tuya's real reason visible — it tells us whether this is a
                # signing problem, a region/account mismatch or wrong credentials.
                _LOGGER.error("Grid Connect sign-in failed: %s", err)
                errors["base"] = "invalid_auth"
                placeholders["error_detail"] = str(err)
            except Exception as err:  # noqa: BLE001 - surface the real cause
                # Anything not already a GridConnectError: show the type + message
                # (and log the traceback) instead of HA's opaque "Unknown error".
                _LOGGER.exception("Grid Connect sign-in: unexpected error")
                errors["base"] = "invalid_auth"
                placeholders["error_detail"] = f"{type(err).__name__}: {err}"
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
                    ["auto", *sorted(REGIONS)]
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )
