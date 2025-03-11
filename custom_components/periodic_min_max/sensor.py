"""Sensor platform for periodic_min_max."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
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
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType

from .const import CONF_ENTITY_ID, DOMAIN, LOGGER, PLATFORMS

ATTR_MIN_VALUE = "min_value"
ATTR_MAX_VALUE = "max_value"

ICON = "mdi:calculator"

SENSOR_TYPES = {
    ATTR_MIN_VALUE: "min",
    ATTR_MAX_VALUE: "max",
}

SERVICE_RESET = "reset"

SENSOR_TYPE_TO_ATTR = {v: k for k, v in SENSOR_TYPES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize min/max/mean config entry."""
    registry = er.async_get(hass)
    entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_ENTITY_ID]
    )
    sensor_type = config_entry.options[CONF_TYPE]

    async_add_entities(
        [
            PeriodicMinMaxSensor(
                entity_id,
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


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the min/max/mean sensor."""
    entity_id: str = config[CONF_ENTITY_ID]
    name: str | None = config.get(CONF_NAME)
    sensor_type: str = config[CONF_TYPE]
    unique_id = config.get(CONF_UNIQUE_ID)

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)

    async_add_entities([PeriodicMinMaxSensor(entity_id, name, sensor_type, unique_id)])


class PeriodicMinMaxSensor(SensorEntity, RestoreEntity):
    """Representation of a periodic min/max sensor."""

    _attr_icon = ICON
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
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


        self._unit_of_measurement = None
        self._unit_of_measurement_mismatch = False
        self.min_value: float | None = None
        self.max_value: float | None = None
        self._state: Any = None

    async def async_added_to_hass(self) -> None:
        """Handle added to Hass."""

        # Mirror the source entity attributes
        registry = er.async_get(self.hass)
        entry = registry.async_get(self._source_entity_id)
        self._unit_of_measurement = entry.unit_of_measurement
        self._attr_device_class = entry.device_class if entry.device_class else entry.original_device_class
        self._attr_icon = entry.icon if entry.icon else entry.original_icon

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._source_entity_id, self._async_min_max_sensor_state_listener
            )
        )

        state = await self.async_get_last_state()
        if state is not None and state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            self._state = float(state.state)
            self._calc_values()

        # Replay current state of source entitiy
        state = self.hass.states.get(self._source_entity_id)
        state_event: Event[EventStateChangedData] = Event(
            "", {"entity_id": self._source_entity_id, "new_state": state, "old_state": None}
        )
        self._async_min_max_sensor_state_listener(state_event, update_state=False)

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

    @callback
    def _async_min_max_sensor_state_listener(
        self, event: Event[EventStateChangedData], update_state: bool = True
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
            if not update_state:
                return

            self._calc_values()
            self.async_write_ha_state()
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

        if not update_state:
            return

        self._calc_values()
        self.async_write_ha_state()

    @callback
    def _calc_values(self) -> None:
        """Calculate the values."""

        """Calculate min value, honoring unknown states."""
        if self._state not in [STATE_UNKNOWN, STATE_UNAVAILABLE] and (
            self.min_value is None or self.min_value > self._state
        ):
            self.min_value = self._state

        """Calculate max value, honoring unknown states."""
        if self._state not in [STATE_UNKNOWN, STATE_UNAVAILABLE] and (
            self.max_value is None or self.max_value < self._state
        ):
            self.max_value = self._state

    async def handle_reset(self) -> None:
        """Set the min & max to current state."""
        self.min_value = self._state
        self.max_value = self._state

        self.async_write_ha_state()