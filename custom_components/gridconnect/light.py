"""Light platform for Grid Connect lighting devices.

Tuya lighting products (categories ``dj`` light, ``dd`` strip, ``dc`` string,
``xdd`` ceiling, ``fwd`` ambient) use a conventional datapoint layout:

* on/off  -> dp "20" (newer, "switch_led") or dp "1" (older)
* bright   -> dp "22" (newer) or dp "2" (older), range 10..1000

Only on/off + brightness are modelled here, since those are the two datapoints
whose meaning is stable across Tuya lighting products. Colour/temperature dps
vary per product and are left to a future, schema-aware revision rather than
shipped as guesses.
"""

from __future__ import annotations

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .pytuya_gridconnect import Device
from .const import DOMAIN
from .coordinator import GridConnectCoordinator
from .entity import GridConnectEntity

LIGHT_CATEGORIES = {"dj", "dd", "dc", "xdd", "fwd", "tgq", "tyndj"}

_BRIGHT_MIN = 10
_BRIGHT_MAX = 1000


def light_switch_dp(device: Device) -> str | None:
    """Return the on/off dp a light uses, or None if it has no boolean dp."""
    for candidate in ("20", "1"):
        if isinstance(device.dps.get(candidate), bool):
            return candidate
    return None


def _bright_dp(device: Device) -> str | None:
    for candidate in ("22", "2"):
        if isinstance(device.dps.get(candidate), (int, float)):
            return candidate
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GridConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[GridConnectLight] = []
    for dev_id, device in coordinator.data.items():
        if device.category in LIGHT_CATEGORIES and light_switch_dp(device):
            entities.append(GridConnectLight(coordinator, dev_id))
    async_add_entities(entities)


class GridConnectLight(GridConnectEntity, LightEntity):
    """A Grid Connect light (on/off, plus brightness when the device reports it)."""

    _attr_name = None  # use the device name

    def __init__(self, coordinator: GridConnectCoordinator, dev_id: str) -> None:
        super().__init__(coordinator, dev_id)
        self._attr_unique_id = f"{dev_id}-light"
        device = self.device
        self._switch_dp = light_switch_dp(device) if device else "20"
        self._bright_dp = _bright_dp(device) if device else None
        if self._bright_dp:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self) -> bool | None:
        dev = self.device
        if dev is None:
            return None
        return bool(dev.dps.get(self._switch_dp))

    @property
    def brightness(self) -> int | None:
        dev = self.device
        if dev is None or not self._bright_dp:
            return None
        raw = dev.dps.get(self._bright_dp)
        if not isinstance(raw, (int, float)):
            return None
        # Map Tuya 10..1000 to HA 0..255.
        scaled = (raw - _BRIGHT_MIN) / (_BRIGHT_MAX - _BRIGHT_MIN) * 255
        return max(0, min(255, round(scaled)))

    async def async_turn_on(self, **kwargs) -> None:
        dps: dict[str, object] = {self._switch_dp: True}
        if ATTR_BRIGHTNESS in kwargs and self._bright_dp:
            ha = kwargs[ATTR_BRIGHTNESS]
            tuya = round(ha / 255 * (_BRIGHT_MAX - _BRIGHT_MIN) + _BRIGHT_MIN)
            dps[self._bright_dp] = max(_BRIGHT_MIN, min(_BRIGHT_MAX, tuya))
        await self.coordinator.async_set_dps(self._dev_id, dps)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_dps(self._dev_id, {self._switch_dp: False})
