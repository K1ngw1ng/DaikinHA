from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DaikinOneClient, DaikinOneError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type DaikinOneConfigEntry = ConfigEntry[DaikinOneCoordinator]


class DaikinOneCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /query/info for one thermostat."""

    config_entry: DaikinOneConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: DaikinOneConfigEntry,
        client: DaikinOneClient,
        api_info: dict[str, Any],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.api_info = api_info

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_status()
        except DaikinOneError as err:
            raise UpdateFailed(str(err)) from err
