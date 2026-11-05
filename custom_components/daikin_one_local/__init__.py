from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DaikinOneClient, DaikinOneError
from .coordinator import DaikinOneConfigEntry, DaikinOneCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: DaikinOneConfigEntry) -> bool:
    client = DaikinOneClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT]
    )
    try:
        api_info = await client.get_api_info()
    except DaikinOneError as err:
        raise ConfigEntryNotReady(f"Thermostat not reachable: {err}") from err

    coordinator = DaikinOneCoordinator(hass, entry, client, api_info)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DaikinOneConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
