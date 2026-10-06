"""Deliberately minimal diagnostics: never dump configuration or API payloads."""

from .const import CONF_EPG, CONF_METADATA, CONF_POLL, DEFAULTS, VERSION


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = getattr(entry, "runtime_data", None)
    options = DEFAULTS | entry.options
    data = coordinator.data if coordinator and coordinator.data else {}
    media = getattr(coordinator, "media_coordinator", None)
    return {
        "integration_version": VERSION,
        "dispatcharr_version": entry.data.get("version"),
        "connected": bool(coordinator and coordinator.last_update_success),
        "intervals": {key: options[key] for key in (CONF_POLL, CONF_METADATA, CONF_EPG)},
        "active_channels": data.get("active_channels"),
        "viewer_count": data.get("viewer_count"),
        "warnings": data.get("warnings", []),
        "media_servers": [
            {key: source.get(key) for key in ("type", "connected", "error", "session_count")}
            for source in ((media.data or {}).get("media_sources", []) if media else [])
        ],
    }
