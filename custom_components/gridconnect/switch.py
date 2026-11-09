"""Switch platform: one switch per boolean datapoint.

Grid Connect plugs and wall switches expose their relays as boolean datapoints
(dp "1", "2", ... for multi-gang). Rather than guess a per-product schema, every
boolean dp becomes a switch; lighting devices are handled by the light platform
instead (their on/off dp is claimed there), so they are skipped here.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GridConnectCoordinator
from .entity import GridConnectEntity
from .light import LIGHT_CATEGORIES, light_switch_dp


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GridConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[GridConnectSwitch] = []
    for dev_id, device in coordinator.data.items():
        claimed = light_switch_dp(device) if device.category in LIGHT_CATEGORIES else None
        for dp, value in device.dps.items():
            if isinstance(value, bool) and dp != claimed:
                entities.append(GridConnectSwitch(coordinator, dev_id, dp))
    async_add_entities(entities)


class GridConnectSwitch(GridConnectEntity, SwitchEntity):
    """A single boolean datapoint exposed as a switch."""

    def __init__(
        self, coordinator: GridConnectCoordinator, dev_id: str, dp: str
    ) -> None:
        super().__init__(coordinator, dev_id)
        self._dp = dp
        self._attr_unique_id = f"{dev_id}-{dp}"
        # dp "1" is the main relay -> use the device name; others get a suffix.
        self._attr_name = None if dp == "1" else f"Switch {dp}"

    @property
    def is_on(self) -> bool | None:
        dev = self.device
        if dev is None:
            return None
        return bool(dev.dps.get(self._dp))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_dps(self._dev_id, {self._dp: True})

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_dps(self._dev_id, {self._dp: False})
