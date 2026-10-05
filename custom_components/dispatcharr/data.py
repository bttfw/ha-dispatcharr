"""Shared polling and independently expiring enrichment caches."""

import asyncio
import time

from .api import DispatcharrError, InvalidAuth, InvalidResponse
from .models import identity, viewers


class SnapshotLoader:
    def __init__(self, api, metadata_interval=900, epg_interval=60, clock=time.monotonic):
        self.api = api
        self.metadata_interval = metadata_interval
        self.epg_interval = epg_interval
        self.clock = clock
        self.users = {}
        self.providers = {}
        self.profiles = {}
        self.channels = {}
        self.programmes = {}
        self._channel_times = {}
        self._epg_times = {}
        self._directory_time = float("-inf")
        self._lock = asyncio.Lock()

    async def directories(self):
        users, accounts, profiles = await asyncio.gather(
            self.api.collection("/api/accounts/users/"),
            self.api.collection("/api/m3u/accounts/"),
            self.api.collection("/api/core/outputprofiles/"),
        )
        self.users = {
            identity(x.get("id")): self.api.text(x.get("username"))
            for x in users
            if identity(x.get("id"))
        }
        self.profiles = {
            identity(x.get("id")): self.api.text(x.get("name"))
            for x in profiles
            if identity(x.get("id"))
        }
        self.providers = {
            identity(p.get("id")): {
                "provider": self.api.text(a.get("name")),
                "profile": self.api.text(p.get("name")),
            }
            for a in accounts
            for p in a.get("profiles", [])
            if isinstance(p, dict) and identity(p.get("id"))
        }

    async def snapshot(self, aliases=None):
        async with self._lock:
            raw = await self.api.status()
            now = self.clock()
            active = {c["channel_id"] for c in raw}
            warnings = []
            if now - self._directory_time >= self.metadata_interval:
                try:
                    await self.directories()
                except InvalidAuth:
                    raise
                except DispatcharrError:
                    self.users, self.providers, self.profiles = {}, {}, {}
                    warnings.append("directory_unavailable")
                self._directory_time = now
            # Keep only active metadata. No growing history of client/channel IDs.
            for cache in (self.channels, self.programmes, self._channel_times, self._epg_times):
                for key in cache.keys() - active:
                    del cache[key]
            needed = sorted(
                uuid
                for uuid in active
                if now - self._channel_times.get(uuid, float("-inf")) >= self.metadata_interval
            )
            if needed:
                try:
                    rows = await self.api.channels(needed)
                    for uuid in needed:
                        self.channels.pop(uuid, None)
                    for row in rows:
                        uuid = row.get("uuid")
                        if uuid not in active:
                            continue
                        logo = identity(row.get("effective_logo_id", row.get("logo_id")))
                        self.channels[uuid] = {
                            "id": identity(row.get("id")),
                            "name": self.api.text(row.get("effective_name") or row.get("name")),
                            "logo_id": int(logo) if logo else None,
                        }
                except InvalidAuth:
                    raise
                except DispatcharrError:
                    for uuid in needed:
                        self.channels.pop(uuid, None)
                    warnings.append("metadata_unavailable")
                self._channel_times.update(dict.fromkeys(needed, now))
            needed = sorted(
                uuid
                for uuid in active
                if now - self._epg_times.get(uuid, float("-inf")) >= self.epg_interval
            )
            if needed:
                try:
                    rows = await self.api.epg(needed)
                    for uuid in needed:
                        self.programmes.pop(uuid, None)
                    for row in rows:
                        uuid = row.get("channel_uuid")
                        if uuid in active:
                            self.programmes[uuid] = {
                                "title": self.api.text(row.get("title")),
                                "start_time": row.get("start_time"),
                                "end_time": row.get("end_time"),
                            }
                except InvalidAuth:
                    raise
                except DispatcharrError:
                    for uuid in needed:
                        self.programmes.pop(uuid, None)
                    warnings.append("epg_unavailable")
                self._epg_times.update(dict.fromkeys(needed, now))
            normalized = viewers(
                raw,
                self.channels,
                self.users,
                self.providers,
                self.profiles,
                self.programmes,
                aliases or {},
                self.api.text,
            )
            return {
                "active_channels": len(raw),
                "viewer_count": len(normalized),
                "viewers": normalized,
                "warnings": warnings,
            }


class SessionController:
    """No client action can call the channel stop method."""

    def __init__(self, api, refresh, enabled, sleep=asyncio.sleep):
        self.api, self.refresh, self.enabled, self.sleep = api, refresh, enabled, sleep
        self._lock = asyncio.Lock()

    async def stop(self, uuid, client=None, *, confirm_all=False):
        from .api import NotFound

        async with self._lock:
            if not self.enabled():
                raise DispatcharrError("control_disabled")
            if client is None and confirm_all is not True:
                raise DispatcharrError("confirmation_required")
            try:
                try:
                    before = await self.api.detail(uuid)
                except NotFound:
                    raise DispatcharrError("session_expired") from None
                clients = before.get("clients")
                if not isinstance(clients, list) or before.get("client_count") != len(clients):
                    raise InvalidResponse("incomplete_clients")
                if client is not None and not any(x.get("client_id") == client for x in clients):
                    raise DispatcharrError("session_expired")
                if not self.enabled():
                    raise DispatcharrError("control_disabled")
                if client is not None:
                    await self.api.stop_client(uuid, client)
                else:
                    await self.api.stop_channel(uuid)
                # Dispatcharr stops asynchronously. An HTTP 200 is only acknowledgement.
                for attempt in range(4):
                    if attempt:
                        await self.sleep(1)
                    try:
                        after = await self.api.detail(uuid)
                    except NotFound:
                        return
                    remaining = after.get("clients")
                    if not isinstance(remaining, list) or after.get("client_count") != len(
                        remaining
                    ):
                        raise InvalidResponse("incomplete_clients")
                    if client is not None and not any(
                        x.get("client_id") == client for x in remaining
                    ):
                        return
                    if client is None and not remaining:
                        return
                raise DispatcharrError("stop_not_confirmed")
            finally:
                await self.refresh()
