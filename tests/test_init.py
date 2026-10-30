"""Tests for periodic_min_max lifecycle and source registry changes."""

import pytest
from custom_components.periodic_min_max import async_migrate_entry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ENTITY_ID, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from . import setup_integration
from .const import ENTITY_ID, SOURCE_ENTITY_ID


@pytest.mark.usefixtures("source_sensor")
async def test_setup_and_remove(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test one entity is created, reload preserves its identity, and removal cleans it up."""
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entities) == 1
    assert entities[0].entity_id == ENTITY_ID
    assert entities[0].unique_id == mock_config_entry.entry_id
    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert entity_registry.async_get(ENTITY_ID).id == entities[0].id
    assert await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID) is None
    assert entity_registry.async_get(ENTITY_ID) is None
    assert entity_registry.async_get(SOURCE_ENTITY_ID) is not None


@pytest.mark.usefixtures("source_sensor")
async def test_unload(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test unloading unsubscribes source state listeners."""
    await setup_integration(hass, mock_config_entry)
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    previous = hass.states.get(ENTITY_ID)
    assert previous.state == "unavailable"
    hass.states.async_set(SOURCE_ENTITY_ID, "off")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID) == previous


@pytest.mark.usefixtures("source_sensor")
async def test_source_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test removing a required source removes the helper entry and entity."""
    await setup_integration(hass, mock_config_entry)
    entity_registry.async_remove(SOURCE_ENTITY_ID)
    await hass.async_block_till_done()
    assert hass.config_entries.async_get_entry(mock_config_entry.entry_id) is None
    assert entity_registry.async_get(ENTITY_ID) is None
    assert hass.states.get(ENTITY_ID) is None


@pytest.mark.usefixtures("source_sensor")
async def test_source_renamed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test renaming a source updates the stored reference and reloads the helper."""
    await setup_integration(hass, mock_config_entry)
    renamed = f"{SOURCE_ENTITY_ID}_renamed"
    entity_registry.async_update_entity(SOURCE_ENTITY_ID, new_entity_id=renamed)
    await hass.async_block_till_done()
    assert (
        er.async_validate_entity_id(
            entity_registry, mock_config_entry.options[CONF_ENTITY_ID]
        )
        == renamed
    )
    assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_unknown_source_registry_id(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test an unresolved registry ID produces a setup error."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_ENTITY_ID: "missing-registry-id"},
    )
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.usefixtures("source_sensor")
async def test_options_reload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test saving options reloads the helper with the new settings."""
    await setup_integration(hass, mock_config_entry)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    options = {
        key: value for key, value in mock_config_entry.options.items() if key != "name"
    }
    options.update({CONF_TYPE: "min"})
    await hass.config_entries.options.async_configure(result["flow_id"], options)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert dict(mock_config_entry.options) == {
        "name": mock_config_entry.title,
        **options,
    }


@pytest.mark.usefixtures("source_sensor")
async def test_source_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the helper uses the source device and remains when the source is detached."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id, identifiers={("test", "source")}
    )
    entity_registry.async_update_entity(SOURCE_ENTITY_ID, device_id=device.id)
    await setup_integration(hass, mock_config_entry)
    assert entity_registry.async_get(ENTITY_ID).device_id == device.id
    entity_registry.async_update_entity(SOURCE_ENTITY_ID, device_id=None)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize(
    ("version", "minor_version", "expected"),
    [
        pytest.param(1, 1, True, id="legacy"),
        pytest.param(1, 2, True, id="current"),
        pytest.param(2, 1, False, id="future"),
    ],
)
async def test_migrate(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    version: int,
    minor_version: int,
    expected: bool,
) -> None:
    """Test legacy migration and refusal to downgrade a future config version."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, version=version, minor_version=minor_version
    )
    options = dict(mock_config_entry.options)
    assert await async_migrate_entry(hass, mock_config_entry) is expected
    assert dict(mock_config_entry.options) == options
    assert mock_config_entry.version == version
    assert mock_config_entry.minor_version == {True: 2, False: minor_version}[expected]


@pytest.mark.usefixtures("source_sensor")
async def test_registry_notifications(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test irrelevant registry events and a repeated device update leave the helper loaded."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id, identifiers={("test", "source")}
    )
    entity_registry.async_update_entity(SOURCE_ENTITY_ID, device_id=device.id)
    await setup_integration(hass, mock_config_entry)
    hass.bus.async_fire(
        er.EVENT_ENTITY_REGISTRY_UPDATED,
        {"action": "create", "entity_id": SOURCE_ENTITY_ID},
    )
    await hass.async_block_till_done()
    hass.bus.async_fire(
        er.EVENT_ENTITY_REGISTRY_UPDATED,
        {
            "action": "update",
            "entity_id": SOURCE_ENTITY_ID,
            "changes": {"device_id": device.id},
        },
    )
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert entity_registry.async_get(ENTITY_ID).device_id == device.id


@pytest.mark.usefixtures("source_sensor")
async def test_migrate_device_link(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test migration removes the helper device and links its entity to the source."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id, identifiers={("test", "migration")}
    )
    entity_registry.async_update_entity(SOURCE_ENTITY_ID, device_id=device.id)
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, minor_version=1)
    helper_device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={("periodic_min_max", "legacy")},
    )
    helper_entity = entity_registry.async_get_or_create(
        "sensor",
        "periodic_min_max",
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=helper_device.id,
    )

    assert await async_migrate_entry(hass, mock_config_entry)

    assert device_registry.async_get(helper_device.id) is None
    assert device_registry.async_get(device.id) is not None
    assert entity_registry.async_get(helper_entity.entity_id).device_id == device.id
    assert mock_config_entry.minor_version == 2
