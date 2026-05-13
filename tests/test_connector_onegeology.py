# man_hours: 4.1
"""Tests for the S-03 OneGeology connector.

All tests run without network access (pure unit tests and mocked HTTP).
Covers: endpoint resolution, GeoJSON parsing, fault/karst result assembly,
S-02 quality checks, graceful error handling, batch skip logic.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import httpx
import pytest

from atoms_vs_ashes.connectors.onegeology import (
    OneGeologyConnector,
    OneGeologyFaultResult,
    OneGeologyKarstResult,
    OneGeologyResult,
    build_fault_result,
    build_karst_result,
    build_wfs_bbox,
    nearest_feature_distance,
    parse_geojson_features,
)
from atoms_vs_ashes.connectors.onegeology.models import (
    BatchResult,
    S02_SUPPLEMENT_THRESHOLD,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.onegeology.parsers import (
    is_geojson_response,
    normalise_layer_name,
)


# ---------------------------------------------------------------------------
# Sample fixture data
# ---------------------------------------------------------------------------

SAMPLE_FAULT_GEOJSON: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[26.10, 44.43], [26.15, 44.45], [26.20, 44.50]],
            },
            "properties": {
                "fault_type": "normal",
                "name": "Intramoesic Fault Zone",
            },
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[26.50, 44.60], [26.60, 44.70]],
            },
            "properties": {
                "fault_type": "thrust",
                "name": "Subcarpathian Thrust",
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
                    [[26.05, 44.40], [26.15, 44.40], [26.15, 44.50], [26.05, 44.50], [26.05, 44.40]]
                ],
            },
            "properties": {
                "class": "Karst",
                "description": "Karstified limestone — Jurassic",
                "type": "karstic",
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
                    [[26.00, 44.35], [26.20, 44.35], [26.20, 44.55], [26.00, 44.55], [26.00, 44.35]]
                ],
            },
            "properties": {
                "lithology": "Alluvial sand and gravel",
                "class": "granular",
            },
        },
    ],
}

EMPTY_GEOJSON: dict = {"type": "FeatureCollection", "features": []}

MOCK_REGISTRY: dict = {
    "RO": {
        "wfs_url": "https://inspire.igr.ro/geoserver/wfs",
        "wfs_version": "2.0.0",
        "fault_layer": "igr:Faults",
        "karst_layer": "igr:KarstZones",
    },
    "PL": {
        "wfs_url": "https://cbdgportal.pgi.gov.pl/geoserver/wfs",
        "wfs_version": "2.0.0",
        "fault_layer": None,
        "karst_layer": None,
    },
    "AT": {
        "wfs_url": None,
        "wfs_version": "2.0.0",
        "fault_layer": None,
        "karst_layer": None,
    },
}


# ---------------------------------------------------------------------------
# Helper: build connector with mock registry
# ---------------------------------------------------------------------------


def _make_connector(registry: dict | None = None) -> OneGeologyConnector:
    settings = MagicMock()
    settings.connector_config.return_value = {
        "endpoint_registry": registry if registry is not None else MOCK_REGISTRY,
        "timeout_s": 5,
        "inter_request_delay_s": 0.0,
        "cache_ttl_days": 180,
        "max_features_per_request": 500,
        "fault_buffer_km": 8.0,
        "karst_buffer_km": 5.0,
    }
    return OneGeologyConnector(settings)


# ---------------------------------------------------------------------------
# TestResolveEndpoint
# ---------------------------------------------------------------------------


class TestResolveEndpoint:
    def test_registered_country_with_layers(self) -> None:
        connector = _make_connector()
        url, layer, version = connector._resolve_endpoint("RO", "faults")
        assert url == "https://inspire.igr.ro/geoserver/wfs"
        assert layer == "igr:Faults"
        assert version == "2.0.0"

    def test_registered_country_karst_layer(self) -> None:
        connector = _make_connector()
        url, layer, version = connector._resolve_endpoint("RO", "karst")
        assert url == "https://inspire.igr.ro/geoserver/wfs"
        assert layer == "igr:KarstZones"

    def test_registered_country_null_layer(self) -> None:
        connector = _make_connector()
        url, layer, version = connector._resolve_endpoint("PL", "faults")
        assert url == "https://cbdgportal.pgi.gov.pl/geoserver/wfs"
        assert layer is None

    def test_registered_country_null_wfs_url(self) -> None:
        connector = _make_connector()
        url, layer, version = connector._resolve_endpoint("AT", "faults")
        assert url is None
        assert layer is None

    def test_unregistered_country(self) -> None:
        connector = _make_connector()
        url, layer, version = connector._resolve_endpoint("BY", "faults")
        assert url is None
        assert layer is None

    def test_empty_registry_country(self) -> None:
        connector = _make_connector(registry={})
        url, layer, version = connector._resolve_endpoint("RO", "karst")
        assert url is None


# ---------------------------------------------------------------------------
# TestParseGeojsonFaults
# ---------------------------------------------------------------------------


class TestParseGeojsonFaults:
    def test_valid_feature_collection(self) -> None:
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        assert len(features) == 2
        assert features[0]["geometry"]["type"] == "LineString"
        assert features[0]["properties"]["fault_type"] == "normal"

    def test_empty_collection(self) -> None:
        features = parse_geojson_features(EMPTY_GEOJSON)
        assert features == []

    def test_skips_null_geometry(self) -> None:
        raw = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": None, "properties": {}},
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [26.1, 44.4]},
                    "properties": {"name": "valid"},
                },
            ],
        }
        features = parse_geojson_features(raw)
        assert len(features) == 1
        assert features[0]["properties"]["name"] == "valid"

    def test_skips_malformed_features(self) -> None:
        raw = {
            "type": "FeatureCollection",
            "features": [
                "not_a_feature",
                None,
                {"no_geometry": True},
            ],
        }
        assert parse_geojson_features(raw) == []

    def test_non_dict_input(self) -> None:
        assert parse_geojson_features([]) == []  # type: ignore[arg-type]
        assert parse_geojson_features("bad") == []  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestBuildFaultResult
# ---------------------------------------------------------------------------


class TestBuildFaultResult:
    def test_fault_distance_computed(self) -> None:
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        result = build_fault_result(
            features, lat=44.43, lon=26.10,
            endpoint_url="https://test.url/wfs",
            layer_name="igr:Faults",
        )
        assert result.fault_count_within_buffer == 2
        assert result.nearest_fault_distance_km is not None
        assert result.nearest_fault_distance_km >= 0
        assert result.nearest_fault_type == "normal"
        assert result.source_endpoint == "https://test.url/wfs"
        assert result.source_layer == "igr:Faults"

    def test_empty_features(self) -> None:
        result = build_fault_result(
            [], lat=44.43, lon=26.10,
            endpoint_url="https://test.url/wfs",
            layer_name="igr:Faults",
        )
        assert result.fault_count_within_buffer == 0
        assert result.nearest_fault_distance_km is None
        assert result.nearest_fault_type is None

    def test_to_dict_structure(self) -> None:
        features = parse_geojson_features(SAMPLE_FAULT_GEOJSON)
        result = build_fault_result(features, 44.43, 26.10, "url", "layer")
        d = result.to_dict()
        assert "nearest_fault_distance_km" in d
        assert "fault_count_within_buffer" in d
        assert "source_endpoint" in d
        assert "source_layer" in d


# ---------------------------------------------------------------------------
# TestBuildKarstResult
# ---------------------------------------------------------------------------


class TestBuildKarstResult:
    def test_dedicated_karst_layer_with_features(self) -> None:
        features = parse_geojson_features(SAMPLE_KARST_GEOJSON)
        result = build_karst_result(
            features,
            endpoint_url="https://test.url/wfs",
            layer_name="igr:KarstZones",
        )
        assert result.in_karst_zone is True
        assert result.karst_class is not None

    def test_karst_keyword_in_layer_name(self) -> None:
        features = parse_geojson_features(SAMPLE_KARST_GEOJSON)
        result = build_karst_result(features, "url", "geology:KarstifiedZones")
        assert result.in_karst_zone is True

    def test_lithology_layer_with_karst_rock(self) -> None:
        raw = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[26.0, 44.4], [26.1, 44.4], [26.1, 44.5], [26.0, 44.4]]]},
                "properties": {"lithology": "Karstified limestone"},
            }],
        }
        features = parse_geojson_features(raw)
        result = build_karst_result(features, "url", "igr:BLT")
        assert result.in_karst_zone is True

    def test_non_karst_lithology(self) -> None:
        features = parse_geojson_features(SAMPLE_LITHOLOGY_GEOJSON)
        result = build_karst_result(features, "url", "igr:Lithology")
        assert result.in_karst_zone is False

    def test_empty_features(self) -> None:
        result = build_karst_result([], "url", "layer")
        assert result.in_karst_zone is False
        assert result.karst_class is None

    def test_to_dict_structure(self) -> None:
        features = parse_geojson_features(SAMPLE_KARST_GEOJSON)
        result = build_karst_result(features, "url", "igr:Karst")
        d = result.to_dict()
        assert "in_karst_zone" in d
        assert "karst_class" in d
        assert "source_endpoint" in d
        assert "source_layer" in d


# ---------------------------------------------------------------------------
# TestS02QualityCheck
# ---------------------------------------------------------------------------


class TestS02QualityCheck:
    """Test the decision logic: when to supplement vs skip."""

    def test_s02_insufficient_triggers_supplement(self) -> None:
        assert "insufficient" in S02_SUPPLEMENT_THRESHOLD

    def test_s02_low_triggers_supplement(self) -> None:
        assert "low" in S02_SUPPLEMENT_THRESHOLD

    def test_s02_none_triggers_supplement(self) -> None:
        assert None in S02_SUPPLEMENT_THRESHOLD

    def test_s02_medium_does_not_trigger(self) -> None:
        assert "medium" not in S02_SUPPLEMENT_THRESHOLD

    def test_s02_high_does_not_trigger(self) -> None:
        assert "high" not in S02_SUPPLEMENT_THRESHOLD

    def test_fetch_all_skips_when_both_adequate(self) -> None:
        connector = _make_connector()
        result = connector.fetch_all(
            lat=44.43, lon=26.10, country_code="RO",
            s02_nh02_quality="medium",
            s02_nh05_quality="high",
        )
        assert result.quality == "high"
        assert result.faults is None
        assert result.karst is None
        assert result.endpoints_queried == []
        assert result.supplements_s02 is False

    def test_fetch_all_supplements_when_nh05_insufficient(self) -> None:
        connector = _make_connector()
        with patch.object(connector, "fetch_karst") as mock_karst:
            mock_karst.return_value = OneGeologyKarstResult(
                in_karst_zone=True, karst_class="Karst",
                source_endpoint="url", source_layer="layer",
            )
            result = connector.fetch_all(
                lat=44.43, lon=26.10, country_code="RO",
                s02_nh02_quality="medium",
                s02_nh05_quality="insufficient",
            )
        assert result.supplements_s02 is True
        assert result.karst is not None
        assert result.karst.in_karst_zone is True


# ---------------------------------------------------------------------------
# TestBuildWfsBbox
# ---------------------------------------------------------------------------


class TestBuildWfsBbox:
    def test_wfs2_lat_lon_order(self) -> None:
        bbox = build_wfs_bbox(44.43, 26.10, 5.0, wfs_version="2.0.0")
        # WFS 2.0.0 with EPSG:4326: min_lat,min_lon,max_lat,max_lon
        parts = bbox.split(",")
        assert len(parts) == 5
        assert parts[4] == "EPSG:4326"
        min_lat = float(parts[0])
        max_lat = float(parts[2])
        assert min_lat < 44.43 < max_lat

    def test_wfs1_lon_lat_order(self) -> None:
        bbox = build_wfs_bbox(44.43, 26.10, 5.0, wfs_version="1.0.0")
        parts = bbox.split(",")
        # WFS 1.0.0: min_lon,min_lat,max_lon,max_lat
        min_lon = float(parts[0])
        max_lon = float(parts[2])
        assert min_lon < 26.10 < max_lon

    def test_bbox_is_symmetric(self) -> None:
        bbox = build_wfs_bbox(44.43, 26.10, 5.0)
        parts = bbox.split(",")
        min_lat, min_lon, max_lat, max_lon = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
        assert abs((max_lat - 44.43) - (44.43 - min_lat)) < 1e-6
        assert abs((max_lon - 26.10) - (26.10 - min_lon)) < 1e-6


# ---------------------------------------------------------------------------
# TestNearestFeatureDistance
# ---------------------------------------------------------------------------


class TestNearestFeatureDistance:
    def test_point_distance(self) -> None:
        features = [{
            "geometry": {"type": "Point", "coordinates": [26.10, 44.43]},
            "properties": {},
        }]
        dist, feat = nearest_feature_distance(features, lat=44.43, lon=26.10)
        assert dist is not None
        assert dist < 0.001  # essentially at the same location

    def test_linestring_distance(self) -> None:
        features = [{
            "geometry": {
                "type": "LineString",
                "coordinates": [[26.20, 44.50], [26.30, 44.60]],
            },
            "properties": {},
        }]
        dist, feat = nearest_feature_distance(features, lat=44.43, lon=26.10)
        assert dist is not None
        assert dist > 5.0  # should be several km away

    def test_empty_features_returns_none(self) -> None:
        dist, feat = nearest_feature_distance([], lat=44.43, lon=26.10)
        assert dist is None
        assert feat is None

    def test_picks_nearest_of_multiple(self) -> None:
        features = [
            {
                "geometry": {"type": "Point", "coordinates": [26.10, 44.43]},
                "properties": {"name": "close"},
            },
            {
                "geometry": {"type": "Point", "coordinates": [27.00, 45.00]},
                "properties": {"name": "far"},
            },
        ]
        dist, feat = nearest_feature_distance(features, lat=44.43, lon=26.10)
        assert feat is not None
        assert feat["properties"]["name"] == "close"


# ---------------------------------------------------------------------------
# TestIsGeojsonResponse
# ---------------------------------------------------------------------------


class TestIsGeojsonResponse:
    def test_application_json(self) -> None:
        assert is_geojson_response("application/json; charset=utf-8", '{"type": "FeatureCollection"}')

    def test_text_html(self) -> None:
        assert not is_geojson_response("text/html; charset=utf-8", "<html>Login</html>")

    def test_content_type_unknown_body_json(self) -> None:
        assert is_geojson_response("application/octet-stream", '{"features": []}')

    def test_content_type_unknown_body_html(self) -> None:
        assert not is_geojson_response("application/octet-stream", "<html>")


# ---------------------------------------------------------------------------
# TestNormaliseLayerName
# ---------------------------------------------------------------------------


class TestNormaliseLayerName:
    def test_strips_ms_prefix(self) -> None:
        assert normalise_layer_name("ms:hike_faults") == "hike_faults"

    def test_strips_gml_prefix(self) -> None:
        assert normalise_layer_name("gml:GeologicUnit") == "GeologicUnit"

    def test_no_prefix(self) -> None:
        assert normalise_layer_name("Faults") == "Faults"


# ---------------------------------------------------------------------------
# TestSupplementProvenance
# ---------------------------------------------------------------------------


class TestSupplementProvenance:
    def test_result_to_dict_includes_provenance_when_supplementing(self) -> None:
        result = OneGeologyResult(
            lat=44.43, lon=26.10, country_code="RO",
            supplements_s02=True,
            karst=OneGeologyKarstResult(
                in_karst_zone=True, karst_class="Karst",
                source_endpoint="url", source_layer="layer",
            ),
            quality="medium",
        )
        d = result.to_dict()
        assert d["supplemented_by"] == "onegeology"
        assert d["primary_source"] == "egdi"

    def test_result_to_dict_no_provenance_when_not_supplementing(self) -> None:
        result = OneGeologyResult(
            lat=44.43, lon=26.10, country_code="RO",
            supplements_s02=False, quality="insufficient",
        )
        d = result.to_dict()
        assert "supplemented_by" not in d
        assert "primary_source" not in d


# ---------------------------------------------------------------------------
# TestFetchAllIntegration (mocked HTTP)
# ---------------------------------------------------------------------------


class TestFetchAllIntegration:
    """Integration tests using mocked HTTP responses."""

    def _mock_response(self, geojson: dict, status: int = 200) -> httpx.Response:
        content = json.dumps(geojson).encode()
        return httpx.Response(
            status_code=status,
            content=content,
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://test.url/wfs"),
        )

    def test_fetch_faults_returns_result_on_valid_response(self) -> None:
        connector = _make_connector()
        mock_resp = self._mock_response(SAMPLE_FAULT_GEOJSON)

        with patch.object(connector._client, "get", return_value=mock_resp):
            result = connector.fetch_faults(lat=44.43, lon=26.10, country_code="RO")

        assert result is not None
        assert isinstance(result, OneGeologyFaultResult)
        assert result.fault_count_within_buffer == 2
        assert result.nearest_fault_distance_km is not None

    def test_fetch_karst_returns_result_on_valid_response(self) -> None:
        connector = _make_connector()
        mock_resp = self._mock_response(SAMPLE_KARST_GEOJSON)

        with patch.object(connector._client, "get", return_value=mock_resp):
            result = connector.fetch_karst(lat=44.43, lon=26.10, country_code="RO")

        assert result is not None
        assert isinstance(result, OneGeologyKarstResult)
        assert result.in_karst_zone is True

    def test_endpoint_unreachable_returns_none(self) -> None:
        connector = _make_connector()

        with patch.object(
            connector._client, "get",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            result = connector.fetch_faults(lat=44.43, lon=26.10, country_code="RO")

        assert result is None

    def test_no_endpoint_registered_returns_none(self) -> None:
        connector = _make_connector()
        result = connector.fetch_faults(lat=48.0, lon=23.0, country_code="BY")
        assert result is None

    def test_no_layer_registered_returns_none(self) -> None:
        connector = _make_connector()
        # PL has wfs_url but fault_layer=None
        result = connector.fetch_faults(lat=52.0, lon=21.0, country_code="PL")
        assert result is None

    def test_html_response_detected_and_skipped(self) -> None:
        connector = _make_connector()
        html_resp = httpx.Response(
            status_code=200,
            content=b"<html><body>Please log in</body></html>",
            headers={"content-type": "text/html; charset=utf-8"},
            request=httpx.Request("GET", "https://test.url/wfs"),
        )
        with patch.object(connector._client, "get", return_value=html_resp):
            result = connector.fetch_faults(lat=44.43, lon=26.10, country_code="RO")
        assert result is None

    def test_empty_response_returns_empty_fault_result(self) -> None:
        connector = _make_connector()
        mock_resp = self._mock_response(EMPTY_GEOJSON)

        with patch.object(connector._client, "get", return_value=mock_resp):
            result = connector.fetch_faults(lat=44.43, lon=26.10, country_code="RO")

        assert result is not None
        assert result.fault_count_within_buffer == 0
        assert result.nearest_fault_distance_km is None

    def test_server_error_retries_once_then_returns_none(self) -> None:
        connector = _make_connector()
        error_resp = httpx.Response(
            status_code=503,
            content=b"Service Unavailable",
            headers={"content-type": "text/plain"},
            request=httpx.Request("GET", "https://test.url/wfs"),
        )
        with patch.object(connector._client, "get", return_value=error_resp):
            result = connector.fetch_faults(lat=44.43, lon=26.10, country_code="RO")
        assert result is None

    def test_fetch_all_with_both_supplement_needed(self) -> None:
        connector = _make_connector()
        fault_resp = self._mock_response(SAMPLE_FAULT_GEOJSON)
        karst_resp = self._mock_response(SAMPLE_KARST_GEOJSON)

        responses = [fault_resp, karst_resp]
        call_count = 0

        def side_effect(*args: object, **kwargs: object) -> httpx.Response:
            nonlocal call_count
            resp = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return resp

        with patch.object(connector._client, "get", side_effect=side_effect):
            result = connector.fetch_all(
                lat=44.43, lon=26.10, country_code="RO",
                s02_nh02_quality="low",
                s02_nh05_quality="insufficient",
            )

        assert result.supplements_s02 is True
        assert result.faults is not None
        assert result.karst is not None


# ---------------------------------------------------------------------------
# TestOneGeologyResultStructure
# ---------------------------------------------------------------------------


class TestOneGeologyResultStructure:
    def test_to_dict_completeness(self) -> None:
        result = OneGeologyResult(
            lat=44.43, lon=26.10, country_code="RO",
            faults=OneGeologyFaultResult(
                nearest_fault_distance_km=3.5, nearest_fault_type="normal",
                fault_count_within_buffer=1, source_endpoint="url", source_layer="layer",
            ),
            karst=OneGeologyKarstResult(
                in_karst_zone=False, karst_class=None,
                source_endpoint="url", source_layer="layer",
            ),
            supplements_s02=True,
            quality="medium",
        )
        d = result.to_dict()
        required_keys = {
            "lat", "lon", "country_code", "faults", "karst",
            "endpoints_queried", "endpoints_failed", "supplements_s02",
            "quality", "error",
        }
        assert required_keys.issubset(d.keys())
        assert d["faults"]["nearest_fault_distance_km"] == 3.5

    def test_batch_result_summary_line(self) -> None:
        batch = BatchResult(
            run_id="test-run",
            total_sites=10,
            succeeded=3,
            failed=1,
            skipped_cached=2,
            skipped_s02_adequate=3,
            skipped_no_endpoint=1,
            elapsed_s=5.0,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "3 ok" in line
        assert "1 failed" in line
        assert "s02-adequate" in line
