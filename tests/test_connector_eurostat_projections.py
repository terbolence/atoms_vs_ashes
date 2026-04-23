# man_hours: 3.0
"""Unit tests for S-17 Eurostat Demographic Projections connector.

Pure tests — no network, no database. All tests use inline fixture data
matching the JSON-stat 2.0 format returned by the Eurostat Statistics API.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from atoms_vs_ashes.connectors.eurostat_projections.models import (
    CRITERION_IDS,
    IN_SCOPE_CANDIDATE,
    IN_SCOPE_EU,
    IN_SCOPE_NON_EU,
    NsoProjection,
    PolicyProxyResult,
    PopulationProjectionResult,
    SocioeconomicResult,
    WorkforceResult,
    EurostatProjectionsResult,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.eurostat_projections.parsers import (
    classify_growth,
    compute_deprivation_index,
    compute_growth_trajectory,
    compute_pop_change_pct_per_decade,
    compute_receptor_growth_factor,
    compute_retraining_pool_index,
    compute_urban_expansion_pressure,
    parse_jsonstat_indicators,
    parse_jsonstat_projection,
    parse_jsonstat_tabular,
    parse_jsonstat_employment,
    parse_nso_supplement,
)


# ---------------------------------------------------------------------------
# Fixtures (inline — no network)
# ---------------------------------------------------------------------------

SAMPLE_NATIONAL_PROJECTION_JSONSTAT: dict[str, Any] = {
    "version": "2.0",
    "class": "dataset",
    "label": "Population on 1st January by age, sex and type of projection",
    "id": ["projection", "freq", "sex", "age", "geo", "time"],
    "size": [1, 1, 1, 1, 2, 3],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "sex": {"category": {"index": {"T": 0}}},
        "age": {"category": {"index": {"TOTAL": 0}}},
        "geo": {"category": {"index": {"RO": 0, "BG": 1}}},
        "time": {"category": {"index": {"2030": 0, "2050": 1, "2080": 2}}},
    },
    "value": [
        18800000, 17200000, 14100000,
        6200000,  5400000,  4100000,
    ],
}

SAMPLE_INDICATORS_JSONSTAT: dict[str, Any] = {
    "version": "2.0",
    "class": "dataset",
    "label": "Demographic balances and indicators by type of projection",
    "id": ["projection", "freq", "indic_de", "geo", "time"],
    "size": [1, 1, 3, 1, 2],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "indic_de": {"category": {"index": {"MEDAGEPOP": 0, "OLDDEP": 1, "GROWRT": 2}}},
        "geo": {"category": {"index": {"RO": 0}}},
        "time": {"category": {"index": {"2050": 0, "2080": 1}}},
    },
    "value": [
        49.8, 53.2,
        0.48, 0.56,
        -0.45, -0.38,
    ],
}

SAMPLE_REGIONAL_PROJECTION_JSONSTAT: dict[str, Any] = {
    "version": "2.0",
    "class": "dataset",
    "label": "Population on 1 January by age, sex, type of projection and NUTS 3 region",
    "id": ["projection", "freq", "sex", "age", "geo", "time"],
    "size": [1, 1, 1, 1, 2, 2],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "sex": {"category": {"index": {"T": 0}}},
        "age": {"category": {"index": {"TOTAL": 0}}},
        "geo": {"category": {"index": {"RO411": 0, "RO414": 1}}},
        "time": {"category": {"index": {"2030": 0, "2050": 1}}},
    },
    "value": [
        620000, 540000,
        380000, 310000,
    ],
}

SAMPLE_NSO_SUPPLEMENT: dict[str, Any] = {
    "country_code": "UA",
    "country_name": "Ukraine",
    "source": "UN World Population Prospects 2024 (medium variant)",
    "source_url": "https://population.un.org/wpp/",
    "retrieved_date": "2026-03-15",
    "projection_variant": "medium",
    "base_year": 2023,
    "projections": {
        "2030": {"population": 36500000, "growth_rate": -0.008},
        "2040": {"population": 33200000, "growth_rate": -0.009},
        "2050": {"population": 30100000, "growth_rate": -0.010},
        "2060": {"population": 27500000, "growth_rate": -0.009},
        "2080": {"population": 23800000, "growth_rate": -0.007},
    },
    "median_age_2050": 48.2,
    "old_age_dependency_2050": 0.42,
    "quality_note": "Based on UN WPP 2024 medium variant",
}

SAMPLE_TABULAR_JSONSTAT: dict[str, Any] = {
    "version": "2.0",
    "class": "dataset",
    "id": ["unit", "geo", "time"],
    "size": [1, 2, 1],
    "dimension": {
        "unit": {"category": {"index": {"EUR_HAB": 0}}},
        "geo": {"category": {"index": {"RO411": 0, "RO41": 1}}},
        "time": {"category": {"index": {"2022": 0}}},
    },
    "value": [7800.0, 8200.0],
}

SAMPLE_EMPLOYMENT_JSONSTAT: dict[str, Any] = {
    "version": "2.0",
    "class": "dataset",
    "id": ["sex", "age", "nace_r2", "geo", "time"],
    "size": [1, 1, 4, 1, 1],
    "dimension": {
        "sex": {"category": {"index": {"T": 0}}},
        "age": {"category": {"index": {"Y15-64": 0}}},
        "nace_r2": {"category": {"index": {"TOTAL": 0, "B-E": 1, "F": 2, "D": 3}}},
        "geo": {"category": {"index": {"RO41": 0}}},
        "time": {"category": {"index": {"2023": 0}}},
    },
    "value": [1000000, 280000, 75000, 42000],
}


# ---------------------------------------------------------------------------
# DB compatibility (static — no DB)
# ---------------------------------------------------------------------------

class TestCriteriaSeedCompleteness:
    def test_criterion_ids_declared(self) -> None:
        assert CRITERION_IDS == ("RI-06", "NS-09", "NS-10", "NS-12")

    def test_criterion_ids_count(self) -> None:
        assert len(CRITERION_IDS) == 4

    def test_ri06_in_criterion_ids(self) -> None:
        assert "RI-06" in CRITERION_IDS

    def test_ns09_in_criterion_ids(self) -> None:
        assert "NS-09" in CRITERION_IDS

    def test_ns10_in_criterion_ids(self) -> None:
        assert "NS-10" in CRITERION_IDS

    def test_ns12_in_criterion_ids(self) -> None:
        assert "NS-12" in CRITERION_IDS


# ---------------------------------------------------------------------------
# JSON-stat parsing
# ---------------------------------------------------------------------------

class TestParseJsonstatProjection:
    def test_basic_parse(self) -> None:
        result = parse_jsonstat_projection(SAMPLE_NATIONAL_PROJECTION_JSONSTAT)
        assert "RO" in result
        assert "BG" in result

    def test_ro_projections(self) -> None:
        result = parse_jsonstat_projection(SAMPLE_NATIONAL_PROJECTION_JSONSTAT)
        assert result["RO"]["2030"] == pytest.approx(18_800_000)
        assert result["RO"]["2050"] == pytest.approx(17_200_000)
        assert result["RO"]["2080"] == pytest.approx(14_100_000)

    def test_bg_projections(self) -> None:
        result = parse_jsonstat_projection(SAMPLE_NATIONAL_PROJECTION_JSONSTAT)
        assert result["BG"]["2030"] == pytest.approx(6_200_000)
        assert result["BG"]["2050"] == pytest.approx(5_400_000)
        assert result["BG"]["2080"] == pytest.approx(4_100_000)

    def test_regional_projections(self) -> None:
        result = parse_jsonstat_projection(SAMPLE_REGIONAL_PROJECTION_JSONSTAT)
        assert "RO411" in result
        assert "RO414" in result
        assert result["RO411"]["2030"] == pytest.approx(620_000)
        assert result["RO411"]["2050"] == pytest.approx(540_000)
        assert result["RO414"]["2030"] == pytest.approx(380_000)

    def test_empty_dataset_returns_empty(self) -> None:
        result = parse_jsonstat_projection({})
        assert result == {}

    def test_wrong_class_returns_empty(self) -> None:
        result = parse_jsonstat_projection({"class": "collection"})
        assert result == {}


class TestParseJsonstatIndicators:
    def test_basic_parse(self) -> None:
        result = parse_jsonstat_indicators(SAMPLE_INDICATORS_JSONSTAT)
        assert "RO" in result

    def test_median_age(self) -> None:
        result = parse_jsonstat_indicators(SAMPLE_INDICATORS_JSONSTAT)
        # Parser takes the most recent year (2080) → 53.2
        assert result["RO"]["MEDAGEPOP"] == pytest.approx(53.2)

    def test_old_age_dependency(self) -> None:
        result = parse_jsonstat_indicators(SAMPLE_INDICATORS_JSONSTAT)
        # Parser takes the most recent year (2080) → 0.56
        assert result["RO"]["OLDDEP"] == pytest.approx(0.56)

    def test_growth_rate(self) -> None:
        result = parse_jsonstat_indicators(SAMPLE_INDICATORS_JSONSTAT)
        # Parser takes the most recent year (2080) → -0.38
        assert result["RO"]["GROWRT"] == pytest.approx(-0.38)

    def test_empty_dataset_returns_empty(self) -> None:
        result = parse_jsonstat_indicators({})
        assert result == {}


class TestParseJsonstatTabular:
    def test_basic_parse(self) -> None:
        result = parse_jsonstat_tabular(SAMPLE_TABULAR_JSONSTAT)
        assert "RO411" in result
        assert result["RO411"] == pytest.approx(7800.0)
        assert result["RO41"] == pytest.approx(8200.0)

    def test_empty_returns_empty(self) -> None:
        result = parse_jsonstat_tabular({})
        assert result == {}


class TestParseJsonstatEmployment:
    def test_basic_parse(self) -> None:
        result = parse_jsonstat_employment(SAMPLE_EMPLOYMENT_JSONSTAT)
        assert "RO41" in result

    def test_industry_pct(self) -> None:
        result = parse_jsonstat_employment(SAMPLE_EMPLOYMENT_JSONSTAT)
        ro41 = result["RO41"]
        assert ro41["B-E"] == pytest.approx(28.0, abs=1.0)

    def test_energy_pct(self) -> None:
        result = parse_jsonstat_employment(SAMPLE_EMPLOYMENT_JSONSTAT)
        ro41 = result["RO41"]
        assert ro41["D"] == pytest.approx(4.2, abs=0.5)

    def test_total_retained(self) -> None:
        result = parse_jsonstat_employment(SAMPLE_EMPLOYMENT_JSONSTAT)
        assert result["RO41"]["TOTAL"] == pytest.approx(1_000_000)


# ---------------------------------------------------------------------------
# NSO supplement parsing
# ---------------------------------------------------------------------------

class TestParseNsoSupplement:
    def test_basic_parse(self) -> None:
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        assert nso is not None
        assert nso.country_code == "UA"
        assert nso.base_year == 2023

    def test_projection_years(self) -> None:
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        assert nso.population_at(2050) == 30_100_000
        assert nso.population_at(2080) == 23_800_000

    def test_growth_rate_access(self) -> None:
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        assert nso.growth_rate_at(2050) == pytest.approx(-0.010)

    def test_missing_required_field_returns_none(self) -> None:
        bad_data = {k: v for k, v in SAMPLE_NSO_SUPPLEMENT.items() if k != "country_code"}
        result = parse_nso_supplement(bad_data)
        assert result is None

    def test_demographic_indicators(self) -> None:
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        assert nso.median_age_2050 == pytest.approx(48.2)
        assert nso.old_age_dependency_2050 == pytest.approx(0.42)

    def test_missing_year_returns_none(self) -> None:
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        assert nso.population_at(2090) is None


# ---------------------------------------------------------------------------
# Computation functions
# ---------------------------------------------------------------------------

class TestComputeGrowthTrajectory:
    def test_with_regional_projection(self) -> None:
        national = {"2030": 18800000.0, "2050": 17200000.0, "2080": 14100000.0}
        regional = {"2030": 620000.0, "2050": 540000.0}
        trajectory = compute_growth_trajectory(national, regional, 19000000, 660000)
        assert "2030" in trajectory
        assert "2050" in trajectory
        assert "2080" in trajectory
        assert trajectory["2030"] == 620000
        assert trajectory["2050"] == 540000

    def test_extrapolation_beyond_regional_horizon(self) -> None:
        national = {"2030": 18800000.0, "2050": 17200000.0, "2080": 14100000.0}
        regional = {"2030": 620000.0, "2050": 540000.0}
        trajectory = compute_growth_trajectory(national, regional, 18800000, 620000)
        assert "2080" in trajectory
        national_factor = 14100000 / 17200000
        expected_2080 = round(540000 * national_factor)
        assert trajectory["2080"] == pytest.approx(expected_2080, abs=1)

    def test_national_only_with_regional_base(self) -> None:
        national = {"2030": 18800000.0, "2050": 17200000.0, "2080": 14100000.0}
        trajectory = compute_growth_trajectory(national, None, 19000000, 660000)
        share = 660000 / 19000000
        assert trajectory["2050"] == round(17200000 * share)

    def test_national_only_no_regional_base(self) -> None:
        national = {"2030": 18800000.0, "2050": 17200000.0}
        trajectory = compute_growth_trajectory(national, None, 19000000, None)
        assert trajectory["2050"] == 17200000

    def test_empty_national_returns_empty(self) -> None:
        trajectory = compute_growth_trajectory({}, None, 19000000, None)
        assert trajectory == {}


class TestClassifyGrowth:
    def test_rapid_growth(self) -> None:
        assert classify_growth(6.0) == "rapid_growth"
        assert classify_growth(5.01) == "rapid_growth"

    def test_moderate_growth(self) -> None:
        assert classify_growth(1.01) == "moderate_growth"
        assert classify_growth(4.99) == "moderate_growth"
        assert classify_growth(5.0) == "moderate_growth"

    def test_stable(self) -> None:
        assert classify_growth(0.0) == "stable"
        assert classify_growth(0.5) == "stable"
        assert classify_growth(-0.5) == "stable"
        assert classify_growth(1.0) == "stable"

    def test_moderate_decline(self) -> None:
        assert classify_growth(-1.01) == "moderate_decline"
        assert classify_growth(-4.99) == "moderate_decline"

    def test_rapid_decline(self) -> None:
        assert classify_growth(-5.0) == "rapid_decline"
        assert classify_growth(-10.0) == "rapid_decline"


class TestComputeReceptorGrowthFactor:
    def test_growing_population(self) -> None:
        rgf = compute_receptor_growth_factor(10_000_000, 12_000_000)
        assert rgf == pytest.approx(1.2)

    def test_declining_population(self) -> None:
        rgf = compute_receptor_growth_factor(10_000_000, 6_360_000)
        assert rgf == pytest.approx(0.636, abs=0.001)

    def test_zero_base_returns_one(self) -> None:
        rgf = compute_receptor_growth_factor(0, 10_000_000)
        assert rgf == pytest.approx(1.0)

    def test_stable_population(self) -> None:
        rgf = compute_receptor_growth_factor(5_000_000, 5_000_000)
        assert rgf == pytest.approx(1.0)


class TestComputeUrbanExpansionPressure:
    def test_faster_than_national(self) -> None:
        pressure = compute_urban_expansion_pressure(2.0, -0.5)
        assert pressure == pytest.approx(2.5)

    def test_slower_than_national(self) -> None:
        pressure = compute_urban_expansion_pressure(-2.0, 0.5)
        assert pressure == pytest.approx(-2.5)

    def test_equal_returns_zero(self) -> None:
        pressure = compute_urban_expansion_pressure(1.0, 1.0)
        assert pressure == pytest.approx(0.0)


class TestComputeRetrainingPoolIndex:
    def test_coal_region_high_index(self) -> None:
        idx = compute_retraining_pool_index(
            employment_industry_pct=35.0,
            employment_energy_pct=5.0,
            employment_construction_pct=10.0,
            unemployment_rate_pct=12.0,
        )
        assert 0.7 <= idx <= 1.0

    def test_service_region_low_index(self) -> None:
        idx = compute_retraining_pool_index(
            employment_industry_pct=5.0,
            employment_energy_pct=0.5,
            employment_construction_pct=2.0,
            unemployment_rate_pct=3.0,
        )
        assert idx < 0.3

    def test_none_inputs_handled(self) -> None:
        idx = compute_retraining_pool_index(None, None, None, None)
        assert idx == pytest.approx(0.0)

    def test_index_bounded_0_1(self) -> None:
        idx = compute_retraining_pool_index(100.0, 100.0, 100.0, 100.0)
        assert 0.0 <= idx <= 1.0


class TestComputeDeprivationIndex:
    def test_high_deprivation(self) -> None:
        idx = compute_deprivation_index(
            gdp_gap_to_national_pct=-50.0,
            unemployment_rate_pct=18.0,
            tertiary_education_pct=10.0,
        )
        assert idx > 0.6

    def test_low_deprivation(self) -> None:
        idx = compute_deprivation_index(
            gdp_gap_to_national_pct=20.0,
            unemployment_rate_pct=3.0,
            tertiary_education_pct=45.0,
        )
        assert idx < 0.2

    def test_none_inputs_handled(self) -> None:
        idx = compute_deprivation_index(None, None, None)
        assert 0.0 <= idx <= 1.0

    def test_index_bounded_0_1(self) -> None:
        idx = compute_deprivation_index(-100.0, 50.0, 0.0)
        assert 0.0 <= idx <= 1.0


class TestComputePopChangePctPerDecade:
    def test_declining(self) -> None:
        pct = compute_pop_change_pct_per_decade(19000000, 17200000, 2022, 2050)
        assert pct is not None
        assert pct < 0

    def test_growing(self) -> None:
        pct = compute_pop_change_pct_per_decade(10000000, 12000000, 2022, 2050)
        assert pct is not None
        assert pct > 0

    def test_zero_base_returns_none(self) -> None:
        pct = compute_pop_change_pct_per_decade(0, 12000000, 2022, 2050)
        assert pct is None

    def test_same_year_returns_none(self) -> None:
        pct = compute_pop_change_pct_per_decade(10000000, 12000000, 2022, 2022)
        assert pct is None


# ---------------------------------------------------------------------------
# Model dataclass tests
# ---------------------------------------------------------------------------

class TestResultStructure:
    def test_population_projection_to_dict(self) -> None:
        pp = PopulationProjectionResult(
            base_population=19_000_000,
            base_year=2022,
            projected_pop_2050=17_200_000,
            growth_classification="moderate_decline",
            receptor_growth_factor_60yr=0.636,
        )
        d = pp.to_dict()
        assert d["base_population"] == 19_000_000
        assert d["growth_classification"] == "moderate_decline"
        assert d["projected_pop_2050"] == 17_200_000
        assert "projection_source" in d

    def test_socioeconomic_to_dict(self) -> None:
        se = SocioeconomicResult(
            nuts3_gdp_per_capita_eur=7800.0,
            gdp_gap_to_national_pct=-47.7,
        )
        d = se.to_dict()
        assert d["nuts3_gdp_per_capita_eur"] == 7800.0
        assert "deprivation_index" in d

    def test_workforce_to_dict(self) -> None:
        wf = WorkforceResult(
            working_age_pop=410_000,
            employment_energy_pct=4.2,
            retraining_pool_index=0.55,
        )
        d = wf.to_dict()
        assert d["working_age_pop"] == 410_000
        assert d["employment_energy_pct"] == 4.2

    def test_policy_proxy_to_dict(self) -> None:
        pp = PolicyProxyResult(
            nuclear_policy_stance="favourable",
            energy_sector_dependence=0.042,
        )
        d = pp.to_dict()
        assert d["nuclear_policy_stance"] == "favourable"
        assert d["policy_source"] == "curated_2026"

    def test_result_to_dict_complete(self) -> None:
        result = EurostatProjectionsResult(
            lat=44.15, lon=23.12,
            country_code="RO",
            nuts3_code="RO411",
            nuts2_code="RO41",
            quality="high",
        )
        d = result.to_dict()
        assert d["lat"] == 44.15
        assert d["lon"] == 23.12
        assert d["country_code"] == "RO"
        assert d["nuts3_code"] == "RO411"
        assert "quality" in d
        assert "error" in d

    def test_batch_result_summary_line(self) -> None:
        batch = BatchResult(
            run_id="test-run",
            total_sites=10,
            succeeded=8,
            failed=1,
            skipped_cached=1,
            elapsed_s=5.0,
        )
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line


# ---------------------------------------------------------------------------
# Connector unit tests (no HTTP)
# ---------------------------------------------------------------------------

class TestConnectorDefaults:
    def test_instantiate_no_settings(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        assert c._api_url.startswith("https://")
        assert c._timeout == 30
        assert not c.data_loaded()
        c.close()

    def test_instantiate_with_none_settings(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector(None)
        assert c._delay == 0.5
        c.close()

    def test_nuclear_policy_defaults_populated(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        assert c._nuclear_policy["PL"] == "favourable"
        assert c._nuclear_policy["AT"] == "unfavourable"
        assert c._nuclear_policy["SI"] == "neutral"
        c.close()


class TestCountryGrouping:
    def test_eu12_in_scope(self) -> None:
        for cc in ["PL", "RO", "BG", "HU", "CZ", "SK", "AT", "SI", "HR", "EE", "LV", "LT"]:
            assert cc in IN_SCOPE_EU, f"{cc} should be in IN_SCOPE_EU"

    def test_candidate_in_scope(self) -> None:
        for cc in ["TR", "RS", "ME", "MK", "AL"]:
            assert cc in IN_SCOPE_CANDIDATE

    def test_non_eu_in_scope(self) -> None:
        for cc in ["BA", "XK", "MD", "UA", "BY", "AM"]:
            assert cc in IN_SCOPE_NON_EU

    def test_groups_are_disjoint(self) -> None:
        assert len(IN_SCOPE_EU & IN_SCOPE_CANDIDATE) == 0
        assert len(IN_SCOPE_EU & IN_SCOPE_NON_EU) == 0
        assert len(IN_SCOPE_CANDIDATE & IN_SCOPE_NON_EU) == 0


class TestNsoLoading:
    def test_load_nso_supplements_from_fixture(self, tmp_path: Path) -> None:
        """Connector loads NSO supplements from the configured directory."""
        nso_dir = tmp_path / "nso_projections"
        nso_dir.mkdir()
        (nso_dir / "UA.json").write_text(json.dumps(SAMPLE_NSO_SUPPLEMENT))

        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        c._nso_dir = nso_dir
        supplements = c._load_nso_supplements()
        assert "UA" in supplements
        assert supplements["UA"].country_code == "UA"
        c.close()

    def test_invalid_nso_json_skipped(self, tmp_path: Path) -> None:
        nso_dir = tmp_path / "nso_projections"
        nso_dir.mkdir()
        (nso_dir / "XX.json").write_text("{invalid json}")

        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        c._nso_dir = nso_dir
        supplements = c._load_nso_supplements()
        assert "XX" not in supplements
        c.close()

    def test_missing_required_field_skipped(self, tmp_path: Path) -> None:
        nso_dir = tmp_path / "nso_projections"
        nso_dir.mkdir()
        bad = {k: v for k, v in SAMPLE_NSO_SUPPLEMENT.items() if k != "base_year"}
        (nso_dir / "UA.json").write_text(json.dumps(bad))

        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        c._nso_dir = nso_dir
        supplements = c._load_nso_supplements()
        assert "UA" not in supplements
        c.close()


class TestFetchNsoSite:
    """Test fetch() for non-EU countries using preloaded NSO data."""

    def test_fetch_ukraine_nso(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        from atoms_vs_ashes.connectors.eurostat_projections.parsers import (
            parse_nso_supplement,
        )

        c = EurostatProjectionsConnector()
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        c._nso_supplements = {"UA": nso}
        c._data_loaded = True

        result = c.fetch(50.45, 30.52, country_code="UA")
        assert result.quality == "low"
        assert result.country_code == "UA"
        assert result.population_projection is not None
        assert result.population_projection.projected_pop_2050 == 30_100_000
        c.close()

    def test_fetch_missing_nso_returns_insufficient(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        c = EurostatProjectionsConnector()
        c._data_loaded = True

        result = c.fetch(41.3, 19.8, country_code="AL")
        assert result.quality == "insufficient"
        assert result.population_projection is None
        c.close()

    def test_policy_proxy_always_present(self) -> None:
        from atoms_vs_ashes.connectors.eurostat_projections.client import (
            EurostatProjectionsConnector,
        )
        from atoms_vs_ashes.connectors.eurostat_projections.parsers import (
            parse_nso_supplement,
        )
        c = EurostatProjectionsConnector()
        nso = parse_nso_supplement(SAMPLE_NSO_SUPPLEMENT)
        c._nso_supplements = {"UA": nso}
        c._data_loaded = True

        result = c.fetch(50.45, 30.52, country_code="UA")
        assert result.policy_proxy is not None
        assert result.policy_proxy.nuclear_policy_stance == "favourable"
        c.close()


class TestValidation:
    def test_growth_factor_plausibility_range(self) -> None:
        rgf_decline = compute_receptor_growth_factor(10_000_000, 4_000_000)
        assert 0.3 <= rgf_decline <= 3.0, "RGF outside plausibility range"

        rgf_growth = compute_receptor_growth_factor(10_000_000, 25_000_000)
        assert 0.3 <= rgf_growth <= 3.0, "RGF outside plausibility range"

    def test_deprivation_bounded(self) -> None:
        for gdp in [-80, -40, 0, 20]:
            for unemp in [0, 5, 15, 30]:
                for edu in [5, 20, 40, 70]:
                    idx = compute_deprivation_index(gdp, unemp, edu)
                    assert 0.0 <= idx <= 1.0

    def test_retraining_bounded(self) -> None:
        for ind in [0, 15, 30, 50]:
            for ene in [0, 2.5, 5, 10]:
                for con in [0, 5, 10, 20]:
                    for unemp in [0, 5, 15, 30]:
                        idx = compute_retraining_pool_index(ind, ene, con, unemp)
                        assert 0.0 <= idx <= 1.0
