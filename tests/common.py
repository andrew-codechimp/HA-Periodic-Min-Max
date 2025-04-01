"""Common helper and classes for number entity tests."""

from homeassistant.components.number import NumberEntity, RestoreNumber
from pytest_homeassistant_custom_component.common import MockEntity


class MockNumberEntity(MockEntity, NumberEntity):
    """Mock number class."""

    @property
    def native_max_value(self):
        """Return the native native_max_value."""
        return self._handle("native_max_value")

    @property
    def native_min_value(self):
        """Return the native native_min_value."""
        return self._handle("native_min_value")

    @property
    def native_step(self):
        """Return the native native_step."""
        return self._handle("native_step")

    @property
    def native_unit_of_measurement(self):
        """Return the native unit_of_measurement."""
        return self._handle("native_unit_of_measurement")

    @property
    def native_value(self):
        """Return the native value of this number."""
        return self._handle("native_value")

    def set_native_value(self, value: float) -> None:
        """Change the selected option."""
        self._values["native_value"] = value