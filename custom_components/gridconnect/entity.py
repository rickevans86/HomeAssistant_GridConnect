"""Shared base entity for Grid Connect."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .pytuya_gridconnect import Device
from .const import DOMAIN
from .coordinator import GridConnectCoordinator


class GridConnectEntity(CoordinatorEntity[GridConnectCoordinator]):
    """Base for all Grid Connect entities, keyed by device id."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GridConnectCoordinator, dev_id: str) -> None:
        super().__init__(coordinator)
        self._dev_id = dev_id

    @property
    def device(self) -> Device | None:
        return self.coordinator.data.get(self._dev_id)

    @property
    def available(self) -> bool:
        dev = self.device
        return super().available and dev is not None and dev.online

    @property
    def device_info(self) -> DeviceInfo:
        dev = self.device
        name = dev.name if dev else self._dev_id
        model = dev.product_id if dev else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=name,
            manufacturer="Grid Connect",
            model=model,
        )
