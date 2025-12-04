"""Services for periodic_min_max."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import service
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from .const import DOMAIN

SERVICE_RESET = "reset"


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register periodic_min_max services."""

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_RESET,
        entity_domain=SENSOR_DOMAIN,
        schema=None,
        func="handle_reset",
    )
