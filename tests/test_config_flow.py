"""Tests for Periodic Min/Max config and options flows."""

from unittest.mock import AsyncMock

import pytest
from custom_components.periodic_min_max.const import CONF_EQUAL_UPDATES, DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import DEFAULT_NAME, SOURCE_ENTITY_ID


@pytest.mark.parametrize("sensor_type", ["min", "max"])
@pytest.mark.parametrize(
    "options",
    [
        pytest.param({}, id="defaults"),
        pytest.param({CONF_EQUAL_UPDATES: True}, id="equal-updates"),
    ],
)
async def test_user_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    sensor_type: str,
    options: dict[str, bool],
) -> None:
    """Test a named minimum or maximum helper is created with the requested options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: SOURCE_ENTITY_ID,
            CONF_TYPE: sensor_type,
            **options,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {}
    assert result["version"] == 1
    assert result["minor_version"] == 2
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: SOURCE_ENTITY_ID,
        CONF_TYPE: sensor_type,
        CONF_EQUAL_UPDATES: False,
        **options,
    }
    mock_setup_entry.assert_awaited_once()


async def test_options(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test options suggest saved values and preserve the helper name."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
    } == {
        key: value
        for key, value in mock_config_entry.options.items()
        if key != CONF_NAME
    }
    options = {
        CONF_ENTITY_ID: "input_number.other",
        CONF_TYPE: "min",
        CONF_EQUAL_UPDATES: True,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_NAME: DEFAULT_NAME, **options}
    assert mock_config_entry.title == DEFAULT_NAME
    assert mock_config_entry.data == {}


async def test_source_selector(hass: HomeAssistant) -> None:
    """Test one sensor, number, or input number can be selected as the source."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    selector = result["data_schema"].schema[CONF_ENTITY_ID]
    assert selector.config["domain"] == ["sensor", "number", "input_number"]
    assert not selector.config["multiple"]
