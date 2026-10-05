"""Exercise real HA classes against the synthetic Dispatcharr API."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, Unauthorized

from custom_components.dispatcharr.binary_sensor import DispatcharrConnectivity
from custom_components.dispatcharr.config_flow import DispatcharrConfigFlow, DispatcharrOptionsFlow
from custom_components.dispatcharr.coordinator import DispatcharrCoordinator
from custom_components.dispatcharr.diagnostics import async_get_config_entry_diagnostics
from custom_components.dispatcharr.sensor import DispatcharrCount, LastSuccess
from custom_components.dispatcharr.services import async_setup_services


@pytest.fixture
async def hass(tmp_path):
    instance = HomeAssistant(str(tmp_path))
    yield instance
    await instance.async_stop()


@pytest.fixture
def entry(dispatcharr):
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain="dispatcharr",
        title="Test instance",
        data={
            "url": dispatcharr.client.url,
            "api_key": dispatcharr.client._api_key,
            "version": "0.31.0",
        },
        source="user",
        unique_id=None,
        options={},
        discovery_keys={},
        subentries_data=[],
    )


async def test_coordinator_outage_and_recovery(hass, entry, dispatcharr):
    coordinator = DispatcharrCoordinator(hass, entry, dispatcharr.client)
    connection = DispatcharrConnectivity(coordinator)
    count = DispatcharrCount(coordinator, "viewer_count", "mdi:account-group")
    last = LastSuccess(coordinator)
    await coordinator.async_refresh()
    assert connection.is_on and count.available and count.native_value == 2
    timestamp = last.native_value
    dispatcharr.failures["/proxy/ts/status"] = 500
    await coordinator.async_refresh()
    assert not connection.is_on and connection.available
    assert not count.available and last.available and last.native_value == timestamp
    dispatcharr.failures.clear()
    await coordinator.async_refresh()
    assert connection.is_on and count.available and last.native_value >= timestamp
    await coordinator.async_shutdown()


async def test_coordinator_auth_failure(hass, entry, dispatcharr):
    coordinator = DispatcharrCoordinator(hass, entry, dispatcharr.client)
    dispatcharr.failures["/proxy/ts/status"] = 401
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_entity_ids_survive_new_coordinator(hass, entry, dispatcharr):
    one = DispatcharrCount(
        DispatcharrCoordinator(hass, entry, dispatcharr.client), "viewer_count", "mdi:account-group"
    )
    two = DispatcharrCount(
        DispatcharrCoordinator(hass, entry, dispatcharr.client), "viewer_count", "mdi:account-group"
    )
    assert one.unique_id == two.unique_id
    assert dispatcharr.client.url not in one.unique_id


async def test_last_success_link_uses_entity_registry_after_rename(hass, entry, dispatcharr):
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    registry = er.async_get(hass)
    await registry.async_load()
    viewer = registry.async_get_or_create("sensor", "dispatcharr", f"{entry.entry_id}_viewer_count")
    registry.async_update_entity(viewer.entity_id, new_entity_id="sensor.renamed_viewers")
    coordinator = DispatcharrCoordinator(hass, entry, dispatcharr.client)
    last = LastSuccess(coordinator)
    last.hass = hass
    assert last.extra_state_attributes == {"viewer_entity_id": "sensor.renamed_viewers"}
    await coordinator.async_refresh()
    timestamp = last.native_value
    dispatcharr.failures["/proxy/ts/status"] = 503
    await coordinator.async_refresh()
    assert last.available and last.native_value == timestamp
    assert last.extra_state_attributes["viewer_entity_id"] == "sensor.renamed_viewers"
    await coordinator.async_shutdown()


async def test_diagnostics_never_dump_private_data(hass, entry, dispatcharr):
    import json

    coordinator = DispatcharrCoordinator(hass, entry, dispatcharr.client)
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    report = json.dumps(await async_get_config_entry_diagnostics(hass, entry))
    for private in (
        dispatcharr.client._api_key,
        dispatcharr.client.url,
        "Actual user",
        "client_0",
        "192.0.2",
    ):
        assert private not in report
    await coordinator.async_shutdown()


async def test_flow_only_requires_url_and_api_key(hass, dispatcharr, monkeypatch):
    import custom_components.dispatcharr.config_flow as module

    monkeypatch.setattr(module, "async_get_clientsession", lambda hass: dispatcharr.client.session)
    flow = DispatcharrConfigFlow()
    flow.hass = hass
    flow._async_current_entries = lambda: []
    first = await flow.async_step_user()
    assert {str(k) for k in first["data_schema"].schema} == {"url", "api_key"}
    bad = await flow.async_step_user({"url": dispatcharr.client.url, "api_key": "invalid"})
    assert bad["errors"] == {"base": "invalid_auth"}
    forbidden = await flow.async_step_user({"url": "http://user:secret@host", "api_key": "x"})
    assert forbidden["errors"] == {"url": "invalid_url"}
    dispatcharr.admin = False
    denied = await flow.async_step_user(
        {"url": dispatcharr.client.url, "api_key": dispatcharr.client._api_key}
    )
    assert denied["errors"] == {"base": "insufficient_permissions"}


async def test_options_are_gui_menu_with_bounded_advanced_fields(hass, entry, monkeypatch):
    monkeypatch.setattr(DispatcharrOptionsFlow, "config_entry", property(lambda self: entry))
    flow = DispatcharrOptionsFlow()
    flow.hass = hass
    menu = await flow.async_step_init()
    assert menu["menu_options"] == ["control", "aliases", "advanced"]
    control = await flow.async_step_control()
    assert control["data_schema"]({}) == {"enable_control": False}
    advanced = await flow.async_step_advanced()
    assert advanced["data_schema"]({}) == {
        "poll_interval": 10,
        "metadata_interval": 900,
        "epg_interval": 60,
    }
    assert (await flow.async_step_aliases())["reason"] == "no_devices"


async def test_alias_flow_choices_are_observed_devices(hass, entry, dispatcharr, monkeypatch):
    coordinator = DispatcharrCoordinator(hass, entry, dispatcharr.client)
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    monkeypatch.setattr(DispatcharrOptionsFlow, "config_entry", property(lambda self: entry))
    flow = DispatcharrOptionsFlow()
    flow.hass = hass
    result = await flow.async_step_aliases()
    assert result["step_id"] == "aliases"
    assert {str(k) for k in result["data_schema"].schema} == {"device", "alias"}
    await coordinator.async_shutdown()


def test_translations_cover_every_error_and_control():
    import json

    root = Path(__file__).parents[1] / "custom_components/dispatcharr"
    en = json.loads((root / "strings.json").read_text())
    de = json.loads((root / "translations/de.json").read_text())

    def paths(node, prefix=""):
        return {
            p
            for key, value in node.items()
            for p in (
                paths(value, prefix + key + ".") if isinstance(value, dict) else [prefix + key]
            )
        }

    assert paths(en) == paths(de)


async def test_stop_service_rejects_non_admin_before_network(hass, dispatcharr):
    hass.auth = SimpleNamespace(
        async_get_user=AsyncMock(return_value=SimpleNamespace(is_admin=False))
    )
    async_setup_services(hass)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "dispatcharr",
            "stop_session",
            {
                "config_entry_id": "any",
                "channel_uuid": "11111111-2222-4333-8444-555555555555",
                "client_id": "client_0",
            },
            blocking=True,
            context=Context(user_id="not-an-admin"),
        )
    assert dispatcharr.calls == []
