"""Custom integration to provide periodic_min_max helpers for Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/HA-Periodic-Min-Max
"""

from __future__ import annotations

import voluptuous as vol
from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION  # noqa: N812
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.helper_integration import (
    async_handle_source_entity_changes,
    async_remove_helper_config_entry_from_source_device,
)
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_ENTITY_ID,
    DOMAIN,
    LOGGER,
    MIN_HA_VERSION,
    PLATFORMS,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@callback
def async_get_source_entity_device_id(
    hass: HomeAssistant, entity_id: str
) -> str | None:
    """Get the entity device id."""
    registry = er.async_get(hass)

    if not (source_entity := registry.async_get(entity_id)):
        return None

    return source_entity.device_id


async def async_setup(
    hass: HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,  # pylint: disable=unused-argument
) -> bool:
    """Integration setup."""

    if AwesomeVersion(HA_VERSION) < AwesomeVersion(MIN_HA_VERSION):  # pragma: no cover
        msg = (
            "This integration requires at least Home Assistant version "
            f" {MIN_HA_VERSION}, you are running version {HA_VERSION}."
            " Please upgrade Home Assistant to continue using this integration."
        )
        LOGGER.critical(msg)
        return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Min/Max from a config entry."""

    entity_registry = er.async_get(hass)
    try:
        entity_id = er.async_validate_entity_id(
            entity_registry, entry.options[CONF_ENTITY_ID]
        )
    except vol.Invalid:
        # The entity is identified by an unknown entity registry ID
        LOGGER.error(
            "Failed to setup switch_as_x for unknown entity %s",
            entry.options[CONF_ENTITY_ID],
        )
        return False

    def set_source_entity_id_or_uuid(source_entity_id: str) -> None:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_ENTITY_ID: source_entity_id},
        )

    async def source_entity_removed() -> None:
        # The source entity has been removed, we remove the config entry because
        # switch_as_x does not allow replacing the wrapped entity.
        await hass.config_entries.async_remove(entry.entry_id)

    entry.async_on_unload(
        async_handle_source_entity_changes(
            hass,
            add_helper_config_entry_to_device=False,
            helper_config_entry_id=entry.entry_id,
            set_source_entity_id_or_uuid=set_source_entity_id_or_uuid,
            source_device_id=async_get_source_entity_device_id(hass, entity_id),
            source_entity_id_or_uuid=entry.options[CONF_ENTITY_ID],
            source_entity_removed=source_entity_removed,
        )
    )
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    LOGGER.debug(
        "Migrating from version %s.%s", config_entry.version, config_entry.minor_version
    )

    if config_entry.version > 1:
        # This means the user has downgraded from a future version
        return False
    if config_entry.version == 1:
        options = {**config_entry.options}
        if config_entry.minor_version < 2:
            # Remove the periodic min/max config entry from the source device
            if source_device_id := async_get_source_entity_device_id(
                hass, options[CONF_ENTITY_ID]
            ):
                async_remove_helper_config_entry_from_source_device(
                    hass,
                    helper_config_entry_id=config_entry.entry_id,
                    source_device_id=source_device_id,
                )
        hass.config_entries.async_update_entry(
            config_entry, options=options, minor_version=2
        )

    LOGGER.debug(
        "Migration to version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True
