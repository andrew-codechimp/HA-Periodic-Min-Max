"""The test for the periodic_min_max sensor platform."""

import pytest
from custom_components.periodic_min_max.const import (
    ATTR_LAST_MODIFIED,
    CONF_EQUAL_UPDATES,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

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

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My periodic min max",
            "entity_id": "sensor.test_1",
            "type": "min",
        },
        title="My periodic_min_max",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(sensor_entity_entry.entity_id, value)
        await hass.async_block_till_done()

    state = hass.states.get(periodic_min_max_entity_id)

    assert str(float(MIN_VALUE)) == state.state
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT


async def test_max_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the max sensor."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_1", "unique", suggested_object_id="test_1"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_1"

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My periodic min max",
            "entity_id": "sensor.test_1",
            "type": "max",
        },
        title="My periodic_min_max",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(sensor_entity_entry.entity_id, value)
        await hass.async_block_till_done()

    state = hass.states.get(periodic_min_max_entity_id)

    assert str(float(MAX_VALUE)) == state.state
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT


async def test_value_error(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test value error."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_1", "unique", suggested_object_id="test_1"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_1"

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My periodic min max",
            "entity_id": "sensor.test_1",
            "type": "max",
        },
        title="My periodic_min_max",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for value in VALUES_ERROR:
        hass.states.async_set(sensor_entity_entry.entity_id, value)
        await hass.async_block_till_done()

    state = hass.states.get(periodic_min_max_entity_id)

    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT


async def test_max_sensor_equal_updates_with_initial_none(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test equal updates when max sensor has no prior value."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_equal", "unique_equal", suggested_object_id="test_equal"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_equal"

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My periodic min max",
            "entity_id": "sensor.test_equal",
            "type": "max",
            CONF_EQUAL_UPDATES: True,
        },
        title="My periodic_min_max",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(sensor_entity_entry.entity_id, 3.0)
    await hass.async_block_till_done()

    state = hass.states.get(periodic_min_max_entity_id)
    assert state is not None
    assert state.state == "3.0"


@pytest.mark.parametrize(
    ("equal_updates", "last_modified_should_change"),
    [(False, False), (True, True)],
)
async def test_equal_updates_controls_last_modified_on_equal_value(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer,
    equal_updates: bool,
    last_modified_should_change: bool,
) -> None:
    """Test if equal values update last_modified based on equal_updates option."""
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor",
        "test_equal_updates",
        "unique_equal_updates",
        suggested_object_id="test_equal_updates",
    )
    assert sensor_entity_entry.entity_id == "sensor.test_equal_updates"

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My periodic min max",
            "entity_id": "sensor.test_equal_updates",
            "type": "max",
            CONF_EQUAL_UPDATES: equal_updates,
        },
        title="My periodic_min_max",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    freezer.move_to("2026-01-01 00:00:00+00:00")
    hass.states.async_set(sensor_entity_entry.entity_id, 7.0, {"source": "one"})
    await hass.async_block_till_done()

    first_state = hass.states.get(periodic_min_max_entity_id)
    assert first_state is not None
    first_last_modified = first_state.attributes[ATTR_LAST_MODIFIED]

    freezer.move_to("2026-01-01 00:00:01+00:00")
    hass.states.async_set(sensor_entity_entry.entity_id, 7.0, {"source": "two"})
    await hass.async_block_till_done()

    second_state = hass.states.get(periodic_min_max_entity_id)
    assert second_state is not None
    second_last_modified = second_state.attributes[ATTR_LAST_MODIFIED]

    assert (first_last_modified != second_last_modified) is last_modified_should_change
