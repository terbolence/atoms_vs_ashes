# man_hours: 2.5
"""Tests for the S-29 HydroRIVERS connector.

Covers: feature parsing, spatial index construction, nearest-river query,
river source type classification, result dataclass structure, edge cases,
and batch result aggregation.

No network, no fiona dependency — all spatial I/O is mocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from shapely.geometry import LineString, MultiLineString, Point, box

from atoms_vs_ashes.connectors.hydrorivers import (
    CRITERION_ID,
    BatchResult,
    HydroRiversConnector,
    RiverResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.hydrorivers.models import (
    DEFAULT_SEARCH_RADIUS_KM,
    MIN_COOLING_STRAHLER_ORDER,
    REGION_URLS,
    SOURCE_NAME,
    SOURCE_URL,
    RiverReach,
    RiverSpatialIndex,
    river_source_type,
)
from atoms_vs_ashes.connectors.hydrorivers.parsers import (
    build_spatial_index,
    parse_feature,
    query_site,
)


# ---------------------------------------------------------------------------
# Helpers: mock river reaches and spatial index
# ---------------------------------------------------------------------------

def _make_river_reach(
    hyriv_id: int = 1000,
    ord_stra: int = 4,
    dis_av_cms: float = 25.0,
    coords: list[tuple[float, float]] | None = None,
    river_name: str | None = "Danube",
) -> RiverReach:
    """Build a RiverReach with a simple LineString geometry."""
    if coords is None:
        coords = [(25.0, 44.0), (26.0, 44.5)]
    geom = LineString(coords)
    return RiverReach(
        hyriv_id=hyriv_id,
        next_down=0,
        main_riv=100,
        length_km=50.0,
        ord_stra=ord_stra,
        ord_clas=ord_stra,
        dis_av_cms=dis_av_cms,
        river_name=river_name,
        geometry=geom,
    )


def _make_index(*reaches: RiverReach, min_strahler: int = 1) -> RiverSpatialIndex:
    """Build a RiverSpatialIndex from one or more RiverReach objects."""
    return build_spatial_index(list(reaches), min_strahler=min_strahler)


# ---------------------------------------------------------------------------
# TestRiverSourceType — classification logic
# ---------------------------------------------------------------------------

class TestRiverSourceType:
    """Tests for river_source_type() classification."""

    def test_major_river_by_discharge(self):
        assert river_source_type(4, 150.0) == "major_river"

    def test_major_river_by_order(self):
        assert river_source_type(6, 50.0) == "major_river"

    def test_river(self):
        assert river_source_type(4, 30.0) == "river"

    def test_small_river(self):
        assert river_source_type(3, 5.0) == "small_river"

    def test_stream(self):
        assert river_source_type(2, 0.5) == "stream"

    def test_stream_no_discharge(self):
        assert river_source_type(1, None) == "stream"

    def test_major_river_high_order(self):
        assert river_source_type(7, None) == "major_river"


# ---------------------------------------------------------------------------
# TestParseFeature — GeoJSON feature parsing
# ---------------------------------------------------------------------------

class TestParseFeature:
    """Tests for parse_feature() with GeoJSON-like dicts."""

    def test_valid_linestring(self):
        feature = {
            "geometry": {
                "type": "LineString",
                "coordinates": [(25.0, 44.0), (26.0, 44.5)],
            },
            "properties": {
                "HYRIV_ID": 12345,
                "ORD_STRA": 4,
                "DIS_AV_CMS": 25.5,
                "LENGTH_KM": 50.0,
                "NEXT_DOWN": 12344,
                "MAIN_RIV": 100,
                "ORD_CLAS": 4,
            },
        }
        reach = parse_feature(feature, fid=0)
        assert reach is not None
        assert reach.hyriv_id == 12345
        assert reach.ord_stra == 4
        assert reach.dis_av_cms == pytest.approx(25.5)

    def test_missing_hyriv_id_returns_none(self):
        feature = {
            "geometry": {
                "type": "LineString",
                "coordinates": [(25.0, 44.0), (26.0, 44.5)],
            },
            "properties": {"ORD_STRA": 3},
        }
        assert parse_feature(feature, fid=0) is None

    def test_empty_geometry_returns_none(self):
        feature = {
            "geometry": {"type": "LineString", "coordinates": []},
            "properties": {"HYRIV_ID": 1},
        }
        assert parse_feature(feature, fid=0) is None

    def test_missing_geometry_returns_none(self):
        feature = {"properties": {"HYRIV_ID": 1}}
        assert parse_feature(feature, fid=0) is None

    def test_river_name_extracted(self):
        feature = {
            "geometry": {
                "type": "LineString",
                "coordinates": [(25.0, 44.0), (26.0, 44.5)],
            },
            "properties": {
                "HYRIV_ID": 1,
                "RIVER_NAME": "Danube",
                "ORD_STRA": 6,
                "DIS_AV_CMS": 100.0,
            },
        }
        reach = parse_feature(feature, fid=0)
        assert reach is not None
        assert reach.river_name == "Danube"

    def test_defaults_for_missing_attributes(self):
        feature = {
            "geometry": {
                "type": "LineString",
                "coordinates": [(25.0, 44.0), (26.0, 44.5)],
            },
            "properties": {"HYRIV_ID": 1},
        }
        reach = parse_feature(feature, fid=0)
        assert reach is not None
        assert reach.ord_stra == 1
        assert reach.dis_av_cms == 0.0
        assert reach.river_name is None


# ---------------------------------------------------------------------------
# TestSpatialIndex — index construction
# ---------------------------------------------------------------------------

class TestSpatialIndex:
    """Tests for build_spatial_index()."""

    def test_empty_list(self):
        idx = build_spatial_index([])
        assert idx.feature_count == 0

    def test_single_reach(self):
        r = _make_river_reach()
        idx = _make_index(r)
        assert idx.feature_count == 1

    def test_multiple_reaches(self):
        r1 = _make_river_reach(hyriv_id=1, coords=[(25.0, 44.0), (26.0, 44.5)])
        r2 = _make_river_reach(hyriv_id=2, coords=[(27.0, 45.0), (28.0, 45.5)])
        idx = _make_index(r1, r2)
        assert idx.feature_count == 2

    def test_strahler_filter(self):
        r1 = _make_river_reach(hyriv_id=1, ord_stra=2)
        r2 = _make_river_reach(hyriv_id=2, ord_stra=4)
        idx = _make_index(r1, r2, min_strahler=3)
        assert idx.feature_count == 1

    def test_none_geometry_filtered(self):
        r1 = _make_river_reach(hyriv_id=1)
        r2 = RiverReach(hyriv_id=2, next_down=0, main_riv=0, length_km=0,
                        ord_stra=3, ord_clas=3, dis_av_cms=0, geometry=None)
        idx = build_spatial_index([r1, r2])
        assert idx.feature_count == 1


# ---------------------------------------------------------------------------
# TestQuerySite — nearest river queries
# ---------------------------------------------------------------------------

class TestQuerySite:
    """Tests for query_site() with mock spatial indices."""

    def test_nearest_river_found(self):
        r = _make_river_reach(
            hyriv_id=42, ord_stra=5, dis_av_cms=50.0,
            coords=[(25.0, 44.0), (26.0, 44.5)],
            river_name="Test River",
        )
        idx = _make_index(r)
        result = query_site(lat=44.3, lon=25.5, index=idx)
        assert result.nearest_river_km is not None
        assert result.nearest_river_km < 50.0
        assert result.river_name == "Test River"
        assert result.river_id == 42
        assert result.strahler_order == 5
        assert result.discharge_m3s == pytest.approx(50.0)
        assert result.cooling_viable is True
        assert result.error is None

    def test_no_cooling_viable_stream(self):
        r = _make_river_reach(hyriv_id=1, ord_stra=2, dis_av_cms=0.5,
                              coords=[(25.0, 44.0), (26.0, 44.5)])
        idx = _make_index(r)
        result = query_site(lat=44.3, lon=25.5, index=idx)
        assert result.cooling_viable is False
        assert result.source_type == "stream"

    def test_empty_index(self):
        idx = build_spatial_index([])
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.error is not None
        assert result.nearest_river_km is None

    def test_river_beyond_search_radius(self):
        r = _make_river_reach(coords=[(0.0, 0.0), (1.0, 0.5)])
        idx = _make_index(r)
        result = query_site(lat=44.5, lon=25.5, index=idx, search_radius_km=10.0)
        assert result.error is not None
        assert "limit" in result.error

    def test_coordinates_preserved(self):
        r = _make_river_reach()
        idx = _make_index(r)
        result = query_site(lat=44.3, lon=25.5, index=idx)
        assert result.lat == pytest.approx(44.3)
        assert result.lon == pytest.approx(25.5)


# ---------------------------------------------------------------------------
# TestRiverResultStructure
# ---------------------------------------------------------------------------

class TestRiverResultStructure:
    """Tests for RiverResult dataclass and to_dict()."""

    def test_default_values(self):
        r = RiverResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "hydrorivers_global"
        assert r.cooling_viable is False

    def test_to_dict_keys(self):
        r = RiverResult(lat=44.0, lon=28.0, nearest_river_km=5.0)
        d = r.to_dict()
        expected = {
            "lat", "lon", "nearest_river_km", "river_name", "river_id",
            "strahler_order", "discharge_m3s", "source_type",
            "cooling_viable", "source", "quality", "error",
        }
        assert set(d.keys()) == expected

    def test_distance_rounding(self):
        r = RiverResult(lat=44.0, lon=28.0, nearest_river_km=5.12345)
        d = r.to_dict()
        assert d["nearest_river_km"] == pytest.approx(5.123, abs=0.001)

    def test_discharge_rounding(self):
        r = RiverResult(lat=44.0, lon=28.0, discharge_m3s=123.456)
        d = r.to_dict()
        assert d["discharge_m3s"] == pytest.approx(123.46, abs=0.01)


# ---------------------------------------------------------------------------
# TestBatchResult
# ---------------------------------------------------------------------------

class TestBatchResult:
    """Tests for BatchResult and SiteEnrichmentSummary."""

    def test_empty_batch(self):
        b = BatchResult(run_id="test-001")
        assert b.total_sites == 0
        assert "0 sites" in b.summary_line()

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", nearest_river_km=2.5,
                discharge_m3s=50.0, source_type="river",
            )],
        )
        d = b.to_dict()
        assert d["run_id"] == "test-001"
        assert len(d["per_site"]) == 1
        assert d["per_site"][0]["site_id"] == str(sid)


# ---------------------------------------------------------------------------
# TestConnectorInit
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for HydroRiversConnector initialization."""

    def test_default_settings(self):
        c = HydroRiversConnector()
        assert "hydrorivers" in str(c.data_dir)
        assert c._cache_ttl_days == 36500

    def test_custom_settings(self):
        settings = MagicMock()
        settings.connector_config.return_value = {
            "data_dir": "/tmp/rivers",
            "search_radius_km": 30,
        }
        c = HydroRiversConnector(settings)
        assert str(c._data_dir) == "/tmp/rivers"
        assert c._search_radius_km == 30

    def test_context_manager(self):
        with HydroRiversConnector() as c:
            assert isinstance(c, HydroRiversConnector)


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module-level constants."""

    def test_criterion_id(self):
        assert CRITERION_ID == "NS-01"

    def test_source_name(self):
        assert SOURCE_NAME == "hydrorivers"

    def test_region_urls(self):
        assert "eu" in REGION_URLS
        assert "as" in REGION_URLS
        for url in REGION_URLS.values():
            assert url.endswith(".zip")

    def test_min_strahler_order(self):
        assert MIN_COOLING_STRAHLER_ORDER == 3

    def test_search_radius(self):
        assert DEFAULT_SEARCH_RADIUS_KM == 50.0
