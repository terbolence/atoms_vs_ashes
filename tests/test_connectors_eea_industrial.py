# man_hours: 3.0
"""Tests for S-37 EEA Industrial Emissions connector — parsing and transformation logic."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eea_industrial.models import (
    CRITERION_IDS,
    EU_MEMBER_COUNTRIES,
    NACE_HAZARD_MAP,
    NO_COVERAGE_COUNTRIES,
    PARTIAL_COVERAGE_COUNTRIES,
    EpzIndustrialAssessment,
    FacilityIndex,
    HazardProximity,
    IndustrialFacility,
    IndustrialProximityResult,
    NearbyFacility,
)
from atoms_vs_ashes.connectors.eea_industrial.parsers import (
    assess_data_quality,
    build_facility_index,
    classify_hazard,
    compute_proximity_metrics,
    parse_eprtr_csv,
    query_facilities_in_radius,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_EPRTR_CSV = """\
FacilityID,FacilityName,CountryCode,Latitude,Longitude,NACEMainEconomicActivityCode,NACEMainEconomicActivityName,EPRTRAnnexIMainActivityCode,SevesoPart,ParentCompanyName,City
E-PRTR-RO-00142,OMV Petrom SA Petrobrazi,RO,44.9833,26.0167,19.20,Manufacture of refined petroleum products,1.2,Upper tier,OMV Petrom,Brazi
E-PRTR-RO-00087,Chimcomplex SA Borzesti,RO,46.3667,26.8333,20.14,Manufacture of other organic basic chemicals,4.1,Upper tier,Chimcomplex SA,Onesti
E-PRTR-HU-00201,MOL Nyrt Danube Refinery,HU,47.1500,18.4167,19.20,Manufacture of refined petroleum products,1.2,Upper tier,MOL Hungarian Oil and Gas,Szazhalombatta
E-PRTR-PL-00312,PKN Orlen SA Plock,PL,52.6333,19.6833,19.20,Manufacture of refined petroleum products,1.2,Upper tier,PKN Orlen SA,Plock
E-PRTR-BG-00056,Lukoil Neftochim Burgas,BG,42.4833,27.4500,19.20,Manufacture of refined petroleum products,1.2,Lower tier,LITASCO SA,Burgas
"""

SAMPLE_EPRTR_CSV_EMPTY = """\
FacilityID,FacilityName,CountryCode,Latitude,Longitude,NACEMainEconomicActivityCode
"""

SAMPLE_EPRTR_CSV_MALFORMED = """\
FacilityID,FacilityName,CountryCode,Latitude,Longitude,NACEMainEconomicActivityCode
BAD-001,Bad Coords,RO,not_a_number,26.0,19.20
BAD-002,No Coords,RO,,26.0,19.20
BAD-003,Out of Europe,RO,-50.0,26.0,19.20
GOOD-001,Valid Facility,RO,44.5,26.0,19.20
"""


def _make_facility(
    fid: str = "F-001",
    name: str = "Test Facility",
    lat: float = 44.9833,
    lon: float = 26.0167,
    cc: str = "RO",
    nace: str = "19.20",
    seveso: str | None = "upper",
    hazards: set[str] | None = None,
) -> IndustrialFacility:
    return IndustrialFacility(
        facility_id=fid,
        name=name,
        latitude=lat,
        longitude=lon,
        country_code=cc,
        nace_code=nace,
        seveso_status=seveso,
        hazard_categories=hazards or {"chemical", "fire"},
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestParseEprtrCsv:
    """Test CSV parsing of E-PRTR facility data."""

    def test_parse_valid_csv(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV)
        assert len(facilities) == 5

    def test_facility_fields(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV)
        petrom = facilities[0]
        assert petrom.facility_id == "E-PRTR-RO-00142"
        assert petrom.name == "OMV Petrom SA Petrobrazi"
        assert petrom.country_code == "RO"
        assert petrom.latitude == pytest.approx(44.9833, abs=1e-4)
        assert petrom.longitude == pytest.approx(26.0167, abs=1e-4)
        assert petrom.nace_code == "19.20"
        assert petrom.seveso_status == "upper"

    def test_country_filter(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV, country_filter={"RO"})
        assert len(facilities) == 2
        assert all(f.country_code == "RO" for f in facilities)

    def test_empty_csv(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV_EMPTY)
        assert facilities == []

    def test_malformed_coordinates(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV_MALFORMED)
        assert len(facilities) == 1
        assert facilities[0].facility_id == "GOOD-001"

    def test_completely_empty_input(self) -> None:
        facilities = parse_eprtr_csv("")
        assert facilities == []

    def test_hazard_categories_assigned(self) -> None:
        facilities = parse_eprtr_csv(SAMPLE_EPRTR_CSV)
        petrom = facilities[0]
        assert "fire" in petrom.hazard_categories
        assert "chemical" in petrom.hazard_categories


class TestClassifyHazard:
    """Test NACE code → hazard category classification."""

    def test_petroleum_refining(self) -> None:
        cats = classify_hazard(nace_code="19.20")
        assert "fire" in cats
        assert "chemical" in cats

    def test_organic_chemicals(self) -> None:
        cats = classify_hazard(nace_code="20.14")
        assert "chemical" in cats
        assert "toxic" in cats
        assert "fire" in cats

    def test_explosives(self) -> None:
        cats = classify_hazard(nace_code="20.51")
        assert "chemical" in cats

    def test_hazardous_waste(self) -> None:
        cats = classify_hazard(nace_code="38.22")
        assert "toxic" in cats

    def test_seveso_upper_with_no_nace(self) -> None:
        cats = classify_hazard(seveso_status="upper")
        assert cats == {"chemical", "toxic", "fire"}

    def test_eprtr_activity_code(self) -> None:
        cats = classify_hazard(eprtr_activity_code="4.1")
        assert "chemical" in cats
        assert "toxic" in cats

    def test_no_classification(self) -> None:
        cats = classify_hazard(nace_code="99.99")
        assert cats == set()

    def test_none_inputs(self) -> None:
        cats = classify_hazard()
        assert cats == set()

    def test_all_nace_codes_in_map(self) -> None:
        for code, expected_cats in NACE_HAZARD_MAP.items():
            cats = classify_hazard(nace_code=code)
            for expected in expected_cats:
                assert expected in cats, f"NACE {code} should have {expected}"


class TestBuildFacilityIndex:
    """Test spatial index construction."""

    def test_build_from_facilities(self) -> None:
        facs = [
            _make_facility(fid="F-001", lat=44.0, lon=26.0),
            _make_facility(fid="F-002", lat=45.0, lon=27.0),
        ]
        index = build_facility_index(facs)
        assert index.facility_count == 2
        assert index.tree is not None

    def test_build_empty(self) -> None:
        index = build_facility_index([])
        assert index.facility_count == 0

    def test_countries_tracked(self) -> None:
        facs = [
            _make_facility(fid="F-001", cc="RO"),
            _make_facility(fid="F-002", cc="HU"),
        ]
        index = build_facility_index(facs)
        assert "HU" in index.countries_loaded
        assert "RO" in index.countries_loaded


class TestQueryFacilitiesInRadius:
    """Test spatial proximity queries."""

    def _build_test_index(self) -> FacilityIndex:
        facs = [
            _make_facility(fid="F-001", name="Near", lat=44.98, lon=26.02),
            _make_facility(fid="F-002", name="Medium", lat=45.05, lon=26.10),
            _make_facility(fid="F-003", name="Far", lat=46.00, lon=27.00),
        ]
        return build_facility_index(facs)

    def test_finds_nearby(self) -> None:
        index = self._build_test_index()
        results = query_facilities_in_radius(44.98, 26.02, index, radius_km=5.0)
        assert len(results) >= 1
        assert results[0][0].name == "Near"
        assert results[0][1] < 1.0

    def test_respects_radius(self) -> None:
        index = self._build_test_index()
        results = query_facilities_in_radius(44.98, 26.02, index, radius_km=1.0)
        names = [f.name for f, _ in results]
        assert "Far" not in names

    def test_sorted_by_distance(self) -> None:
        index = self._build_test_index()
        results = query_facilities_in_radius(44.98, 26.02, index, radius_km=200.0)
        distances = [d for _, d in results]
        assert distances == sorted(distances)

    def test_empty_index(self) -> None:
        index = build_facility_index([])
        results = query_facilities_in_radius(44.0, 26.0, index, radius_km=100.0)
        assert results == []


class TestComputeProximityMetrics:
    """Test proximity metric computation."""

    def _make_facs_with_dist(self) -> list[tuple[IndustrialFacility, float]]:
        return [
            (_make_facility(fid="F-1", name="Close Chemical", hazards={"chemical"}, seveso="upper"), 1.5),
            (_make_facility(fid="F-2", name="Medium Toxic", hazards={"toxic"}, seveso="lower"), 4.0),
            (_make_facility(fid="F-3", name="Far Fire", hazards={"fire"}, seveso="upper"), 8.0),
            (_make_facility(fid="F-4", name="Very Far", hazards={"chemical", "fire"}, seveso=None), 20.0),
        ]

    def test_chemical_proximity(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.chemical is not None
        assert result.chemical.nearest_facility_km == pytest.approx(1.5)
        assert result.chemical.nearest_facility_name == "Close Chemical"
        assert result.chemical.count_within_2km == 1
        assert result.chemical.count_within_5km == 1
        assert result.chemical.count_within_25km == 2

    def test_toxic_proximity(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.toxic is not None
        assert result.toxic.nearest_facility_km == pytest.approx(4.0)
        assert result.toxic.count_within_5km == 1

    def test_fire_proximity(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.fire is not None
        assert result.fire.nearest_facility_km == pytest.approx(8.0)
        assert result.fire.count_within_10km == 1
        assert result.fire.count_within_25km == 2

    def test_epz_assessment(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        epz = result.epz_assessment
        assert epz.seveso_upper_within_5km == 1
        assert epz.seveso_all_within_5km == 2  # upper@1.5km + lower@4.0km
        assert epz.seveso_all_within_16km == 3  # + upper@8.0km
        assert epz.seveso_upper_within_25km == 2

    def test_empty_facilities(self) -> None:
        result = compute_proximity_metrics(44.0, 26.0, [])
        assert result.chemical is not None
        assert result.chemical.nearest_facility_km is None
        assert result.facility_count_total == 0

    def test_all_facilities_list(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert len(result.all_facilities) == 4
        assert all(isinstance(f, NearbyFacility) for f in result.all_facilities)

    def test_upper_tier_counts(self) -> None:
        facs = self._make_facs_with_dist()
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.chemical.upper_tier_within_5km == 1
        assert result.chemical.upper_tier_within_10km == 1


class TestAssessDataQuality:
    """Test data quality assessment logic."""

    def test_eu_country_with_data(self) -> None:
        assert assess_data_quality("RO", 5, ["eprtr"]) == "high"

    def test_eu_country_no_facilities(self) -> None:
        assert assess_data_quality("EE", 0, ["eprtr"]) == "medium"

    def test_partial_country_with_data(self) -> None:
        assert assess_data_quality("RS", 3, ["eprtr"]) == "medium"

    def test_partial_country_no_data(self) -> None:
        assert assess_data_quality("TR", 0, []) == "low"

    def test_no_coverage_country(self) -> None:
        assert assess_data_quality("UA", 0, []) == "insufficient"
        assert assess_data_quality("XK", 0, []) == "insufficient"
        assert assess_data_quality("AM", 0, []) == "insufficient"

    def test_unknown_country(self) -> None:
        assert assess_data_quality("XX", 0, []) == "insufficient"


class TestResultStructure:
    """Test result dataclass structure and serialisation."""

    def test_industrial_proximity_result_to_dict(self) -> None:
        result = IndustrialProximityResult(lat=44.0, lon=26.0, country_code="RO")
        d = result.to_dict()
        assert "lat" in d
        assert "lon" in d
        assert "chemical" in d
        assert "toxic" in d
        assert "fire" in d
        assert "epz_assessment" in d
        assert "quality" in d

    def test_hazard_proximity_to_dict(self) -> None:
        prox = HazardProximity(
            hazard_type="chemical",
            nearest_facility_km=2.5,
            nearest_facility_name="Test",
            count_within_5km=3,
        )
        d = prox.to_dict()
        assert d["hazard_type"] == "chemical"
        assert d["nearest_facility_km"] == 2.5
        assert d["count_within_5km"] == 3

    def test_nearby_facility_to_dict(self) -> None:
        fac = NearbyFacility(
            name="Test", latitude=44.0, longitude=26.0,
            distance_km=5.0, hazard_categories={"fire", "chemical"},
        )
        d = fac.to_dict()
        assert d["name"] == "Test"
        assert d["distance_km"] == 5.0
        assert sorted(d["hazard_categories"]) == ["chemical", "fire"]

    def test_epz_assessment_to_dict(self) -> None:
        epz = EpzIndustrialAssessment(
            seveso_upper_within_5km=2,
            industrial_hazard_density_25km=1.234567,
        )
        d = epz.to_dict()
        assert d["seveso_upper_within_5km"] == 2
        assert d["industrial_hazard_density_25km"] == pytest.approx(1.2346, abs=1e-4)


class TestCriterionIds:
    """Test criterion ID constants."""

    def test_criterion_ids_present(self) -> None:
        assert "chemical" in CRITERION_IDS
        assert "toxic" in CRITERION_IDS
        assert "fire" in CRITERION_IDS
        assert "epz" in CRITERION_IDS

    def test_criterion_id_values(self) -> None:
        assert CRITERION_IDS["chemical"] == "HI-02"
        assert CRITERION_IDS["toxic"] == "HI-03"
        assert CRITERION_IDS["fire"] == "HI-04"
        assert CRITERION_IDS["epz"] == "EP-05"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_facility_at_zero_distance(self) -> None:
        facs = [(_make_facility(lat=44.0, lon=26.0, hazards={"chemical"}), 0.0)]
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.chemical.nearest_facility_km == 0.0
        assert result.chemical.count_within_2km == 1

    def test_facility_at_exact_boundary(self) -> None:
        facs = [(_make_facility(hazards={"toxic"}), 5.0)]
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.toxic.count_within_5km == 1

    def test_null_nearest_facility(self) -> None:
        result = compute_proximity_metrics(44.0, 26.0, [])
        assert result.chemical.nearest_facility_km is None
        assert result.chemical.nearest_facility_name is None

    def test_facility_with_no_hazard_categories(self) -> None:
        fac = IndustrialFacility(
            facility_id="F-EMPTY", name="No Hazard",
            latitude=44.5, longitude=26.0, country_code="RO",
            hazard_categories=set(),
        )
        facs = [(fac, 3.0)]
        result = compute_proximity_metrics(44.0, 26.0, facs)
        assert result.chemical.nearest_facility_km is None
        assert result.toxic.nearest_facility_km is None
        assert result.fire.nearest_facility_km is None
