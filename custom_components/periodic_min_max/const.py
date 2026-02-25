"""Constants for periodic_min_max."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2025.10"

DOMAIN = "periodic_min_max"
CONFIG_VERSION = 1

PLATFORMS = [Platform.SENSOR]

ATTR_LAST_MODIFIED = "last_modified"
