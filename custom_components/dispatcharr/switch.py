"""Persistent control gate visible and editable in the HA GUI."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_CONTROL
from .entity import DispatcharrEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DispatcharrControl(entry.runtime_data)])


class DispatcharrControl(DispatcharrEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:shield-lock"

    def __init__(self, coordinator):
        super().__init__(coordinator, "enable_control")

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.control_enabled

    async def _set(self, enabled):
        if self._context.user_id:
            user = await self.hass.auth.async_get_user(self._context.user_id)
            if not user or not user.is_admin:
                raise Unauthorized()
        entry = self.coordinator.entry
        self.hass.config_entries.async_update_entry(
            entry, options=dict(entry.options) | {CONF_CONTROL: enabled}
        )
        self.coordinator.async_update_listeners()

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)
