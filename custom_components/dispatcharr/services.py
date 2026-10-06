"""Separate, administrator-only actions with exact IDs."""

import voluptuous as vol
from homeassistant.core import callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.service import async_register_admin_service

from .api import DispatcharrError
from .const import DOMAIN


@callback
def async_setup_services(hass):
    if hass.services.has_service(DOMAIN, "stop_session"):
        return

    async def handle(call):
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if (
            not entry
            or entry.domain != DOMAIN
            or not getattr(entry, "runtime_data", None)
            or entry.state.value != "loaded"
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="instance_unavailable"
            )
        coordinator = entry.runtime_data
        try:
            if call.service == "stop_media_session":
                await coordinator.media_coordinator.stop(
                    call.data["source_id"], call.data["session_id"], call.data["item_id"]
                )
            else:
                await coordinator.controller.stop(
                    call.data["channel_uuid"],
                    call.data.get("client_id") if call.service == "stop_session" else None,
                    confirm_all=call.data.get("confirm_all", False),
                )
        except DispatcharrError as error:
            key = str(error)
            known = {
                "control_disabled",
                "confirmation_required",
                "session_expired",
                "stop_not_confirmed",
                "invalid_auth",
                "insufficient_permissions",
                "media_control_unavailable",
            }
            if call.service == "stop_media_session" and key in {
                "invalid_auth",
                "insufficient_permissions",
            }:
                key = "media_" + key
                known.add(key)
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key=key if key in known else "action_failed"
            ) from None

    common = {vol.Required("config_entry_id"): str, vol.Required("channel_uuid"): str}
    async_register_admin_service(
        hass,
        DOMAIN,
        "stop_media_session",
        handle,
        schema=vol.Schema(
            {
                vol.Required(key): str
                for key in ("config_entry_id", "source_id", "session_id", "item_id")
            }
        ),
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        "stop_session",
        handle,
        schema=vol.Schema(common | {vol.Required("client_id"): str}),
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        "stop_channel",
        handle,
        schema=vol.Schema(common | {vol.Required("confirm_all"): vol.All(bool, vol.Equal(True))}),
    )
