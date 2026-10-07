"""Credential-free GUI checks and actionable network failures."""

import errno
import socket
from copy import deepcopy

import aiohttp
import pytest
import test_ha
import test_media

from custom_components.dispatcharr.api import (
    CannotConnect,
    InvalidAuth,
    ValidationChecks,
    transport_error,
)
from custom_components.dispatcharr.config_flow import DispatcharrOptionsFlow

hass = test_ha.hass
entry = test_ha.entry
media_servers = test_media.media_servers
media_entry = test_media.media_entry


@pytest.mark.parametrize(
    "error,reason",
    [
        (TimeoutError("private URL"), "connection_timeout"),
        (socket.gaierror(-2, "private hostname"), "connection_dns"),
        (ConnectionRefusedError(errno.ECONNREFUSED, "private host"), "connection_refused"),
        (aiohttp.ClientConnectionError("private key"), "cannot_connect"),
    ],
)
def test_transport_error_classification_never_echoes_private_data(error, reason):
    assert transport_error(error) == reason
    assert "private" not in transport_error(error)


async def test_checks_report_exact_stage_and_do_not_stop_streams(dispatcharr):
    checks = ValidationChecks()
    await dispatcharr.client.validate(checks)
    assert set(checks.results.values()) == {"✓"}
    assert not any(method != "OPTIONS" and "/stop" in path for method, path, _ in dispatcharr.calls)
    dispatcharr.failures["/proxy/ts/status"] = 503
    checks = ValidationChecks()
    with pytest.raises(CannotConnect):
        await dispatcharr.client.validate(checks)
    assert checks.results == {
        "connection": "✓",
        "authentication": "✓",
        "sessions": "✗",
        "metadata": "—",
        "permissions": "—",
    }
    dispatcharr.failures.clear()
    dispatcharr.client._api_key = "bad"
    checks = ValidationChecks()
    with pytest.raises(InvalidAuth):
        await dispatcharr.client.validate(checks)
    assert checks.results["connection"] == "✓" and checks.results["authentication"] == "✗"
    assert checks.results["sessions"] == "—"


async def test_check_options_preserve_config_and_show_actual_failures(
    hass, entry, dispatcharr, monkeypatch
):
    import custom_components.dispatcharr.connection_check as module

    monkeypatch.setattr(module, "async_get_clientsession", lambda hass: dispatcharr.client.session)
    monkeypatch.setattr(DispatcharrOptionsFlow, "config_entry", property(lambda self: entry))
    before = deepcopy(dict(entry.options))
    flow = DispatcharrOptionsFlow()
    flow.hass = hass
    first = await flow.async_step_connection_check()
    assert first["data_schema"]({}) == {"source": "dispatcharr"}
    good = await flow.async_step_connection_check({"source": "dispatcharr"})
    assert good["step_id"] == "connection_result" and not good["errors"]
    assert good["description_placeholders"]["sessions"] == "✓"
    assert (await flow.async_step_connection_result({}))["type"] == "menu"
    dispatcharr.failures["/proxy/ts/status"] = 403
    bad = await flow.async_step_connection_check({"source": "dispatcharr"})
    assert bad["errors"] == {"base": "check_permissions"}
    assert bad["description_placeholders"]["sessions"] == "✗"
    assert bad["description_placeholders"]["authentication"] == "✓"
    assert dict(entry.options) == before
    assert dispatcharr.client._api_key not in str(bad)


async def test_failed_transport_does_not_claim_reachability():
    checks = ValidationChecks()
    with pytest.raises(CannotConnect), checks.stage("authentication"):
        raise CannotConnect("connection_timeout")
    assert checks.results["connection"] == "✗"
    assert checks.results["authentication"] == "✗"
    assert checks.results["sessions"] == "—"


@pytest.mark.parametrize("kind", ["jellyfin", "plex", "emby"])
async def test_media_checks_use_exact_server_and_never_claim_stop_support(
    hass, media_servers, media_entry, monkeypatch, kind
):
    import custom_components.dispatcharr.connection_check as module

    monkeypatch.setattr(module, "async_get_clientsession", lambda hass: media_servers.session)
    monkeypatch.setattr(DispatcharrOptionsFlow, "config_entry", property(lambda self: media_entry))
    flow = DispatcharrOptionsFlow()
    flow.hass = hass
    result = await flow.async_step_connection_check({"source": kind})
    assert result["step_id"] == "media_connection_result" and not result["errors"]
    assert result["description_placeholders"]["sessions"] == "✓"
    assert result["description_placeholders"]["permissions"] == "—"
    for name, server in media_servers.servers.items():
        if name != kind:
            assert not server.calls
        assert all(call[0] == "GET" for call in server.calls)
    server = media_servers.servers[kind]
    server.failure = 401
    result = await flow.async_step_connection_check({"source": kind})
    assert result["errors"] == {"base": "check_invalid_auth"}
    assert result["description_placeholders"]["authentication"] == "✗"
    assert test_media.KEY not in str(result)
    server.failure = 0
    assert not (await flow.async_step_connection_check({"source": kind}))["errors"]
