import json

import pytest
from aiohttp import web
from conftest import KEY, UUID, channel

from custom_components.dispatcharr.api import (
    CannotConnect,
    DispatcharrClient,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
    normalize_url,
)


async def test_setup_uses_api_key_and_read_only_permission_probes(dispatcharr):
    assert await dispatcharr.client.validate() == {"version": "0.31.0", "can_control": True}
    assert not any(method != "OPTIONS" and "/stop" in path for method, path, _ in dispatcharr.calls)
    assert ("POST", "/api/epg/current-programs/", {"channel_uuids": []}) in dispatcharr.calls
    assert not any("token" in path or "login" in path for _, path, _ in dispatcharr.calls)


async def test_wrong_key(dispatcharr):
    dispatcharr.client._api_key = "invalid"
    with pytest.raises(InvalidAuth, match="invalid_auth"):
        await dispatcharr.client.validate()


async def test_non_admin(dispatcharr):
    dispatcharr.admin = False
    with pytest.raises(Forbidden):
        await dispatcharr.client.validate()


async def test_truncated_status_is_completed(dispatcharr):
    dispatcharr.channels = [channel(15)]
    rows = await dispatcharr.client.status()
    assert len(rows[0]["clients"]) == 15
    assert ("GET", f"/proxy/ts/status/{UUID}", None) in dispatcharr.calls


async def test_untruncated_status_avoids_detail_calls(dispatcharr):
    assert len((await dispatcharr.client.status())[0]["clients"]) == 2
    assert dispatcharr.calls == [("GET", "/proxy/ts/status", None)]


async def test_incomplete_detail_is_not_a_successful_snapshot(dispatcharr):
    dispatcharr.channels = [channel(15)]
    dispatcharr.detail_mismatch = True
    with pytest.raises(InvalidResponse, match="incomplete_clients"):
        await dispatcharr.client.status()


async def test_channel_disappears_during_detail(dispatcharr):
    dispatcharr.channels = [channel(15)]
    dispatcharr.failures[f"/proxy/ts/status/{UUID}"] = 404
    assert await dispatcharr.client.status() == []


@pytest.mark.parametrize(
    "status,error",
    [(401, InvalidAuth), (403, Forbidden), (500, CannotConnect), (429, CannotConnect)],
)
async def test_http_errors_are_credential_free(dispatcharr, status, error):
    dispatcharr.failures["/proxy/ts/status"] = status
    with pytest.raises(error) as caught:
        await dispatcharr.client.status()
    assert KEY not in str(caught.value)


async def test_reconnection(dispatcharr):
    dispatcharr.failures["/proxy/ts/status"] = 503
    with pytest.raises(CannotConnect):
        await dispatcharr.client.status()
    dispatcharr.failures.clear()
    assert len(await dispatcharr.client.status()) == 1


@pytest.mark.parametrize(
    "response",
    [
        "<html>proxy error</html>",
        "[]",
        '{"channels": [], "count": 1}',
        '{"channels": null,"count":0}',
    ],
)
async def test_invalid_json_or_shape(dispatcharr, response):
    dispatcharr.failures["/proxy/ts/status"] = response
    with pytest.raises(InvalidResponse):
        await dispatcharr.client.status()


async def test_duplicate_ids_rejected(dispatcharr):
    dispatcharr.channels[0]["clients"][1]["client_id"] = "client_0"
    with pytest.raises(InvalidResponse, match="duplicate_client"):
        await dispatcharr.client.status()


@pytest.mark.parametrize(
    "url",
    [
        "ftp://host",
        "http://user:secret@host",
        "http://host/?api_key=x",
        "http://host/#key",
        "http://",
        "http://host:invalid",
        "http://host/../x",
    ],
)
def test_unsafe_base_url(url):
    with pytest.raises(ValueError):
        normalize_url(url)


def test_normalize_url():
    assert (
        normalize_url(" HTTPS://Example.test:443/dispatcharr/ ")
        == "https://example.test/dispatcharr"
    )
    assert normalize_url("http://[::1]:9191/") == "http://[::1]:9191"


async def test_redirect_never_leaks_key(dispatcharr, aiohttp_server):
    received = []

    async def sink(request):
        received.append(dict(request.headers))
        return web.json_response({})

    app = web.Application()
    app.router.add_get("/sink", sink)
    target = await aiohttp_server(app)

    async def redirect(request):
        raise web.HTTPFound(str(target.make_url("/sink")))

    app = web.Application()
    app.router.add_get("/redirect", redirect)
    source = await aiohttp_server(app)
    client = DispatcharrClient(dispatcharr.client.session, str(source.make_url("/")), KEY)
    with pytest.raises(InvalidResponse):
        await client.request("GET", "/redirect")
    assert received == []


async def test_unsafe_pagination_rejected(dispatcharr):
    dispatcharr.failures["/api/accounts/users/"] = json.dumps(
        {"results": [], "next": "https://outside.invalid/api/accounts/users/?page=2"}
    )
    with pytest.raises(InvalidResponse, match="unsafe_pagination"):
        await dispatcharr.client.collection("/api/accounts/users/")


async def test_logo_uses_id_without_key_url(dispatcharr):
    data, mime = await dispatcharr.client.logo(3)
    assert data.startswith(b"\x89PNG") and mime == "image/png"
    assert dispatcharr.calls == [("GET", "/api/channels/logos/3/cache/", None)]
