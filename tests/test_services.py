"""Tests for the periodic_min_max services."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    setup_test_component_platform,
)

from custom_components.periodic_min_max.const import DOMAIN
from custom_components.periodic_min_max.sensor import SERVICE_RESET

from .common import MockNumberEntity
from .test_sensor import LAST_VALUE, VALUES_NUMERIC


async def test_service_reset(
    hass: HomeAssistant,
    mock_number_entities: list[MockNumberEntity],
) -> None:
    """Test the post service."""

    source_config = {
        "sensor": {
            "platform": "number",
            "name": "test_1",
            "unique_id": "very_unique_source_id",
        }
    }

    config = {
        "sensor": {
            "platform": "periodic_min_max",
            "name": "test_min_service",
            "type": "min",
            "entity_id": "sensor.test_1",
            "unique_id": "very_unique_id",
        }
    }

    setup_test_component_platform(hass, "number", mock_number_entities)
    assert await async_setup_component(hass, "sensor", source_config)

    hass.states.async_set("sensor.test_1", str(float(LAST_VALUE)))

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_id = config["sensor"]["entity_id"]


    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET,
        target={"entity_id": "sensor.test_min_service"},
        blocking=True,
        return_response=False,
    )

    state = hass.states.get("sensor.test_min")

    assert str(float(LAST_VALUE)) == state.state
