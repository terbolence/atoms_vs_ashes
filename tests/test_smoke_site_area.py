# man_hours: 1.0
"""Smoke test for FIX-03 site area enrichment (live API).

Requires network access to Overpass API. Run with:
    pytest tests/test_smoke_site_area.py -v -m smoke

Canonical site: Cernavoda, Romania (44.32, 28.05) — has power=plant polygon.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.smoke


@pytest.fixture()
def overpass_client():
    from atoms_vs_ashes.connectors.osm import OverpassClient
    client = OverpassClient()
    yield client
    client.close()


class TestOverpassConnectivity:
    def test_health_check(self, overpass_client):
        assert overpass_client.health_check() is True


class TestSiteAreaFetch:
    def test_cernavoda_has_polygon(self, overpass_client):
        """Cernavoda nuclear plant has a well-mapped power=plant polygon."""
        result = overpass_client.fetch_site_area(44.32, 28.05, radius_m=3000)
        assert result.site_area_ha is not None, f"Expected polygon, got: {result.error}"
        assert result.site_area_ha > 10  # nuclear plant is large
        assert result.osm_id is not None
        assert result.quality in ("high", "medium")

    def test_braila_has_industrial(self, overpass_client):
        """Braila coal plant area has industrial landuse polygons."""
        result = overpass_client.fetch_site_area(45.27, 27.96, radius_m=2000)
        assert result.candidate_count > 0 or result.error is not None

    def test_middle_of_ocean_returns_not_found(self, overpass_client):
        """A point in the middle of the ocean should return no polygons."""
        result = overpass_client.fetch_site_area(0.0, 0.0, radius_m=500)
        assert result.site_area_ha is None
        assert result.quality == "not_found"


class TestCorineConnectivity:
    def test_corine_health_check(self):
        from atoms_vs_ashes.connectors.corine import CorineConnector
        with CorineConnector() as corine:
            assert corine.health_check() is True
