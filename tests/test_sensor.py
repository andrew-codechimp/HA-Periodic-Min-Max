"""The test for the periodic_min_max sensor platform."""

from unittest.mock import patch

import pytest
from homeassistant import config as hass_config
from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    SERVICE_RELOAD,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.periodic_min_max.const import DOMAIN

VALUES_NUMERIC = [17, 20, 15.2, 5, 3.8, 9.2, 6.7, 14, 6]
VALUES_ERROR = [17, "string", 15.3]
COUNT = len(VALUES_NUMERIC)
MIN_VALUE = min(VALUES_NUMERIC)
MAX_VALUE = max(VALUES_NUMERIC)
LAST_VALUE = VALUES_NUMERIC[-1]


async def test_min_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the min sensor."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_1", "unique", suggested_object_id="test_1"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_1"

    config = {
        "sensor": {
            "platform": "periodic_min_max",
            "name": "test_min",
            "type": "min",
            "entity_id": "sensor.test_1",
            "unique_id": "very_unique_id",
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(sensor_entity_entry.entity_id, value)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.test_min")

    assert str(float(MIN_VALUE)) == state.state
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    entity = entity_registry.async_get("sensor.test_min")
    assert entity.unique_id == "very_unique_id"


async def test_max_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the max sensor."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_1", "unique", suggested_object_id="test_1"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_1"

    config = {
        "sensor": {
            "platform": "periodic_min_max",
            "name": "test_max",
            "type": "max",
            "entity_id": "sensor.test_1",
            "unique_id": "very_unique_id",
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(sensor_entity_entry.entity_id, value)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.test_max")

    assert str(float(MAX_VALUE)) == state.state
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    entity = entity_registry.async_get("sensor.test_max")
    assert entity.unique_id == "very_unique_id"