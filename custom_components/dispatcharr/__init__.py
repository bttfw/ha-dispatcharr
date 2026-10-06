"""Dispatcharr, independently integrated with Home Assistant."""

from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DispatcharrClient
from .const import PLATFORMS
from .coordinator import DispatcharrCoordinator
from .frontend import async_setup_frontend
from .media_coordinator import CONF_MEDIA, MediaCoordinator
from .services import async_setup_services


async def async_setup_entry(hass, entry):
    # The card must remain loadable even if Dispatcharr is offline at HA startup.
    await async_setup_frontend(hass)
    async_setup_services(hass)
    api = DispatcharrClient(
        async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY]
    )
    coordinator = DispatcharrCoordinator(hass, entry, api)
    if entry.options.get(CONF_MEDIA):
        await coordinator.async_refresh()
    else:
        await coordinator.async_config_entry_first_refresh()
    coordinator.media_coordinator = MediaCoordinator(hass, entry, async_get_clientsession(hass))
    await coordinator.media_coordinator.async_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
