"""Exercise the real HA resource collection used to load the bundled card."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.lovelace import LovelaceData
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.dashboard import LovelaceStorage
from homeassistant.components.lovelace.resources import (
    ResourceStorageCollection,
    ResourceYAMLCollection,
)
from homeassistant.core import HomeAssistant

from custom_components.dispatcharr.const import CARD_URL
from custom_components.dispatcharr.frontend import async_setup_frontend


@pytest.fixture
async def frontend_hass(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock(), register_view=Mock())
    resources = ResourceStorageCollection(hass, LovelaceStorage(hass, None))
    hass.data[LOVELACE_DATA] = LovelaceData("storage", {}, resources, {})
    yield hass
    await hass.async_stop()


async def test_first_setup_registers_module_in_lovelace(frontend_hass):
    await async_setup_frontend(frontend_hass)
    items = frontend_hass.data[LOVELACE_DATA].resources.async_items()
    assert len(items) == 1
    assert items[0]["url"] == CARD_URL
    assert items[0]["type"] == "module"


async def test_concurrent_instances_and_reload_do_not_duplicate(frontend_hass):
    await asyncio.gather(*(async_setup_frontend(frontend_hass) for _ in range(3)))
    await async_setup_frontend(frontend_hass)
    assert len(frontend_hass.data[LOVELACE_DATA].resources.async_items()) == 1
    frontend_hass.http.async_register_static_paths.assert_awaited_once()
    assert [call.args[0].name for call in frontend_hass.http.register_view.call_args_list] == [
        "api:dispatcharr:logo",
        "api:dispatcharr:media_image",
    ]


async def test_version_upgrade_deduplicates_only_our_local_card(frontend_hass):
    resources = frontend_hass.data[LOVELACE_DATA].resources
    previous = await resources.async_create_item(
        {"url": "/dispatcharr_static/dispatcharr-card.js?v=0.1.2", "res_type": "js"}
    )
    await resources.async_create_item(
        {"url": "/dispatcharr_static/dispatcharr-card.js", "res_type": "module"}
    )
    others = [
        await resources.async_create_item({"url": url, "res_type": "module"})
        for url in (
            "/local/another-card.js",
            "https://example.invalid/dispatcharr_static/dispatcharr-card.js",
        )
    ]
    await async_setup_frontend(frontend_hass)
    items = resources.async_items()
    assert len(items) == 3
    assert {**previous, "url": CARD_URL, "type": "module"} in items
    assert all(other in items for other in others)


async def test_restart_loads_existing_resource_from_storage(frontend_hass):
    resources = frontend_hass.data[LOVELACE_DATA].resources
    previous = await resources.async_create_item(
        {"url": "/dispatcharr_static/dispatcharr-card.js?v=0.1.2", "res_type": "module"}
    )
    await resources.store.async_save({"items": resources.async_items()})
    restored = ResourceStorageCollection(frontend_hass, LovelaceStorage(frontend_hass, None))
    frontend_hass.data[LOVELACE_DATA].resources = restored
    await async_setup_frontend(frontend_hass)
    assert restored.async_items() == [{**previous, "url": CARD_URL}]


async def test_yaml_owned_resources_are_not_modified(frontend_hass, monkeypatch):
    extra_module = Mock()
    monkeypatch.setattr(
        "custom_components.dispatcharr.frontend.frontend.add_extra_js_url", extra_module
    )
    items = [{"url": "/local/owner-managed.js", "type": "module"}]
    frontend_hass.data[LOVELACE_DATA].resources = ResourceYAMLCollection(items.copy())
    await async_setup_frontend(frontend_hass)
    assert frontend_hass.data[LOVELACE_DATA].resources.async_items() == items
    extra_module.assert_called_once_with(frontend_hass, CARD_URL)
