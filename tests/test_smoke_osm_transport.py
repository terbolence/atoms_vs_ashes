# man_hours: 1.5
"""Smoke tests for P11 OSM transport access — requires live API access.

Run with:
    pytest tests/test_smoke_osm_transport.py -v -m smoke

Canonical site: Braila, Romania (45.27, 27.96) — coal plant near Danube.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


@pytest.fixture()
def overpass_client():
    from atoms_vs_ashes.connectors.osm import OverpassClient
    client = OverpassClient()
    yield client
    client.close()


class TestTransportConnectivity:
    def test_health_check(self, overpass_client):
        assert overpass_client.health_check() is True

    def test_highway_fetch_returns_elements(self, overpass_client):
        elements = overpass_client.fetch_nearest_highway(_TEST_LAT, _TEST_LON)
        assert isinstance(elements, list)
        assert len(elements) > 0, "Expected highways near Braila"

    def test_railway_fetch_returns_elements(self, overpass_client):
        elements = overpass_client.fetch_nearest_railway(_TEST_LAT, _TEST_LON)
        assert isinstance(elements, list)
        assert len(elements) > 0, "Expected railways near Braila"

    def test_waterway_fetch_returns_elements(self, overpass_client):
        elements = overpass_client.fetch_nearest_navigable_waterway(
            _TEST_LAT, _TEST_LON,
        )
        assert isinstance(elements, list)


class TestTransportClassification:
    def test_highway_classification(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import classify_highways
        elements = overpass_client.fetch_nearest_highway(_TEST_LAT, _TEST_LON)
        result = classify_highways(_TEST_LAT, _TEST_LON, elements)
        assert result.nearest_highway_km is not None
        assert result.nearest_highway_km >= 0
        assert result.nearest_highway_type in (
            "motorway", "trunk", "primary", None,
        )

    def test_railway_classification(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import classify_railways
        elements = overpass_client.fetch_nearest_railway(_TEST_LAT, _TEST_LON)
        result = classify_railways(
            _TEST_LAT, _TEST_LON, elements, country_code="RO",
        )
        assert result.nearest_rail_km is not None
        assert result.nearest_rail_km >= 0
        assert result.rail_gauge_mm in (1435, 1520, 760, None)

    def test_waterway_classification(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import classify_waterways
        elements = overpass_client.fetch_nearest_navigable_waterway(
            _TEST_LAT, _TEST_LON,
        )
        result = classify_waterways(_TEST_LAT, _TEST_LON, elements)
        if result.nearest_waterway_km is not None:
            assert result.nearest_waterway_km >= 0


class TestEndToEndSingleSite:
    def test_full_transport_assessment(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import (
            assess_heavy_haul,
            classify_highways,
            classify_railways,
            classify_waterways,
        )

        hw_elements = overpass_client.fetch_nearest_highway(_TEST_LAT, _TEST_LON)
        rw_elements = overpass_client.fetch_nearest_railway(_TEST_LAT, _TEST_LON)
        ww_elements = overpass_client.fetch_nearest_navigable_waterway(
            _TEST_LAT, _TEST_LON,
        )

        hw = classify_highways(_TEST_LAT, _TEST_LON, hw_elements)
        rw = classify_railways(_TEST_LAT, _TEST_LON, rw_elements, country_code="RO")
        ww = classify_waterways(_TEST_LAT, _TEST_LON, ww_elements)

        capable, confidence = assess_heavy_haul(hw, rw, ww)
        assert capable in (True, None)
        assert confidence in ("high", "medium", "low")


class TestCoverageEdges:
    def test_out_of_coverage_ocean(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import classify_highways
        elements = overpass_client.fetch_nearest_highway(0.0, 0.0, radius_km=5)
        result = classify_highways(0.0, 0.0, elements)
        assert result.nearest_highway_km is None or result.element_count == 0

    def test_armenia_boundary(self, overpass_client):
        from atoms_vs_ashes.connectors.osm.parsers import classify_railways
        elements = overpass_client.fetch_nearest_railway(40.18, 44.51, radius_km=10)
        result = classify_railways(40.18, 44.51, elements, country_code="AM")
        assert result is not None
        if result.rail_gauge_mm is not None:
            assert result.rail_gauge_mm == 1520
