"""Test periodic_min_max setup process."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.periodic_min_max.const import DOMAIN

from .const import DEFAULT_NAME


async def test_unload_entry(hass: HomeAssistant, loaded_entry: MockConfigEntry) -> None:
    """Test unload an entry."""

    assert loaded_entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the setup of the helper PeriodicMinMax."""

    # Source entity device config entry
    source_config_entry = MockConfigEntry()
    source_config_entry.add_to_hass(hass)

    # Device entry of the source entity
    source_device1_entry = device_registry.async_get_or_create(
        config_entry_id=source_config_entry.entry_id,
        identifiers={("sensor", "test_source")},
    )

    # Source entity registry
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=source_config_entry,
        device_id=source_device1_entry.id,
    )
    await hass.async_block_till_done()
    assert entity_registry.async_get("sensor.test_source") is not None

    # Configure the configuration entry for PeriodicMinMax
    periodicminmax_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": DEFAULT_NAME,
            "entity_id": "sensor.test_source",
            "type": "max",
        },
        title=DEFAULT_NAME
    )
    periodicminmax_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(periodicminmax_config_entry.entry_id)
    await hass.async_block_till_done()

    # Confirm the link between the source entity device and the periodicminmax sensor
    periodicminmax_entity = entity_registry.async_get("sensor.periodicminmax")
    assert periodicminmax_entity is not None
    assert periodicminmax_entity.device_id == source_entity.device_id


    # Before reloading the config entry, two devices are expected to be linked
    devices_before_reload = device_registry.devices.get_devices_for_config_entry_id(
        periodicminmax_config_entry.entry_id
    )
    assert len(devices_before_reload) == 1

    # Config entry reload
    await hass.config_entries.async_reload(periodicminmax_config_entry.entry_id)
    await hass.async_block_till_done()

    # Confirm the link between the source entity device and the periodicminmax sensor
    periodicminmax_entity = entity_registry.async_get("sensor.periodicminmax")
    assert periodicminmax_entity is not None
    assert periodicminmax_entity.device_id == source_entity.device_id

    # After reloading the config entry, only one linked device is expected
    devices_after_reload = device_registry.devices.get_devices_for_config_entry_id(
        periodicminmax_config_entry.entry_id
    )
    assert len(devices_after_reload) == 1

    assert devices_after_reload[0].id == source_device1_entry.id


# @pytest.mark.parametrize("platform", "sensor")
# async def test_setup_and_remove_config_entry(
#     hass: HomeAssistant,
#     entity_registry: er.EntityRegistry,
#     platform: str,
# ) -> None:
#     """Test setting up and removing a config entry."""
#     hass.states.async_set("sensor.input_one", "10")

#     input_sensor = "sensor.input_one"

#     periodic_min_max_entity_id = f"{platform}.my_periodic_min_max"

#     # Setup the config entry
#     config_entry = MockConfigEntry(
#         data={},
#         domain=DOMAIN,
#         options={
#             "entity_id": input_sensor,
#             "name": "My min_max",
#             "round_digits": 2.0,
#             "type": "min",
#         },
#         title="My min_max",
#     )
#     config_entry.add_to_hass(hass)
#     assert await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     # Check the entity is registered in the entity registry
#     assert entity_registry.async_get(periodic_min_max_entity_id) is not None

#     # Check the platform is setup correctly
#     state = hass.states.get(periodic_min_max_entity_id)
#     assert state.state == "10.0"

#     # Remove the config entry
#     assert await hass.config_entries.async_remove(config_entry.entry_id)
#     await hass.async_block_till_done()

#     # Check the state and entity registry entry are removed
#     assert hass.states.get(periodic_min_max_entity_id) is None
#     assert entity_registry.async_get(periodic_min_max_entity_id) is None
