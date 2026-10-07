"""Fixtures for Periodic Min/Max tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.periodic_min_max.const import CONF_EQUAL_UPDATES, DOMAIN
from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DEFAULT_NAME, SOURCE_ENTITY_ID


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Use the Home Assistant snapshot serializer."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in Home Assistant."""


@pytest.fixture(autouse=True)
def freeze_setup_time(freezer: FrozenDateTimeFactory) -> None:
    """Keep entity timestamps and scheduled callbacks stable."""
    freezer.move_to("2026-07-01T12:00:00+00:00")


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock integration setup when testing flows in isolation."""
    with patch(
        "custom_components.periodic_min_max.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry(request: pytest.FixtureRequest) -> MockConfigEntry:
    """Create a helper entry with default options and optional overrides."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=2,
        entry_id="helper-entry",
        title=DEFAULT_NAME,
        data={},
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: SOURCE_ENTITY_ID,
            CONF_TYPE: "max",
            CONF_EQUAL_UPDATES: False,
            **getattr(request, "param", {}),
        },
    )


@pytest.fixture
def source_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> er.RegistryEntry:
    """Register a source sensor and publish an initial numeric reading."""
    entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        suggested_object_id="test_source",
        original_name="Source",
    )
    hass.states.async_set(entity.entity_id, "10")
    return entity
