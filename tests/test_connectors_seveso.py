# man_hours: 3.0
"""Tests for S-12 SEVESO III connector — parsing, merge, and transformation logic."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eea_industrial.models import IndustrialFacility
from atoms_vs_ashes.connectors.eea_industrial.parsers import build_facility_index
from atoms_vs_ashes.connectors.seveso.models import (
    CRITERION_IDS,
    EU_SEVESO_COUNTRIES,
    MergeStats,
    MinervaEstablishment,
    NationalFacility,
)
from atoms_vs_ashes.connectors.seveso.parsers import (
    merge_facilities,
    parse_minerva_csv,
    parse_national_csv,
)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

SAMPLE_MINERVA_CSV = """\
EstablishmentName,Country,Latitude,Longitude,SevesoStatus,Activity
OMV Petrom Petrobrazi Refinery,RO,44.9831,26.0171,Upper tier,Petroleum refining
Chimcomplex Borzesti,RO,46.3670,26.8330,Upper tier,Chemical manufacturing
MOL Danube Refinery,HU,47.1502,18.4170,Upper tier,Petroleum refining
Azomures SA,RO,46.5500,24.5667,Upper tier,Fertilizer production (ammonia)
Oltchim SA,RO,45.1000,24.3667,Upper tier,Chlor-alkali and PVC production
"""

SAMPLE_MINERVA_CSV_FULL_NAMES = """\
EstablishmentName,Country,Latitude,Longitude,SevesoStatus,Activity
Test Plant,Romania,44.5,26.0,Upper tier,Testing
"""

SAMPLE_MINERVA_CSV_EMPTY = """\
EstablishmentName,Country,Latitude,Longitude,SevesoStatus,Activity
"""

SAMPLE_NATIONAL_RS_CSV = """\
name,latitude,longitude,seveso_tier,hazard_categories,activity,source_url
NIS Rafinerija Pancevo,44.8697,20.6403,upper,"explosion;toxic;fire","petroleum refining","https://www.ekologija.gov.rs/"
HIP Petrohemija Pancevo,44.8653,20.6442,upper,"toxic;fire","petrochemical production","https://www.ekologija.gov.rs/"
Messer Tehnogas Beograd,44.8186,20.4681,lower,"explosion","industrial gases","https://www.ekologija.gov.rs/"
"""

SAMPLE_NATIONAL_MALFORMED = """\
name,latitude,longitude,seveso_tier,hazard_categories,activity,source_url
Bad Coords,not_a_number,20.0,upper,"fire","testing","http://example.com"
Good Facility,44.5,20.0,upper,"fire","testing","http://example.com"
"""


def _make_eprtr_facility(
    fid: str = "E-001",
    name: str = "E-PRTR Facility",
    lat: float = 44.9833,
    lon: float = 26.0167,
    cc: str = "RO",
    nace: str = "19.20",
    seveso: str | None = None,
) -> IndustrialFacility:
    return IndustrialFacility(
        facility_id=fid,
        name=name,
        latitude=lat,
        longitude=lon,
        country_code=cc,
        nace_code=nace,
        seveso_status=seveso,
        hazard_categories={"chemical", "fire"},
        source="eprtr",
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestParseMinervaCsv:
    """Test Minerva SEVESO CSV parsing."""

    def test_parse_valid_csv(self) -> None:
        establishments = parse_minerva_csv(SAMPLE_MINERVA_CSV)
        assert len(establishments) == 5

    def test_establishment_fields(self) -> None:
        establishments = parse_minerva_csv(SAMPLE_MINERVA_CSV)
        petrom = establishments[0]
        assert petrom.name == "OMV Petrom Petrobrazi Refinery"
        assert petrom.country_code == "RO"
        assert petrom.latitude == pytest.approx(44.9831, abs=1e-4)
        assert petrom.longitude == pytest.approx(26.0171, abs=1e-4)
        assert petrom.seveso_tier == "upper"
        assert petrom.activity == "Petroleum refining"

    def test_country_filter(self) -> None:
        establishments = parse_minerva_csv(SAMPLE_MINERVA_CSV, country_filter={"HU"})
        assert len(establishments) == 1
        assert establishments[0].country_code == "HU"

    def test_empty_csv(self) -> None:
        establishments = parse_minerva_csv(SAMPLE_MINERVA_CSV_EMPTY)
        assert establishments == []

    def test_full_country_names(self) -> None:
        establishments = parse_minerva_csv(SAMPLE_MINERVA_CSV_FULL_NAMES)
        assert len(establishments) == 1
        assert establishments[0].country_code == "RO"

    def test_empty_input(self) -> None:
        establishments = parse_minerva_csv("")
        assert establishments == []


class TestParseNationalCsv:
    """Test national register CSV parsing."""

    def test_parse_valid_csv(self) -> None:
        facilities = parse_national_csv(SAMPLE_NATIONAL_RS_CSV, "RS")
        assert len(facilities) == 3

    def test_facility_fields(self) -> None:
        facilities = parse_national_csv(SAMPLE_NATIONAL_RS_CSV, "RS")
        pancevo = facilities[0]
        assert pancevo.name == "NIS Rafinerija Pancevo"
        assert pancevo.latitude == pytest.approx(44.8697, abs=1e-4)
        assert pancevo.seveso_tier == "upper"
        assert pancevo.country_code == "RS"

    def test_hazard_categories_parsed(self) -> None:
        facilities = parse_national_csv(SAMPLE_NATIONAL_RS_CSV, "RS")
        pancevo = facilities[0]
        assert "toxic" in pancevo.hazard_categories
        assert "fire" in pancevo.hazard_categories

    def test_malformed_coordinates(self) -> None:
        facilities = parse_national_csv(SAMPLE_NATIONAL_MALFORMED, "RS")
        assert len(facilities) == 1
        assert facilities[0].name == "Good Facility"

    def test_country_code_assigned(self) -> None:
        facilities = parse_national_csv(SAMPLE_NATIONAL_RS_CSV, "RS")
        assert all(f.country_code == "RS" for f in facilities)

    def test_empty_csv(self) -> None:
        facilities = parse_national_csv("name,latitude,longitude,seveso_tier,hazard_categories,activity,source_url\n", "RS")
        assert facilities == []


class TestMergeFacilities:
    """Test three-source facility merge and deduplication."""

    def _make_overlapping_data(self) -> tuple[
        list[IndustrialFacility],
        list[MinervaEstablishment],
        list[NationalFacility],
    ]:
        eprtr = [
            _make_eprtr_facility(
                fid="E-001", name="OMV Petrom Petrobrazi",
                lat=44.9833, lon=26.0167,
            ),
            _make_eprtr_facility(
                fid="E-002", name="Chimcomplex SA Borzesti",
                lat=46.3667, lon=26.8333,
            ),
        ]
        minerva = [
            MinervaEstablishment(
                name="OMV Petrom Petrobrazi",
                country_code="RO", latitude=44.9831, longitude=26.0171,
                seveso_tier="upper", activity="Petroleum refining",
            ),
            MinervaEstablishment(
                name="Azomures SA",
                country_code="RO", latitude=46.5500, longitude=24.5667,
                seveso_tier="upper", activity="Fertilizer production",
            ),
        ]
        national: list[NationalFacility] = []
        return eprtr, minerva, national

    def test_merge_enriches_eprtr_with_minerva(self) -> None:
        eprtr, minerva, national = self._make_overlapping_data()
        merged, stats = merge_facilities(eprtr, minerva, national)
        petrom = next(f for f in merged if "Petrom" in f.name and f.source.startswith("eprtr"))
        assert petrom.seveso_status == "upper"
        assert "minerva" in petrom.source

    def test_merge_adds_unmatched_minerva(self) -> None:
        eprtr, minerva, national = self._make_overlapping_data()
        merged, stats = merge_facilities(eprtr, minerva, national)
        assert stats.minerva_unmatched >= 1
        azomures = [f for f in merged if "Azomures" in f.name]
        assert len(azomures) == 1
        assert azomures[0].source == "minerva"

    def test_merge_stats(self) -> None:
        eprtr, minerva, national = self._make_overlapping_data()
        _, stats = merge_facilities(eprtr, minerva, national)
        assert stats.eprtr_count == 2
        assert stats.minerva_count == 2
        assert stats.merged_total >= 3

    def test_merge_with_national(self) -> None:
        eprtr = [_make_eprtr_facility(fid="E-001", name="Test", lat=44.0, lon=26.0)]
        minerva: list[MinervaEstablishment] = []
        national = [
            NationalFacility(
                name="National Facility",
                latitude=45.0, longitude=27.0,
                seveso_tier="upper",
                hazard_categories={"fire"},
                country_code="RS",
            ),
        ]
        merged, stats = merge_facilities(eprtr, minerva, national)
        assert stats.national_count == 1
        assert any(f.source == "national" for f in merged)

    def test_dedup_removes_close_duplicates(self) -> None:
        eprtr = [_make_eprtr_facility(fid="E-001", name="Test Facility", lat=44.0, lon=26.0)]
        national = [
            NationalFacility(
                name="Test Facility",
                latitude=44.0001, longitude=26.0001,
                seveso_tier="upper",
                hazard_categories={"fire"},
                country_code="RO",
            ),
        ]
        merged, stats = merge_facilities(eprtr, [], national)
        assert stats.duplicates_removed == 1
        assert len(merged) == 1

    def test_merge_empty_inputs(self) -> None:
        merged, stats = merge_facilities([], [], [])
        assert stats.merged_total == 0
        assert merged == []

    def test_merge_stats_to_dict(self) -> None:
        stats = MergeStats(eprtr_count=10, minerva_count=5, merged_total=12)
        d = stats.to_dict()
        assert d["eprtr_count"] == 10
        assert d["merged_total"] == 12


class TestNameSimilarity:
    """Test the Jaccard name similarity function used in deduplication."""

    def test_identical_names(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _name_similarity
        assert _name_similarity("Test Facility", "Test Facility") == pytest.approx(1.0)

    def test_similar_names(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _name_similarity
        sim = _name_similarity("OMV Petrom SA Petrobrazi", "OMV Petrom Petrobrazi Refinery")
        assert sim > 0.5

    def test_different_names(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _name_similarity
        sim = _name_similarity("Alpha Beta Gamma", "Zeta Omega Epsilon")
        assert sim == 0.0

    def test_empty_name(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _name_similarity
        assert _name_similarity("", "Test") == 0.0
        assert _name_similarity("Test", "") == 0.0


class TestNormaliseTier:
    """Test SEVESO tier normalisation."""

    def test_upper_tier(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_tier
        assert _normalise_tier("Upper tier") == "upper"
        assert _normalise_tier("upper") == "upper"
        assert _normalise_tier("UPPER TIER") == "upper"

    def test_lower_tier(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_tier
        assert _normalise_tier("Lower tier") == "lower"
        assert _normalise_tier("lower") == "lower"

    def test_unknown(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_tier
        assert _normalise_tier("") == "unknown"
        assert _normalise_tier("something else") == "unknown"


class TestNormaliseCountry:
    """Test country code normalisation."""

    def test_iso_code(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_country
        assert _normalise_country("RO") == "RO"
        assert _normalise_country("ro") == "RO"

    def test_full_name(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_country
        assert _normalise_country("Romania") == "RO"
        assert _normalise_country("Czech Republic") == "CZ"
        assert _normalise_country("North Macedonia") == "MK"

    def test_empty(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _normalise_country
        assert _normalise_country("") == ""


class TestCriterionIds:
    """Test SEVESO criterion ID constants."""

    def test_criterion_ids(self) -> None:
        assert CRITERION_IDS["chemical"] == "HI-02"
        assert CRITERION_IDS["toxic"] == "HI-03"
        assert CRITERION_IDS["fire"] == "HI-04"
        assert CRITERION_IDS["epz"] == "EP-05"


class TestResultStructure:
    """Test result dataclass structure."""

    def test_minerva_establishment_to_dict(self) -> None:
        est = MinervaEstablishment(
            name="Test", country_code="RO",
            latitude=44.0, longitude=26.0,
            seveso_tier="upper",
        )
        d = est.to_dict()
        assert d["name"] == "Test"
        assert d["seveso_tier"] == "upper"

    def test_national_facility_to_dict(self) -> None:
        fac = NationalFacility(
            name="Test", latitude=44.0, longitude=26.0,
            seveso_tier="upper", hazard_categories={"fire", "toxic"},
            country_code="RS",
        )
        d = fac.to_dict()
        assert d["country_code"] == "RS"
        assert sorted(d["hazard_categories"]) == ["fire", "toxic"]

    def test_batch_result_summary(self) -> None:
        from atoms_vs_ashes.connectors.seveso.models import BatchResult
        batch = BatchResult(
            run_id="test", total_sites=10,
            succeeded=8, failed=1, skipped_cached=1,
            elapsed_s=5.5,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line


class TestParseHazardCategories:
    """Test hazard category string parsing."""

    def test_semicolon_separated(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _parse_hazard_categories
        cats = _parse_hazard_categories("explosion;toxic;fire")
        assert "toxic" in cats
        assert "fire" in cats

    def test_empty_string(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _parse_hazard_categories
        cats = _parse_hazard_categories("")
        assert cats == set()

    def test_invalid_categories_filtered(self) -> None:
        from atoms_vs_ashes.connectors.seveso.parsers import _parse_hazard_categories
        cats = _parse_hazard_categories("fire;invalid;toxic")
        assert "fire" in cats
        assert "toxic" in cats
        assert "invalid" not in cats
