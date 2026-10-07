"""Tests for extrema, timestamps, restoration, and source metadata."""

from unittest.mock import Mock

import pytest
from custom_components.periodic_min_max.const import (
    ATTR_LAST_MODIFIED,
    CONF_EQUAL_UPDATES,
)
from custom_components.periodic_min_max.sensor import (
    async_get_source_entity_device_id,
    async_setup_entry,
)
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, CONF_ENTITY_ID, CONF_TYPE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from .const import ENTITY_ID, SOURCE_ENTITY_ID

pytestmark = pytest.mark.usefixtures("source_sensor")


async def test_entity(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test entity metadata and published source values."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(SOURCE_ENTITY_ID, "12")
    await hass.async_block_till_done()
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("mock_config_entry", "expected"),
    [
        pytest.param({CONF_TYPE: "min"}, "3.8", id="minimum"),
        pytest.param({CONF_TYPE: "max"}, "20.0", id="maximum"),
    ],
    indirect=["mock_config_entry"],
)
async def test_extrema(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, expected: str
) -> None:
    """Test readings update the requested extremum and later readings retain it."""
    await setup_integration(hass, mock_config_entry)
    for value in (17, 20, 15.2, 5, 3.8, 9.2, 6.7, 14, 6):
        hass.states.async_set(SOURCE_ENTITY_ID, str(value))
        await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == expected


@pytest.mark.parametrize("sensor_type", ["min", "max"])
@pytest.mark.parametrize(
    "equal_updates", [False, True], ids=["ignore-equal", "record-equal"]
)
async def test_equal_updates(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    sensor_type: str,
    equal_updates: bool,
) -> None:
    """Test equal readings change the timestamp only when equal_updates is enabled."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            CONF_TYPE: sensor_type,
            CONF_EQUAL_UPDATES: equal_updates,
        },
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set(SOURCE_ENTITY_ID, "10", {"report": 1})
    await hass.async_block_till_done()
    first = hass.states.get(ENTITY_ID).attributes[ATTR_LAST_MODIFIED]
    freezer.tick(1)
    hass.states.async_set(SOURCE_ENTITY_ID, "10", {"report": 2})
    await hass.async_block_till_done()
    second = hass.states.get(ENTITY_ID).attributes[ATTR_LAST_MODIFIED]
    assert (first != second) is equal_updates


@pytest.mark.parametrize("source_state", ["unknown", "unavailable", "invalid"])
async def test_invalid_readings(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, source_state: str
) -> None:
    """Test invalid readings preserve the extremum and valid reports recover."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(SOURCE_ENTITY_ID, source_state)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "10.0"
    hass.states.async_set(SOURCE_ENTITY_ID, "15")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "15.0"


async def test_source_state_removed(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test a removed source state retains the stored extremum."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_remove(SOURCE_ENTITY_ID)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "10.0"


@pytest.mark.parametrize(
    ("mock_config_entry", "restored_value"),
    [
        pytest.param({CONF_TYPE: "min"}, "2.0", id="minimum"),
        pytest.param({CONF_TYPE: "max"}, "20.0", id="maximum"),
    ],
    indirect=["mock_config_entry"],
)
async def test_restore(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, restored_value: str
) -> None:
    """Test stored extrema and their modification timestamps survive a restart."""
    modified = "2026-06-01T12:00:00+00:00"
    mock_restore_cache(
        hass, [State(ENTITY_ID, restored_value, {ATTR_LAST_MODIFIED: modified})]
    )
    await setup_integration(hass, mock_config_entry)
    state = hass.states.get(ENTITY_ID)
    assert state.state == restored_value
    assert state.attributes[ATTR_LAST_MODIFIED] == modified


async def test_source_metadata(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test device class, icon, and units are mirrored from the source."""
    entity_registry.async_update_entity(
        SOURCE_ENTITY_ID,
        device_class="temperature",
        icon="mdi:thermometer",
        unit_of_measurement="°C",
    )
    hass.states.async_set(SOURCE_ENTITY_ID, "10", {ATTR_UNIT_OF_MEASUREMENT: "°C"})
    await setup_integration(hass, mock_config_entry)
    state = hass.states.get(ENTITY_ID)
    assert state.attributes["device_class"] == "temperature"
    assert state.attributes["icon"] == "mdi:thermometer"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "°C"


async def test_unit_mismatch(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test a changed unit invalidates the extremum rather than combining units."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(SOURCE_ENTITY_ID, "12", {ATTR_UNIT_OF_MEASUREMENT: "kWh"})
    await hass.async_block_till_done()
    hass.states.async_set(SOURCE_ENTITY_ID, "15", {ATTR_UNIT_OF_MEASUREMENT: "W"})
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state.state == "unknown"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "ERR"


async def test_unknown_source_registry_id(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test platform setup rejects an unknown source registry ID."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_ENTITY_ID: "missing-registry-id"},
    )
    add_entities = Mock()
    assert not await async_setup_entry(hass, mock_config_entry, add_entities)
    add_entities.assert_not_called()


@pytest.mark.parametrize("source_id", [SOURCE_ENTITY_ID, "sensor.missing"])
async def test_source_device_lookup(hass: HomeAssistant, source_id: str) -> None:
    """Test sources without a device and missing registry entries return no device."""
    assert async_get_source_entity_device_id(hass, source_id) is None


async def test_default_name(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test an unnamed helper receives a name derived from its statistic."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, title="")
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.max_sensor").state == "10.0"
    assert (
        hass.states.get("sensor.max_sensor").attributes["friendly_name"] == "Max sensor"
    )


async def test_unregistered_source(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test a source entity ID absent from the registry loads an unknown helper."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_ENTITY_ID: "sensor.unregistered"},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unknown"
