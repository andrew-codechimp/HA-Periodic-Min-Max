"""Global fixtures for periodic_min_max integration."""

from __future__ import annotations

from collections.abc import Generator
from datetime import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.periodic_min_max.const import DOMAIN

from .common import MockNumberEntity
from .test_sensor import VALUES_NUMERIC

pytest_plugins = "pytest_homeassistant_custom_component"

# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    yield

@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Automatically path uuid generator."""
    with patch(
        "custom_components.periodic_min_max.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture(name="get_config")
async def get_config_to_integration_load() -> dict[str, Any]:
    """Return configuration.

    To override the config, tests can be marked with:
    @pytest.mark.parametrize("get_config", [{...}])
    """
    return {
        CONF_NAME: "My periodic_min_max sensor",
        CONF_ENTITY_ID: "sensor.test_monitored",
        CONF_TYPE: "max",
    }


@pytest.fixture(name="loaded_entry")
async def load_integration(
    hass: HomeAssistant, get_config: dict[str, Any]
) -> MockConfigEntry:
    """Set up the periodic_min_max integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options=get_config,
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
        )
    await hass.async_block_till_done()

    return config_entry

@pytest.fixture
def mock_number_entities() -> list[MockNumberEntity]:
    """Return a list of mock number entities."""
    return [
        MockNumberEntity(
            name="test_1",
            unique_id="unique_number",
            native_value=50.0,
        ),
    ]
