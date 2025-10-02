"""The test for the periodic_min_max sensor platform."""

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
