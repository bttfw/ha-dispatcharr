"""Verified media API contracts with synthetic sessions; no real streams opened."""

import copy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from aiohttp import ClientSession, web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.dispatcharr.api import (
    DispatcharrError,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
)
from custom_components.dispatcharr.config_flow import DispatcharrOptionsFlow
from custom_components.dispatcharr.coordinator import DispatcharrCoordinator
from custom_components.dispatcharr.media_api import MediaClient
from custom_components.dispatcharr.media_coordinator import MediaCoordinator
from custom_components.dispatcharr.sensor import DispatcharrCount, TotalStreams

KEY = "synthetic-private-key"


def emby_row(identity="session-one", user="42"):
    return {
        "Id": identity,
        "UserId": user,
        "UserName": "Same display name",
        "DeviceId": "device:with.dots",
        "DeviceName": "Test TV",
        "Client": "Test client",
        "SupportsRemoteControl": True,
        "PlayState": {
            "IsPaused": False,
            "PositionTicks": 1200000000,
            "MediaSourceId": "source1",
            "AudioStreamIndex": 1,
            "PlayMethod": "DirectPlay",
        },
        "NowPlayingItem": {
            "Id": "item1",
            "Name": "Test film",
            "Type": "Movie",
            "RunTimeTicks": 36000000000,
            "ImageTags": {"Primary": "abc123"},
            "MediaSources": [
                {
                    "Id": "source1",
                    "Bitrate": 8000000,
                    "MediaStreams": [
                        {
                            "Type": "Video",
                            "Codec": "h264",
                            "Width": 1920,
                            "Height": 1080,
                            "AverageFrameRate": 24,
                        },
                        {"Type": "Audio", "Index": 1, "Codec": "aac"},
                    ],
                }
            ],
        },
    }


def plex_row(identity="plex-session-one", user=42):
    return {
        "sessionKey": "wrong-session-key",
        "Session": {"id": identity},
        "ratingKey": "10",
        "User": {"id": user, "title": "Same display name"},
        "Player": {"machineIdentifier": "device:with.dots", "title": "Test TV", "state": "paused"},
        "title": "Test episode",
        "type": "episode",
        "grandparentTitle": "Example series",
        "parentIndex": 1,
        "index": 2,
        "viewOffset": 120000,
        "duration": 3600000,
        "thumb": "/library/metadata/10/thumb/1234",
        "Media": [
            {
                "width": 3840,
                "height": 2160,
                "bitrate": 24000,
                "videoCodec": "hevc",
                "audioCodec": "ac3",
            }
        ],
        "TranscodeSession": {
            "width": 1920,
            "height": 1080,
            "videoCodec": "h264",
            "audioCodec": "aac",
        },
    }


@pytest.fixture
async def media_servers(aiohttp_server):
    async with ClientSession() as session:
        servers = {}
        for kind in ("jellyfin", "emby", "plex"):
            state = SimpleNamespace(
                kind=kind,
                rows=[plex_row() if kind == "plex" else emby_row()],
                calls=[],
                failure=0,
                ignore_stop=False,
                claimed=True,
                total=None,
            )

            async def handler(request, state=state):
                state.calls.append(
                    (request.method, request.path, dict(request.query), dict(request.headers))
                )
                auth = (
                    request.headers.get("X-Plex-Token")
                    if state.kind == "plex"
                    else request.headers.get("Authorization")
                )
                expected = KEY if state.kind == "plex" else f'MediaBrowser Token="{KEY}"'
                if auth != expected:
                    return web.json_response({"secret": KEY}, status=401)
                if state.failure:
                    return web.json_response({"secret": KEY}, status=state.failure)
                if request.path == "/identity":
                    return web.json_response({"MediaContainer": {"claimed": state.claimed}})
                if request.path == "/":
                    return web.json_response(
                        {
                            "MediaContainer": {
                                "machineIdentifier": "server-plex",
                                "version": "1.43.4",
                            }
                        }
                    )
                if request.path == "/System/Info":
                    return web.json_response(
                        {
                            "Id": "server-" + state.kind,
                            "Version": "12.1.0" if state.kind == "jellyfin" else "4.10.1.0",
                        }
                    )
                if request.path in ("/Sessions", "/status/sessions"):
                    if state.kind != "plex":
                        return web.json_response(state.rows)
                    result = {"size": len(state.rows), "Metadata": state.rows}
                    if state.total is not None:
                        result["totalSize"] = state.total
                    return web.json_response({"MediaContainer": result})
                if request.method == "POST":
                    if getattr(state, "stop_failure", 0):
                        return web.json_response({"secret": KEY}, status=state.stop_failure)
                    identity = (
                        request.query["sessionId"]
                        if state.kind == "plex"
                        else request.path.split("/")[2]
                    )
                    if not state.ignore_stop:
                        state.rows = [
                            r
                            for r in state.rows
                            if (r["Session"]["id"] if state.kind == "plex" else r["Id"]) != identity
                        ]
                    return web.Response(text="OK", content_type="text/html")
                return web.Response(status=404)

            app = web.Application()
            app.router.add_route("*", "/{path:.*}", handler)
            server = await aiohttp_server(app)
            state.source = {
                "id": kind,
                "kind": kind,
                "name": kind.title(),
                "url": str(server.make_url("/")).rstrip("/"),
                "api_key": KEY,
                "server_id": "server-" + kind,
                "enable_control": True,
            }
            state.client = MediaClient(session, state.source)
            servers[kind] = state
        yield SimpleNamespace(servers=servers, session=session)


@pytest.fixture
async def media_hass(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    yield hass
    await hass.async_stop()


@pytest.fixture
def media_entry(media_servers, dispatcharr):
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain="dispatcharr",
        title="Media test",
        data={"url": dispatcharr.client.url, "api_key": "dispatcharr-key", "version": "0.31.0"},
        source="user",
        unique_id=None,
        discovery_keys={},
        subentries_data=[],
        options={
            "enable_control": True,
            "media_servers": [s.source for s in media_servers.servers.values()],
        },
    )


@pytest.mark.parametrize("kind", ["jellyfin", "emby", "plex"])
async def test_live_contract_normalization_and_header_only_auth(media_servers, kind):
    state = media_servers.servers[kind]
    assert (await state.client.validate())["server_id"] == "server-" + kind
    rows = await state.client.sessions()
    assert len(rows) == 1
    row = rows[0]
    assert row["user_id"] == "42" and row["position_seconds"] == 120
    assert row["device_id"] == "device:with.dots"
    assert row["source_type"] == kind and row["image_key"]
    assert KEY not in json.dumps(rows)
    assert all(
        KEY not in path and KEY not in json.dumps(query) for _, path, query, _ in state.calls
    )
    if kind == "plex":
        assert row["session_id"] == "plex-session-one"
        assert row["playback_status"] == "paused"
        assert row["source_resolution"] == "3840x2160"
        assert row["output_resolution"] == "1920x1080"
        assert row["source_fps"] is None
    else:
        assert row["source_bitrate_kbps"] == 8000
        assert row["video_codec"] == "h264" and row["source_fps"] == 24


@pytest.mark.parametrize("kind", ["jellyfin", "emby", "plex"])
async def test_invalid_key_is_rejected_without_response_body(media_servers, kind):
    state = media_servers.servers[kind]
    client = MediaClient(media_servers.session, state.source | {"api_key": "bad-key"})
    with pytest.raises(InvalidAuth) as error:
        await client.validate()
    assert KEY not in str(error.value)


async def test_partial_plex_response_and_unclaimed_server_rejected(media_servers):
    state = media_servers.servers["plex"]
    state.total = 2
    with pytest.raises(InvalidResponse, match="incomplete_sessions"):
        await state.client.sessions()
    state.claimed = False
    with pytest.raises(InvalidResponse, match="plex_unclaimed"):
        await state.client.validate()


async def test_plex_duplicate_termination_ids_keep_both_rows_without_unsafe_stop(
    media_hass, media_entry, media_servers
):
    state = media_servers.servers["plex"]
    second = copy.deepcopy(state.rows[0])
    second["sessionKey"] = "another-playback"
    state.rows.append(second)
    rows = await state.client.sessions()
    assert len(rows) == 2 and all(not row["can_stop"] for row in rows)
    coordinator = MediaCoordinator(media_hass, media_entry, media_servers.session)
    with pytest.raises(DispatcharrError, match="media_control_unavailable"):
        await coordinator.stop("plex", "plex-session-one", "10")
    assert not any(c[0] == "POST" for c in state.calls)
    await coordinator.async_shutdown()


async def test_plex_stop_feature_denial_is_not_reported_as_a_bad_key(media_servers):
    state = media_servers.servers["plex"]
    assert await state.client.validate()
    state.stop_failure = 401
    with pytest.raises(Forbidden, match="insufficient_permissions"):
        await state.client.stop("plex-session-one")


async def test_device_aliases_are_scoped_to_server_and_actual_device_id(
    media_hass, media_entry, media_servers
):
    jellyfin = (await media_servers.servers["jellyfin"].client.sessions())[0]
    emby = (await media_servers.servers["emby"].client.sessions())[0]
    assert jellyfin["device_id"] == emby["device_id"]
    assert jellyfin["device_key"] != emby["device_key"]
    options = dict(media_entry.options) | {
        "device_aliases": {jellyfin["device_key"]: "Living room"}
    }
    alias_entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain="dispatcharr",
        title="Alias test",
        data=dict(media_entry.data),
        source="user",
        unique_id=None,
        discovery_keys={},
        subentries_data=[],
        options=options,
    )
    coordinator = MediaCoordinator(media_hass, alias_entry, media_servers.session)
    await coordinator.async_refresh()
    rows = {r["source_id"]: r for r in coordinator.data["sessions"]}
    assert rows["jellyfin"]["device_alias"] == "Living room"
    assert rows["emby"]["device_alias"] is None
    await coordinator.async_shutdown()


async def test_media_redirect_is_rejected(media_servers):
    state = media_servers.servers["jellyfin"]
    state.failure = 302
    with pytest.raises(InvalidResponse, match="unexpected_http_status"):
        await state.client.sessions()


async def test_missing_metadata_unknown_and_no_logged_in_users_counted(media_servers):
    state = media_servers.servers["jellyfin"]
    state.rows = [
        {"Id": "idle", "UserName": "Idle user"},
        {"Id": "playing", "NowPlayingItem": {"Id": "item"}},
    ]
    rows = await state.client.sessions()
    assert len(rows) == 1
    row = rows[0]
    assert row["title"] is None and row["username"] is None and row["source_resolution"] is None
    assert row["duration_seconds"] is None and row["playback_status"] is None
    assert row["can_stop"] is False and row["image_key"] is None


async def test_unmatched_selected_source_does_not_report_other_quality(media_servers):
    state = media_servers.servers["emby"]
    state.rows[0]["PlayState"]["MediaSourceId"] = "other-source"
    row = (await state.client.sessions())[0]
    assert row["source_resolution"] is None and row["source_bitrate_kbps"] is None


async def test_source_isolation_recovery_and_no_name_deduplication(
    media_hass, media_entry, media_servers, dispatcharr
):
    coordinator = MediaCoordinator(media_hass, media_entry, media_servers.session)
    proxy = DispatcharrCoordinator(media_hass, media_entry, dispatcharr.client)
    await proxy.async_refresh()
    await coordinator.async_refresh()
    assert len(proxy.data["viewers"]) == 2 and len(coordinator.data["sessions"]) == 3
    last = coordinator.last_success["jellyfin"]
    media_servers.servers["jellyfin"].failure = 401
    dispatcharr.failures["/proxy/ts/status"] = 401
    await proxy.async_refresh()
    await coordinator.async_refresh()
    assert not proxy.last_update_success
    assert len(coordinator.data["sessions"]) == 2
    status = coordinator.data["media_sources"][0]
    assert status["error"] == "invalid_auth" and status["last_success"] == last
    for s in media_servers.servers.values():
        s.failure = 503
    await coordinator.async_refresh()
    assert coordinator.data["sessions"] == []
    assert all(not s["connected"] for s in coordinator.data["media_sources"])
    for s in media_servers.servers.values():
        s.failure = 0
    await coordinator.async_refresh()
    assert len(coordinator.data["sessions"]) == 3
    assert KEY not in json.dumps(coordinator.data)
    await coordinator.async_shutdown()
    await proxy.async_shutdown()


@pytest.fixture
async def stream_counter(media_hass, media_entry, media_servers, dispatcharr):
    proxy = DispatcharrCoordinator(media_hass, media_entry, dispatcharr.client)
    media = MediaCoordinator(media_hass, media_entry, media_servers.session)
    proxy.media_coordinator = media
    counter = TotalStreams(proxy)
    yield counter
    await proxy.async_shutdown()
    await media.async_shutdown()


async def test_total_streams_counts_all_sources_without_changing_existing_counts(stream_counter):
    counter = stream_counter
    assert not counter.available and counter.native_value is None
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    assert counter.available and counter.native_value == 5  # 2 clients + JF/Emby/Plex
    assert counter.extra_state_attributes == {
        "dispatcharr_clients": 2,
        "media_sessions": 3,
        "complete": True,
        "unavailable_sources": [],
    }
    # Both clients share one channel; all media sources have the same user name.
    assert (
        DispatcharrCount(counter.coordinator, "active_channels", "mdi:television").native_value == 1
    )
    assert (
        DispatcharrCount(counter.coordinator, "viewer_count", "mdi:account-group").native_value == 2
    )


async def test_total_streams_updates_from_either_coordinator_and_removes_listeners(
    stream_counter, dispatcharr, media_servers
):
    counter = stream_counter
    callbacks = []
    counter.async_on_remove = callbacks.append
    counter.async_write_ha_state = Mock()
    await counter.async_added_to_hass()
    assert len(callbacks) == 2
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    assert counter.async_write_ha_state.call_count == 2
    assert counter.native_value == 5
    media_servers.servers["jellyfin"].rows.append(emby_row("session-two"))
    await counter.media_coordinator.async_refresh()
    assert counter.native_value == 6
    dispatcharr.channels.clear()
    await counter.coordinator.async_refresh()
    assert counter.native_value == 4
    assert counter.async_write_ha_state.call_count == 4
    calls = len(dispatcharr.calls) + sum(len(s.calls) for s in media_servers.servers.values())
    for _ in range(5):
        assert counter.available and counter.native_value == 4
        assert counter.extra_state_attributes["complete"]
    assert calls == len(dispatcharr.calls) + sum(
        len(s.calls) for s in media_servers.servers.values()
    )
    for remove in callbacks:
        remove()
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    assert counter.async_write_ha_state.call_count == 4


async def test_total_streams_outages_do_not_reuse_stale_counts_and_recover(
    stream_counter, dispatcharr, media_servers
):
    counter = stream_counter
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    assert counter.native_value == 5
    dispatcharr.failures["/proxy/ts/status"] = 503
    await counter.coordinator.async_refresh()
    assert counter.available and counter.native_value == 3
    assert counter.extra_state_attributes["dispatcharr_clients"] is None
    assert counter.extra_state_attributes["unavailable_sources"] == ["dispatcharr"]
    assert counter.extra_state_attributes["complete"] is False
    media_servers.servers["jellyfin"].failure = 401
    await counter.media_coordinator.async_refresh()
    assert counter.native_value == 2
    assert set(counter.extra_state_attributes["unavailable_sources"]) == {"dispatcharr", "jellyfin"}
    for source in media_servers.servers.values():
        source.failure = 503
    await counter.media_coordinator.async_refresh()
    assert not counter.available and counter.native_value is None
    assert counter.extra_state_attributes["media_sessions"] is None
    for source in media_servers.servers.values():
        source.failure = 0
        source.rows.clear()
    await counter.media_coordinator.async_refresh()
    assert counter.available and counter.native_value == 0
    assert counter.extra_state_attributes["complete"] is False
    dispatcharr.failures.clear()
    dispatcharr.channels.clear()
    await counter.coordinator.async_refresh()
    assert counter.native_value == 0 and counter.extra_state_attributes["complete"]


async def test_total_streams_dispatcharr_only_and_missing_media_snapshot(stream_counter):
    counter = stream_counter
    await counter.coordinator.async_refresh()
    counter.media_coordinator.clients.clear()
    assert counter.native_value == 2 and counter.extra_state_attributes["complete"]
    assert counter.extra_state_attributes["media_sessions"] == 0
    counter.media_coordinator.clients["new-server"] = object()
    assert counter.native_value == 2 and not counter.extra_state_attributes["complete"]
    assert counter.extra_state_attributes["unavailable_sources"] == ["new-server"]
    counter.media_coordinator.clients.clear()


async def test_total_streams_media_coordinator_failure_drops_cached_snapshot(stream_counter):
    from homeassistant.helpers.update_coordinator import UpdateFailed

    counter = stream_counter
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    counter.media_coordinator.async_set_update_error(UpdateFailed("synthetic failure"))
    assert counter.native_value == 2
    assert counter.extra_state_attributes["media_sessions"] is None
    assert set(counter.extra_state_attributes["unavailable_sources"]) == {
        "jellyfin",
        "emby",
        "plex",
    }
    await counter.media_coordinator.async_refresh()
    assert counter.native_value == 5 and counter.extra_state_attributes["complete"]


async def test_total_streams_multiple_servers_same_type_and_stable_id(
    stream_counter, media_servers, media_hass, media_entry, dispatcharr
):
    counter = stream_counter
    second_source = {**media_servers.servers["jellyfin"].source, "id": "jellyfin-two"}
    counter.media_coordinator.clients["jellyfin-two"] = MediaClient(
        media_servers.session, second_source
    )
    await counter.coordinator.async_refresh()
    await counter.media_coordinator.async_refresh()
    assert counter.native_value == 6
    replacement = DispatcharrCoordinator(media_hass, media_entry, dispatcharr.client)
    replacement.media_coordinator = counter.media_coordinator
    assert TotalStreams(replacement).unique_id == counter.unique_id
    await replacement.async_shutdown()


async def test_total_streams_registered_automatically(stream_counter, media_hass):
    from custom_components.dispatcharr.sensor import async_setup_entry

    entry = SimpleNamespace(runtime_data=stream_counter.coordinator)
    entities = []
    await async_setup_entry(media_hass, entry, entities.extend)
    assert sum(isinstance(entity, TotalStreams) for entity in entities) == 1


@pytest.mark.parametrize("kind", ["jellyfin", "emby", "plex"])
async def test_stop_exact_one_of_two_sessions_and_refresh(
    media_hass, media_entry, media_servers, kind
):
    state = media_servers.servers[kind]
    second = copy.deepcopy(state.rows[0])
    if kind == "plex":
        second["Session"]["id"] = "session-two"
        second["sessionKey"] = "second-session-key"
    else:
        second["Id"] = "session-two"
    state.rows.append(second)
    coordinator = MediaCoordinator(media_hass, media_entry, media_servers.session)
    await coordinator.async_refresh()
    row = next(
        r
        for r in coordinator.data["sessions"]
        if r["source_id"] == kind and r["session_id"] != "session-two"
    )
    await coordinator.stop(kind, row["session_id"], row["item_id"])
    remaining = [r for r in coordinator.data["sessions"] if r["source_id"] == kind]
    assert len(remaining) == 1 and remaining[0]["session_id"] == "session-two"
    posts = [(method, path, query) for method, path, query, _ in state.calls if method == "POST"]
    assert len(posts) == 1
    if kind == "plex":
        assert posts[0][1] == "/status/sessions/terminate"
        assert posts[0][2]["sessionId"] == "plex-session-one"
    else:
        assert posts[0][1] == "/Sessions/session-one/Playing/Stop"
    assert all(
        not any(c[0] == "POST" for c in s.calls)
        for k, s in media_servers.servers.items()
        if k != kind
    )
    await coordinator.async_shutdown()


async def test_stale_item_disabled_controls_and_no_fallback(media_hass, media_entry, media_servers):
    coordinator = MediaCoordinator(media_hass, media_entry, media_servers.session)
    state = media_servers.servers["jellyfin"]
    with pytest.raises(DispatcharrError, match="session_expired"):
        await coordinator.stop("jellyfin", "session-one", "previous-item")
    state.source["enable_control"] = False
    with pytest.raises(DispatcharrError, match="control_disabled"):
        await coordinator.stop("jellyfin", "session-one", "item1")
    assert not any(c[0] == "POST" for c in state.calls)
    state.source["enable_control"] = True
    state.ignore_stop = True
    with pytest.raises(DispatcharrError, match="stop_not_confirmed"):
        await coordinator.stop("jellyfin", "session-one", "item1")
    assert [c[1] for c in state.calls if c[0] == "POST"] == ["/Sessions/session-one/Playing/Stop"]
    await coordinator.async_shutdown()


async def test_media_gui_validates_duplicate_and_preserves_secrets(
    media_hass, media_entry, media_servers, monkeypatch
):
    import custom_components.dispatcharr.media_config as module

    monkeypatch.setattr(module, "async_get_clientsession", lambda hass: media_servers.session)
    monkeypatch.setattr(DispatcharrOptionsFlow, "config_entry", property(lambda self: media_entry))
    flow = DispatcharrOptionsFlow()
    flow.hass = media_hass
    source = media_servers.servers["jellyfin"].source
    result = await flow.async_step_media_add(source)
    assert result["errors"] == {"base": "media_duplicate"}
    await flow.async_step_media_manage({"source": "jellyfin", "action": "edit"})
    form = await flow.async_step_media_edit()
    assert (
        form["data_schema"]({"kind": "jellyfin", "name": "new", "url": source["url"]})["api_key"]
        == ""
    )
    result = await flow.async_step_media_edit(
        {
            "kind": "jellyfin",
            "name": "New label",
            "url": source["url"],
            "api_key": "",
            "enable_control": False,
        }
    )
    sources = result["data"]["media_servers"]
    assert len(sources) == 3
    assert sources[0]["api_key"] == KEY and sources[0]["id"] == "jellyfin"
    assert sources[0]["name"] == "New label" and not sources[0]["enable_control"]
