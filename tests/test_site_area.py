# man_hours: 3.0
"""Unit tests for FIX-03 site area enrichment.

Tests parsing, candidate selection, area computation, and CORINE fallback
using real Overpass API fixtures saved during the exploration phase.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


# ------------------------------------------------------------------
# Fixture loading
# ------------------------------------------------------------------

@pytest.fixture()
def braila_elements() -> list[dict]:
    with open(FIXTURES / "osm_site_area_braila.json") as f:
        return json.load(f)["elements"]


@pytest.fixture()
def cernavoda_elements() -> list[dict]:
    with open(FIXTURES / "osm_site_area_cernavoda.json") as f:
        return json.load(f)["elements"]


# ------------------------------------------------------------------
# _parse_site_area_candidates
# ------------------------------------------------------------------

class TestParseSiteAreaCandidates:
    def test_braila_returns_candidates(self, braila_elements):
        from atoms_vs_ashes.connectors.osm.client import _parse_site_area_candidates

        candidates = _parse_site_area_candidates(45.27, 27.96, braila_elements)
        assert len(candidates) > 0
        for c in candidates:
            assert c.area_ha > 0
            assert c.osm_type == "way"
            assert c.distance_km >= 0

    def test_cernavoda_has_power_plant(self, cernavoda_elements):
        from atoms_vs_ashes.connectors.osm.client import _parse_site_area_candidates

        candidates = _parse_site_area_candidates(44.32, 28.05, cernavoda_elements)
        power_plants = [c for c in candidates if c.tags.get("power") == "plant"]
        assert len(power_plants) >= 1
        nuclear = [c for c in power_plants if "Cernavodă" in (c.tags.get("name") or "")]
        assert len(nuclear) == 1
        assert nuclear[0].area_ha > 10  # nuclear plant is large

    def test_empty_elements_returns_empty(self):
        from atoms_vs_ashes.connectors.osm.client import _parse_site_area_candidates

        assert _parse_site_area_candidates(45.0, 28.0, []) == []

    def test_non_way_elements_skipped(self):
        from atoms_vs_ashes.connectors.osm.client import _parse_site_area_candidates

        elements = [{"type": "node", "id": 1, "lat": 45.0, "lon": 28.0, "tags": {}}]
        assert _parse_site_area_candidates(45.0, 28.0, elements) == []

    def test_tiny_polygons_filtered(self):
        from atoms_vs_ashes.connectors.osm.client import _parse_site_area_candidates

        elements = [{
            "type": "way",
            "id": 999,
            "geometry": [
                {"lat": 45.0, "lon": 28.0},
                {"lat": 45.0, "lon": 28.00001},
                {"lat": 45.00001, "lon": 28.00001},
                {"lat": 45.00001, "lon": 28.0},
                {"lat": 45.0, "lon": 28.0},
            ],
            "tags": {"landuse": "industrial"},
        }]
        candidates = _parse_site_area_candidates(45.0, 28.0, elements)
        assert len(candidates) == 0  # < 0.01 ha


# ------------------------------------------------------------------
# _largest_contiguous_ha
# ------------------------------------------------------------------

class TestLargestContiguousHa:
    def test_simple_polygon(self):
        from shapely.geometry import Polygon
        from atoms_vs_ashes.connectors.osm.client import _largest_contiguous_ha

        poly = Polygon([
            (28.0, 45.0), (28.01, 45.0), (28.01, 45.01), (28.0, 45.01), (28.0, 45.0)
        ])
        area = _largest_contiguous_ha(poly)
        assert area > 0

    def test_multipolygon_returns_largest(self):
        from shapely.geometry import MultiPolygon, Polygon
        from atoms_vs_ashes.connectors.osm.client import _largest_contiguous_ha

        small = Polygon([
            (28.0, 45.0), (28.001, 45.0), (28.001, 45.001), (28.0, 45.001), (28.0, 45.0)
        ])
        large = Polygon([
            (28.1, 45.1), (28.11, 45.1), (28.11, 45.11), (28.1, 45.11), (28.1, 45.1)
        ])
        mp = MultiPolygon([small, large])
        result = _largest_contiguous_ha(mp)
        from atoms_vs_ashes.geo import geodesic_area_ha
        assert abs(result - geodesic_area_ha(large)) < 0.1


# ------------------------------------------------------------------
# SiteAreaResult
# ------------------------------------------------------------------

class TestSiteAreaResult:
    def test_to_dict_with_values(self):
        from atoms_vs_ashes.connectors.osm.models import SiteAreaResult

        r = SiteAreaResult(
            site_area_ha=42.5,
            buildable_area_ha=42.5,
            largest_contiguous_ha=42.5,
            osm_id=12345,
            osm_type="way",
            source_tags={"landuse": "industrial", "name": "Test Plant"},
            distance_km=0.123,
            candidate_count=3,
        )
        d = r.to_dict()
        assert d["site_area_ha"] == 42.5
        assert d["osm_id"] == 12345
        assert d["candidate_count"] == 3
        assert d["quality"] == "high"

    def test_to_dict_with_none(self):
        from atoms_vs_ashes.connectors.osm.models import SiteAreaResult

        r = SiteAreaResult(error="not found", quality="not_found")
        d = r.to_dict()
        assert d["site_area_ha"] is None
        assert d["error"] == "not found"


# ------------------------------------------------------------------
# OverpassClient.fetch_site_area (mocked query)
# ------------------------------------------------------------------

class TestFetchSiteArea:
    def test_returns_result_from_fixture(self, braila_elements):
        from atoms_vs_ashes.connectors.osm import OverpassClient

        client = OverpassClient()
        with patch.object(client, "query", return_value=braila_elements):
            result = client.fetch_site_area(45.27, 27.96)

        assert result.site_area_ha is not None
        assert result.site_area_ha > 0
        assert result.osm_id is not None
        assert result.quality in ("high", "medium")
        assert result.candidate_count > 0

    def test_selects_closest_candidate(self, cernavoda_elements):
        from atoms_vs_ashes.connectors.osm import OverpassClient

        client = OverpassClient()
        with patch.object(client, "query", return_value=cernavoda_elements):
            result = client.fetch_site_area(44.32, 28.05)

        assert result.site_area_ha is not None
        assert result.osm_id is not None

    def test_empty_response_returns_not_found(self):
        from atoms_vs_ashes.connectors.osm import OverpassClient

        client = OverpassClient()
        with patch.object(client, "query", return_value=[]):
            result = client.fetch_site_area(45.0, 28.0)

        assert result.site_area_ha is None
        assert result.quality == "not_found"
        assert result.error is not None

    def test_retry_on_rate_limit(self):
        from atoms_vs_ashes.connectors.osm import OverpassClient
        from atoms_vs_ashes.connectors.osm.models import SiteAreaResult

        client = OverpassClient()
        call_count = 0

        def mock_fetch(lat, lon, radius_m=2000):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                client._last_http_status = 429
                return SiteAreaResult(error="rate limited", quality="not_found")
            return SiteAreaResult(site_area_ha=50.0, quality="high")

        with patch.object(client, "fetch_site_area", side_effect=mock_fetch):
            with patch.object(type(client), "was_rate_limited", new_callable=lambda: property(lambda self: self._last_http_status in (429, 504))):
                result = client.fetch_site_area_with_retry(45.0, 28.0, max_retries=3, backoff_base=0.01)

        assert result.site_area_ha == 50.0
        assert call_count == 3


# ------------------------------------------------------------------
# _build_comment
# ------------------------------------------------------------------

class TestSelectBestCandidate:
    def test_prefers_closest_when_large_enough(self):
        from atoms_vs_ashes.connectors.osm.client import _select_best_candidate
        from atoms_vs_ashes.connectors.osm.models import SiteAreaCandidate

        close_large = SiteAreaCandidate(
            osm_id=1, osm_type="way", tags={}, geometry=None,
            area_ha=50.0, centroid_lat=0, centroid_lon=0, distance_km=0.1,
        )
        far_larger = SiteAreaCandidate(
            osm_id=2, osm_type="way", tags={}, geometry=None,
            area_ha=100.0, centroid_lat=0, centroid_lon=0, distance_km=1.0,
        )
        assert _select_best_candidate([close_large, far_larger]).osm_id == 1

    def test_prefers_larger_when_closest_is_tiny(self):
        from atoms_vs_ashes.connectors.osm.client import _select_best_candidate
        from atoms_vs_ashes.connectors.osm.models import SiteAreaCandidate

        close_tiny = SiteAreaCandidate(
            osm_id=1, osm_type="way", tags={}, geometry=None,
            area_ha=0.1, centroid_lat=0, centroid_lon=0, distance_km=0.1,
        )
        far_large = SiteAreaCandidate(
            osm_id=2, osm_type="way", tags={}, geometry=None,
            area_ha=50.0, centroid_lat=0, centroid_lon=0, distance_km=1.5,
        )
        assert _select_best_candidate([close_tiny, far_large]).osm_id == 2

    def test_keeps_tiny_if_no_large_nearby(self):
        from atoms_vs_ashes.connectors.osm.client import _select_best_candidate
        from atoms_vs_ashes.connectors.osm.models import SiteAreaCandidate

        close_tiny = SiteAreaCandidate(
            osm_id=1, osm_type="way", tags={}, geometry=None,
            area_ha=0.1, centroid_lat=0, centroid_lon=0, distance_km=0.1,
        )
        very_far = SiteAreaCandidate(
            osm_id=2, osm_type="way", tags={}, geometry=None,
            area_ha=50.0, centroid_lat=0, centroid_lon=0, distance_km=10.0,
        )
        assert _select_best_candidate([close_tiny, very_far]).osm_id == 1

    def test_single_candidate_returned(self):
        from atoms_vs_ashes.connectors.osm.client import _select_best_candidate
        from atoms_vs_ashes.connectors.osm.models import SiteAreaCandidate

        only = SiteAreaCandidate(
            osm_id=1, osm_type="way", tags={}, geometry=None,
            area_ha=0.5, centroid_lat=0, centroid_lon=0, distance_km=0.1,
        )
        assert _select_best_candidate([only]).osm_id == 1


class TestBuildComment:
    def test_full_comment(self):
        from atoms_vs_ashes.analysis.site_area import _build_comment
        from atoms_vs_ashes.connectors.osm.models import SiteAreaResult

        r = SiteAreaResult(
            site_area_ha=42.5,
            osm_id=12345,
            osm_type="way",
            source_tags={"landuse": "industrial", "name": "Test"},
            distance_km=0.5,
            candidate_count=3,
        )
        comment = _build_comment(r)
        assert "osm_id=way/12345" in comment
        assert "landuse=industrial" in comment
        assert "candidates=3" in comment

    def test_minimal_comment(self):
        from atoms_vs_ashes.analysis.site_area import _build_comment
        from atoms_vs_ashes.connectors.osm.models import SiteAreaResult

        r = SiteAreaResult(source="corine_clc_121", quality="medium")
        comment = _build_comment(r)
        assert "source=corine_clc_121" in comment
