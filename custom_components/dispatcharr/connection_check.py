"""On-demand GUI checks. No configuration changes or playback actions."""

import voluptuous as vol
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    CannotConnect,
    DispatcharrClient,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
    NotFound,
    ValidationChecks,
    connection_error_reason,
)
from .media_api import MediaClient
from .media_coordinator import CONF_MEDIA


class ConnectionCheckMixin:
    async def async_step_connection_check(self, user_input=None):
        sources = self.config_entry.options.get(CONF_MEDIA, [])
        choices = [{"value": "dispatcharr", "label": "Dispatcharr"}]
        choices.extend(
            {"value": source["id"], "label": f"{source['name']} ({source['kind']})"}
            for source in sources
        )
        if user_input is None:
            return self.async_show_form(
                step_id="connection_check",
                data_schema=vol.Schema(
                    {
                        vol.Required("source", default="dispatcharr"): selector.SelectSelector(
                            {"options": choices, "mode": "dropdown"}
                        )
                    }
                ),
            )
        selected = user_input.get("source")
        if selected not in {choice["value"] for choice in choices}:
            return self.async_abort(reason="no_media_servers")
        session = async_get_clientsession(self.hass)
        checks = ValidationChecks()
        errors = {}
        name = "Dispatcharr"
        try:
            if selected == "dispatcharr":
                client = DispatcharrClient(
                    session, self.config_entry.data["url"], self.config_entry.data["api_key"]
                )
            else:
                source = next(s for s in sources if s["id"] == selected)
                client = MediaClient(session, source)
                name = client.name
            await client.validate(checks)
        except InvalidAuth:
            errors["base"] = "check_invalid_auth"
        except Forbidden:
            errors["base"] = "check_permissions"
        except CannotConnect as error:
            errors["base"] = connection_error_reason(error)
        except (InvalidResponse, NotFound) as error:
            errors["base"] = (
                "plex_unclaimed" if str(error) == "plex_unclaimed" else "check_unsupported_api"
            )
        except ValueError:
            errors["base"] = "invalid_url"
        self._check_result = {
            "step_id": "connection_result"
            if selected == "dispatcharr"
            else "media_connection_result",
            "data_schema": vol.Schema({}),
            "description_placeholders": {"name": name, **checks.results},
            "errors": errors,
        }
        return self.async_show_form(**self._check_result)

    async def async_step_connection_result(self, user_input=None):
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(**self._check_result)

    async def async_step_media_connection_result(self, user_input=None):
        return await self.async_step_connection_result(user_input)
