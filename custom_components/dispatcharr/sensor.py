"""Stable summary sensors; sessions are transient attributes."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import DispatcharrEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(
        [
            DispatcharrCount(coordinator, "active_channels", "mdi:television"),
            DispatcharrCount(coordinator, "viewer_count", "mdi:account-group"),
            LastSuccess(coordinator),
        ]
    )


class DispatcharrCount(DispatcharrEntity, SensorEntity):
    # Avoid persisting transient viewing history in the recorder.
    _unrecorded_attributes = frozenset({"viewers", "last_success", "warnings"})

    def __init__(self, coordinator, key, icon):
        super().__init__(coordinator, key)
        self.key = key
        self._attr_icon = icon

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.key)

    @property
    def extra_state_attributes(self):
        if self.key != "viewer_count":
            return None
        data = self.coordinator.data or {}
        return {**data, "control_enabled": self.coordinator.control_enabled}


class LastSuccess(DispatcharrEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "last_success")

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        return self.coordinator.last_success
