"""Define services for the Periodic Min Max integration."""

import logging
from typing import cast

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    LOGGER,
)

SERVICE_RESET = "reset"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"

SERVICE_RESET_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
    }
)


_LOGGER = logging.getLogger(__name__)


def async_get_entry(hass: HomeAssistant, config_entry_id: str) -> ConfigEntry:
    """Get the PeriodicMinMax config entry."""
    if not (entry := hass.config_entries.async_get_entry(config_entry_id)):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="integration_not_found",
            translation_placeholders={"target": DOMAIN},
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_loaded",
            translation_placeholders={"target": entry.title},
        )
    return entry


def get_entity_value(
    hass: HomeAssistant, entry_id: str, entity_key: str, default: float
) -> float:
    """Get an entities value store in hass data."""
    if entry_id not in hass.data[DOMAIN]:
        return default

    return cast(float, hass.data[DOMAIN][entry_id].get(entity_key, default))


def setup_services(hass: HomeAssistant) -> None:
    """Set up the services used by PeriodicMinMax component."""

    async def handle_reset(call: ServiceCall) -> ServiceResponse:
        """Handle the service call."""
        entry = async_get_entry(hass, call.data[ATTR_CONFIG_ENTRY_ID])

        # TODO: reset
        return None

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET,
        handle_reset,
        schema=SERVICE_RESET_SCHEMA,
    )
