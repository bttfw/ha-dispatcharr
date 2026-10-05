"""Dispatcharr, independently integrated with Home Assistant."""

from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DispatcharrClient
from .const import PLATFORMS
from .coordinator import DispatcharrCoordinator
from .frontend import async_setup_frontend
from .services import async_setup_services


async def async_setup_entry(hass, entry):
    api = DispatcharrClient(
        async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY]
    )
    coordinator = DispatcharrCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await async_setup_frontend(hass)
    async_setup_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
