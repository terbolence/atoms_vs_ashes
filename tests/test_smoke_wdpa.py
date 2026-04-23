# man_hours: 1.0
"""Smoke tests for WDPA Protected Planet API — requires live API access.

Run with: pytest tests/test_smoke_wdpa.py -m smoke -v --tb=short

Requires WDPA_TOKEN environment variable or connectors.wdpa.api_token in config.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.wdpa import WdpaConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    def test_health_check(self):
        with WdpaConnector() as c:
            assert c.health_check() is True

    def test_single_country_fetch(self):
        with WdpaConnector() as c:
            areas = c.fetch_country_protected_areas("ROU", with_geometry=False)
            assert len(areas) > 0


class TestResponseFormat:
    def test_field_names_match_v4(self):
        with WdpaConnector() as c:
            areas = c.fetch_country_protected_areas("ROU", with_geometry=False)
            assert len(areas) > 0
            pa = areas[0]
            assert pa.site_id > 0
            assert isinstance(pa.name_english, str)
            assert pa.site_type in ("pa", "oecm")

    def test_single_site_fetch(self):
        with WdpaConnector() as c:
            c.ingest_country("ROU")
            result = c.fetch(_TEST_LAT, _TEST_LON, country_code="RO")
            assert result.error is None
            d = result.to_dict()
            for key in ["lat", "lon", "source", "quality"]:
                assert key in d


class TestCoverageEdges:
    def test_ukraine_has_ramsar(self):
        with WdpaConnector() as c:
            areas = c.fetch_country_protected_areas("UKR", with_geometry=False)
            ramsar = [a for a in areas if a.is_ramsar]
            assert len(ramsar) > 0, "Ukraine should have Ramsar sites in WDPA"

    def test_kosovo_may_be_empty(self):
        with WdpaConnector() as c:
            areas = c.fetch_country_protected_areas("XKX", with_geometry=False)
            # Kosovo may or may not have separate entries; this is informational
            if not areas:
                pytest.skip("Kosovo (XKX) has no separate WDPA entries — expected")
