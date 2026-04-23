# man_hours: 0.3
"""Live Google Earth Engine smoke tests — opt-in only (see config + pip extra)."""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skip(
        reason=(
            "Google Earth Engine is off by default (connectors.earth_engine.enabled: false) "
            "and requires pip extra [earth-engine] plus Google Cloud / app review. "
            "Enable in YAML and set GEE_* env vars to run live tests."
        ),
    ),
]


class TestEarthEngineLivePlaceholder:
    def test_placeholder(self) -> None:
        assert True
