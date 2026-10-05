"""GUI-only setup, reconfiguration, authentication and options."""

from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    CannotConnect,
    DispatcharrClient,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
    NotFound,
    normalize_url,
)
from .const import CONF_ALIASES, CONF_CONTROL, CONF_EPG, CONF_METADATA, CONF_POLL, DEFAULTS, DOMAIN


class DispatcharrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DispatcharrOptionsFlow()

    async def _credentials(self, step, user_input=None):
        errors = {}
        entry = None
        if step == "reconfigure":
            entry = self._get_reconfigure_entry()
        elif step == "reauth_confirm":
            entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                url = normalize_url(user_input[CONF_URL])
                key = user_input[CONF_API_KEY].strip()
                if not key:
                    raise InvalidAuth()
                if any(
                    e.entry_id != (entry.entry_id if entry else None) and e.data[CONF_URL] == url
                    for e in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                api = DispatcharrClient(async_get_clientsession(self.hass), url, key)
                capabilities = await api.validate()
                data = {CONF_URL: url, CONF_API_KEY: key, "version": capabilities["version"]}
                if entry:
                    return self.async_update_reload_and_abort(entry, data_updates=data)
                return self.async_create_entry(
                    title=f"Dispatcharr ({urlsplit(url).netloc})", data=data
                )
            except ValueError:
                errors[CONF_URL] = "invalid_url"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Forbidden:
                errors["base"] = "insufficient_permissions"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except (InvalidResponse, NotFound):
                errors["base"] = "unsupported_api"
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_URL, default=entry.data[CONF_URL] if entry else ""
                ): selector.TextSelector({"type": "url"}),
                vol.Required(CONF_API_KEY): selector.TextSelector({"type": "password"}),
            }
        )
        return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

    async def async_step_user(self, user_input=None):
        return await self._credentials("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._credentials("reconfigure", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._credentials("reauth_confirm", user_input)


class DispatcharrOptionsFlow(config_entries.OptionsFlowWithReload):
    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id="init", menu_options=["control", "aliases", "advanced"])

    async def async_step_control(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options) | user_input)
        return self.async_show_form(
            step_id="control",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONTROL, default=self.config_entry.options.get(CONF_CONTROL, False)
                    ): bool,
                }
            ),
        )

    async def async_step_advanced(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options) | user_input)
        values = DEFAULTS | self.config_entry.options
        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POLL, default=values[CONF_POLL]): vol.All(
                        vol.Coerce(int), vol.Range(min=5, max=300)
                    ),
                    vol.Required(CONF_METADATA, default=values[CONF_METADATA]): vol.All(
                        vol.Coerce(int), vol.Range(min=300, max=86400)
                    ),
                    vol.Required(CONF_EPG, default=values[CONF_EPG]): vol.All(
                        vol.Coerce(int), vol.Range(min=30, max=3600)
                    ),
                }
            ),
        )

    async def async_step_aliases(self, user_input=None):
        aliases = dict(self.config_entry.options.get(CONF_ALIASES, {}))
        devices = {key: f"{name} ({key[-6:]})" for key, name in aliases.items()}
        coordinator = getattr(self.config_entry, "runtime_data", None)
        if coordinator and coordinator.data:
            for row in coordinator.data["viewers"]:
                if key := row["device_key"]:
                    devices[key] = (
                        f"{row['username'] or '?'} · {row['device_description'] or '?'} ({key[-6:]})"
                    )
        if not devices:
            return self.async_abort(reason="no_devices")
        if user_input is not None:
            key = user_input["device"]
            if key not in devices:
                return self.async_abort(reason="no_devices")
            name = user_input.get("alias", "").strip()[:80]
            if name:
                aliases[key] = name
            else:
                aliases.pop(key, None)
            return self.async_create_entry(
                data=dict(self.config_entry.options) | {CONF_ALIASES: aliases}
            )
        return self.async_show_form(
            step_id="aliases",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): selector.SelectSelector(
                        {
                            "options": [{"value": k, "label": v} for k, v in devices.items()],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("alias", default=""): selector.TextSelector(),
                }
            ),
        )
