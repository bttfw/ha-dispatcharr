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
            TotalStreams(coordinator),
            LastSuccess(coordinator),
            MediaSessions(coordinator.media_coordinator),
        ]
    )


class TotalStreams(DispatcharrEntity, SensorEntity):
    """Count reported connections across both independently polled coordinators."""

    _attr_icon = "mdi:play-network"
    _unrecorded_attributes = frozenset(
        {"dispatcharr_clients", "media_sessions", "complete", "unavailable_sources"}
    )

    def __init__(self, coordinator):
        super().__init__(coordinator, "total_streams")
        self.media_coordinator = coordinator.media_coordinator

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            self.media_coordinator.async_add_listener(self._handle_coordinator_update)
        )

    def _counts(self):
        """Do not reuse stale counts when a source is unavailable."""
        data = self.coordinator.data or {}
        count = data.get("viewer_count")
        counts = {
            "dispatcharr": count
            if self.coordinator.last_update_success and type(count) is int and count >= 0
            else None
        }
        media = self.media_coordinator
        statuses = {s["id"]: s for s in (media.data or {}).get("media_sources", [])}
        for source_id in media.clients:
            status = statuses.get(source_id, {})
            count = status.get("session_count")
            counts[source_id] = (
                count
                if media.last_update_success
                and status.get("connected")
                and type(count) is int
                and count >= 0
                else None
            )
        return counts

    @property
    def available(self):
        return any(count is not None for count in self._counts().values())

    @property
    def native_value(self):
        counts = [count for count in self._counts().values() if count is not None]
        return sum(counts) if counts else None

    @property
    def extra_state_attributes(self):
        counts = self._counts()
        media = [count for key, count in counts.items() if key != "dispatcharr"]
        return {
            "dispatcharr_clients": counts["dispatcharr"],
            "media_sessions": sum(count for count in media if count is not None)
            if not media or any(count is not None for count in media)
            else None,
            "complete": all(count is not None for count in counts.values()),
            "unavailable_sources": [key for key, count in counts.items() if count is None],
        }


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
