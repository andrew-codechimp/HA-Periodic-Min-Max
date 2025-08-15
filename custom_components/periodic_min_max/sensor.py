"""Sensor platform for periodic_min_max."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.event import (
    async_track_entity_registry_updated_event,
    async_track_state_change_event,
)
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_LAST_MODIFIED,
    CONF_ENTITY_ID,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)

ATTR_MIN_VALUE = "min_value"
ATTR_MAX_VALUE = "max_value"

ICON = "mdi:calculator"

SENSOR_TYPES = {
    ATTR_MIN_VALUE: "min",
    ATTR_MAX_VALUE: "max",
}

SERVICE_RESET = "reset"

SENSOR_TYPE_TO_ATTR = {v: k for k, v in SENSOR_TYPES.items()}


@callback
def async_get_source_entity_device_id(
    hass: HomeAssistant, entity_id: str
) -> str | None:
    """Get the entity device id."""
    registry = er.async_get(hass)

    if not (source_entity := registry.async_get(entity_id)):
        return None

    return source_entity.device_id


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> bool:
    """Initialize periodic min/max config entry."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    try:
        source_entity_id = er.async_validate_entity_id(
            entity_registry, config_entry.options[CONF_ENTITY_ID]
        )
    except vol.Invalid:
        # The entity is identified by an unknown entity registry ID
        LOGGER.error(
            "Failed to setup periodic_min_max for unknown entity %s",
            config_entry.options[CONF_ENTITY_ID],
        )
        return False

    source_entity = entity_registry.async_get(source_entity_id)
    device_id = source_entity.device_id if source_entity else None

    sensor_type = config_entry.options[CONF_TYPE]

    async def async_registry_updated(
        event: Event[er.EventEntityRegistryUpdatedData],
    ) -> None:
        """Handle entity registry update."""
        data = event.data
        if data["action"] == "remove":
            await hass.config_entries.async_remove(config_entry.entry_id)

        if data["action"] != "update":
            return

        if "entity_id" in data["changes"]:
            # Entity_id changed, reload the config entry
            await hass.config_entries.async_reload(config_entry.entry_id)

        if device_id and "device_id" in data["changes"]:
            # If the tracked entity is no longer in the device, remove our config entry
            # from the device
            if (
                not (entity_entry := entity_registry.async_get(data["entity_id"]))
                or not device_registry.async_get(device_id)
                or entity_entry.device_id == device_id
            ):
                # No need to do any cleanup
                return

            device_registry.async_update_device(
                device_id, remove_config_entry_id=config_entry.entry_id
            )

    config_entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass, source_entity_id, async_registry_updated
        )
    )
    config_entry.async_on_unload(
        config_entry.add_update_listener(config_entry_update_listener)
    )

    async_add_entities(
        [
            PeriodicMinMaxSensor(
                hass,
                source_entity_id,
                config_entry.title,
                sensor_type,
                config_entry.entry_id,
            )
        ]
    )

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_RESET,
        None,
        "handle_reset",
    )

    return True


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the periodic min/max sensor."""
    source_entity_id: str = config[CONF_ENTITY_ID]
    name: str | None = config.get(CONF_NAME)
    sensor_type: str = config[CONF_TYPE]
    unique_id = config.get(CONF_UNIQUE_ID)

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)

    async_add_entities(
        [PeriodicMinMaxSensor(hass, source_entity_id, name, sensor_type, unique_id)]
    )


class PeriodicMinMaxSensor(SensorEntity, RestoreEntity):
    """Representation of a periodic min/max sensor."""

    _attr_icon = ICON
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _state_had_real_change = False
    _attr_last_modified: str = dt_util.utcnow().isoformat()

    def __init__(
        self,
        hass: HomeAssistant,
        source_entity_id: str,
        name: str | None,
        sensor_type: str,
        unique_id: str | None,
    ) -> None:
        """Initialize the min/max sensor."""
        self._attr_unique_id = unique_id
        self._source_entity_id = source_entity_id
        self._sensor_type = sensor_type

        if name:
            self._attr_name = name
        else:
            self._attr_name = f"{sensor_type} sensor".capitalize()
        self._sensor_attr = SENSOR_TYPE_TO_ATTR[self._sensor_type]

        self._unit_of_measurement: str | None = None
        self._unit_of_measurement_mismatch = False
        self.min_value: float | None = None
        self.max_value: float | None = None
        self._state: Any = None

        registry = er.async_get(hass)
        device_registry = dr.async_get(hass)
        source_entity = registry.async_get(source_entity_id)
        device_id = source_entity.device_id if source_entity else None

        if device_id and (device := device_registry.async_get(device_id)):
            self.device_entry = device

    async def async_added_to_hass(self) -> None:
        """Handle added to Hass."""

        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state:
            last_attrs = last_state.attributes
            if last_attrs and ATTR_LAST_MODIFIED in last_attrs:
                self._attr_last_modified = last_attrs[ATTR_LAST_MODIFIED]

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._source_entity_id,
                self._async_min_max_sensor_state_listener,
            )
        )

        # Mirror the source entity attributes
        registry = er.async_get(self.hass)
        entry = registry.async_get(self._source_entity_id)

        if not entry:
            LOGGER.warning(
                "Unable to find entity %s",
                self._source_entity_id,
            )

        if entry:
            self._unit_of_measurement = entry.unit_of_measurement
            self._attr_device_class = (
                SensorDeviceClass(entry.device_class) if entry.device_class else None
            )
            self._attr_icon = (
                entry.icon
                if entry.icon
                else entry.original_icon
                if entry.original_icon
                else ICON
            )

            state = await self.async_get_last_state()
            if state is not None and state.state not in [
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ]:
                self._state = float(state.state)
                self._calc_values()

            # Replay current state of source entitiy
            state = self.hass.states.get(self._source_entity_id)
            state_event: Event[EventStateChangedData] = Event(
                "",
                {
                    "entity_id": self._source_entity_id,
                    "new_state": state,
                    "old_state": None,
                },
            )
            self._async_min_max_sensor_state_listener(state_event)

            self._calc_values()

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        if self._unit_of_measurement_mismatch:
            return None
        value: StateType | datetime = getattr(self, self._sensor_attr)
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        if self._unit_of_measurement_mismatch:
            return "ERR"
        return self._unit_of_measurement

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device specific state attributes."""
        attributes: dict[str, Any] = {}

        attributes[ATTR_LAST_MODIFIED] = self._attr_last_modified

        return attributes

    @callback
    def _async_min_max_sensor_state_listener(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle the sensor state changes."""
        new_state = event.data["new_state"]

        if (
            new_state is None
            or new_state.state is None
            or new_state.state
            in [
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ]
        ):
            self._state = STATE_UNKNOWN
            return

        if self._unit_of_measurement is None:
            self._unit_of_measurement = new_state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT
            )

        if self._unit_of_measurement != new_state.attributes.get(
            ATTR_UNIT_OF_MEASUREMENT
        ):
            LOGGER.warning(
                "Units of measurement do not match for entity %s", self.entity_id
            )
            self._unit_of_measurement_mismatch = True

        try:
            self._state = float(new_state.state)
        except ValueError:
            LOGGER.warning("Unable to store state. Only numerical states are supported")

        self._calc_values()

        if self._state_had_real_change:
            self._attr_last_modified = dt_util.utcnow().isoformat(sep=" ")

        self.async_write_ha_state()

    @callback
    def _calc_values(self) -> None:
        """Calculate the values."""
        self._state_had_real_change = False

        """Calculate min value, honoring unknown states."""
        if self._sensor_attr == ATTR_MIN_VALUE:
            if self._state not in [STATE_UNKNOWN, STATE_UNAVAILABLE] and (
                self.min_value is None or self.min_value > self._state
            ):
                self.min_value = self._state
                self._state_had_real_change = True

        """Calculate max value, honoring unknown states."""
        if self._sensor_attr == ATTR_MAX_VALUE:
            if self._state not in [STATE_UNKNOWN, STATE_UNAVAILABLE] and (
                self.max_value is None or self.max_value < self._state
            ):
                self.max_value = self._state
                self._state_had_real_change = True

    async def handle_reset(self) -> None:
        """Set the min & max to current state."""
        if self._state is None or self._state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            LOGGER.warning(
                "Cannot reset %s, current state is unknown or unavailable",
                self.entity_id,
            )
            return

        self.min_value = self._state
        self.max_value = self._state

        self.async_write_ha_state()
