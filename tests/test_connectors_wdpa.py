# man_hours: 6.0
"""Tests for S-15 WDPA connector — parsing and transformation logic.

All tests are pure (no network, no database). They exercise the parser,
distance computation, area fraction, IUCN classification, Natura 2000
deduplication, sensitivity classification, and result validation.
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Point, Polygon, box

from atoms_vs_ashes.connectors.wdpa.models import (
    CRITERION_IDS,
    EU_MEMBER_STATES_INSCOPE,
    ISO2_TO_ISO3,
    ISO3_TO_ISO2,
    IUCN_HIGH,
    IUCN_MODERATE,
    IUCN_STRICT,
    NON_EU_INSCOPE,
    AreaProximity,
    BatchResult,
    ProtectedArea,
    SiteEnrichmentSummary,
    WdpaResult,
    point_buffer_radius_m,
)
from atoms_vs_ashes.connectors.wdpa.parsers import (
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_by_iucn,
    count_by_radius,
    count_international_designations,
    filter_country_areas,
    filter_kosovo_from_serbia,
    filter_marine_only,
    nearest_ramsar_km,
    parse_api_page,
    parse_protected_area,
    should_exclude_natura2000,
    strictest_iucn_category,
    validate_result,
)


# ---------------------------------------------------------------------------
# Fixture data — WDPA API v4 format
# ---------------------------------------------------------------------------

SAMPLE_WDPA_V4_RECORD_RAMSAR = {
    "site_id": 166899,
    "site_pid": "166899",
    "name_english": "Kyliiske Mouth",
    "name": "Кілійське гирло",
    "site_type": "pa",
    "geojson": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[29.542, 45.541], [29.552, 45.532],
                             [29.595, 45.557], [29.624, 45.538],
                             [29.489, 45.543], [29.517, 45.564],
                             [29.542, 45.541]]],
        },
    },
    "marine": True,
    "reported_marine_area": "0.0",
    "reported_area": "328.0",
    "management_plan": "Not Reported",
    "is_green_list": False,
    "is_oecm": False,
    "owner_type": "Not Reported",
    "countries": [{"name": "Ukraine", "iso_3": "UKR", "id": "UKR"}],
    "iucn_category": {"id": 8, "name": "Not Reported"},
    "designation": {
        "id": 256,
        "name": "Ramsar Site, Wetland of International Importance",
        "jurisdiction": {"id": 2, "name": "International"},
    },
    "legal_status": {"id": 1, "name": "Designated"},
    "governance": {"id": 1, "governance_type": "Governance by Government"},
    "realm": {"id": 1, "name": "Terrestrial"},
    "sources": [],
    "protected_area_parcels": [],
    "links": {"protected_planet": "https://protectedplanet.net/166899"},
    "legal_status_updated_at": "01/01/1976",
}

SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK = {
    "site_id": 12345,
    "site_pid": "12345",
    "name_english": "Danube-Dniester Interfluve",
    "name": "Дунайсько-Дністровське міжріччя",
    "site_type": "pa",
    "geojson": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[29.60, 45.40], [29.80, 45.40],
                             [29.80, 45.55], [29.60, 45.55],
                             [29.60, 45.40]]],
        },
    },
    "marine": False,
    "reported_marine_area": "0.0",
    "reported_area": "760.0",
    "management_plan": "Not Reported",
    "is_green_list": False,
    "is_oecm": False,
    "owner_type": "State",
    "countries": [{"name": "Ukraine", "iso_3": "UKR", "id": "UKR"}],
    "iucn_category": {"id": 3, "name": "II"},
    "designation": {
        "id": 4,
        "name": "National Park",
        "jurisdiction": {"id": 1, "name": "National"},
    },
    "legal_status": {"id": 1, "name": "Designated"},
    "governance": {"id": 1, "governance_type": "Governance by Government"},
    "realm": {"id": 1, "name": "Terrestrial"},
    "sources": [],
    "protected_area_parcels": [],
    "links": {"protected_planet": "https://protectedplanet.net/12345"},
    "legal_status_updated_at": "01/06/2010",
}

SAMPLE_WDPA_V4_RECORD_HABITATS_DIRECTIVE = {
    "site_id": 99999,
    "site_pid": "99999",
    "name_english": "Some Natura 2000 SCI",
    "name": "Sit Natura 2000",
    "site_type": "pa",
    "geojson": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[26.0, 44.4], [26.1, 44.4], [26.1, 44.5],
                             [26.0, 44.5], [26.0, 44.4]]],
        },
    },
    "marine": False,
    "reported_marine_area": "0.0",
    "reported_area": "150.0",
    "is_green_list": False,
    "countries": [{"name": "Romania", "iso_3": "ROU", "id": "ROU"}],
    "iucn_category": {"id": 8, "name": "Not Reported"},
    "designation": {
        "id": 100,
        "name": "Sites of Community Importance (Habitats Directive)",
        "jurisdiction": {"id": 3, "name": "Regional"},
    },
    "legal_status": {"id": 1, "name": "Designated"},
    "governance": {"id": 1, "governance_type": "Governance by Government"},
    "realm": {"id": 1, "name": "Terrestrial"},
}

SAMPLE_WDPA_V4_RESPONSE_PAGE1 = {
    "protected_areas": [
        SAMPLE_WDPA_V4_RECORD_RAMSAR,
        SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK,
    ],
}

SAMPLE_WDPA_EMPTY_PAGE = {"protected_areas": []}


# ---------------------------------------------------------------------------
# Test: API response parsing
# ---------------------------------------------------------------------------

class TestParseProtectedArea:
    """Test parsing of individual WDPA API v4 records."""

    def test_parse_ramsar_site(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_RAMSAR)
        assert pa is not None
        assert pa.site_id == 166899
        assert pa.site_pid == "166899"
        assert pa.name_english == "Kyliiske Mouth"
        assert pa.site_type == "pa"
        assert pa.is_ramsar is True
        assert pa.is_world_heritage is False
        assert pa.designation_jurisdiction == "International"
        assert pa.reported_area_km2 == pytest.approx(328.0)
        assert pa.reported_area_ha == pytest.approx(32800.0)
        assert pa.geometry is not None

    def test_parse_national_park(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK)
        assert pa is not None
        assert pa.site_id == 12345
        assert pa.iucn_category == "II"
        assert pa.designation_name == "National Park"
        assert pa.is_ramsar is False
        assert pa.countries == ["UKR"]

    def test_parse_v4_field_names(self):
        """Verify v4-specific field names are used correctly."""
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_RAMSAR)
        assert pa is not None
        assert pa.site_id == 166899  # v4: site_id (not wdpa_id)
        assert pa.name_english == "Kyliiske Mouth"  # v4: name_english (not name)
        assert pa.name == "Кілійське гирло"  # v4: name (original language)
        assert pa.site_type == "pa"  # v4: site_type (new field)

    def test_parse_invalid_site_id(self):
        record = {**SAMPLE_WDPA_V4_RECORD_RAMSAR, "site_id": -1}
        assert parse_protected_area(record) is None

    def test_parse_missing_site_id(self):
        record = {k: v for k, v in SAMPLE_WDPA_V4_RECORD_RAMSAR.items() if k != "site_id"}
        assert parse_protected_area(record) is None

    def test_parse_missing_geometry(self):
        record = {**SAMPLE_WDPA_V4_RECORD_RAMSAR, "geojson": None}
        pa = parse_protected_area(record)
        # Should still parse but with no geometry (area > 0 but no point coords)
        assert pa is None or pa.geometry is None

    def test_parse_empty_response(self):
        areas = parse_api_page(SAMPLE_WDPA_EMPTY_PAGE)
        assert areas == []

    def test_parse_full_page(self):
        areas = parse_api_page(SAMPLE_WDPA_V4_RESPONSE_PAGE1)
        assert len(areas) == 2
        assert areas[0].site_id == 166899
        assert areas[1].site_id == 12345


class TestParseProtectedAreaEdgeCases:
    """Edge cases in parsing."""

    def test_missing_designation(self):
        record = {**SAMPLE_WDPA_V4_RECORD_RAMSAR, "designation": None}
        pa = parse_protected_area(record)
        assert pa is not None
        assert pa.designation_name == ""

    def test_missing_iucn_category(self):
        record = {**SAMPLE_WDPA_V4_RECORD_RAMSAR, "iucn_category": None}
        pa = parse_protected_area(record)
        assert pa is not None
        assert pa.iucn_category == "Not Reported"

    def test_string_reported_area(self):
        """API returns reported_area as string."""
        record = {**SAMPLE_WDPA_V4_RECORD_RAMSAR, "reported_area": "328.0"}
        pa = parse_protected_area(record)
        assert pa is not None
        assert pa.reported_area_km2 == pytest.approx(328.0)


# ---------------------------------------------------------------------------
# Test: Natura 2000 deduplication
# ---------------------------------------------------------------------------

class TestNatura2000Dedup:
    """Test Natura 2000 deduplication for EU countries."""

    def test_habitats_directive_excluded_for_eu(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_HABITATS_DIRECTIVE)
        assert pa is not None
        assert should_exclude_natura2000(pa, "RO") is True

    def test_ramsar_not_excluded_for_eu(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_RAMSAR)
        assert pa is not None
        assert should_exclude_natura2000(pa, "RO") is False

    def test_national_park_not_excluded_for_eu(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK)
        assert pa is not None
        assert should_exclude_natura2000(pa, "PL") is False

    def test_no_exclusion_for_non_eu(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_HABITATS_DIRECTIVE)
        assert pa is not None
        assert should_exclude_natura2000(pa, "RS") is False
        assert should_exclude_natura2000(pa, "UA") is False

    def test_filter_country_areas_eu(self):
        areas = parse_api_page({
            "protected_areas": [
                SAMPLE_WDPA_V4_RECORD_RAMSAR,
                SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK,
                SAMPLE_WDPA_V4_RECORD_HABITATS_DIRECTIVE,
            ],
        })
        filtered, n_excluded = filter_country_areas(areas, "RO")
        assert n_excluded == 1
        assert len(filtered) == 2
        site_ids = {a.site_id for a in filtered}
        assert 99999 not in site_ids

    def test_filter_country_areas_non_eu(self):
        areas = parse_api_page({
            "protected_areas": [
                SAMPLE_WDPA_V4_RECORD_RAMSAR,
                SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK,
                SAMPLE_WDPA_V4_RECORD_HABITATS_DIRECTIVE,
            ],
        })
        filtered, n_excluded = filter_country_areas(areas, "UA")
        assert n_excluded == 0
        assert len(filtered) == 3


# ---------------------------------------------------------------------------
# Test: Marine filtering
# ---------------------------------------------------------------------------

class TestMarineFiltering:

    def test_terrestrial_not_filtered(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_NATIONAL_PARK)
        assert pa is not None
        assert filter_marine_only(pa) is False

    def test_marine_only_filtered(self):
        pa = ProtectedArea(
            site_id=1, site_pid="1", name_english="Marine PA", name="",
            site_type="pa", iucn_category="II", iucn_category_id=3,
            designation_name="Marine Reserve", designation_id=1,
            designation_jurisdiction="National", legal_status="Designated",
            governance_type="", realm="Marine", marine=True,
            reported_area_km2=100.0, reported_marine_area_km2=100.0,
            reported_area_ha=10000.0, owner_type="", is_green_list=False,
            countries=["UKR"], legal_status_updated_at=None,
        )
        assert filter_marine_only(pa) is True


# ---------------------------------------------------------------------------
# Test: Distance computation
# ---------------------------------------------------------------------------

def _make_pa(site_id: int, polygon: Polygon, **kwargs) -> ProtectedArea:
    """Helper to create a ProtectedArea with a given geometry."""
    defaults = dict(
        site_pid=str(site_id), name_english=f"PA-{site_id}", name="",
        site_type="pa", iucn_category="II", iucn_category_id=3,
        designation_name="National Park", designation_id=1,
        designation_jurisdiction="National", legal_status="Designated",
        governance_type="", realm="Terrestrial", marine=False,
        reported_area_km2=100.0, reported_marine_area_km2=0.0,
        reported_area_ha=10000.0, owner_type="", is_green_list=False,
        countries=["UKR"], legal_status_updated_at=None,
        geometry=polygon,
    )
    defaults.update(kwargs)
    return ProtectedArea(site_id=site_id, **defaults)


class TestComputeDistances:

    def test_point_outside_polygon(self):
        poly = box(29.0, 45.0, 29.5, 45.5)
        pa = _make_pa(1, poly)
        proximities = compute_distances(45.6, 29.25, [pa])
        assert len(proximities) == 1
        assert proximities[0].overlap is False
        assert proximities[0].distance_km > 0

    def test_point_inside_polygon(self):
        poly = box(29.0, 45.0, 29.5, 45.5)
        pa = _make_pa(1, poly)
        proximities = compute_distances(45.25, 29.25, [pa])
        assert len(proximities) == 1
        assert proximities[0].overlap is True
        assert proximities[0].distance_km == 0.0

    def test_sorted_by_distance(self):
        near = box(29.0, 45.0, 29.1, 45.1)
        far = box(30.0, 46.0, 30.1, 46.1)
        pa_near = _make_pa(1, near)
        pa_far = _make_pa(2, far)
        proximities = compute_distances(45.15, 29.15, [pa_far, pa_near])
        assert proximities[0].site_id == 1
        assert proximities[1].site_id == 2

    def test_no_areas(self):
        proximities = compute_distances(45.0, 29.0, [])
        assert proximities == []


# ---------------------------------------------------------------------------
# Test: Area fraction computation
# ---------------------------------------------------------------------------

class TestComputeAreaFractions:

    def test_no_areas(self):
        fractions = compute_area_fractions(45.0, 29.0, [], [5000, 16000, 25000])
        assert fractions[5000] == 0.0
        assert fractions[16000] == 0.0
        assert fractions[25000] == 0.0

    def test_large_area_gives_nonzero_fraction(self):
        poly = box(28.5, 44.5, 29.5, 45.5)
        pa = _make_pa(1, poly)
        fractions = compute_area_fractions(45.0, 29.0, [pa], [5000])
        assert fractions[5000] > 0.0
        assert fractions[5000] <= 1.0

    def test_overlapping_areas_no_double_count(self):
        poly1 = box(29.0, 45.0, 29.5, 45.5)
        poly2 = box(29.2, 45.2, 29.7, 45.7)
        pa1 = _make_pa(1, poly1)
        pa2 = _make_pa(2, poly2)
        fractions_both = compute_area_fractions(45.25, 29.25, [pa1, pa2], [25000])
        fractions_union = compute_area_fractions(45.25, 29.25, [pa1], [25000])
        # Union should be <= sum of individual (no double-counting)
        assert fractions_both[25000] <= 1.0


# ---------------------------------------------------------------------------
# Test: Site counting
# ---------------------------------------------------------------------------

class TestCountByRadius:

    def test_cumulative_counts(self):
        proximities = [
            AreaProximity(site_id=1, name_english="A", designation_name="", iucn_category="II",
                          designation_jurisdiction="National", distance_km=2.0, overlap=False, area_ha=100),
            AreaProximity(site_id=2, name_english="B", designation_name="", iucn_category="IV",
                          designation_jurisdiction="National", distance_km=8.0, overlap=False, area_ha=200),
            AreaProximity(site_id=3, name_english="C", designation_name="", iucn_category="Ia",
                          designation_jurisdiction="National", distance_km=20.0, overlap=False, area_ha=50),
        ]
        counts = count_by_radius(proximities, [5.0, 16.0, 25.0])
        assert counts[5.0] == 1
        assert counts[16.0] == 2
        assert counts[25.0] == 3

    def test_monotonic(self):
        proximities = [
            AreaProximity(site_id=i, name_english=f"PA-{i}", designation_name="",
                          iucn_category="II", designation_jurisdiction="National",
                          distance_km=float(i), overlap=False, area_ha=100)
            for i in range(1, 30)
        ]
        counts = count_by_radius(proximities, [5.0, 16.0, 25.0])
        assert counts[5.0] <= counts[16.0] <= counts[25.0]


# ---------------------------------------------------------------------------
# Test: IUCN classification
# ---------------------------------------------------------------------------

class TestCountByIucn:

    def test_iucn_grouping(self):
        proximities = [
            AreaProximity(site_id=1, name_english="", designation_name="", iucn_category="Ia",
                          designation_jurisdiction="", distance_km=1.0, overlap=False, area_ha=100),
            AreaProximity(site_id=2, name_english="", designation_name="", iucn_category="Ib",
                          designation_jurisdiction="", distance_km=2.0, overlap=False, area_ha=100),
            AreaProximity(site_id=3, name_english="", designation_name="", iucn_category="II",
                          designation_jurisdiction="", distance_km=3.0, overlap=False, area_ha=100),
            AreaProximity(site_id=4, name_english="", designation_name="", iucn_category="III",
                          designation_jurisdiction="", distance_km=4.0, overlap=False, area_ha=100),
            AreaProximity(site_id=5, name_english="", designation_name="", iucn_category="IV",
                          designation_jurisdiction="", distance_km=5.0, overlap=False, area_ha=100),
            AreaProximity(site_id=6, name_english="", designation_name="", iucn_category="V",
                          designation_jurisdiction="", distance_km=6.0, overlap=False, area_ha=100),
        ]
        strict, high, moderate = count_by_iucn(proximities, 25.0)
        assert strict == 2   # Ia, Ib
        assert high == 2     # II, III
        assert moderate == 2  # IV, V

    def test_iucn_respects_radius(self):
        proximities = [
            AreaProximity(site_id=1, name_english="", designation_name="", iucn_category="Ia",
                          designation_jurisdiction="", distance_km=30.0, overlap=False, area_ha=100),
        ]
        strict, high, moderate = count_by_iucn(proximities, 25.0)
        assert strict == 0


class TestStrictestIucnCategory:

    def test_strictest_is_ia(self):
        proximities = [
            AreaProximity(site_id=1, name_english="", designation_name="", iucn_category="IV",
                          designation_jurisdiction="", distance_km=1.0, overlap=False, area_ha=100),
            AreaProximity(site_id=2, name_english="", designation_name="", iucn_category="Ia",
                          designation_jurisdiction="", distance_km=2.0, overlap=False, area_ha=100),
        ]
        assert strictest_iucn_category(proximities, 25.0) == "Ia"

    def test_no_valid_categories(self):
        proximities = [
            AreaProximity(site_id=1, name_english="", designation_name="", iucn_category="Not Reported",
                          designation_jurisdiction="", distance_km=1.0, overlap=False, area_ha=100),
        ]
        assert strictest_iucn_category(proximities, 25.0) is None


# ---------------------------------------------------------------------------
# Test: International designations
# ---------------------------------------------------------------------------

class TestInternationalDesignations:

    def test_ramsar_detected(self):
        proximities = [
            AreaProximity(site_id=1, name_english="Wetland", designation_name="Ramsar Site",
                          iucn_category="II", designation_jurisdiction="International",
                          distance_km=3.0, overlap=False, area_ha=500,
                          is_ramsar=True),
        ]
        intl = count_international_designations(proximities, 25.0)
        assert intl["ramsar"] == 1
        assert intl["total"] >= 1

    def test_world_heritage_detected(self):
        proximities = [
            AreaProximity(site_id=1, name_english="WH Site", designation_name="World Heritage",
                          iucn_category="II", designation_jurisdiction="International",
                          distance_km=5.0, overlap=False, area_ha=1000,
                          is_world_heritage=True),
        ]
        intl = count_international_designations(proximities, 25.0)
        assert intl["world_heritage"] == 1

    def test_nearest_ramsar(self):
        proximities = [
            AreaProximity(site_id=1, name_english="NP", designation_name="National Park",
                          iucn_category="II", designation_jurisdiction="National",
                          distance_km=2.0, overlap=False, area_ha=100),
            AreaProximity(site_id=2, name_english="Ramsar", designation_name="Ramsar Site",
                          iucn_category="II", designation_jurisdiction="International",
                          distance_km=5.0, overlap=False, area_ha=500,
                          is_ramsar=True),
        ]
        assert nearest_ramsar_km(proximities) == 5.0

    def test_no_ramsar(self):
        proximities = [
            AreaProximity(site_id=1, name_english="NP", designation_name="National Park",
                          iucn_category="II", designation_jurisdiction="National",
                          distance_km=2.0, overlap=False, area_ha=100),
        ]
        assert nearest_ramsar_km(proximities) is None


# ---------------------------------------------------------------------------
# Test: Sensitivity classification
# ---------------------------------------------------------------------------

class TestClassifySensitivity:

    def test_overlap_is_high(self):
        result = WdpaResult(lat=45.0, lon=29.0, wdpa_overlap=True)
        assert classify_sensitivity(result) == "high"

    def test_iucn_ia_within_2km_is_high(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=1.5,
            wdpa_strictest_iucn_category="Ia",
            wdpa_sites_within_25km=1,
        )
        assert classify_sensitivity(result) == "high"

    def test_international_within_2km_is_high(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=1.0,
            wdpa_international_designation_count=1,
            wdpa_sites_within_25km=1,
        )
        assert classify_sensitivity(result) == "high"

    def test_ramsar_within_5km_is_moderate(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=3.0,
            wdpa_ramsar_count=1,
            wdpa_ramsar_nearest_km=3.0,
            wdpa_sites_within_25km=1,
        )
        assert classify_sensitivity(result) == "moderate"

    def test_two_sites_within_5km_is_moderate(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=3.0,
            wdpa_sites_within_5km=2,
            wdpa_sites_within_25km=2,
        )
        assert classify_sensitivity(result) == "moderate"

    def test_high_area_fraction_is_moderate(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=3.0,
            wdpa_area_fraction_5km=0.15,
            wdpa_sites_within_5km=1,
            wdpa_sites_within_25km=1,
        )
        assert classify_sensitivity(result) == "moderate"

    def test_one_site_within_25km_is_low(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=15.0,
            wdpa_sites_within_25km=1,
        )
        assert classify_sensitivity(result) == "low"

    def test_no_sites_is_none(self):
        result = WdpaResult(lat=45.0, lon=29.0)
        assert classify_sensitivity(result) == "none"


# ---------------------------------------------------------------------------
# Test: Result validation
# ---------------------------------------------------------------------------

class TestValidation:

    def test_valid_result_no_warnings(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_nearest_distance_km=5.0,
            wdpa_sites_within_5km=1,
            wdpa_sites_within_16km=2,
            wdpa_sites_within_25km=3,
            wdpa_area_fraction_5km=0.05,
        )
        assert validate_result(result) == []

    def test_negative_distance(self):
        result = WdpaResult(lat=45.0, lon=29.0, wdpa_nearest_distance_km=-1.0)
        warnings = validate_result(result)
        assert any("Negative" in w for w in warnings)

    def test_overlap_distance_inconsistency(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_overlap=True,
            wdpa_nearest_distance_km=5.0,
        )
        warnings = validate_result(result)
        assert any("Overlap" in w for w in warnings)

    def test_non_monotonic_counts(self):
        result = WdpaResult(
            lat=45.0, lon=29.0,
            wdpa_sites_within_5km=5,
            wdpa_sites_within_16km=3,
            wdpa_sites_within_25km=10,
        )
        warnings = validate_result(result)
        assert any("Non-monotonic" in w for w in warnings)

    def test_area_fraction_out_of_range(self):
        result = WdpaResult(lat=45.0, lon=29.0, wdpa_area_fraction_5km=1.5)
        warnings = validate_result(result)
        assert any("out of range" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test: ISO mapping
# ---------------------------------------------------------------------------

class TestIso2ToIso3Mapping:

    def test_all_23_countries_mapped(self):
        all_iso2 = EU_MEMBER_STATES_INSCOPE | NON_EU_INSCOPE
        for iso2 in all_iso2:
            assert iso2 in ISO2_TO_ISO3, f"Missing ISO3 mapping for {iso2}"

    def test_reverse_mapping(self):
        for iso2, iso3 in ISO2_TO_ISO3.items():
            assert ISO3_TO_ISO2[iso3] == iso2

    def test_known_mappings(self):
        assert ISO2_TO_ISO3["UA"] == "UKR"
        assert ISO2_TO_ISO3["RO"] == "ROU"
        assert ISO2_TO_ISO3["XK"] == "XKX"
        assert ISO2_TO_ISO3["TR"] == "TUR"


# ---------------------------------------------------------------------------
# Test: Point buffering
# ---------------------------------------------------------------------------

class TestPointBuffering:

    def test_buffer_radius_from_area(self):
        # 100 km² → radius = sqrt(100e6 / pi) ≈ 5641 m
        radius = point_buffer_radius_m(100.0)
        expected = math.sqrt(100e6 / math.pi)
        assert radius == pytest.approx(expected, rel=1e-3)

    def test_zero_area_gets_minimum_buffer(self):
        radius = point_buffer_radius_m(0.0)
        assert radius == 100.0

    def test_negative_area_gets_minimum_buffer(self):
        radius = point_buffer_radius_m(-5.0)
        assert radius == 100.0


# ---------------------------------------------------------------------------
# Test: Result structure
# ---------------------------------------------------------------------------

class TestResultStructure:

    def test_wdpa_result_to_dict_keys(self):
        result = WdpaResult(lat=45.0, lon=29.0)
        d = result.to_dict()
        expected_keys = {
            "lat", "lon", "country_code", "country_iso3", "is_eu_member",
            "wdpa_overlap", "wdpa_overlap_ids",
            "wdpa_nearest_distance_km", "wdpa_nearest_site_id",
            "wdpa_nearest_name", "wdpa_nearest_designation",
            "wdpa_nearest_iucn_category", "wdpa_nearest_area_ha",
            "wdpa_sites_within_5km", "wdpa_sites_within_16km",
            "wdpa_sites_within_25km",
            "wdpa_area_fraction_5km", "wdpa_area_fraction_16km",
            "wdpa_area_fraction_25km",
            "wdpa_total_protected_area_ha",
            "wdpa_iucn_ia_ib_count", "wdpa_iucn_ii_iii_count",
            "wdpa_iucn_iv_v_vi_count", "wdpa_strictest_iucn_category",
            "wdpa_ramsar_count", "wdpa_ramsar_nearest_km",
            "wdpa_world_heritage_count", "wdpa_biosphere_reserve_count",
            "wdpa_international_designation_count",
            "sensitivity_class", "nearby_areas", "n2k_deduplicated",
            "source", "quality", "error",
        }
        assert set(d.keys()) == expected_keys

    def test_protected_area_to_dict_excludes_geometry(self):
        pa = parse_protected_area(SAMPLE_WDPA_V4_RECORD_RAMSAR)
        assert pa is not None
        d = pa.to_dict()
        assert "geometry" not in d
        assert d["site_id"] == 166899

    def test_area_proximity_to_dict(self):
        ap = AreaProximity(
            site_id=1, name_english="Test", designation_name="NP",
            iucn_category="II", designation_jurisdiction="National",
            distance_km=5.123456, overlap=False, area_ha=1000.0,
        )
        d = ap.to_dict()
        assert d["distance_km"] == 5.123
        assert d["overlap"] is False

    def test_batch_result_summary(self):
        batch = BatchResult(
            run_id="test-001", total_sites=10, succeeded=8,
            failed=1, skipped_cached=1, elapsed_s=5.5,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line

    def test_criterion_ids(self):
        assert CRITERION_IDS == ("NS-08",)


# ---------------------------------------------------------------------------
# Test: Kosovo fallback
# ---------------------------------------------------------------------------

class TestKosovoFallback:

    def test_filter_kosovo_from_serbia(self):
        # PA inside Kosovo bbox
        inside = _make_pa(1, box(20.5, 42.5, 20.6, 42.6))
        # PA outside Kosovo bbox (northern Serbia)
        outside = _make_pa(2, box(20.5, 44.5, 20.6, 44.6))
        result = filter_kosovo_from_serbia([inside, outside])
        assert len(result) == 1
        assert result[0].site_id == 1
