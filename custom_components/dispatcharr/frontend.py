"""Bundled card and authenticated, bounded backend logo cache."""

import asyncio
from pathlib import Path
from time import monotonic

from aiohttp import web
from homeassistant.components import frontend
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .api import DispatcharrError
from .const import CARD_URL, DOMAIN


async def async_setup_frontend(hass):
    state = hass.data.setdefault(DOMAIN, {})
    async with state.setdefault("frontend_lock", asyncio.Lock()):
        if not state.get("frontend"):
            await hass.http.async_register_static_paths(
                [StaticPathConfig("/dispatcharr_static", str(Path(__file__).parent / "www"), False)]
            )
            hass.http.register_view(DispatcharrLogoView(hass))
            hass.http.register_view(MediaImageView(hass))
            state["frontend"] = True
        await async_register_card_resource(hass)


async def async_register_card_resource(hass):
    """Load the card through Lovelace even when the app shell is cached."""
    resources = hass.data[LOVELACE_DATA].resources
    if not isinstance(resources, ResourceStorageCollection):
        # YAML-owned resource collections must not be edited by the integration.
        frontend.add_extra_js_url(hass, CARD_URL)
        return
    # Public helper also loads the collection before we inspect existing items.
    await resources.async_get_info()
    path = CARD_URL.partition("?")[0]
    existing = [r for r in resources.async_items() if r["url"].partition("?")[0] == path]
    if not existing:
        await resources.async_create_item({"url": CARD_URL, "res_type": "module"})
        return
    first, *duplicates = existing
    if first["url"] != CARD_URL or first["type"] != "module":
        await resources.async_update_item(first["id"], {"url": CARD_URL, "res_type": "module"})
    for duplicate in duplicates:
        await resources.async_delete_item(duplicate["id"])


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


class MediaImageView(HomeAssistantView):
    url = "/api/dispatcharr/media_image/{entry_id}/{source_id}/{image_key}"
    name = "api:dispatcharr:media_image"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def get(self, request, entry_id, source_id, image_key):
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN or entry.state.value != "loaded":
            raise web.HTTPNotFound()
        coordinator = entry.runtime_data.media_coordinator
        client = coordinator.clients.get(source_id)
        if not client or image_key not in client.images:
            raise web.HTTPNotFound()
        key = (source_id, image_key)
        async with coordinator.image_lock:
            cache = coordinator.image_cache
            for old in list(cache):
                if monotonic() - cache[old][0] >= 3600:
                    del cache[old]
            if key not in cache:
                try:
                    body, mime = await client.image(image_key)
                except DispatcharrError:
                    raise web.HTTPNotFound() from None
                if len(cache) >= 64:
                    del cache[min(cache, key=lambda k: cache[k][0])]
                cache[key] = (monotonic(), body, mime)
            cached = cache[key]
        return web.Response(
            body=cached[1],
            content_type=cached[2],
            headers={
                "Cache-Control": "private, max-age=3600",
                "X-Content-Type-Options": "nosniff",
            },
        )
