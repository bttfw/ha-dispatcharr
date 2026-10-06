"""One shared coordinator for each Dispatcharr instance."""

import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import DispatcharrError, InvalidAuth
from .const import CONF_ALIASES, CONF_CONTROL, CONF_EPG, CONF_METADATA, CONF_POLL, DEFAULTS, DOMAIN
from .data import SessionController, SnapshotLoader
from .media_coordinator import CONF_MEDIA

_LOGGER = logging.getLogger(__name__)


class DispatcharrCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, api):
        options = DEFAULTS | entry.options
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=options[CONF_POLL]),
        )
        self.api = api
        self.entry = entry
        self.loader = SnapshotLoader(api, options[CONF_METADATA], options[CONF_EPG])
        self.last_success = None
        self.version = entry.data.get("version")
        self.controller = SessionController(api, self.async_refresh, lambda: self.control_enabled)
        self.logo_cache = {}
        self.logo_locks = {}

    @property
    def control_enabled(self):
        return self.entry.options.get(CONF_CONTROL, False)

    async def _async_update_data(self):
        try:
            data = await self.loader.snapshot(self.entry.options.get(CONF_ALIASES, {}))
        except InvalidAuth:
            if self.entry.options.get(CONF_MEDIA):
                # A rejected Dispatcharr key must not unload healthy media sources.
                raise UpdateFailed("invalid_auth") from None
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from None
        except DispatcharrError as error:
            raise UpdateFailed(str(error)) from None
        self.last_success = dt_util.utcnow()
        data["last_success"] = self.last_success.isoformat()
        data["control_enabled"] = self.control_enabled
        data["entry_id"] = self.entry.entry_id
        return data
