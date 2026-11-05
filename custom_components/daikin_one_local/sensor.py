from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DaikinOneConfigEntry, DaikinOneCoordinator
from .entity import DaikinOneEntity

EQUIPMENT_STATES = {
    1: "cooling",
    2: "overcooling",
    3: "heating",
    4: "fan",
    5: "idle",
    6: "waiting_to_cool",
    7: "waiting_to_heat",
    8: "aux_heat",
}


@dataclass(frozen=True, kw_only=True)
class DaikinOneSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS = (
    DaikinOneSensorDescription(
        key="space_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("spaceTemp"),
    ),
    DaikinOneSensorDescription(
        key="space_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("spaceHum"),
    ),
    DaikinOneSensorDescription(
        key="equipment_state",
        translation_key="equipment_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(EQUIPMENT_STATES.values()),
        value_fn=lambda d: EQUIPMENT_STATES.get(d.get("state")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaikinOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(DaikinOneSensor(coordinator, desc) for desc in SENSORS)


class DaikinOneSensor(DaikinOneEntity, SensorEntity):
    entity_description: DaikinOneSensorDescription

    def __init__(
        self, coordinator: DaikinOneCoordinator, description: DaikinOneSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)
