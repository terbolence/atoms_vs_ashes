# man_hours: 2.0
"""Tests for S-10 Copernicus EMS connector — parsing and classification logic.

No network calls. Tests pure logic by calling static/class methods with fixture data.
"""

from __future__ import annotations

import json

import pytest

from atoms_vs_ashes.connectors.copernicus_ems.models import (
    BatchResult,
    FlashFloodAssessment,
    FloodFootprint,
    FootprintSummary,
    RapidActivation,
    RrmActivation,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.copernicus_ems.parsers import (
    classify_susceptibility,
    determine_quality,
    parse_rapid_activation,
    parse_rrm_activation,
    validate_activation_date,
    validate_footprint_area,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_RRM_RESPONSE = {
    "code": "EMSN193",
    "name": "Flood risks in Tazlau River basin, Romania",
    "activator": "Romanian IGSU",
    "reason": "Flash flood risk assessment for Tazlau River basin",
    "actDrmPhase": "Preparedness",
    "activationTime": "2023-06-15T08:00:00",
    "countries": ["Romania"],
    "continent": "Europe",
    "category": "Flood",
    "subCategory": "Flash flood",
    "centroid": "POINT (26.45 46.55)",
    "sensitive": False,
    "closed": True,
    "products": [
        {
            "productName": "P04_FloodDelineation",
            "productAcronym": "P04",
            "analysisName": "Flood extent modelling",
            "briefDescription": "Modelled flash flood extent for 100yr return period",
            "drmPhase": "Preparedness",
            "feasible": True,
            "statusCode": "finished",
            "mapsDownload": "https://riskandrecovery.emergency.copernicus.eu/media/activations/EMSN193/geodata.zip",
        }
    ],
}

SAMPLE_RAPID_RESPONSE = {
    "code": "EMSR680",
    "countries": [{"short_name": "Romania"}],
    "category": {"slug": "flood", "name": "Flood"},
    "name": "Flood in Galati County, Romania",
    "centroid": "POINT (27.95 45.43)",
    "activationTime": "2024-09-14T10:30:00",
    "lastUpdate": "2024-09-20T15:00:00",
    "drmPhase": "response",
    "closed": True,
    "n_aois": 4,
    "n_products": 3,
}


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestParseRrmActivation:
    def test_parses_valid_activation(self) -> None:
        act = parse_rrm_activation(SAMPLE_RRM_RESPONSE)
        assert act is not None
        assert act.code == "EMSN193"
        assert act.name == "Flood risks in Tazlau River basin, Romania"
        assert act.category == "Flood"
        assert act.sub_category == "Flash flood"
        assert act.drm_phase == "Preparedness"
        assert "RO" in act.countries
        assert act.centroid_lon == pytest.approx(26.45)
        assert act.centroid_lat == pytest.approx(46.55)
        assert act.closed is True
        assert len(act.download_urls) == 1

    def test_missing_code_returns_none(self) -> None:
        data = {"name": "No code"}
        assert parse_rrm_activation(data) is None

    def test_empty_products(self) -> None:
        data = {**SAMPLE_RRM_RESPONSE, "products": []}
        act = parse_rrm_activation(data)
        assert act is not None
        assert act.download_urls == []

    def test_missing_centroid(self) -> None:
        data = {**SAMPLE_RRM_RESPONSE, "centroid": None}
        act = parse_rrm_activation(data)
        assert act is not None
        assert act.centroid_lon is None
        assert act.centroid_lat is None

    def test_to_dict(self) -> None:
        act = parse_rrm_activation(SAMPLE_RRM_RESPONSE)
        d = act.to_dict()
        assert d["code"] == "EMSN193"
        assert d["category"] == "Flood"


class TestParseRapidActivation:
    def test_parses_valid_activation(self) -> None:
        act = parse_rapid_activation(SAMPLE_RAPID_RESPONSE)
        assert act is not None
        assert act.code == "EMSR680"
        assert act.category == "flood"
        assert "RO" in act.countries
        assert act.centroid_lon == pytest.approx(27.95)
        assert act.centroid_lat == pytest.approx(45.43)
        assert act.n_aois == 4
        assert act.n_products == 3

    def test_missing_code_returns_none(self) -> None:
        data = {"name": "No code"}
        assert parse_rapid_activation(data) is None

    def test_category_as_string(self) -> None:
        data = {**SAMPLE_RAPID_RESPONSE, "category": "flood"}
        act = parse_rapid_activation(data)
        assert act is not None
        assert act.category == "flood"

    def test_to_dict(self) -> None:
        act = parse_rapid_activation(SAMPLE_RAPID_RESPONSE)
        d = act.to_dict()
        assert d["code"] == "EMSR680"


class TestClassifySusceptibility:
    def test_high_intersection(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.5, distance_km=0.0, n_events=1,
        )
        assert result == "high"

    def test_medium_within_10km(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=5.0, n_events=1,
        )
        assert result == "medium"

    def test_low_within_50km(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=30.0, n_events=1,
        )
        assert result == "low"

    def test_negligible_within_100km(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=60.0, n_events=1,
        )
        assert result == "negligible"

    def test_none_beyond_100km(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=120.0, n_events=1,
        )
        assert result is None

    def test_none_no_events(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=5.0, n_events=0,
        )
        assert result is None

    def test_none_no_distance(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=None, n_events=3,
        )
        assert result is None

    def test_custom_thresholds(self) -> None:
        result = classify_susceptibility(
            intersection_area_km2=0.0, distance_km=15.0, n_events=1,
            medium_distance_km=20.0,
        )
        assert result == "medium"


class TestDetermineQuality:
    def test_insufficient_no_events(self) -> None:
        assert determine_quality(0, None) == "insufficient"

    def test_high_many_events(self) -> None:
        assert determine_quality(5, "high") == "high"

    def test_medium_few_events(self) -> None:
        assert determine_quality(2, "medium") == "medium"

    def test_medium_single_event(self) -> None:
        assert determine_quality(1, "low") == "medium"


class TestValidation:
    def test_valid_footprint_area(self) -> None:
        assert validate_footprint_area(100.0) is True
        assert validate_footprint_area(0.0) is False
        assert validate_footprint_area(60000.0) is False

    def test_valid_activation_date(self) -> None:
        assert validate_activation_date("2023-06-15T08:00:00") is True
        assert validate_activation_date("2010-01-01T00:00:00") is False
        assert validate_activation_date(None) is False
        assert validate_activation_date("not-a-date") is False


class TestResultStructure:
    def test_flash_flood_assessment_to_dict(self) -> None:
        result = FlashFloodAssessment(
            lat=44.43, lon=26.10,
            susceptibility="medium",
            distance_to_nearest_km=8.5,
            n_events_within_buffer=3,
            nearest_activation_code="EMSN193",
            quality="medium",
        )
        d = result.to_dict()
        assert d["lat"] == 44.43
        assert d["susceptibility"] == "medium"
        assert d["distance_to_nearest_km"] == 8.5
        assert d["n_events_within_buffer"] == 3

    def test_batch_result_summary_line(self) -> None:
        batch = BatchResult(
            run_id="test-001",
            total_sites=100,
            succeeded=60,
            failed=2,
            skipped_cached=5,
            no_data=33,
            elapsed_s=12.0,
        )
        line = batch.summary_line()
        assert "100 sites" in line
        assert "60 ok" in line
        assert "33 no-data" in line

    def test_flood_footprint_to_dict(self) -> None:
        fp = FloodFootprint(
            activation_code="EMSN193",
            activation_type="rrm",
            activation_date="2023-06-15",
            category="flood",
            countries=["RO"],
            area_km2=50.0,
        )
        d = fp.to_dict()
        assert d["activation_code"] == "EMSN193"
        assert d["area_km2"] == 50.0

    def test_footprint_summary_to_dict(self) -> None:
        fs = FootprintSummary(
            activation_code="EMSR680",
            distance_km=12.5,
            category="flood",
        )
        d = fs.to_dict()
        assert d["distance_km"] == 12.5


class TestEdgeCases:
    def test_empty_countries_list(self) -> None:
        data = {**SAMPLE_RRM_RESPONSE, "countries": []}
        act = parse_rrm_activation(data)
        assert act is not None
        assert act.countries == []

    def test_unknown_country_name(self) -> None:
        data = {**SAMPLE_RRM_RESPONSE, "countries": ["Atlantis"]}
        act = parse_rrm_activation(data)
        assert act is not None
        assert act.countries == []

    def test_rapid_country_dict_format(self) -> None:
        data = {
            **SAMPLE_RAPID_RESPONSE,
            "countries": [{"short_name": "Turkey", "name": "Türkiye"}],
        }
        act = parse_rapid_activation(data)
        assert act is not None
        assert "TR" in act.countries

    def test_wkt_point_various_formats(self) -> None:
        from atoms_vs_ashes.connectors.copernicus_ems.parsers import _parse_wkt_point

        assert _parse_wkt_point("POINT (26.45 46.55)") == (pytest.approx(26.45), pytest.approx(46.55))
        assert _parse_wkt_point("POINT(26.45 46.55)") == (pytest.approx(26.45), pytest.approx(46.55))
        assert _parse_wkt_point("") == (None, None)
        assert _parse_wkt_point(None) == (None, None)
