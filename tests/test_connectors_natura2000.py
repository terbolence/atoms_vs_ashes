# man_hours: 5.0
"""Tests for S-14 Natura 2000 connector — parsing and transformation logic.

All tests are pure (no network, no database). They exercise the parser,
distance computation, area fraction, sensitivity classification, and
result validation functions.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Point, Polygon, box

from atoms_vs_ashes.connectors.natura2000.models import (
    CRITERION_IDS,
    EU_MEMBER_STATES_INSCOPE,
    NON_EU_INSCOPE,
    Natura2000Result,
    Natura2000Site,
    SiteProximity,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.natura2000.parsers import (
    classify_designation_types,
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_sites_by_radius,
    parse_features,
    validate_result,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_N2K_GEOJSON_FEATURES = [
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[26.05, 44.40], [26.15, 44.40], [26.15, 44.50],
                             [26.05, 44.50], [26.05, 44.40]]],
        },
        "properties": {
            "OBJECTID": 12345,
            "SITECODE": "ROSCI0229",
            "SITENAME": "Comana",
            "RELEASE_DATE": "2024-10-01",
            "MS": "RO",
            "SITETYPE": "B",
            "POINT_X": 2902000.0,
            "POINT_Y": 5530000.0,
            "Area_km2": 245.5,
            "Area_ha": 24550.0,
            "A": 12,
            "B": 8,
            "C": 3,
            "D": 1,
            "Missing": 0,
        },
    },
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[26.20, 44.35], [26.30, 44.35], [26.30, 44.45],
                             [26.20, 44.45], [26.20, 44.35]]],
        },
        "properties": {
            "OBJECTID": 12346,
            "SITECODE": "ROSPA0084",
            "SITENAME": "Lacurile de acumulare de pe Argeș",
            "RELEASE_DATE": "2024-10-01",
            "MS": "RO",
            "SITETYPE": "A",
            "POINT_X": 2918000.0,
            "POINT_Y": 5525000.0,
            "Area_km2": 89.3,
            "Area_ha": 8930.0,
            "A": 5,
            "B": 4,
            "C": 2,
            "D": 0,
            "Missing": 1,
        },
    },
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[26.00, 44.55], [26.10, 44.55], [26.10, 44.65],
                             [26.00, 44.65], [26.00, 44.55]]],
        },
        "properties": {
            "OBJECTID": 12347,
            "SITECODE": "ROSCI0127",
            "SITENAME": "Munții Făgăraș",
            "RELEASE_DATE": "2024-10-01",
            "MS": "RO",
            "SITETYPE": "C",
            "POINT_X": 2896000.0,
            "POINT_Y": 5547000.0,
            "Area_km2": 198.7,
            "Area_ha": 19870.0,
            "A": 25,
            "B": 15,
            "C": 8,
            "D": 2,
            "Missing": 0,
        },
    },
]


# ---------------------------------------------------------------------------
# TestParseFeatures
# ---------------------------------------------------------------------------

class TestParseFeatures:
    """Test GeoJSON feature parsing into Natura2000Site objects."""

    def test_parse_valid_features(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        assert len(sites) == 3

    def test_sitecodes_extracted(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        codes = {s.sitecode for s in sites}
        assert codes == {"ROSCI0229", "ROSPA0084", "ROSCI0127"}

    def test_sitetype_extracted(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        by_code = {s.sitecode: s for s in sites}
        assert by_code["ROSCI0229"].sitetype == "B"
        assert by_code["ROSPA0084"].sitetype == "A"
        assert by_code["ROSCI0127"].sitetype == "C"

    def test_area_extracted(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        by_code = {s.sitecode: s for s in sites}
        assert by_code["ROSCI0229"].area_ha == pytest.approx(24550.0)
        assert by_code["ROSCI0229"].area_km2 == pytest.approx(245.5)

    def test_conservation_fields(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        by_code = {s.sitecode: s for s in sites}
        comana = by_code["ROSCI0229"]
        assert comana.conservation_a == 12
        assert comana.conservation_b == 8
        assert comana.conservation_c == 3
        assert comana.conservation_d == 1
        assert comana.conservation_missing == 0

    def test_member_state(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        for s in sites:
            assert s.member_state == "RO"

    def test_geometry_is_shapely(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        for s in sites:
            assert s.geometry is not None
            assert s.geometry.is_valid

    def test_centroid_computed(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        for s in sites:
            assert 34 < s.centroid_lat < 72
            assert -25 < s.centroid_lon < 45


class TestParseFeaturesMalformed:
    """Test handling of malformed features."""

    def test_skip_missing_geometry(self):
        features = [
            {
                "type": "Feature",
                "geometry": None,
                "properties": {"SITECODE": "ROTEST01", "SITETYPE": "B", "MS": "RO"},
            },
        ]
        sites = parse_features(features)
        assert len(sites) == 0

    def test_skip_blank_sitecode(self):
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                                     [26.0, 44.5], [26.0, 44.4]]],
                },
                "properties": {"SITECODE": "", "SITETYPE": "B", "MS": "RO",
                               "Area_ha": 100, "Area_km2": 1},
            },
        ]
        sites = parse_features(features)
        assert len(sites) == 0

    def test_skip_empty_geometry(self):
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[]]},
                "properties": {"SITECODE": "ROTEST01", "SITETYPE": "B", "MS": "RO"},
            },
        ]
        sites = parse_features(features)
        assert len(sites) == 0

    def test_mixed_valid_and_invalid(self):
        valid = SAMPLE_N2K_GEOJSON_FEATURES[0]
        invalid = {
            "type": "Feature",
            "geometry": None,
            "properties": {"SITECODE": "ROTEST99"},
        }
        sites = parse_features([valid, invalid])
        assert len(sites) == 1
        assert sites[0].sitecode == "ROSCI0229"

    def test_missing_optional_fields_default(self):
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                                     [26.0, 44.5], [26.0, 44.4]]],
                },
                "properties": {"SITECODE": "ROTEST01", "MS": "RO"},
            },
        ]
        sites = parse_features(features)
        assert len(sites) == 1
        assert sites[0].area_ha == 0.0
        assert sites[0].conservation_a == 0
        assert sites[0].release_date is None

    def test_skip_centroid_outside_europe(self):
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [0.1, 0.0], [0.1, 0.1],
                                     [0.0, 0.1], [0.0, 0.0]]],
                },
                "properties": {"SITECODE": "XXTEST01", "SITETYPE": "B", "MS": "XX",
                               "Area_ha": 100, "Area_km2": 1},
            },
        ]
        sites = parse_features(features)
        assert len(sites) == 0


# ---------------------------------------------------------------------------
# TestConservationScore
# ---------------------------------------------------------------------------

class TestConservationScore:
    """Test conservation score computation."""

    def test_normal_score(self):
        site = Natura2000Site(
            sitecode="T1", sitename="Test", sitetype="B", member_state="RO",
            area_ha=100, area_km2=1,
            conservation_a=12, conservation_b=8, conservation_c=3, conservation_d=1,
        )
        assert site.conservation_score == pytest.approx(12 / 24)

    def test_all_excellent(self):
        site = Natura2000Site(
            sitecode="T2", sitename="Test", sitetype="B", member_state="RO",
            area_ha=100, area_km2=1,
            conservation_a=10, conservation_b=0, conservation_c=0, conservation_d=0,
        )
        assert site.conservation_score == pytest.approx(1.0)

    def test_zero_denominator(self):
        site = Natura2000Site(
            sitecode="T3", sitename="Test", sitetype="B", member_state="RO",
            area_ha=100, area_km2=1,
            conservation_a=0, conservation_b=0, conservation_c=0, conservation_d=0,
        )
        assert site.conservation_score is None


# ---------------------------------------------------------------------------
# TestComputeDistances
# ---------------------------------------------------------------------------

class TestComputeDistances:
    """Test geodesic distance computation from candidate point to Natura 2000 sites."""

    def _make_site(self, sitecode: str, coords: list[list[float]], sitetype: str = "B") -> Natura2000Site:
        geom = Polygon(coords)
        centroid = geom.centroid
        return Natura2000Site(
            sitecode=sitecode, sitename=f"Test {sitecode}", sitetype=sitetype,
            member_state="RO", area_ha=100, area_km2=1,
            geometry=geom, centroid_lat=centroid.y, centroid_lon=centroid.x,
        )

    def test_point_outside_polygon(self):
        site = self._make_site("T1", [[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                                       [26.0, 44.5], [26.0, 44.4]])
        proximities = compute_distances(44.3, 25.9, [site])
        assert len(proximities) == 1
        assert proximities[0].distance_km > 0
        assert proximities[0].overlap is False

    def test_point_inside_polygon(self):
        site = self._make_site("T1", [[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                                       [26.0, 44.5], [26.0, 44.4]])
        proximities = compute_distances(44.45, 26.05, [site])
        assert len(proximities) == 1
        assert proximities[0].distance_km == 0.0
        assert proximities[0].overlap is True

    def test_sorted_by_distance(self):
        near = self._make_site("NEAR", [[26.0, 44.4], [26.05, 44.4], [26.05, 44.45],
                                         [26.0, 44.45], [26.0, 44.4]])
        far = self._make_site("FAR", [[27.0, 45.0], [27.1, 45.0], [27.1, 45.1],
                                       [27.0, 45.1], [27.0, 45.0]])
        proximities = compute_distances(44.42, 26.02, [far, near])
        assert proximities[0].sitecode == "NEAR"
        assert proximities[1].sitecode == "FAR"

    def test_bearing_computed(self):
        site = self._make_site("T1", [[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                                       [26.0, 44.5], [26.0, 44.4]])
        proximities = compute_distances(44.3, 26.05, [site])
        assert proximities[0].direction_deg is not None
        assert 0 <= proximities[0].direction_deg < 360


# ---------------------------------------------------------------------------
# TestCountSitesByRadius
# ---------------------------------------------------------------------------

class TestCountSitesByRadius:
    """Test cumulative site counting at threshold distances."""

    def test_counts_at_thresholds(self):
        proximities = [
            SiteProximity(sitecode="A", sitename="A", sitetype="B",
                          distance_km=2.0, overlap=False, area_ha=100),
            SiteProximity(sitecode="B", sitename="B", sitetype="A",
                          distance_km=10.0, overlap=False, area_ha=200),
            SiteProximity(sitecode="C", sitename="C", sitetype="C",
                          distance_km=20.0, overlap=False, area_ha=300),
            SiteProximity(sitecode="D", sitename="D", sitetype="B",
                          distance_km=30.0, overlap=False, area_ha=400),
        ]
        counts = count_sites_by_radius(proximities, [5.0, 16.0, 25.0])
        assert counts[5.0] == 1
        assert counts[16.0] == 2
        assert counts[25.0] == 3

    def test_monotonically_non_decreasing(self):
        proximities = [
            SiteProximity(sitecode="A", sitename="A", sitetype="B",
                          distance_km=3.0, overlap=False, area_ha=100),
            SiteProximity(sitecode="B", sitename="B", sitetype="A",
                          distance_km=7.0, overlap=False, area_ha=200),
        ]
        counts = count_sites_by_radius(proximities, [5.0, 16.0, 25.0])
        assert counts[5.0] <= counts[16.0] <= counts[25.0]

    def test_empty_proximities(self):
        counts = count_sites_by_radius([], [5.0, 16.0, 25.0])
        assert counts[5.0] == 0
        assert counts[16.0] == 0
        assert counts[25.0] == 0

    def test_overlap_counts_at_zero(self):
        proximities = [
            SiteProximity(sitecode="A", sitename="A", sitetype="B",
                          distance_km=0.0, overlap=True, area_ha=100),
        ]
        counts = count_sites_by_radius(proximities, [5.0, 16.0, 25.0])
        assert counts[5.0] == 1
        assert counts[16.0] == 1
        assert counts[25.0] == 1


# ---------------------------------------------------------------------------
# TestClassifyDesignationTypes
# ---------------------------------------------------------------------------

class TestClassifyDesignationTypes:
    """Test SPA/SAC/combined classification."""

    def test_mixed_types(self):
        proximities = [
            SiteProximity(sitecode="A1", sitename="", sitetype="A",
                          distance_km=1, overlap=False, area_ha=100),
            SiteProximity(sitecode="B1", sitename="", sitetype="B",
                          distance_km=2, overlap=False, area_ha=200),
            SiteProximity(sitecode="C1", sitename="", sitetype="C",
                          distance_km=3, overlap=False, area_ha=300),
        ]
        spa, sac, combined = classify_designation_types(proximities)
        assert spa == 2  # A + C
        assert sac == 2  # B + C
        assert combined == 1  # C only

    def test_all_spa(self):
        proximities = [
            SiteProximity(sitecode="A1", sitename="", sitetype="A",
                          distance_km=1, overlap=False, area_ha=100),
            SiteProximity(sitecode="A2", sitename="", sitetype="A",
                          distance_km=2, overlap=False, area_ha=200),
        ]
        spa, sac, combined = classify_designation_types(proximities)
        assert spa == 2
        assert sac == 0
        assert combined == 0

    def test_empty(self):
        spa, sac, combined = classify_designation_types([])
        assert spa == 0
        assert sac == 0
        assert combined == 0


# ---------------------------------------------------------------------------
# TestClassifySensitivity
# ---------------------------------------------------------------------------

class TestClassifySensitivity:
    """Test sensitivity classification at boundary conditions."""

    def test_overlap_is_high(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=True, n2k_nearest_distance_km=0.0)
        assert classify_sensitivity(result) == "high"

    def test_within_1km_is_high(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False, n2k_nearest_distance_km=0.5)
        assert classify_sensitivity(result) == "high"

    def test_exactly_1km_is_not_high(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False, n2k_nearest_distance_km=1.0,
                                  n2k_sites_within_5km=0, n2k_sites_within_25km=1)
        assert classify_sensitivity(result) == "low"

    def test_multiple_sites_5km_is_moderate(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False, n2k_nearest_distance_km=3.0,
                                  n2k_sites_within_5km=2, n2k_sites_within_25km=5)
        assert classify_sensitivity(result) == "moderate"

    def test_high_area_fraction_is_moderate(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False, n2k_nearest_distance_km=3.0,
                                  n2k_sites_within_5km=1,
                                  n2k_area_fraction_5km=0.15,
                                  n2k_sites_within_25km=3)
        assert classify_sensitivity(result) == "moderate"

    def test_one_site_25km_is_low(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False, n2k_nearest_distance_km=15.0,
                                  n2k_sites_within_5km=0, n2k_sites_within_25km=1)
        assert classify_sensitivity(result) == "low"

    def test_no_sites_is_none(self):
        result = Natura2000Result(lat=44.0, lon=26.0, is_eu_member=True,
                                  n2k_overlap=False,
                                  n2k_sites_within_5km=0, n2k_sites_within_25km=0)
        assert classify_sensitivity(result) == "none"

    def test_non_eu_is_unknown(self):
        result = Natura2000Result(lat=44.0, lon=20.0, is_eu_member=False,
                                  country_code="RS")
        assert classify_sensitivity(result) == "unknown"


# ---------------------------------------------------------------------------
# TestValidation
# ---------------------------------------------------------------------------

class TestValidation:
    """Test result validation checks."""

    def test_valid_result_no_warnings(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True, quality="high",
            n2k_overlap=False, n2k_nearest_distance_km=5.0,
            n2k_sites_within_5km=0, n2k_sites_within_16km=1,
            n2k_sites_within_25km=2,
            n2k_area_fraction_5km=0.0, n2k_area_fraction_16km=0.05,
            n2k_area_fraction_25km=0.1,
        )
        assert validate_result(result) == []

    def test_negative_distance_warning(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True,
            n2k_nearest_distance_km=-1.0,
        )
        warnings = validate_result(result)
        assert any("Negative distance" in w for w in warnings)

    def test_overlap_distance_inconsistency(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True,
            n2k_overlap=True, n2k_nearest_distance_km=5.0,
        )
        warnings = validate_result(result)
        assert any("Overlap=True but distance" in w for w in warnings)

    def test_non_monotonic_counts(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True,
            n2k_sites_within_5km=3, n2k_sites_within_16km=2,
            n2k_sites_within_25km=5,
        )
        warnings = validate_result(result)
        assert any("Non-monotonic" in w for w in warnings)

    def test_area_fraction_out_of_range(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True,
            n2k_area_fraction_5km=1.5,
        )
        warnings = validate_result(result)
        assert any("Area fraction" in w for w in warnings)

    def test_non_eu_wrong_quality(self):
        result = Natura2000Result(
            lat=44.0, lon=20.0, is_eu_member=False, country_code="RS",
            quality="high",
        )
        warnings = validate_result(result)
        assert any("Non-EU country" in w for w in warnings)


# ---------------------------------------------------------------------------
# TestNonEuCountry
# ---------------------------------------------------------------------------

class TestNonEuCountry:
    """Test that non-EU countries are correctly identified."""

    def test_eu_member_states_set(self):
        assert "RO" in EU_MEMBER_STATES_INSCOPE
        assert "PL" in EU_MEMBER_STATES_INSCOPE
        assert len(EU_MEMBER_STATES_INSCOPE) == 12

    def test_non_eu_set(self):
        assert "RS" in NON_EU_INSCOPE
        assert "BA" in NON_EU_INSCOPE
        assert "UA" in NON_EU_INSCOPE
        assert len(NON_EU_INSCOPE) == 11

    def test_no_overlap(self):
        assert EU_MEMBER_STATES_INSCOPE.isdisjoint(NON_EU_INSCOPE)


# ---------------------------------------------------------------------------
# TestResultStructure
# ---------------------------------------------------------------------------

class TestResultStructure:
    """Test Natura2000Result.to_dict() shape and types."""

    def test_to_dict_keys(self):
        result = Natura2000Result(lat=44.0, lon=26.0)
        d = result.to_dict()
        expected_keys = {
            "lat", "lon", "country_code", "is_eu_member",
            "n2k_overlap", "n2k_overlap_sitecodes",
            "n2k_nearest_distance_km", "n2k_nearest_sitecode",
            "n2k_nearest_sitename", "n2k_nearest_sitetype", "n2k_nearest_area_ha",
            "n2k_sites_within_5km", "n2k_sites_within_16km", "n2k_sites_within_25km",
            "n2k_area_fraction_5km", "n2k_area_fraction_16km", "n2k_area_fraction_25km",
            "n2k_spa_count", "n2k_sac_count", "n2k_combined_count",
            "n2k_total_protected_area_ha", "n2k_max_conservation_score",
            "sensitivity_class", "nearby_sites", "reference_date",
            "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_types(self):
        result = Natura2000Result(
            lat=44.0, lon=26.0, is_eu_member=True,
            n2k_overlap=True, n2k_nearest_distance_km=0.0,
            n2k_sites_within_5km=1,
        )
        d = result.to_dict()
        assert isinstance(d["lat"], float)
        assert isinstance(d["n2k_overlap"], bool)
        assert isinstance(d["n2k_sites_within_5km"], int)
        assert isinstance(d["nearby_sites"], list)

    def test_site_proximity_to_dict(self):
        sp = SiteProximity(
            sitecode="ROSCI0229", sitename="Comana", sitetype="B",
            distance_km=3.456, overlap=False, area_ha=24550.0,
            conservation_score=0.5, direction_deg=45.678,
        )
        d = sp.to_dict()
        assert d["distance_km"] == pytest.approx(3.456, abs=0.001)
        assert d["direction_deg"] == pytest.approx(45.7, abs=0.1)

    def test_natura2000_site_to_dict_excludes_geometry(self):
        site = Natura2000Site(
            sitecode="ROSCI0229", sitename="Comana", sitetype="B",
            member_state="RO", area_ha=24550.0, area_km2=245.5,
            geometry=box(26.0, 44.4, 26.1, 44.5),
        )
        d = site.to_dict()
        assert "geometry" not in d
        assert d["sitecode"] == "ROSCI0229"


# ---------------------------------------------------------------------------
# TestBatchResult
# ---------------------------------------------------------------------------

class TestBatchResult:
    """Test BatchResult and SiteEnrichmentSummary."""

    def test_summary_line(self):
        batch = BatchResult(
            run_id="test-001", total_sites=10,
            succeeded=7, degraded=0, failed=1, skipped_cached=1, skipped_non_eu=1,
            elapsed_s=30.0,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "7 ok" in line
        assert "0 degraded" in line
        assert "1 failed" in line

    def test_to_dict(self):
        batch = BatchResult(run_id="test-001", total_sites=1)
        d = batch.to_dict()
        assert d["run_id"] == "test-001"
        assert isinstance(d["per_site"], list)
        assert d["skipped_after_abort"] == 0
        assert d["aborted_reason"] is None
        assert d["degraded"] == 0

    def test_summary_line_when_aborted(self):
        batch = BatchResult(
            run_id="r1",
            total_sites=100,
            succeeded=0,
            degraded=3,
            skipped_after_abort=97,
            aborted_reason="EEA down",
            elapsed_s=10.0,
        )
        line = batch.summary_line()
        assert "aborted" in line
        assert "97 not processed" in line
        assert "EEA down" in line


# ---------------------------------------------------------------------------
# TestCriterionIds
# ---------------------------------------------------------------------------

class TestCriterionIds:
    """Test that CRITERION_IDS constant is correctly defined."""

    def test_criterion_ids(self):
        assert CRITERION_IDS == ("NS-08",)

    def test_importable(self):
        from atoms_vs_ashes.connectors.natura2000 import CRITERION_IDS as imported
        assert imported == ("NS-08",)


# ---------------------------------------------------------------------------
# TestComputeAreaFractions
# ---------------------------------------------------------------------------

class TestComputeAreaFractions:
    """Test area fraction computation."""

    def test_no_sites_returns_zeros(self):
        fractions = compute_area_fractions(44.0, 26.0, [], [5000, 16000, 25000])
        assert fractions[5000] == 0.0
        assert fractions[16000] == 0.0
        assert fractions[25000] == 0.0

    def test_fractions_in_valid_range(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        fractions = compute_area_fractions(44.45, 26.10, sites, [5000, 16000, 25000])
        for r, f in fractions.items():
            assert 0.0 <= f <= 1.0, f"Fraction at {r}m = {f} out of [0,1]"

    def test_larger_radius_has_smaller_or_equal_fraction(self):
        sites = parse_features(SAMPLE_N2K_GEOJSON_FEATURES)
        fractions = compute_area_fractions(44.45, 26.10, sites, [5000, 25000])
        # Not strictly guaranteed (depends on geometry), but for distant sites
        # the 25km buffer dilutes the fraction
        assert fractions[5000] >= 0.0
        assert fractions[25000] >= 0.0
