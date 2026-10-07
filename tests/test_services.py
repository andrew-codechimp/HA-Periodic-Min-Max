"""Tests for the Periodic Min/Max reset action."""

import pytest
from custom_components.periodic_min_max.const import DOMAIN
from custom_components.periodic_min_max.services import SERVICE_RESET
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant

from . import setup_integration
from .const import ENTITY_ID, SOURCE_ENTITY_ID

pytestmark = pytest.mark.usefixtures("source_sensor")


async def test_reset(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, snapshot: SnapshotAssertion
) -> None:
    """Test reset starts a new period at the current reading."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(SOURCE_ENTITY_ID, "20")
    await hass.async_block_till_done()
    hass.states.async_set(SOURCE_ENTITY_ID, "12")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "20.0"
    await hass.services.async_call(
        DOMAIN, SERVICE_RESET, {"entity_id": ENTITY_ID}, blocking=True
    )
    assert hass.states.get(ENTITY_ID) == snapshot
    hass.states.async_set(SOURCE_ENTITY_ID, "15")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "15.0"


@pytest.mark.parametrize("source_state", ["unknown", "unavailable"])
async def test_reset_with_invalid_source(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, source_state: str
) -> None:
    """Test reset preserves the extremum when the current source cannot be used."""
    await setup_integration(hass, mock_config_entry)
    hass.states.async_set(SOURCE_ENTITY_ID, source_state)
    await hass.async_block_till_done()
    previous = hass.states.get(ENTITY_ID)
    await hass.services.async_call(
        DOMAIN, SERVICE_RESET, {"entity_id": ENTITY_ID}, blocking=True
    )
    assert hass.states.get(ENTITY_ID) == previous
