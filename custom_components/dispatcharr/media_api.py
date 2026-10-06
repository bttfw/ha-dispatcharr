"""Optional media-server clients. Credentials and image paths stay in the backend."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re

import aiohttp

from .api import CannotConnect, Forbidden, InvalidAuth, InvalidResponse, NotFound, normalize_url
from .media_models import normalize_emby_session, normalize_plex_session

MEDIA_KINDS = ("jellyfin", "plex", "emby")


def media_id(value):
    """Accept an opaque server ID without allowing URL or path injection."""
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,255}", value):
        raise InvalidResponse("invalid_session_id")
    return value


class MediaClient:
    def __init__(self, session, source):
        self.session = session
        self.source_id = media_id(source["id"])
        self.kind = source["kind"]
        if self.kind not in MEDIA_KINDS:
            raise ValueError("unsupported_server")
        self.url = normalize_url(source["url"])
        self._key = source["api_key"].strip()
        if not self._key or len(self._key) > 512 or re.search(r'[\x00-\x20"\\\x7f]', self._key):
            raise InvalidAuth("invalid_auth")
        self.name = self.text(source.get("name")) or self.kind.title()
        self.images = {}
        self._limit = asyncio.Semaphore(3)

    def text(self, value):
        if value is None or isinstance(value, (dict, list, bool)):
            return None
        value = str(value).strip().replace(self._key, "[redacted]")
        return value[:256] if value and value.lower() not in ("unknown", "none", "null") else None

    def safe_id(self, value):
        result = media_id(value)
        if self._key in result:
            raise InvalidResponse("invalid_session_id")
        return result

    async def request(self, method, path, *, params=None, json_body=None, binary=False):
        if not path.startswith("/") or path.startswith("//") or ".." in path or "?" in path:
            raise InvalidResponse("invalid_path")
        if self.kind == "plex":
            headers = {
                "X-Plex-Token": self._key,
                "X-Plex-Client-Identifier": f"ha-dispatcharr-{self.source_id}",
                "Accept": "application/json",
            }
        else:
            # Jellyfin 12 rejects the legacy X-Emby-Token header. The documented
            # MediaBrowser authorization scheme is also supported by Emby.
            headers = {"Authorization": f'MediaBrowser Token="{self._key}"'}
        try:
            async with (
                self._limit,
                self.session.request(
                    method,
                    self.url + path,
                    headers=headers,
                    params=params,
                    json=json_body,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response,
            ):
                if response.status == 401:
                    if (
                        self.kind == "plex"
                        and method == "POST"
                        and path == "/status/sessions/terminate"
                    ):
                        # PMS also uses 401 when the termination feature is not
                        # enabled, even with an otherwise valid owner token.
                        raise Forbidden("insufficient_permissions")
                    raise InvalidAuth("invalid_auth")
                if response.status == 403:
                    raise Forbidden("insufficient_permissions")
                if response.status == 404:
                    raise NotFound("not_found")
                if response.status >= 500 or response.status == 429:
                    raise CannotConnect("server_unavailable")
                if not 200 <= response.status < 300:
                    raise InvalidResponse("unexpected_http_status")
                limit = 2 * 1024 * 1024 if binary else 8 * 1024 * 1024
                body = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    body.extend(chunk)
                    if len(body) > limit:
                        raise InvalidResponse("response_too_large")
                if binary:
                    if response.content_type not in (
                        "image/png",
                        "image/jpeg",
                        "image/webp",
                        "image/gif",
                    ):
                        raise InvalidResponse("unsupported_logo")
                    return bytes(body), response.content_type
                if method == "POST":
                    # Control endpoints may return empty or HTML success bodies.
                    # Success is verified by querying sessions, never by this body.
                    return None
                if not body:
                    return None
                try:
                    return json.loads(body)
                except (ValueError, UnicodeError):
                    raise InvalidResponse("invalid_json") from None
        except (aiohttp.ClientError, TimeoutError, OSError):
            raise CannotConnect("cannot_connect") from None

    async def validate(self):
        if self.kind == "plex":
            identity = await self.request("GET", "/identity")
            if not isinstance(identity, dict) or not isinstance(
                identity.get("MediaContainer"), dict
            ):
                raise InvalidResponse("unsupported_api")
            if identity["MediaContainer"].get("claimed") is not True:
                raise InvalidResponse("plex_unclaimed")
        info = await self.request("GET", "/" if self.kind == "plex" else "/System/Info")
        if not isinstance(info, dict):
            raise InvalidResponse("unsupported_api")
        if self.kind == "plex":
            info = info.get("MediaContainer")
            if not isinstance(info, dict):
                raise InvalidResponse("unsupported_api")
            server, version = info.get("machineIdentifier"), info.get("version")
        else:
            server, version = info.get("Id"), info.get("Version")
        server = self.safe_id(server)
        await self.sessions()
        return {"server_id": server, "version": self.text(version)}

    async def sessions(self):
        payload = await self.request(
            "GET", "/status/sessions" if self.kind == "plex" else "/Sessions"
        )
        if self.kind == "plex":
            container = payload.get("MediaContainer") if isinstance(payload, dict) else None
            if not isinstance(container, dict):
                raise InvalidResponse("invalid_sessions")
            payload = container.get("Metadata", [])
            if (
                not isinstance(payload, list)
                or container.get("size") != len(payload)
                or container.get("totalSize", len(payload)) != len(payload)
                or container.get("offset", 0) != 0
            ):
                raise InvalidResponse("incomplete_sessions")
        if not isinstance(payload, list) or len(payload) > 2000:
            raise InvalidResponse("invalid_sessions")
        rows, images, seen = [], {}, set()
        for raw in payload:
            if not isinstance(raw, dict):
                raise InvalidResponse("invalid_sessions")
            if self.kind != "plex" and not raw.get("NowPlayingItem"):
                continue
            normalize = normalize_plex_session if self.kind == "plex" else normalize_emby_session
            row, poster = normalize(raw, self.text, self.safe_id)
            row_id = row.get("session_key", row["session_id"])
            if row_id in seen:
                raise InvalidResponse("duplicate_session_id")
            seen.add(row_id)
            row.update(source_id=self.source_id, source_type=self.kind, source_name=self.name)
            row["device_key"] = (
                "media_"
                + hashlib.sha256(
                    json.dumps([self.source_id, row["device_id"]]).encode()
                ).hexdigest()[:24]
                if row["device_id"]
                else None
            )
            row["image_key"] = None
            if poster:
                image_key = hashlib.sha256(json.dumps(poster, sort_keys=True).encode()).hexdigest()[
                    :24
                ]
                images[image_key] = poster
                row["image_key"] = image_key
            rows.append(row)
        if self.kind == "plex":
            # A live PMS can report different sessionKeys with the same
            # Session.id. Keep both rows, but never send an ambiguous stop.
            counts = {}
            for row in rows:
                counts[row["session_id"]] = counts.get(row["session_id"], 0) + 1
            for row in rows:
                if counts[row["session_id"]] != 1:
                    row["can_stop"] = False
        self.images = images
        return sorted(rows, key=lambda row: row.get("session_key", row["session_id"]))

    async def image(self, key):
        if key not in self.images:
            raise NotFound("not_found")
        path, params = self.images[key]
        return await self.request("GET", path, params=params, binary=True)

    async def stop(self, session_id):
        session_id = media_id(session_id)
        if self.kind == "plex":
            return await self.request(
                "POST",
                "/status/sessions/terminate",
                params={"sessionId": session_id, "reason": "Stopped from Home Assistant"},
            )
        return await self.request(
            "POST",
            f"/Sessions/{session_id}/Playing/Stop",
            json_body={"Command": "Stop"} if self.kind == "emby" else None,
        )
