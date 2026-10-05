"""Synthetic Dispatcharr only; no tests open or stop real IPTV streams."""

import base64
import copy
import time
from types import SimpleNamespace

import pytest
from aiohttp import ClientSession, web

from custom_components.dispatcharr.api import DispatcharrClient

UUID = "11111111-2222-4333-8444-555555555555"
OTHER_UUID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
KEY = "test-key-never-in-client-data"


def channel(count=2):
    return {
        "channel_id": UUID,
        "channel_name": "Example TV",
        "state": "active",
        "client_count": count,
        "resolution": "1920x1080",
        "source_fps": 50,
        "video_codec": "h264",
        "audio_codec": "aac",
        "avg_bitrate_kbps": 5200,
        "stream_profile": "ffmpeg",
        "m3u_profile_id": 17,
        "url": "https://provider.invalid/private/password/stream",
        "clients": [
            {
                "client_id": f"client_{i}",
                "user_id": "42",
                "ip_address": f"192.0.2.{i + 1}",
                "user_agent": "Example Player",
                "connected_at": time.time() - 100,
                "output_profile_id": 7,
            }
            for i in range(count)
        ],
    }


@pytest.fixture
async def dispatcharr(aiohttp_server):
    state = SimpleNamespace(
        channels=[channel()],
        calls=[],
        failures={},
        ignore_stop=False,
        users=[{"id": 42, "username": "Actual user", "api_key": KEY, "password": "secret"}],
        metadata=[{"uuid": UUID, "id": 92, "name": "Example TV", "logo_id": 3}],
        programmes=[
            {
                "channel_uuid": UUID,
                "title": "Current programme",
                "start_time": time.time() - 60,
                "end_time": time.time() + 1800,
            }
        ],
        detail_mismatch=False,
        admin=True,
    )

    async def handler(request):
        path = request.path
        body = await request.json() if request.can_read_body else None
        state.calls.append((request.method, path, body))
        if request.headers.get("X-API-Key") != KEY:
            return web.json_response({"detail": "invalid key"}, status=401)
        if path in state.failures:
            failure = state.failures[path]
            if isinstance(failure, int):
                return web.json_response({"private_error": KEY}, status=failure)
            return web.Response(text=failure)
        if path == "/api/accounts/users/me/":
            return web.json_response({"user_level": 10 if state.admin else 1, "api_key": KEY})
        if path == "/api/core/version/":
            return web.json_response({"version": "0.31.0"})
        if path == "/proxy/ts/status":
            rows = copy.deepcopy(state.channels)
            for row in rows:
                row["clients"] = row["clients"][:10]
            return web.json_response({"count": len(rows), "channels": rows})
        if path.startswith("/proxy/ts/status/"):
            row = next(
                (x for x in state.channels if x["channel_id"] == path.rsplit("/", 1)[1]), None
            )
            if row is None:
                return web.json_response({}, status=404)
            row = copy.deepcopy(row)
            if state.detail_mismatch:
                row["clients"] = row["clients"][:1]
            return web.json_response(row)
        if path.startswith("/proxy/ts/stop"):
            if request.method == "OPTIONS":
                return web.json_response({"name": "Stop"}, headers={"Allow": "POST, OPTIONS"})
            uuid = path.rsplit("/", 1)[1]
            if not state.ignore_stop:
                if "/stop_client/" in path:
                    for row in state.channels:
                        if row["channel_id"] == uuid:
                            row["clients"] = [
                                c for c in row["clients"] if c["client_id"] != body["client_id"]
                            ]
                            row["client_count"] = len(row["clients"])
                else:
                    state.channels = [c for c in state.channels if c["channel_id"] != uuid]
            return web.json_response({"message": "processed"})
        if path == "/api/accounts/users/":
            return web.json_response(state.users)
        if path == "/api/m3u/accounts/":
            return web.json_response(
                [
                    {
                        "id": 2,
                        "name": "Example provider",
                        "password": "private",
                        "profiles": [{"id": 17, "name": "Main"}],
                    }
                ]
            )
        if path == "/api/core/outputprofiles/":
            return web.json_response([{"id": 7, "name": "Example output"}])
        if path == "/api/channels/channels/by-uuids/":
            return web.json_response([x for x in state.metadata if x["uuid"] in body["uuids"]])
        if path == "/api/epg/current-programs/":
            return web.json_response(
                [x for x in state.programmes if x["channel_uuid"] in body["channel_uuids"]]
            )
        if path == "/api/channels/logos/3/cache/":
            return web.Response(
                body=base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
                ),
                content_type="image/png",
            )
        return web.json_response({}, status=404)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    server = await aiohttp_server(app)
    async with ClientSession() as session:
        state.client = DispatcharrClient(session, str(server.make_url("/")).rstrip("/"), KEY)
        yield state
