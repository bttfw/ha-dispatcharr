"""Small asynchronous client, limited to the verified Dispatcharr API.

Never log response bodies, request headers, upstream URLs or raw exceptions.
No playback endpoints and no username/password authentication are implemented.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import aiohttp


class DispatcharrError(Exception):
    """A deliberately credential-free error."""


class InvalidAuth(DispatcharrError):
    """API key rejected."""


class Forbidden(DispatcharrError):
    """Authenticated account lacks permissions."""


class NotFound(DispatcharrError):
    """Requested resource has disappeared."""


class CannotConnect(DispatcharrError):
    """Transport/server failure."""


class InvalidResponse(DispatcharrError):
    """Unsupported or incomplete API response."""


def normalize_url(value: str) -> str:
    """Accept a base URL, never credentials, query strings or fragments."""
    try:
        parts = urlsplit(value.strip())
        port = parts.port
    except (ValueError, AttributeError):
        raise ValueError("invalid_url") from None
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or "\\" in value
        or any(ord(c) < 33 for c in value.strip())
    ):
        raise ValueError("invalid_url")
    host = parts.hostname.lower()
    host = f"[{host}]" if ":" in host else host
    if port and port != {"http": 80, "https": 443}[parts.scheme]:
        host += f":{port}"
    path = parts.path.rstrip("/")
    if any(part in (".", "..") for part in path.split("/")):
        raise ValueError("invalid_url")
    return urlunsplit((parts.scheme, host, path, "", ""))


def channel_id(value: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise InvalidResponse("invalid_channel_id") from None


def client_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,255}", value):
        raise InvalidResponse("invalid_client_id")
    return value


def records(value: Any) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise InvalidResponse("invalid_list")
    return value


class DispatcharrClient:
    def __init__(self, session: aiohttp.ClientSession, url: str, api_key: str):
        self.session = session
        self.url = normalize_url(url)
        self._api_key = api_key
        self._limit = asyncio.Semaphore(4)

    def text(self, value: Any) -> str | None:
        """Keep display strings bounded; redact accidental key echoes."""
        if value is None or isinstance(value, (dict, list, bool)):
            return None
        result = str(value).strip()
        if self._api_key:
            result = result.replace(self._api_key, "[redacted]")
        return (
            result[:256] if result and result.lower() not in ("unknown", "none", "null") else None
        )

    async def request(self, method: str, path: str, body=None, *, binary=False):
        if not path.startswith("/") or path.startswith("//") or ".." in path:
            raise InvalidResponse("invalid_path")
        try:
            async with (
                self._limit,
                self.session.request(
                    method,
                    self.url + path,
                    json=body,
                    headers={"X-API-Key": self._api_key},
                    timeout=aiohttp.ClientTimeout(total=15),
                    allow_redirects=False,
                ) as response,
            ):
                if response.status == 401:
                    raise InvalidAuth("invalid_auth")
                if response.status == 403:
                    raise Forbidden("insufficient_permissions")
                if response.status == 404:
                    raise NotFound("not_found")
                if response.status >= 500 or response.status == 429:
                    raise CannotConnect("server_unavailable")
                if response.status < 200 or response.status >= 300:
                    raise InvalidResponse("unexpected_http_status")
                limit = 2 * 1024 * 1024 if binary else 8 * 1024 * 1024
                chunks = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    chunks.extend(chunk)
                    if len(chunks) > limit:
                        raise InvalidResponse("response_too_large")
                if binary:
                    mime = response.content_type
                    if mime not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
                        raise InvalidResponse("unsupported_logo")
                    return bytes(chunks), mime
                try:
                    return json.loads(chunks)
                except (ValueError, UnicodeError):
                    raise InvalidResponse("invalid_json") from None
        except (aiohttp.ClientError, TimeoutError, OSError):
            raise CannotConnect("cannot_connect") from None

    async def collection(self, path: str) -> list[dict]:
        """Follow DRF pagination only inside the original collection URL."""
        result = []
        original = path
        seen = set()
        while path:
            if path in seen or len(seen) >= 100:
                raise InvalidResponse("pagination_loop")
            seen.add(path)
            page = await self.request("GET", path)
            if isinstance(page, list):
                result.extend(records(page))
                break
            if not isinstance(page, dict):
                raise InvalidResponse("invalid_collection")
            result.extend(records(page.get("results")))
            nxt = page.get("next")
            if not nxt:
                break
            parsed = urlsplit(nxt)
            base = urlsplit(self.url)
            expected = base.path + original
            if (
                parsed.scheme and (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc)
            ) or parsed.path != expected:
                raise InvalidResponse("unsafe_pagination")
            path = original + ("?" + parsed.query if parsed.query else "")
        return result

    async def validate(self) -> dict:
        me = await self.request("GET", "/api/accounts/users/me/")
        if not isinstance(me, dict):
            raise InvalidResponse("invalid_account")
        try:
            admin = int(me.get("user_level", 0)) >= 10
        except (TypeError, ValueError):
            admin = False
        if not admin:
            raise Forbidden("insufficient_permissions")
        del me  # The endpoint also returns API keys. Never retain it.
        version = await self.request("GET", "/api/core/version/")
        if not isinstance(version, dict) or not isinstance(version.get("version"), str):
            raise InvalidResponse("unsupported_version")
        await self.status()
        await self.channels([])
        await self.epg([])
        # OPTIONS exercises exactly the same permission classes without stopping.
        probe = "00000000-0000-0000-0000-000000000000"
        for action in ("stop_client", "stop"):
            await self.request("OPTIONS", f"/proxy/ts/{action}/{probe}")
        return {"version": self.text(version["version"]), "can_control": True}

    async def detail(self, uuid: str) -> dict:
        value = await self.request("GET", f"/proxy/ts/status/{channel_id(uuid)}")
        if not isinstance(value, dict) or channel_id(value.get("channel_id")) != channel_id(uuid):
            raise InvalidResponse("invalid_channel_detail")
        clients = records(value.get("clients"))
        if value.get("client_count") != len(clients):
            raise InvalidResponse("incomplete_clients")
        ids = [client_id(c.get("client_id")) for c in clients]
        if len(set(ids)) != len(ids):
            raise InvalidResponse("duplicate_client")
        return value

    async def status(self) -> list[dict]:
        value = await self.request("GET", "/proxy/ts/status")
        if not isinstance(value, dict):
            raise InvalidResponse("invalid_status")
        channels = records(value.get("channels"))
        if value.get("count") != len(channels):
            raise InvalidResponse("incomplete_channels")

        async def complete(row):
            uuid = channel_id(row.get("channel_id"))
            clients = row.get("clients")
            count = row.get("client_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise InvalidResponse("invalid_client_count")
            if not isinstance(clients, list) or count != len(clients):
                try:
                    row = await self.detail(uuid)
                except NotFound:
                    return None  # Channel ended between summary and detail.
                clients = row.get("clients")
                if not isinstance(clients, list) or row.get("client_count") != len(clients):
                    raise InvalidResponse("incomplete_clients")
            seen = set()
            for item in records(clients):
                identity = client_id(item.get("client_id"))
                if identity in seen:
                    raise InvalidResponse("duplicate_client")
                seen.add(identity)
            return row

        rows = [
            row for row in await asyncio.gather(*(complete(c) for c in channels)) if row is not None
        ]
        if len({c["channel_id"] for c in rows}) != len(rows):
            raise InvalidResponse("duplicate_channel")
        return rows

    async def channels(self, uuids: list[str]) -> list[dict]:
        return records(
            await self.request("POST", "/api/channels/channels/by-uuids/", {"uuids": uuids})
        )

    async def epg(self, uuids: list[str]) -> list[dict]:
        # Always send an explicit list: omitted/null asks for ALL channels.
        return records(
            await self.request("POST", "/api/epg/current-programs/", {"channel_uuids": uuids})
        )

    async def stop_client(self, uuid: str, identity: str):
        return await self.request(
            "POST", f"/proxy/ts/stop_client/{channel_id(uuid)}", {"client_id": client_id(identity)}
        )

    async def stop_channel(self, uuid: str):
        return await self.request("POST", f"/proxy/ts/stop/{channel_id(uuid)}", {})

    async def logo(self, identity: int):
        if not isinstance(identity, int) or identity <= 0:
            raise NotFound("no_logo")
        return await self.request("GET", f"/api/channels/logos/{identity}/cache/", binary=True)
