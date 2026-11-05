from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DaikinOneCoordinator


class DaikinOneEntity(CoordinatorEntity[DaikinOneCoordinator]):
    """Ties every entity to the one thermostat device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DaikinOneCoordinator) -> None:
        super().__init__(coordinator)
        info = coordinator.api_info
        brand = str(info.get("brand", "daikin"))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
            name=coordinator.data.get("name") or "Daikin One",
            manufacturer={"dk": "Daikin"}.get(brand, brand.title()),
            model=info.get("model"),
            sw_version=info.get("firmware"),
        )