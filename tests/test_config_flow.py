"""Test periodic_min_max config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.components.recorder import Recorder
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy import SnapshotAssertion

from custom_components.periodic_min_max.const import DOMAIN

from .const import DEFAULT_NAME


async def test_form_sensor(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form for sensor."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_periodic_min_max",
            CONF_TYPE: "max",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 1
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "sensor.test_periodic_min_max",
        CONF_TYPE: "max",
    }

    assert len(mock_setup_entry.mock_calls) == 1