"""Bundled card and authenticated, bounded backend logo cache."""

import asyncio
from pathlib import Path
from time import monotonic

from aiohttp import web
from homeassistant.components import frontend
from homeassistant.components.http import HomeAssistantView, StaticPathConfig

from .api import DispatcharrError
from .const import CARD_URL, DOMAIN


async def async_setup_frontend(hass):
    state = hass.data.setdefault(DOMAIN, {})
    async with state.setdefault("frontend_lock", asyncio.Lock()):
        if state.get("frontend"):
            return
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/dispatcharr_static", str(Path(__file__).parent / "www"), False)]
        )
        hass.http.register_view(DispatcharrLogoView(hass))
        frontend.add_extra_js_url(hass, CARD_URL)
        state["frontend"] = True


class DispatcharrLogoView(HomeAssistantView):
    url = "/api/dispatcharr/logo/{entry_id}/{logo_id}"
    name = "api:dispatcharr:logo"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def get(self, request, entry_id, logo_id):
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN or entry.state.value != "loaded":
            raise web.HTTPNotFound()
        coordinator = entry.runtime_data
        try:
            identity = int(logo_id)
        except ValueError:
            raise web.HTTPNotFound() from None
        allowed = {x.get("logo_id") for x in coordinator.loader.channels.values()}
        if identity not in allowed:
            raise web.HTTPNotFound()
        # Bound memory even when many channels are visited over time.
        for key in list(coordinator.logo_cache):
            if key not in allowed or monotonic() - coordinator.logo_cache[key][0] >= 3600:
                coordinator.logo_cache.pop(key, None)
        lock = coordinator.logo_locks.setdefault(identity, asyncio.Lock())
        async with lock:
            cached = coordinator.logo_cache.get(identity)
            if not cached:
                try:
                    body, mime = await coordinator.api.logo(identity)
                except DispatcharrError:
                    raise web.HTTPNotFound() from None
                if len(coordinator.logo_cache) >= 64:
                    oldest = min(coordinator.logo_cache, key=lambda k: coordinator.logo_cache[k][0])
                    del coordinator.logo_cache[oldest]
                cached = (monotonic(), body, mime)
                coordinator.logo_cache[identity] = cached
        for key in list(coordinator.logo_locks):
            if key not in allowed and not coordinator.logo_locks[key].locked():
                del coordinator.logo_locks[key]
        return web.Response(
            body=cached[1],
            content_type=cached[2],
            headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
        )
