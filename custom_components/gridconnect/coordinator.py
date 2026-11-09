"""Data update coordinator: one cloud login, periodic device polling."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pytuya_gridconnect import Device, GridConnectCloud, GridConnectError
from .const import (
    CONF_COUNTRY,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GridConnectCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Keeps every device's latest datapoints fresh for the entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.cloud = GridConnectCloud(
            country_code=entry.data[CONF_COUNTRY],
            region=entry.data[CONF_REGION],
        )
        self._password = entry.data[CONF_PASSWORD]
        self._email = entry.data[CONF_EMAIL]

    async def _login(self) -> None:
        try:
            await self.hass.async_add_executor_job(
                self.cloud.login_email, self._email, self._password
            )
        except GridConnectError as err:
            raise ConfigEntryAuthFailed(str(err)) from err

    async def _async_update_data(self) -> dict[str, Device]:
        if not self.cloud.logged_in:
            await self._login()
        try:
            devices = await self.hass.async_add_executor_job(self.cloud.devices)
        except GridConnectError as err:
            # Session may have expired; log in again next cycle.
            self.cloud._sess.sid = ""  # noqa: SLF001 - force re-login
            raise UpdateFailed(str(err)) from err
        return {d.dev_id: d for d in devices}

    async def async_set_dps(self, dev_id: str, dps: dict) -> None:
        """Push a datapoint write, then refresh so entities reflect it."""
        try:
            await self.hass.async_add_executor_job(self.cloud.set_dps, dev_id, dps)
        except GridConnectError as err:
            raise UpdateFailed(str(err)) from err
        await self.async_request_refresh()
