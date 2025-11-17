"""Tests for the periodic_min_max services."""

from custom_components.periodic_min_max.const import DOMAIN
from custom_components.periodic_min_max.services import SERVICE_RESET
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity_registry as er

from .test_sensor import LAST_VALUE


async def test_service_reset(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the post service."""

    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor", "test_1", "unique", suggested_object_id="test_1"
    )
    assert sensor_entity_entry.entity_id == "sensor.test_1"

    hass.states.async_set("sensor.test_1", str(float(LAST_VALUE)))

    periodic_min_max_entity_id = "sensor.my_periodic_min_max"

    # Setup the config entry
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

    assert await async_setup_component(hass, DOMAIN, config_entry)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET,
        target={"entity_id": periodic_min_max_entity_id},
        blocking=True,
        return_response=False,
    )

    state = hass.states.get(periodic_min_max_entity_id)

    assert str(float(LAST_VALUE)) == state.state
