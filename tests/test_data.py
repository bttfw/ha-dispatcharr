import json
import time
from unittest.mock import AsyncMock

import pytest
from conftest import KEY, OTHER_UUID, UUID, channel

from custom_components.dispatcharr.api import DispatcharrError, Forbidden
from custom_components.dispatcharr.data import SessionController, SnapshotLoader
from custom_components.dispatcharr.models import device_key, number


async def test_two_viewers_one_channel_and_id_identity(dispatcharr):
    dispatcharr.channels[0]["clients"][1]["user_id"] = "99"
    snap = await SnapshotLoader(dispatcharr.client).snapshot()
    assert snap["active_channels"] == 1 and snap["viewer_count"] == 2
    assert snap["viewers"][0]["username"] == "Actual user"
    assert snap["viewers"][1]["username"] is None
    assert snap["viewers"][0]["channel_id"] == "92"
    assert snap["viewers"][0]["provider"] == "Example provider"
    assert snap["viewers"][0]["output_profile"] == "Example output"
    assert KEY not in json.dumps(snap) and "private/password" not in json.dumps(snap)


async def test_cache_and_targeted_epg(dispatcharr):
    clock = [1000]
    loader = SnapshotLoader(dispatcharr.client, clock=lambda: clock[0])
    await loader.snapshot()
    dispatcharr.calls.clear()
    clock[0] += 10
    await loader.snapshot()
    assert dispatcharr.calls == [("GET", "/proxy/ts/status", None)]
    clock[0] += 60
    await loader.snapshot()
    assert [c for c in dispatcharr.calls if "epg" in c[1]] == [
        ("POST", "/api/epg/current-programs/", {"channel_uuids": [UUID]})
    ]
    assert not any("by-uuids" in c[1] for c in dispatcharr.calls)


async def test_new_active_channel_fetches_only_its_metadata(dispatcharr):
    loader = SnapshotLoader(dispatcharr.client)
    await loader.snapshot()
    dispatcharr.calls.clear()
    extra = channel(1)
    extra["channel_id"] = OTHER_UUID
    dispatcharr.channels.append(extra)
    await loader.snapshot()
    assert (
        "POST",
        "/api/channels/channels/by-uuids/",
        {"uuids": [OTHER_UUID]},
    ) in dispatcharr.calls
    assert (
        "POST",
        "/api/epg/current-programs/",
        {"channel_uuids": [OTHER_UUID]},
    ) in dispatcharr.calls


async def test_no_epg_call_when_nobody_watches(dispatcharr):
    dispatcharr.channels.clear()
    result = await SnapshotLoader(dispatcharr.client).snapshot()
    assert result["viewer_count"] == result["active_channels"] == 0
    assert not any("epg" in path for _, path, _ in dispatcharr.calls)


async def test_missing_data_and_expired_programme(dispatcharr):
    dispatcharr.metadata.clear()
    dispatcharr.users.clear()
    dispatcharr.programmes[0]["end_time"] = time.time() - 10
    row = dispatcharr.channels[0]
    for field in ("resolution", "source_fps", "video_codec", "audio_codec", "avg_bitrate_kbps"):
        row.pop(field)
    row["channel_name"] = "Example UHD 4K"
    result = (await SnapshotLoader(dispatcharr.client).snapshot())["viewers"][0]
    assert all(
        result[key] is None
        for key in (
            "username",
            "source_resolution",
            "source_fps",
            "programme",
            "logo_id",
            "playback_status",
        )
    )


async def test_optional_endpoint_failure_does_not_hide_viewers(dispatcharr):
    dispatcharr.failures["/api/epg/current-programs/"] = 500
    dispatcharr.failures["/api/channels/channels/by-uuids/"] = 500
    result = await SnapshotLoader(dispatcharr.client).snapshot()
    assert result["viewer_count"] == 2
    assert set(result["warnings"]) == {"epg_unavailable", "metadata_unavailable"}


async def test_metadata_failure_remains_visible_and_recovers_without_fifteen_minute_wait(
    dispatcharr,
):
    clock = [1000]
    loader = SnapshotLoader(dispatcharr.client, clock=lambda: clock[0])
    dispatcharr.failures["/api/channels/channels/by-uuids/"] = 500
    assert "metadata_unavailable" in (await loader.snapshot())["warnings"]
    clock[0] += 10
    assert "metadata_unavailable" in (await loader.snapshot())["warnings"]
    dispatcharr.failures.clear()
    clock[0] += 51
    result = await loader.snapshot()
    assert result["warnings"] == [] and result["viewers"][0]["logo_id"] == 3


async def test_expired_channel_fails_without_post(dispatcharr):
    dispatcharr.channels.clear()
    with pytest.raises(DispatcharrError, match="session_expired"):
        await SessionController(dispatcharr.client, AsyncMock(), lambda: True).stop(
            UUID, "client_0"
        )
    assert not any(c[0] == "POST" for c in dispatcharr.calls)


async def test_cached_viewer_data_excludes_key_even_if_upstream_echoes_it(dispatcharr):
    dispatcharr.channels[0]["clients"][0]["user_agent"] = "Player " + KEY
    result = await SnapshotLoader(dispatcharr.client).snapshot()
    assert KEY not in json.dumps(result)


async def test_alias_is_explicit_and_instance_local(dispatcharr):
    key = device_key(dispatcharr.channels[0]["clients"][0])
    one, two = SnapshotLoader(dispatcharr.client), SnapshotLoader(dispatcharr.client)
    assert (await one.snapshot({key: "Living room"}))["viewers"][0]["device_alias"] == "Living room"
    assert (await two.snapshot())["viewers"][0]["device_alias"] is None


async def test_stop_one_client_preserves_other_viewer(dispatcharr):
    refresh = AsyncMock()
    control = SessionController(dispatcharr.client, refresh, lambda: True, sleep=AsyncMock())
    await control.stop(UUID, "client_0")
    assert [x["client_id"] for x in dispatcharr.channels[0]["clients"]] == ["client_1"]
    assert [c for c in dispatcharr.calls if c[0] == "POST"] == [
        ("POST", f"/proxy/ts/stop_client/{UUID}", {"client_id": "client_0"})
    ]
    refresh.assert_awaited_once()
    assert sum(path == f"/proxy/ts/status/{UUID}" for _, path, _ in dispatcharr.calls) == 2


async def test_expired_session_never_sends_stop(dispatcharr):
    refresh = AsyncMock()
    with pytest.raises(DispatcharrError, match="session_expired"):
        await SessionController(dispatcharr.client, refresh, lambda: True).stop(UUID, "expired")
    assert not any(c[0] == "POST" for c in dispatcharr.calls)
    refresh.assert_awaited_once()


async def test_disabled_controls(dispatcharr):
    with pytest.raises(DispatcharrError, match="control_disabled"):
        await SessionController(dispatcharr.client, AsyncMock(), lambda: False).stop(
            UUID, "client_0"
        )
    assert dispatcharr.calls == []


async def test_channel_stop_requires_confirmation(dispatcharr):
    control = SessionController(dispatcharr.client, AsyncMock(), lambda: True)
    with pytest.raises(DispatcharrError, match="confirmation_required"):
        await control.stop(UUID)
    assert dispatcharr.calls == []
    await control.stop(UUID, confirm_all=True)
    assert dispatcharr.channels == []
    assert ("POST", f"/proxy/ts/stop/{UUID}", {}) in dispatcharr.calls


async def test_stop_permission_failure_refreshes_and_never_falls_back(dispatcharr):
    refresh = AsyncMock()
    dispatcharr.failures[f"/proxy/ts/stop_client/{UUID}"] = 403
    with pytest.raises(Forbidden):
        await SessionController(dispatcharr.client, refresh, lambda: True).stop(UUID, "client_0")
    assert len(dispatcharr.channels[0]["clients"]) == 2
    assert not any(path == f"/proxy/ts/stop/{UUID}" for _, path, _ in dispatcharr.calls)
    refresh.assert_awaited_once()


async def test_acknowledgement_is_not_stop_confirmation(dispatcharr):
    dispatcharr.ignore_stop = True
    with pytest.raises(DispatcharrError, match="stop_not_confirmed"):
        await SessionController(
            dispatcharr.client, AsyncMock(), lambda: True, sleep=AsyncMock()
        ).stop(UUID, "client_0")
    assert len(dispatcharr.channels[0]["clients"]) == 2
    assert not any(path == f"/proxy/ts/stop/{UUID}" for _, path, _ in dispatcharr.calls)


@pytest.mark.parametrize("value", [None, "invalid", "nan", "inf", -1, True])
def test_invalid_measurements_stay_unknown(value):
    assert number(value) is None
