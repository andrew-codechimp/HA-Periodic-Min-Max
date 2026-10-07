"""Tests for Periodic Min/Max English action translations."""

import json
from pathlib import Path

import yaml

INTEGRATION_DIR = (
    Path(__file__).resolve().parents[1] / "custom_components/periodic_min_max"
)


def test_service_translations_match_services_yaml() -> None:
    """Test translations cover the action names and fields declared in services.yaml."""
    services = yaml.safe_load((INTEGRATION_DIR / "services.yaml").read_text())
    translations = json.loads((INTEGRATION_DIR / "translations/en.json").read_text())[
        "services"
    ]
    assert set(translations) == set(services)
    for service, definition in services.items():
        assert set(definition.get("fields", {})).issubset(
            translations[service].get("fields", {})
        ), service
        assert translations[service]["name"]
        assert translations[service]["description"]
