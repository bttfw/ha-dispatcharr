"""Stable summary sensors; sessions are transient attributes."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import DispatcharrEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(
        [
            DispatcharrCount(coordinator, "active_channels", "mdi:television"),
            DispatcharrCount(coordinator, "viewer_count", "mdi:account-group"),
            LastSuccess(coordinator),
            MediaSessions(coordinator.media_coordinator),
        ]
    )


class MediaSessions(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "media_sessions"
    _attr_icon = "mdi:play-network"
    _unrecorded_attributes = frozenset({"sessions", "media_sources"})

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_media_sessions"
        self._attr_device_info = {"identifiers": {(DOMAIN, coordinator.entry.entry_id)}}

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        sources = data.get("media_sources", [])
        return (
            len(data.get("sessions", []))
            if not sources or any(s["connected"] for s in sources)
            else None
        )

    @property
    def extra_state_attributes(self):
        return {
            **(self.coordinator.data or {}),
            "viewer_entity_id": er.async_get(self.hass).async_get_entity_id(
                "sensor", DOMAIN, f"{self.coordinator.entry.entry_id}_viewer_count"
            ),
        }


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

    @property
    def extra_state_attributes(self):
        # HA removes normal attributes when a count sensor becomes unavailable.
        # Keep an explicit registry-based link so the card can show this timestamp
        # even when opened during an outage or after the viewer entity is renamed.
        return {
            "viewer_entity_id": er.async_get(self.hass).async_get_entity_id(
                "sensor", DOMAIN, f"{self.coordinator.entry.entry_id}_viewer_count"
            )
        }
