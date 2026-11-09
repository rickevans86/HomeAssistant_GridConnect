"""Sensor platform: surfaces numeric datapoints as diagnostic sensors.

Metered Grid Connect plugs report power-monitoring datapoints with stable ids:

* dp "18" -> current (mA)
* dp "19" -> power (0.1 W)
* dp "20" -> voltage (0.1 V)  [only on plugs; lights use dp 20 for on/off]

These three are given proper units and device classes. Any other numeric dp is
still exposed as a plain diagnostic sensor so nothing is hidden, letting you see
what a given product reports before mapping it.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GridConnectCoordinator
from .entity import GridConnectEntity
from .light import LIGHT_CATEGORIES


@dataclass(frozen=True)
class _Meter:
    name: str
    unit: str
    device_class: SensorDeviceClass
    scale: float


# dp id -> how to present it, for metered plugs (category "cz") and similar.
_METERING: dict[str, _Meter] = {
    "18": _Meter("Current", UnitOfElectricCurrent.MILLIAMPERE, SensorDeviceClass.CURRENT, 1),
    "19": _Meter("Power", UnitOfPower.WATT, SensorDeviceClass.POWER, 0.1),
    "20": _Meter("Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, 0.1),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GridConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for dev_id, device in coordinator.data.items():
        is_light = device.category in LIGHT_CATEGORIES
        for dp, value in device.dps.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            meter = _METERING.get(dp)
            # dp 20 is voltage on plugs but on/off on lights -> don't meter lights.
            if meter and not (is_light and dp == "20"):
                entities.append(GridConnectMeterSensor(coordinator, dev_id, dp, meter))
            else:
                entities.append(GridConnectRawSensor(coordinator, dev_id, dp))
    async_add_entities(entities)


class GridConnectMeterSensor(GridConnectEntity, SensorEntity):
    """A recognised power-metering datapoint with proper units."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: GridConnectCoordinator,
        dev_id: str,
        dp: str,
        meter: _Meter,
    ) -> None:
        super().__init__(coordinator, dev_id)
        self._dp = dp
        self._scale = meter.scale
        self._attr_unique_id = f"{dev_id}-{dp}"
        self._attr_name = meter.name
        self._attr_native_unit_of_measurement = meter.unit
        self._attr_device_class = meter.device_class

    @property
    def native_value(self) -> float | None:
        dev = self.device
        if dev is None:
            return None
        raw = dev.dps.get(self._dp)
        if not isinstance(raw, (int, float)):
            return None
        return round(raw * self._scale, 2)


class GridConnectRawSensor(GridConnectEntity, SensorEntity):
    """An unmapped numeric datapoint, exposed for visibility."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: GridConnectCoordinator, dev_id: str, dp: str
    ) -> None:
        super().__init__(coordinator, dev_id)
        self._dp = dp
        self._attr_unique_id = f"{dev_id}-{dp}"
        self._attr_name = f"DP {dp}"

    @property
    def native_value(self):
        dev = self.device
        return None if dev is None else dev.dps.get(self._dp)
