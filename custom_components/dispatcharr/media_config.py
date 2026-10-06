"""GUI management for optional, independently authenticated media sources."""

from uuid import uuid4

import voluptuous as vol
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, Forbidden, InvalidAuth, InvalidResponse, NotFound
from .const import CONF_CONTROL
from .media_api import MEDIA_KINDS, MediaClient
from .media_coordinator import CONF_MEDIA


class MediaOptionsMixin:
    async def async_step_media(self, user_input=None):
        return self.async_show_menu(step_id="media", menu_options=["media_add", "media_manage"])

    async def async_step_media_add(self, user_input=None):
        if len(self.config_entry.options.get(CONF_MEDIA, [])) >= 16:
            return self.async_abort(reason="media_limit")
        return await self._media_form("media_add", {}, user_input)

    async def async_step_media_manage(self, user_input=None):
        sources = self.config_entry.options.get(CONF_MEDIA, [])
        if not sources:
            return self.async_abort(reason="no_media_servers")
        if user_input is not None:
            self._media_source = next((s for s in sources if s["id"] == user_input["source"]), None)
            if not self._media_source:
                return self.async_abort(reason="no_media_servers")
            if user_input["action"] == "remove":
                return await self.async_step_media_remove()
            return await self.async_step_media_edit()
        return self.async_show_form(
            step_id="media_manage",
            data_schema=vol.Schema(
                {
                    vol.Required("source"): selector.SelectSelector(
                        {
                            "options": [
                                {"value": s["id"], "label": f"{s['name']} ({s['kind']})"}
                                for s in sources
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required("action", default="edit"): selector.SelectSelector(
                        {
                            "options": ["edit", "remove"],
                            "translation_key": "media_action",
                            "mode": "dropdown",
                        }
                    ),
                }
            ),
        )

    async def async_step_media_edit(self, user_input=None):
        return await self._media_form("media_edit", self._media_source, user_input)

    async def async_step_media_remove(self, user_input=None):
        if user_input is not None and user_input.get("confirm") is True:
            sources = [
                s
                for s in self.config_entry.options.get(CONF_MEDIA, [])
                if s["id"] != self._media_source["id"]
            ]
            return self.async_create_entry(
                data=dict(self.config_entry.options) | {CONF_MEDIA: sources}
            )
        return self.async_show_form(
            step_id="media_remove",
            description_placeholders={"name": self._media_source["name"]},
            data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
        )

    async def _media_form(self, step, existing, user_input):
        errors = {}
        if user_input is not None:
            source = {**existing, **user_input, "id": existing.get("id", uuid4().hex)}
            source["api_key"] = user_input.get("api_key", "").strip() or existing.get("api_key", "")
            try:
                client = MediaClient(async_get_clientsession(self.hass), source)
                info = await client.validate()
                sources = self.config_entry.options.get(CONF_MEDIA, [])
                if any(
                    s["id"] != source["id"]
                    and s["kind"] == source["kind"]
                    and (s["server_id"] == info["server_id"] or s["url"] == client.url)
                    for s in sources
                ):
                    errors["base"] = "media_duplicate"
                else:
                    source.update(info, url=client.url, name=client.name[:80])
                    updated = [source if s["id"] == source["id"] else s for s in sources]
                    if not existing:
                        updated.append(source)
                    return self.async_create_entry(
                        data=dict(self.config_entry.options) | {CONF_MEDIA: updated}
                    )
            except ValueError:
                errors["url"] = "invalid_url"
            except InvalidAuth:
                errors["base"] = "media_invalid_auth"
            except Forbidden:
                errors["base"] = "media_permissions"
            except CannotConnect:
                errors["base"] = "media_cannot_connect"
            except (InvalidResponse, NotFound) as error:
                errors["base"] = (
                    "plex_unclaimed" if str(error) == "plex_unclaimed" else "media_unsupported_api"
                )
        return self.async_show_form(
            step_id=step,
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "kind", default=existing.get("kind", "jellyfin")
                    ): selector.SelectSelector(
                        {
                            "options": list(MEDIA_KINDS),
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required("name", default=existing.get("name", "")): selector.TextSelector(),
                    vol.Required("url", default=existing.get("url", "")): selector.TextSelector(
                        {"type": "url"}
                    ),
                    (
                        vol.Optional("api_key", default="") if existing else vol.Required("api_key")
                    ): selector.TextSelector({"type": "password"}),
                    vol.Required(CONF_CONTROL, default=existing.get(CONF_CONTROL, False)): bool,
                }
            ),
        )
