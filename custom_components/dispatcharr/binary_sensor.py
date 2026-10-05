"""Explicit connectivity state, including outages."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import DispatcharrEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DispatcharrConnectivity(entry.runtime_data)])


class DispatcharrConnectivity(DispatcharrEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "connectivity")

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.last_update_success
