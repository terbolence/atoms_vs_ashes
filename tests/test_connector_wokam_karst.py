# man_hours: 3.5
"""Tests for the S-25 WOKAM (World Karst Aquifer Map) connector.

Covers: rock-type normalisation, severity classification, spatial query
logic with mock geometries, result dataclass structure, edge cases,
and batch result aggregation.

No network, no fiona dependency required — all spatial I/O is mocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box

from atoms_vs_ashes.connectors.wokam_karst import (
    CRITERION_ID,
    BatchResult,
    KarstResult,
    SiteEnrichmentSummary,
    WokamKarstConnector,
)
from atoms_vs_ashes.connectors.wokam_karst.models import (
    DOWNLOAD_URL,
    ROCK_TYPE_CODE_MAP,
    ROCK_TYPE_MAP,
    SEVERITY_MAP,
    SOURCE_NAME,
    SOURCE_URL,
    VERDICT_MAP,
    KarstPolygon,
    SpatialIndex,
)
from atoms_vs_ashes.connectors.wokam_karst.parsers import (
    build_spatial_index,
    classify_severity,
    normalise_rock_type,
    parse_feature,
    query_site,
)


# ---------------------------------------------------------------------------
# Helpers: mock karst polygons and spatial index
# ---------------------------------------------------------------------------

def _make_karst_polygon(
    fid: int = 0,
    rock_type: str = "carbonate",
    bounds: tuple[float, float, float, float] = (25.0, 44.0, 26.0, 45.0),
    aquifer_class: str | None = None,
) -> KarstPolygon:
    """Build a KarstPolygon with a rectangular geometry."""
    geom = box(*bounds)
    normalised = normalise_rock_type(rock_type)
    return KarstPolygon(
        fid=fid,
        rock_type=rock_type,
        rock_type_normalised=normalised,
        aquifer_class=aquifer_class,
        geometry=geom,
    )


def _make_index(*polygons: KarstPolygon) -> SpatialIndex:
    """Build a SpatialIndex from one or more KarstPolygon objects."""
    return build_spatial_index(list(polygons))


# ---------------------------------------------------------------------------
# TestRockTypeNormalisation — pure logic, no I/O
# ---------------------------------------------------------------------------

class TestRockTypeNormalisation:
    """Tests for normalise_rock_type() mapping."""

    def test_carbonate_variants(self):
        assert normalise_rock_type("carbonate") == "carbonate"
        assert normalise_rock_type("Carbonate") == "carbonate"
        assert normalise_rock_type("carbonate rocks") == "carbonate"
        assert normalise_rock_type("CARBONATE ROCKS") == "carbonate"

    def test_evaporite_variants(self):
        assert normalise_rock_type("evaporite") == "evaporite"
        assert normalise_rock_type("Evaporite Rocks") == "evaporite"
        assert normalise_rock_type("evaporite rocks") == "evaporite"

    def test_mixed_variants(self):
        assert normalise_rock_type("mixed") == "mixed"
        assert normalise_rock_type("carbonate and evaporite") == "mixed"

    def test_none_defaults_to_carbonate(self):
        assert normalise_rock_type(None) == "carbonate"

    def test_empty_string_defaults_to_carbonate(self):
        assert normalise_rock_type("") == "carbonate"

    def test_unknown_string_defaults_to_carbonate(self):
        assert normalise_rock_type("sandstone") == "carbonate"

    def test_whitespace_handling(self):
        assert normalise_rock_type("  carbonate  ") == "carbonate"

    def test_integer_code_1_carbonate(self):
        assert normalise_rock_type(1) == "carbonate"

    def test_integer_code_2_carbonate(self):
        assert normalise_rock_type(2) == "carbonate"

    def test_integer_code_3_evaporite(self):
        assert normalise_rock_type(3) == "evaporite"

    def test_integer_code_4_mixed(self):
        assert normalise_rock_type(4) == "mixed"

    def test_integer_code_5_evaporite(self):
        assert normalise_rock_type(5) == "evaporite"

    def test_integer_code_unknown_defaults(self):
        assert normalise_rock_type(99) == "carbonate"

    def test_rtypelabel_continuous_carbonate(self):
        assert normalise_rock_type("Continuous carbonate rocks") == "carbonate"

    def test_rtypelabel_discontinuous_carbonate(self):
        assert normalise_rock_type("Discontinuous carbonate rocks") == "carbonate"

    def test_rtypelabel_continuous_evaporite(self):
        assert normalise_rock_type("Continuous evaporite rocks") == "evaporite"

    def test_rtypelabel_mixed(self):
        assert normalise_rock_type("Mixed carbonate and evaporite rocks") == "mixed"


# ---------------------------------------------------------------------------
# TestSeverityClassification — pure logic
# ---------------------------------------------------------------------------

class TestSeverityClassification:
    """Tests for classify_severity() and SEVERITY_MAP."""

    def test_evaporite_is_high(self):
        assert classify_severity("evaporite") == "high"

    def test_mixed_is_high(self):
        assert classify_severity("mixed") == "high"

    def test_carbonate_is_moderate(self):
        assert classify_severity("carbonate") == "moderate"

    def test_unknown_defaults_to_moderate(self):
        assert classify_severity("unknown") == "moderate"

    def test_severity_map_complete(self):
        assert set(SEVERITY_MAP.keys()) == {"evaporite", "mixed", "carbonate"}

    def test_verdict_map_complete(self):
        assert set(VERDICT_MAP.keys()) == {"high", "moderate", "none"}
        assert VERDICT_MAP["high"] == "fail"
        assert VERDICT_MAP["moderate"] == "caution"
        assert VERDICT_MAP["none"] == "pass"


# ---------------------------------------------------------------------------
# TestParseFeature — GeoJSON feature parsing
# ---------------------------------------------------------------------------

class TestParseFeature:
    """Tests for parse_feature() with GeoJSON-like dicts."""

    def test_valid_polygon(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0), (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {"ROCK_TYPE": "carbonate"},
        }
        poly = parse_feature(feature, fid=0)
        assert poly is not None
        assert poly.rock_type == "carbonate"
        assert poly.rock_type_normalised == "carbonate"
        assert poly.fid == 0

    def test_evaporite_feature(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(20.0, 40.0), (21.0, 40.0), (21.0, 41.0), (20.0, 41.0), (20.0, 40.0)]],
            },
            "properties": {"ROCK_TYPE": "evaporite rocks"},
        }
        poly = parse_feature(feature, fid=1)
        assert poly is not None
        assert poly.rock_type_normalised == "evaporite"
        assert poly.severity == "high"

    def test_empty_geometry_returns_none(self):
        feature = {
            "geometry": {"type": "Polygon", "coordinates": []},
            "properties": {"ROCK_TYPE": "carbonate"},
        }
        result = parse_feature(feature, fid=0)
        assert result is None

    def test_missing_geometry_returns_none(self):
        feature = {"properties": {"ROCK_TYPE": "carbonate"}}
        result = parse_feature(feature, fid=0)
        assert result is None

    def test_missing_properties_uses_defaults(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0), (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {},
        }
        poly = parse_feature(feature, fid=0)
        assert poly is not None
        assert poly.rock_type == "unknown"
        assert poly.rock_type_normalised == "carbonate"

    def test_aquifer_class_extracted(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0), (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {"ROCK_TYPE": "carbonate", "AQUIFER": "major karst aquifer"},
        }
        poly = parse_feature(feature, fid=0)
        assert poly is not None
        assert poly.aquifer_class == "major karst aquifer"

    def test_actual_wokam_feature_format(self):
        """Test with the actual WOKAM shapefile attribute schema."""
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0), (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {"rock_type": 3, "RTypeLabel": "Continuous evaporite rocks"},
        }
        poly = parse_feature(feature, fid=0)
        assert poly is not None
        assert poly.rock_type_normalised == "evaporite"
        assert poly.severity == "high"
        assert "evaporite" in poly.rock_type.lower()

    def test_actual_wokam_carbonate_feature(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(25.0, 44.0), (26.0, 44.0), (26.0, 45.0), (25.0, 45.0), (25.0, 44.0)]],
            },
            "properties": {"rock_type": 1, "RTypeLabel": "Continuous carbonate rocks"},
        }
        poly = parse_feature(feature, fid=0)
        assert poly is not None
        assert poly.rock_type_normalised == "carbonate"
        assert poly.severity == "moderate"


# ---------------------------------------------------------------------------
# TestSpatialIndex — index construction
# ---------------------------------------------------------------------------

class TestSpatialIndex:
    """Tests for build_spatial_index()."""

    def test_empty_list(self):
        idx = build_spatial_index([])
        assert idx.feature_count == 0
        assert idx.polygons == []

    def test_single_polygon(self):
        poly = _make_karst_polygon(fid=0)
        idx = _make_index(poly)
        assert idx.feature_count == 1
        assert len(idx.polygons) == 1

    def test_multiple_polygons(self):
        p1 = _make_karst_polygon(fid=0, bounds=(25.0, 44.0, 26.0, 45.0))
        p2 = _make_karst_polygon(fid=1, bounds=(27.0, 44.0, 28.0, 45.0))
        idx = _make_index(p1, p2)
        assert idx.feature_count == 2

    def test_none_geometry_filtered(self):
        p1 = _make_karst_polygon(fid=0)
        p2 = KarstPolygon(fid=1, rock_type="carbonate", rock_type_normalised="carbonate", geometry=None)
        idx = build_spatial_index([p1, p2])
        assert idx.feature_count == 1


# ---------------------------------------------------------------------------
# TestQuerySite — point-in-polygon and nearest distance
# ---------------------------------------------------------------------------

class TestQuerySite:
    """Tests for query_site() with mock spatial indices."""

    def test_point_inside_karst(self):
        poly = _make_karst_polygon(fid=42, rock_type="carbonate", bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(poly)
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.karst_present is True
        assert result.karst_severity == "moderate"
        assert result.distance_to_nearest_km == pytest.approx(0.0)
        assert result.nearest_polygon_id == 42
        assert result.error is None

    def test_point_inside_evaporite(self):
        poly = _make_karst_polygon(fid=7, rock_type="evaporite", bounds=(20.0, 40.0, 21.0, 41.0))
        idx = _make_index(poly)
        result = query_site(lat=40.5, lon=20.5, index=idx)
        assert result.karst_present is True
        assert result.karst_severity == "high"

    def test_point_outside_karst(self):
        poly = _make_karst_polygon(fid=0, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(poly)
        result = query_site(lat=50.0, lon=20.0, index=idx)
        assert result.karst_present is False
        assert result.karst_severity == "none"
        assert result.distance_to_nearest_km is not None
        assert result.distance_to_nearest_km > 0

    def test_empty_index(self):
        idx = build_spatial_index([])
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.karst_present is False
        assert result.error is not None

    def test_point_on_boundary(self):
        poly = _make_karst_polygon(fid=0, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(poly)
        result = query_site(lat=44.0, lon=25.0, index=idx)
        # Boundary behaviour depends on Shapely; either inside or very close
        assert result.error is None

    def test_multiple_polygons_nearest(self):
        p1 = _make_karst_polygon(fid=0, rock_type="carbonate", bounds=(25.0, 44.0, 26.0, 45.0))
        p2 = _make_karst_polygon(fid=1, rock_type="evaporite", bounds=(30.0, 44.0, 31.0, 45.0))
        idx = _make_index(p1, p2)
        result = query_site(lat=44.5, lon=28.0, index=idx)
        assert result.karst_present is False
        assert result.distance_to_nearest_km is not None

    def test_coordinates_preserved(self):
        poly = _make_karst_polygon(fid=0, bounds=(25.0, 44.0, 26.0, 45.0))
        idx = _make_index(poly)
        result = query_site(lat=44.5, lon=25.5, index=idx)
        assert result.lat == pytest.approx(44.5)
        assert result.lon == pytest.approx(25.5)


# ---------------------------------------------------------------------------
# TestKarstResultStructure — dataclass shape and serialization
# ---------------------------------------------------------------------------

class TestKarstResultStructure:
    """Tests for KarstResult dataclass and to_dict()."""

    def test_default_values(self):
        r = KarstResult(lat=44.0, lon=28.0)
        assert r.source == SOURCE_NAME
        assert r.quality == "wokam_global"
        assert r.error is None
        assert r.karst_present is False
        assert r.karst_severity == "none"

    def test_to_dict_keys(self):
        r = KarstResult(lat=44.0, lon=28.0, karst_present=True, karst_severity="moderate")
        d = r.to_dict()
        expected_keys = {
            "lat", "lon", "karst_present", "karst_severity",
            "karst_formation_type", "rock_type_raw", "aquifer_class_raw",
            "distance_to_nearest_km", "nearest_polygon_id",
            "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_values(self):
        r = KarstResult(
            lat=44.32, lon=28.05,
            karst_present=True, karst_severity="high",
            karst_formation_type="evaporite",
            distance_to_nearest_km=0.0,
        )
        d = r.to_dict()
        assert d["lat"] == pytest.approx(44.32)
        assert d["lon"] == pytest.approx(28.05)
        assert d["karst_present"] is True
        assert d["karst_severity"] == "high"
        assert d["distance_to_nearest_km"] == pytest.approx(0.0)

    def test_error_result_to_dict(self):
        r = KarstResult(lat=0.0, lon=0.0, error="No data", quality="low")
        d = r.to_dict()
        assert d["error"] == "No data"
        assert d["karst_present"] is False

    def test_distance_rounding(self):
        r = KarstResult(lat=44.0, lon=28.0, distance_to_nearest_km=12.34567)
        d = r.to_dict()
        assert d["distance_to_nearest_km"] == pytest.approx(12.346, abs=0.001)


# ---------------------------------------------------------------------------
# TestBatchResult — aggregate result structure
# ---------------------------------------------------------------------------

class TestBatchResult:
    """Tests for BatchResult and SiteEnrichmentSummary."""

    def test_empty_batch(self):
        b = BatchResult(run_id="test-001")
        assert b.total_sites == 0
        assert b.summary_line() == "0 sites: 0 ok, 0 failed, 0 cached (0.0 s)"

    def test_batch_summary_seconds(self):
        b = BatchResult(
            run_id="test-001", total_sites=10,
            succeeded=8, failed=1, skipped_cached=1, elapsed_s=5.3,
        )
        line = b.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line
        assert "5.3 s" in line

    def test_batch_summary_minutes(self):
        b = BatchResult(run_id="test-001", total_sites=100, succeeded=95, elapsed_s=120.0)
        assert "2.0 min" in b.summary_line()

    def test_batch_to_dict(self):
        sid = uuid.uuid4()
        b = BatchResult(
            run_id="test-001", total_sites=1, succeeded=1,
            per_site=[SiteEnrichmentSummary(
                site_id=sid, site_name="Test Plant",
                status="ok", karst_present=True, karst_severity="moderate",
            )],
        )
        d = b.to_dict()
        assert d["run_id"] == "test-001"
        assert len(d["per_site"]) == 1
        assert d["per_site"][0]["karst_present"] is True
        assert d["per_site"][0]["site_id"] == str(sid)


# ---------------------------------------------------------------------------
# TestConnectorInit — configuration and lifecycle
# ---------------------------------------------------------------------------

class TestConnectorInit:
    """Tests for connector initialization and configuration."""

    def test_default_settings(self):
        c = WokamKarstConnector()
        assert c._data_dir.name == "wokam"
        assert c._download_url == DOWNLOAD_URL
        assert c._cache_ttl_days == 36500

    def test_custom_settings_via_yaml(self):
        settings = MagicMock()
        settings.connector_config.return_value = {
            "data_dir": "/tmp/custom_karst",
            "cache_ttl_days": 999,
        }
        c = WokamKarstConnector(settings)
        assert str(c._data_dir) == "/tmp/custom_karst"
        assert c._cache_ttl_days == 999

    def test_context_manager(self):
        with WokamKarstConnector() as c:
            assert isinstance(c, WokamKarstConnector)

    def test_data_dir_property(self):
        c = WokamKarstConnector()
        assert "wokam" in str(c.data_dir)


# ---------------------------------------------------------------------------
# TestConstants — domain constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module-level constants."""

    def test_criterion_id(self):
        assert CRITERION_ID == "NH-05"

    def test_source_name(self):
        assert SOURCE_NAME == "wokam_karst"

    def test_source_url_is_bgr(self):
        assert "whymap" in SOURCE_URL.lower() or "bgr" in SOURCE_URL.lower()

    def test_download_url_is_zip(self):
        assert DOWNLOAD_URL.endswith(".zip")
        assert "WOKAM" in DOWNLOAD_URL

    def test_rock_type_map_has_key_variants(self):
        assert "carbonate" in ROCK_TYPE_MAP
        assert "evaporite" in ROCK_TYPE_MAP
        assert "mixed" in ROCK_TYPE_MAP

    def test_severity_map_values(self):
        assert all(v in ("high", "moderate") for v in SEVERITY_MAP.values())
