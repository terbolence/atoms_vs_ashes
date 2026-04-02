# man_hours: 8.0
"""Tests for the S-02 EGDI Geology connector.

Covers: pure parsing, classification, distance computation, result structures,
BBOX axis order, quality assessment, and integration with mocked HTTP.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import httpx
import pytest

from atoms_vs_ashes.connectors.egdi_geology import (
    BatchResult,
    BoreholeAssessment,
    EgdiGeologyConnector,
    EgdiGeologyResult,
    FaultAssessment,
    HydrogeologyAssessment,
    KarstAssessment,
    LithologyAssessment,
    MiningAssessment,
    SiteEnrichmentSummary,
    build_borehole_assessment,
    build_fault_assessment,
    build_karst_assessment,
    build_mining_assessment,
    build_wfs_bbox,
    classify_aquifer,
    classify_fault_activity,
    classify_lithology,
    compute_quality,
    nearest_feature_distance,
    parse_geojson_features,
    validate_coordinates_in_egdi_domain,
)


# ---------------------------------------------------------------------------
# Sample fixture data (trimmed from real EGDI WFS responses)
# ---------------------------------------------------------------------------

SAMPLE_FAULT_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[23.1, 44.15], [23.3, 44.25], [23.5, 44.35]],
            },
            "properties": {
                "fault_type": "normal",
                "activity": "active",
                "slip_rate": 0.5,
                "name": "Jiu Fault",
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[23.0, 44.50], [23.2, 44.60]],
            },
            "properties": {
                "fault_type": "thrust",
                "activity": "inactive",
                "name": "Northern Fault",
            },
        },
    ],
}

SAMPLE_MINE_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [23.12, 44.16]},
            "properties": {
                "status": "closed",
                "commodity": "coal",
                "name": "Petrila Mine",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [23.50, 44.40]},
            "properties": {
                "status": "operating",
                "commodity": "copper",
                "name": "Cupru Mine",
            },
        },
    ],
}

SAMPLE_HYDROGEOLOGY_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[23.0, 44.0], [23.5, 44.0], [23.5, 44.5], [23.0, 44.5], [23.0, 44.0]]
                ],
            },
            "properties": {
                "aquifer_type": "porous",
                "productivity": "moderate",
                "hydrogeologic_unit": "Wallachian Plain aquifer system",
            },
        },
    ],
}

SAMPLE_KARST_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[14.0, 49.8], [14.5, 49.8], [14.5, 50.2], [14.0, 50.2], [14.0, 49.8]]
                ],
            },
            "properties": {
                "karst_class": "mature karst",
                "type": "limestone",
            },
        },
    ],
}

SAMPLE_BOREHOLE_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [23.13, 44.16]},
            "properties": {
                "depth": 45.5,
                "lithology": "clay over sandstone",
                "name": "BH-001",
            },
        },
    ],
}

SAMPLE_LITHOLOGY_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[23.0, 44.0], [23.3, 44.0], [23.3, 44.3], [23.0, 44.3], [23.0, 44.0]]
                ],
            },
            "properties": {
                "lithology": "sandstone",
                "description": "Eocene sandstone formation",
            },
        },
    ],
}

SAMPLE_EMPTY_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [],
}

SAMPLE_MINING_AREA_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[23.0, 44.0], [23.3, 44.0], [23.3, 44.3], [23.0, 44.3], [23.0, 44.0]]
                ],
            },
            "properties": {
                "status": "closed",
                "commodity": "lignite",
                "name": "Oltenia Mining Area",
            },
        },
    ],
}


# ===================================================================
# Unit tests — GeoJSON parsing
# ===================================================================


class TestParseGeojsonFeatures:
    def test_valid_feature_collection(self):
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        assert len(features) == 2
        assert "geometry" in features[0]
        assert "properties" in features[0]

    def test_empty_collection(self):
        features = parse_geojson_features(SAMPLE_EMPTY_GEOJSON)
        assert features == []

    def test_not_a_dict(self):
        assert parse_geojson_features("not json") == []
        assert parse_geojson_features(None) == []
        assert parse_geojson_features(42) == []

    def test_missing_features_key(self):
        assert parse_geojson_features({"type": "FeatureCollection"}) == []

    def test_malformed_feature_skipped(self):
        raw = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature"},  # missing geometry and properties
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [23.0, 44.0]},
                    "properties": {"name": "valid"},
                },
            ],
        }
        features = parse_geojson_features(raw)
        assert len(features) == 1

    def test_feature_with_null_geometry(self):
        raw = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": None, "properties": {"a": 1}},
            ],
        }
        assert parse_geojson_features(raw) == []

    def test_single_feature(self):
        features = parse_geojson_features(SAMPLE_BOREHOLE_GEOJSON)
        assert len(features) == 1
        assert features[0]["properties"]["depth"] == 45.5


# ===================================================================
# Unit tests — Distance computation
# ===================================================================


class TestNearestFeatureDistance:
    def test_exact_point(self):
        features = parse_geojson_features(SAMPLE_BOREHOLE_GEOJSON)
        dist, nearest = nearest_feature_distance(features, 44.16, 23.13)
        assert dist is not None
        assert dist < 0.1  # within ~100 m of exact coordinates

    def test_picks_nearest_of_two(self):
        features = parse_geojson_features(SAMPLE_MINE_GEOJSON)
        dist, nearest = nearest_feature_distance(features, 44.16, 23.12)
        assert dist is not None
        assert dist < 1.0  # Petrila Mine is at the same coords
        assert nearest["properties"]["name"] == "Petrila Mine"

    def test_linestring_distance(self):
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        dist, nearest = nearest_feature_distance(features, 44.15, 23.10)
        assert dist is not None
        assert dist < 2.0  # very close to first fault's start

    def test_empty_features(self):
        dist, nearest = nearest_feature_distance([], 44.0, 23.0)
        assert dist is None
        assert nearest is None

    def test_polygon_distance(self):
        features = parse_geojson_features(SAMPLE_HYDROGEOLOGY_GEOJSON)
        dist, nearest = nearest_feature_distance(features, 44.25, 23.25)
        assert dist is not None
        assert dist < 50  # site is inside or near the polygon


# ===================================================================
# Unit tests — Lithology classification
# ===================================================================


class TestClassifyLithology:
    def test_sandstone(self):
        result = classify_lithology("Eocene sandstone")
        assert result.engineering_soil_group == "granular"
        assert result.rock_type == "sedimentary"
        assert result.liquefaction_susceptibility == "high"
        assert result.lithology_class == "Eocene sandstone"

    def test_granite(self):
        result = classify_lithology("Granite")
        assert result.engineering_soil_group == "rock"
        assert result.rock_type == "igneous"
        assert result.liquefaction_susceptibility == "negligible"

    def test_clay(self):
        result = classify_lithology("Quaternary clay deposits")
        assert result.engineering_soil_group == "cohesive"
        assert result.rock_type == "unconsolidated"
        assert result.liquefaction_susceptibility == "low"

    def test_limestone(self):
        result = classify_lithology("limestone")
        assert result.engineering_soil_group == "rock"
        assert result.rock_type == "sedimentary"

    def test_gneiss(self):
        result = classify_lithology("biotite gneiss")
        assert result.engineering_soil_group == "rock"
        assert result.rock_type == "metamorphic"

    def test_none_input(self):
        result = classify_lithology(None)
        assert result.lithology_class is None
        assert result.engineering_soil_group is None
        assert result.rock_type is None
        assert result.liquefaction_susceptibility is None

    def test_empty_string(self):
        result = classify_lithology("")
        assert result.lithology_class is None

    def test_unknown_lithology(self):
        result = classify_lithology("xenomorphic metacarbonate")
        assert result.lithology_class == "xenomorphic metacarbonate"
        # No match in tables — all derived fields are None
        assert result.engineering_soil_group is None

    def test_case_insensitive(self):
        result = classify_lithology("BASALT")
        assert result.engineering_soil_group == "rock"
        assert result.rock_type == "igneous"

    def test_peat(self):
        result = classify_lithology("peat bog")
        assert result.engineering_soil_group == "organic"
        assert result.liquefaction_susceptibility == "moderate"


# ===================================================================
# Unit tests — Fault activity classification
# ===================================================================


class TestClassifyFaultActivity:
    def test_active_with_slip_rate(self):
        props = {"activity": "active", "slip_rate": 0.5}
        activity, slip = classify_fault_activity(props)
        assert activity == "active"
        assert slip == pytest.approx(0.5)

    def test_case_insensitive_key(self):
        props = {"Activity": "Inactive"}
        activity, slip = classify_fault_activity(props)
        assert activity == "inactive"
        assert slip is None

    def test_missing_attributes(self):
        activity, slip = classify_fault_activity({})
        assert activity is None
        assert slip is None

    def test_negative_slip_rate(self):
        props = {"activity": "unknown", "slip_rate": -1.0}
        activity, slip = classify_fault_activity(props)
        assert activity == "unknown"
        assert slip is None

    def test_non_numeric_slip_rate(self):
        props = {"activity": "active", "slip_rate": "n/a"}
        activity, slip = classify_fault_activity(props)
        assert activity == "active"
        assert slip is None


# ===================================================================
# Unit tests — Aquifer classification
# ===================================================================


class TestClassifyAquifer:
    def test_full_attributes(self):
        props = {
            "aquifer_type": "porous",
            "productivity": "high",
            "vulnerability": "moderate",
            "status": "good",
            "id": "GW-001",
        }
        result = classify_aquifer(props)
        assert result.aquifer_type == "porous"
        assert result.aquifer_productivity == "high"
        assert result.vulnerability_class == "moderate"
        assert result.gw_body_status == "good"
        assert result.gw_body_id == "GW-001"

    def test_empty_props(self):
        result = classify_aquifer({})
        assert result.aquifer_type is None
        assert result.aquifer_productivity is None

    def test_partial_props(self):
        result = classify_aquifer({"aquifer_type": "Fissured"})
        assert result.aquifer_type == "fissured"
        assert result.aquifer_productivity is None


# ===================================================================
# Unit tests — Sub-result builders
# ===================================================================


class TestBuildFaultAssessment:
    def test_with_features(self):
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        result = build_fault_assessment(features, 44.15, 23.10, "ms:hike_all_faults_layer")
        assert result.fault_count_within_buffer == 2
        assert result.nearest_fault_distance_km is not None
        assert result.nearest_fault_distance_km >= 0
        assert result.nearest_fault_type is not None
        assert result.nearest_fault_activity is not None
        assert result.source_layer == "ms:hike_all_faults_layer"

    def test_empty_features(self):
        result = build_fault_assessment([], 44.15, 23.10, "ms:hike_all_faults_layer")
        assert result.fault_count_within_buffer == 0
        assert result.nearest_fault_distance_km is None

    def test_to_dict(self):
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        result = build_fault_assessment(features, 44.15, 23.10, "layer")
        d = result.to_dict()
        assert "nearest_fault_distance_km" in d
        assert "fault_count_within_buffer" in d


class TestBuildMiningAssessment:
    def test_with_point_features(self):
        features = parse_geojson_features(SAMPLE_MINE_GEOJSON)
        result = build_mining_assessment(features, 44.16, 23.12, ["ms:egdi_mines"])
        assert result.mine_count_within_buffer == 2
        assert result.nearest_mine_distance_km is not None
        assert result.nearest_mine_status == "closed"
        assert result.nearest_mine_commodity == "coal"
        assert not result.in_mining_area

    def test_in_mining_area(self):
        features = parse_geojson_features(SAMPLE_MINING_AREA_GEOJSON)
        # Site at 44.15, 23.15 is inside the polygon [23.0-23.3, 44.0-44.3]
        result = build_mining_assessment(features, 44.15, 23.15, ["ms:pp05_cgs_mining_areas"])
        assert result.in_mining_area is True

    def test_empty(self):
        result = build_mining_assessment([], 44.0, 23.0, [])
        assert result.mine_count_within_buffer == 0
        assert result.nearest_mine_distance_km is None


class TestBuildKarstAssessment:
    def test_in_karst_zone_cz(self):
        features = parse_geojson_features(SAMPLE_KARST_GEOJSON)
        result = build_karst_assessment(features, "CZ", "ms:pp05_cgs_karstified_zones")
        assert result.in_karst_zone is True
        assert result.karst_class == "mature karst"
        assert result.coverage_available is True

    def test_no_karst_features_with_coverage(self):
        result = build_karst_assessment([], "CZ", "ms:pp05_cgs_karstified_zones")
        assert result.in_karst_zone is False
        assert result.coverage_available is True

    def test_no_coverage_country(self):
        result = build_karst_assessment([], "RO", None)
        assert result.in_karst_zone is False
        assert result.coverage_available is False

    def test_no_coverage_with_features(self):
        """Features returned even for country without official coverage."""
        features = parse_geojson_features(SAMPLE_KARST_GEOJSON)
        result = build_karst_assessment(features, "RO", "ms:pp05_cgs_karstified_zones")
        assert result.in_karst_zone is True
        assert result.coverage_available is True


class TestBuildBoreholeAssessment:
    def test_with_features(self):
        features = parse_geojson_features(SAMPLE_BOREHOLE_GEOJSON)
        result = build_borehole_assessment(features, 44.16, 23.13, "ms:egdi_geotech_boreholes")
        assert result.borehole_count_within_buffer == 1
        assert result.nearest_borehole_distance_km is not None
        assert result.nearest_borehole_depth_m == pytest.approx(45.5)
        assert result.nearest_borehole_lithology == "clay over sandstone"

    def test_empty(self):
        result = build_borehole_assessment([], 44.0, 23.0, "ms:egdi_geotech_boreholes")
        assert result.borehole_count_within_buffer == 0
        assert result.nearest_borehole_depth_m is None


# ===================================================================
# Unit tests — BBOX construction
# ===================================================================


class TestBuildWfsBbox:
    def test_wfs_200_axis_order(self):
        bbox = build_wfs_bbox(44.15, 23.12, 8, wfs_version="2.0.0")
        parts = bbox.split(",")
        assert len(parts) == 5
        assert parts[-1] == "EPSG:4326"
        # WFS 2.0.0: lat_min, lon_min, lat_max, lon_max
        lat_min = float(parts[0])
        lon_min = float(parts[1])
        lat_max = float(parts[2])
        lon_max = float(parts[3])
        assert lat_min < 44.15 < lat_max
        assert lon_min < 23.12 < lon_max

    def test_wfs_100_axis_order(self):
        bbox = build_wfs_bbox(44.15, 23.12, 8, wfs_version="1.0.0")
        parts = bbox.split(",")
        # WFS 1.0.0: lon_min, lat_min, lon_max, lat_max
        lon_min = float(parts[0])
        lat_min = float(parts[1])
        lon_max = float(parts[2])
        lat_max = float(parts[3])
        assert lat_min < 44.15 < lat_max
        assert lon_min < 23.12 < lon_max

    def test_buffer_size(self):
        bbox = build_wfs_bbox(44.15, 23.12, 10, wfs_version="2.0.0")
        parts = bbox.split(",")
        lat_min = float(parts[0])
        lat_max = float(parts[2])
        # 10 km ≈ 0.09° latitude
        assert 0.05 < (lat_max - lat_min) / 2 < 0.15


# ===================================================================
# Unit tests — Quality assessment
# ===================================================================


class TestComputeQuality:
    def test_all_layers_with_data(self):
        assert compute_quality(["a", "b", "c"], ["a", "b", "c"]) == "high"

    def test_most_layers(self):
        assert compute_quality(["a", "b", "c"], ["a", "b", "c", "d"]) == "high"

    def test_half_layers(self):
        assert compute_quality(["a", "b"], ["a", "b", "c", "d", "e"]) == "medium"

    def test_one_layer(self):
        assert compute_quality(["a"], ["a", "b", "c", "d", "e"]) == "low"

    def test_no_data(self):
        assert compute_quality([], ["a", "b"]) == "insufficient"

    def test_no_queries(self):
        assert compute_quality([], []) == "insufficient"


# ===================================================================
# Unit tests — Coordinate validation
# ===================================================================


class TestCoordinateValidation:
    def test_in_domain(self):
        assert validate_coordinates_in_egdi_domain(44.15, 23.12) is True

    def test_northern_europe(self):
        assert validate_coordinates_in_egdi_domain(60.0, 25.0) is True

    def test_outside_south(self):
        assert validate_coordinates_in_egdi_domain(30.0, 23.0) is False

    def test_outside_east(self):
        assert validate_coordinates_in_egdi_domain(44.0, 50.0) is False

    def test_boundary(self):
        assert validate_coordinates_in_egdi_domain(35.0, -25.0) is True
        assert validate_coordinates_in_egdi_domain(72.0, 45.0) is True


# ===================================================================
# Unit tests — Result structure
# ===================================================================


class TestResultStructure:
    def test_egdi_geology_result_to_dict(self):
        result = EgdiGeologyResult(
            lat=44.15, lon=23.12,
            faults=FaultAssessment(
                nearest_fault_distance_km=3.5,
                nearest_fault_type="normal",
                nearest_fault_activity="active",
                fault_count_within_buffer=2,
                source_layer="ms:hike_all_faults_layer",
            ),
            lithology=LithologyAssessment(
                lithology_class="sandstone",
                engineering_soil_group="granular",
                rock_type="sedimentary",
                source_layer="ms:egdi_surface_lithology_sandstone",
            ),
            layers_queried=["layer_a", "layer_b"],
            layers_with_data=["layer_a"],
            layers_empty=["layer_b"],
            quality="medium",
        )
        d = result.to_dict()
        assert d["lat"] == 44.15
        assert d["lon"] == 23.12
        assert d["faults"]["nearest_fault_distance_km"] == 3.5
        assert d["lithology"]["lithology_class"] == "sandstone"
        assert d["quality"] == "medium"
        assert len(d["layers_queried"]) == 2
        assert d["mines"] is None
        assert d["karst"] is None

    def test_empty_result_to_dict(self):
        result = EgdiGeologyResult(lat=44.0, lon=23.0)
        d = result.to_dict()
        assert d["faults"] is None
        assert d["quality"] == "high"
        assert d["error"] is None

    def test_batch_result_summary_line(self):
        br = BatchResult(
            run_id="test-001",
            total_sites=20, succeeded=18, failed=2,
            skipped_cached=0, elapsed_s=125.0,
        )
        line = br.summary_line()
        assert "20 sites" in line
        assert "18 ok" in line
        assert "2 failed" in line
        assert "min" in line

    def test_batch_result_short_elapsed(self):
        br = BatchResult(run_id="t", elapsed_s=4.5, total_sites=1, succeeded=1)
        line = br.summary_line()
        assert "4.5 s" in line

    def test_batch_result_to_dict(self):
        br = BatchResult(
            run_id="run-x",
            total_sites=2, succeeded=1, failed=1,
            per_site=[
                SiteEnrichmentSummary(
                    site_id=uuid.uuid4(), site_name="Site A",
                    status="ok", criteria_written=["NH-02", "NH-03"],
                    quality="high", elapsed_ms=5000,
                ),
                SiteEnrichmentSummary(
                    site_id=uuid.uuid4(), site_name="Site B",
                    status="error", error="timeout", elapsed_ms=60000,
                ),
            ],
        )
        d = br.to_dict()
        assert d["total_sites"] == 2
        assert len(d["per_site"]) == 2
        assert d["per_site"][0]["status"] == "ok"
        assert d["per_site"][1]["error"] == "timeout"

    def test_all_sub_assessments_to_dict(self):
        fa = FaultAssessment(nearest_fault_distance_km=5.0).to_dict()
        assert "nearest_fault_distance_km" in fa

        la = LithologyAssessment(lithology_class="clay").to_dict()
        assert la["lithology_class"] == "clay"

        ma = MiningAssessment(mine_count_within_buffer=3).to_dict()
        assert ma["mine_count_within_buffer"] == 3

        ka = KarstAssessment(in_karst_zone=True).to_dict()
        assert ka["in_karst_zone"] is True

        ha = HydrogeologyAssessment(aquifer_type="porous").to_dict()
        assert ha["aquifer_type"] == "porous"

        ba = BoreholeAssessment(nearest_borehole_depth_m=50.0).to_dict()
        assert ba["nearest_borehole_depth_m"] == 50.0


# ===================================================================
# Integration tests — mocked HTTP
# ===================================================================


def _mock_json_response(data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = data
    resp.text = json.dumps(data)
    return resp


class TestConnectorSettings:
    def test_defaults_without_settings(self):
        connector = EgdiGeologyConnector()
        assert connector._timeout == 60
        assert connector._inter_request_delay == 1.0
        assert connector._cache_ttl_days == 180
        assert "europe-geology" in connector._wfs_url

    def test_from_settings(self, settings):
        connector = EgdiGeologyConnector(settings)
        assert connector._wfs_url == "https://maps.europe-geology.eu/wfs"
        assert connector._wfs_version == "2.0.0"
        assert connector._timeout == 60


class TestContextManager:
    def test_enter_exit(self):
        with EgdiGeologyConnector() as conn:
            assert isinstance(conn, EgdiGeologyConnector)


class TestHealthCheck:
    def test_healthy(self):
        connector = EgdiGeologyConnector()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<WFS_Capabilities>ms:hike_all_faults_layer ms:egdi_mines ms:egdi_surface_lithology_sandstone</WFS_Capabilities>"
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.health_check()
        assert result["faults"] is True

    def test_unhealthy(self):
        connector = EgdiGeologyConnector()
        with patch.object(connector._client, "get", side_effect=httpx.ConnectError("down")):
            result = connector.health_check()
        assert all(v is False for v in result.values())


class TestWfsQuery:
    def test_successful_query(self):
        connector = EgdiGeologyConnector()
        connector._inter_request_delay = 0.0
        resp = _mock_json_response(SAMPLE_FAULT_GEOJSON)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            features = connector._wfs_query("ms:hike_all_faults_layer", 44.15, 23.12, 8)
        assert len(features) == 2

    def test_empty_response(self):
        connector = EgdiGeologyConnector()
        resp = _mock_json_response(SAMPLE_EMPTY_GEOJSON)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            features = connector._wfs_query("ms:hike_all_faults_layer", 44.15, 23.12, 8)
        assert features == []

    def test_http_failure(self):
        connector = EgdiGeologyConnector()
        with patch.object(connector, "_request_with_retry", return_value=None):
            features = connector._wfs_query("ms:hike_all_faults_layer", 44.15, 23.12, 8)
        assert features == []

    def test_invalid_json(self):
        connector = EgdiGeologyConnector()
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.side_effect = json.JSONDecodeError("err", "", 0)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            features = connector._wfs_query("ms:layer", 44.0, 23.0, 5)
        assert features == []


class TestRetryLogic:
    def test_retries_on_500(self):
        connector = EgdiGeologyConnector()
        connector._base_delay = 0.0
        connector._max_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 500
        fail_resp.request = MagicMock()

        ok_resp = MagicMock(spec=httpx.Response)
        ok_resp.status_code = 200

        with patch.object(connector._client, "get", side_effect=[fail_resp, ok_resp]):
            resp = connector._request_with_retry("http://test", {})
        assert resp is not None
        assert resp.status_code == 200

    def test_no_retry_on_404(self):
        connector = EgdiGeologyConnector()
        connector._base_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 404

        with patch.object(connector._client, "get", return_value=fail_resp) as mock_get:
            resp = connector._request_with_retry("http://test", {})
            assert mock_get.call_count == 1
        assert resp is None

    def test_gives_up_after_max_retries(self):
        connector = EgdiGeologyConnector()
        connector._base_delay = 0.0
        connector._max_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 502
        fail_resp.request = MagicMock()

        with patch.object(connector._client, "get", return_value=fail_resp):
            resp = connector._request_with_retry("http://test", {})
        assert resp is None


class TestFetchAllOrchestration:
    def _make_connector(self) -> EgdiGeologyConnector:
        conn = EgdiGeologyConnector()
        conn._inter_request_delay = 0.0
        conn._base_delay = 0.0
        return conn

    def test_all_layers_respond(self):
        connector = self._make_connector()
        responses = {
            "faults": _mock_json_response(SAMPLE_FAULT_GEOJSON),
            "lithology": _mock_json_response(SAMPLE_LITHOLOGY_GEOJSON),
            "mines": _mock_json_response(SAMPLE_MINE_GEOJSON),
            "karst": _mock_json_response(SAMPLE_EMPTY_GEOJSON),
            "hydrogeology": _mock_json_response(SAMPLE_HYDROGEOLOGY_GEOJSON),
            "boreholes": _mock_json_response(SAMPLE_BOREHOLE_GEOJSON),
        }

        call_count = 0

        def mock_retry(url, params):
            nonlocal call_count
            call_count += 1
            layer = params.get("typeName", "")
            if "fault" in layer:
                return responses["faults"]
            if "lithology" in layer or "sandstone" in layer:
                return responses["lithology"]
            if "mine" in layer or "coal" in layer:
                return responses["mines"]
            if "karst" in layer:
                return responses["karst"]
            if "hydro" in layer or "groundwater" in layer:
                return responses["hydrogeology"]
            if "borehole" in layer:
                return responses["boreholes"]
            return _mock_json_response(SAMPLE_EMPTY_GEOJSON)

        with patch.object(connector, "_request_with_retry", side_effect=mock_retry):
            result = connector.fetch_all(44.15, 23.12, country_code="RO")

        assert result.faults is not None
        assert result.faults.fault_count_within_buffer == 2
        assert result.lithology is not None
        assert result.lithology.lithology_class is not None
        assert result.mines is not None
        assert result.karst is not None
        assert result.karst.in_karst_zone is False
        assert result.hydrogeology is not None
        assert result.boreholes is not None
        assert result.quality in ("high", "medium", "low")
        assert len(result.layers_queried) > 0
        assert call_count >= 6

    def test_all_layers_empty(self):
        connector = self._make_connector()
        empty_resp = _mock_json_response(SAMPLE_EMPTY_GEOJSON)

        with patch.object(connector, "_request_with_retry", return_value=empty_resp):
            result = connector.fetch_all(44.15, 23.12, country_code="RO")

        assert result.quality == "insufficient"
        assert len(result.layers_empty) > 0
        assert len(result.layers_with_data) == 0

    def test_partial_data(self):
        connector = self._make_connector()

        def mock_retry(url, params):
            layer = params.get("typeName", "")
            if "fault" in layer:
                return _mock_json_response(SAMPLE_FAULT_GEOJSON)
            return _mock_json_response(SAMPLE_EMPTY_GEOJSON)

        with patch.object(connector, "_request_with_retry", side_effect=mock_retry):
            result = connector.fetch_all(44.15, 23.12)

        assert result.faults is not None
        assert result.faults.fault_count_within_buffer == 2
        assert result.quality in ("low", "medium")

    def test_karst_coverage_gap_for_non_cz_country(self):
        connector = self._make_connector()
        empty_resp = _mock_json_response(SAMPLE_EMPTY_GEOJSON)

        with patch.object(connector, "_request_with_retry", return_value=empty_resp):
            result = connector.fetch_all(44.15, 23.12, country_code="RO")

        assert result.karst is not None
        assert result.karst.coverage_available is False

    def test_fetch_error_does_not_crash(self):
        """An exception in one domain should not prevent others."""
        connector = self._make_connector()

        call_count = 0

        def mock_retry(url, params):
            nonlocal call_count
            call_count += 1
            layer = params.get("typeName", "")
            if "fault" in layer:
                raise httpx.ConnectError("network error")
            return _mock_json_response(SAMPLE_EMPTY_GEOJSON)

        with patch.object(connector, "_request_with_retry", side_effect=mock_retry):
            result = connector.fetch_all(44.15, 23.12)

        # Should still have results for other layers
        assert result.faults is None  # fetch_faults failed
        assert result.lithology is not None  # others continued


class TestEdgeCases:
    def test_multipolygon_mining_area(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[23.0, 44.0], [23.3, 44.0], [23.3, 44.3], [23.0, 44.3], [23.0, 44.0]]],
                    ],
                },
                "properties": {"status": "abandoned", "commodity": "lignite"},
            }],
        }
        features = parse_geojson_features(geojson)
        result = build_mining_assessment(features, 44.15, 23.15, ["layer"])
        assert result.mine_count_within_buffer == 1
        assert result.in_mining_area is True

    def test_feature_with_no_coordinates(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": []},
                "properties": {"name": "empty"},
            }],
        }
        features = parse_geojson_features(geojson)
        dist, nearest = nearest_feature_distance(features, 44.0, 23.0)
        assert dist is None

    def test_zero_radius_bbox(self):
        bbox = build_wfs_bbox(44.0, 23.0, 0)
        parts = bbox.split(",")
        assert float(parts[0]) == float(parts[2])  # lat_min == lat_max

    def test_extreme_coordinates(self):
        assert validate_coordinates_in_egdi_domain(0.0, 0.0) is False
        assert validate_coordinates_in_egdi_domain(90.0, 0.0) is False
        assert validate_coordinates_in_egdi_domain(50.0, 10.0) is True
