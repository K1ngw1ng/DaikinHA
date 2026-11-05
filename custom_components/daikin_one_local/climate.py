from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import FAN_OFF, FAN_ON
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DaikinOneError
from .coordinator import DaikinOneConfigEntry, DaikinOneCoordinator
from .entity import DaikinOneEntity

# API mode 4 (emergency heat) has no HVACMode equivalent and is not exposed.
HVAC_FROM_MODE = {
    0: HVACMode.OFF,
    1: HVACMode.HEAT,
    2: HVACMode.COOL,
    3: HVACMode.HEAT_COOL,
    5: HVACMode.FAN_ONLY,
    6: HVACMode.DRY,
}
MODE_FROM_HVAC = {v: k for k, v in HVAC_FROM_MODE.items()}

# API equipment state: 1 cool, 2 overcool for dehum, 3 heat, 4 fan, 5 idle,
# 6 waiting to cool, 7 waiting to heat, 8 aux heat.
ACTION_FROM_STATE = {
    1: HVACAction.COOLING,
    2: HVACAction.COOLING,
    3: HVACAction.HEATING,
    4: HVACAction.FAN,
    5: HVACAction.IDLE,
    6: HVACAction.IDLE,
    7: HVACAction.IDLE,
    8: HVACAction.HEATING,
}

# API fan setting: 0 off, 1 always on, 2 on a schedule.
FAN_FROM_VALUE = {0: FAN_OFF, 1: FAN_ON, 2: "schedule"}
VALUE_FROM_FAN = {v: k for k, v in FAN_FROM_VALUE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaikinOneConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DaikinOneClimate(entry.runtime_data)])


class DaikinOneClimate(DaikinOneEntity, ClimateEntity):
    """The thermostat as a climate entity. All temperatures are Celsius."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_fan_modes = list(FAN_FROM_VALUE.values())

    def __init__(self, coordinator: DaikinOneCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_climate"

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [
            HVAC_FROM_MODE[m] for m in self._data["availableModes"] if m in HVAC_FROM_MODE
        ]

    @property
    def hvac_mode(self) -> HVACMode | None:
        return HVAC_FROM_MODE.get(self._data["mode"])

    @property
    def hvac_action(self) -> HVACAction | None:
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        return ACTION_FROM_STATE.get(self._data.get("state"))

    @property
    def supported_features(self) -> ClimateEntityFeature:
        features = (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.FAN_MODE
        )
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return features | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        return features | ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def current_temperature(self) -> float | None:
        return self._data.get("spaceTemp")

    @property
    def current_humidity(self) -> int | None:
        return self._data.get("spaceHum")

    @property
    def target_temperature(self) -> float | None:
        if self.hvac_mode == HVACMode.HEAT:
            return self._data["heatSetpoint"]
        if self.hvac_mode in (HVACMode.COOL, HVACMode.DRY):
            return self._data["coolSetpoint"]
        return None

    @property
    def target_temperature_low(self) -> float | None:
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._data["heatSetpoint"]
        return None

    @property
    def target_temperature_high(self) -> float | None:
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._data["coolSetpoint"]
        return None

    @property
    def min_temp(self) -> float:
        if self.hvac_mode in (HVACMode.COOL, HVACMode.DRY):
            return self._data["coolSetpointMin"]
        return self._data["heatSetpointMin"]

    @property
    def max_temp(self) -> float:
        if self.hvac_mode == HVACMode.HEAT:
            return self._data["heatSetpointMax"]
        return self._data["coolSetpointMax"]

    @property
    def fan_mode(self) -> str | None:
        return FAN_FROM_VALUE.get(self._data["fan"])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self._control(mode=MODE_FROM_HVAC[hvac_mode])

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._control(fan=VALUE_FROM_FAN[fan_mode])

    async def async_set_temperature(self, **kwargs: Any) -> None:
        params: dict[str, Any] = {}
        new_mode = self.hvac_mode
        if (requested := kwargs.get(ATTR_HVAC_MODE)) is not None:
            params["mode"] = MODE_FROM_HVAC[requested]
            new_mode = requested
        if ATTR_TARGET_TEMP_LOW in kwargs:
            params["heatSetpoint"] = kwargs[ATTR_TARGET_TEMP_LOW]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            params["coolSetpoint"] = kwargs[ATTR_TARGET_TEMP_HIGH]
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            key = "heatSetpoint" if new_mode == HVACMode.HEAT else "coolSetpoint"
            params[key] = temp
        await self._control(**params)

    async def _control(self, **params: Any) -> None:
        try:
            await self.coordinator.client.set_control(**params)
        except DaikinOneError as err:
            raise HomeAssistantError(f"Thermostat rejected the change: {err}") from err
        await self.coordinator.async_request_refresh()
