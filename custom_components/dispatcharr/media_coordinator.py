"""Poll optional sources independently and control only exact current sessions."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import CannotConnect, DispatcharrError, Forbidden, InvalidAuth, NotFound
from .const import CONF_ALIASES, CONF_CONTROL, CONF_POLL, DEFAULTS, DOMAIN
from .media_api import MediaClient, media_id

CONF_MEDIA = "media_servers"
_LOGGER = logging.getLogger(__name__)


class MediaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, session):
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} media",
            update_interval=timedelta(seconds=entry.options.get(CONF_POLL, DEFAULTS[CONF_POLL])),
        )
        self.entry = entry
        self.clients = {s["id"]: MediaClient(session, s) for s in entry.options.get(CONF_MEDIA, [])}
        self.last_success = {}
        self.action_locks = {key: asyncio.Lock() for key in self.clients}
        self.image_cache = {}
        self.image_lock = asyncio.Lock()

    def enabled(self, source_id):
        return self.entry.options.get(CONF_CONTROL, False) and any(
            s["id"] == source_id and s.get(CONF_CONTROL, False)
            for s in self.entry.options.get(CONF_MEDIA, [])
        )

    async def _source(self, client):
        status = {
            "id": client.source_id,
            "type": client.kind,
            "name": client.name,
            "connected": False,
            "error": None,
            "control_enabled": self.enabled(client.source_id),
        }
        rows = []
        try:
            rows = await client.sessions()
        except InvalidAuth:
            status["error"] = "invalid_auth"
        except Forbidden:
            status["error"] = "insufficient_permissions"
        except CannotConnect:
            status["error"] = "cannot_connect"
        except DispatcharrError:
            status["error"] = "unsupported_api"
        else:
            status["connected"] = True
            self.last_success[client.source_id] = dt_util.utcnow().isoformat()
            aliases = self.entry.options.get(CONF_ALIASES, {})
            for row in rows:
                row["device_alias"] = client.text(aliases.get(row["device_key"]))
        status["last_success"] = self.last_success.get(client.source_id)
        status["session_count"] = len(rows) if status["connected"] else None
        return status, rows

    async def _async_update_data(self):
        results = await asyncio.gather(*(self._source(client) for client in self.clients.values()))
        return {
            "entry_id": self.entry.entry_id,
            "media_sources": [status for status, _ in results],
            "sessions": [row for _, rows in results for row in rows],
        }

    async def stop(self, source_id, session_id, item_id):
        source_id, session_id, item_id = map(media_id, (source_id, session_id, item_id))
        if source_id not in self.clients:
            raise DispatcharrError("session_expired")
        async with self.action_locks[source_id]:
            if not self.enabled(source_id):
                raise DispatcharrError("control_disabled")
            client = self.clients[source_id]
            matching = [r for r in await client.sessions() if r["session_id"] == session_id]
            if len(matching) > 1:
                raise DispatcharrError("media_control_unavailable")
            current = matching[0] if matching else None
            # Jellyfin/Emby session IDs can outlive a film. Never stop a new item
            # that appeared after the user opened the confirmation dialog.
            if not current or current["item_id"] != item_id:
                await self.async_refresh()
                raise DispatcharrError("session_expired")
            if not current["can_stop"]:
                raise DispatcharrError("media_control_unavailable")
            try:
                await client.stop(session_id)
            except NotFound:
                raise DispatcharrError("session_expired") from None
            finally:
                await self.async_refresh()
            for attempt in range(4):
                data = self.data or {}
                status = next(
                    (s for s in data.get("media_sources", []) if s["id"] == source_id), {}
                )
                remaining = any(
                    r["source_id"] == source_id
                    and r["session_id"] == session_id
                    and r["item_id"] == item_id
                    for r in data.get("sessions", [])
                )
                if status.get("connected") and not remaining:
                    return
                if attempt < 3:
                    await asyncio.sleep(0.5)
                    await self.async_refresh()
            raise DispatcharrError("stop_not_confirmed")
