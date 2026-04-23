# man_hours: 1.0
"""Smoke tests for S-17 Eurostat Demographic Projections connector.

These tests make LIVE API calls to the Eurostat Statistics API and are
therefore tagged with @pytest.mark.smoke.

Run only when explicitly opted in:
    pytest tests/test_smoke_eurostat_projections.py -m smoke -v

H7 batch validation steps 1-3:
  Step 1: Dry run / health check        → test_health_check
  Step 2: Single country sample         → test_ingest_single_country
  Step 3: 3 EU countries enrichment     → test_fetch_three_eu_countries
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.eurostat_projections import (
    EurostatProjectionsConnector,
)
from atoms_vs_ashes.connectors.eurostat_projections.models import (
    IN_SCOPE_EU,
)


@pytest.mark.smoke
class TestEurostatProjectionsSmoke:
    """Live API smoke tests for S-17 connector."""

    def test_health_check(self) -> None:
        """H7-Step-1: Verify Eurostat Statistics API is reachable."""
        with EurostatProjectionsConnector() as connector:
            ok = connector.health_check()
            assert ok, "Eurostat Statistics API health check failed"

    def test_fetch_national_projections_romania(self) -> None:
        """Query proj_23np for Romania (single country probe)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with EurostatProjectionsConnector() as connector:
                connector._cache_dir = __import__("pathlib").Path(tmp)
                result = connector._load_or_fetch_national_projections(
                    ["RO"], ["2030", "2050", "2080"], "BSL",
                )
            assert "RO" in result, "Romania not in national projection results"
            ro = result["RO"]
            assert "2050" in ro, "Year 2050 not in Romania projection"
            assert ro["2050"] > 5_000_000, "Romania 2050 population too low"
            assert ro["2050"] < 30_000_000, "Romania 2050 population too high"

    def test_fetch_national_indicators_romania(self) -> None:
        """Query proj_23ndbi demographic indicators for Romania."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with EurostatProjectionsConnector() as connector:
                connector._cache_dir = __import__("pathlib").Path(tmp)
                result = connector._load_or_fetch_national_indicators(
                    ["RO"], ["2050"], ["MEDAGEPOP", "OLDDEP"],
                )
            assert "RO" in result
            assert result["RO"] is not None

    def test_ingest_single_country(self) -> None:
        """H7-Step-2: Ingest projections for Romania only (quick probe)."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmp:
            with EurostatProjectionsConnector() as connector:
                connector._cache_dir = __import__("pathlib").Path(tmp) / "projections"
                connector._nso_dir = __import__("pathlib").Path(tmp) / "nso"
                connector._cache_dir.mkdir(parents=True)
                connector._nso_dir.mkdir(parents=True)

                connector._national_bsl = connector._load_or_fetch_national_projections(
                    ["RO"], ["2030", "2050", "2080"], "BSL",
                )
                connector._data_loaded = True

                result = connector.fetch(44.15, 23.12, country_code="RO")
                assert result.country_code == "RO"
                assert result.population_projection is not None
                pp = result.population_projection
                assert pp.projected_pop_2050 is not None
                assert pp.projected_pop_2050 > 5_000_000

    def test_fetch_three_eu_countries(self) -> None:
        """H7-Step-3: Ingest + fetch for 3 EU countries (RO, BG, PL)."""
        import tempfile

        countries = ["RO", "BG", "PL"]
        with tempfile.TemporaryDirectory() as tmp:
            with EurostatProjectionsConnector() as connector:
                connector._cache_dir = __import__("pathlib").Path(tmp) / "projections"
                connector._nso_dir = __import__("pathlib").Path(tmp) / "nso"
                connector._cache_dir.mkdir(parents=True)
                connector._nso_dir.mkdir(parents=True)

                connector._national_bsl = connector._load_or_fetch_national_projections(
                    countries, ["2030", "2050", "2080"], "BSL",
                )
                connector._data_loaded = True

                test_coords = [
                    ("RO", 44.15, 23.12),
                    ("BG", 42.70, 23.32),
                    ("PL", 51.07, 17.02),
                ]

                for cc, lat, lon in test_coords:
                    result = connector.fetch(lat, lon, country_code=cc)
                    assert result.country_code == cc, f"Wrong country for {cc}"
                    assert result.quality in {"high", "medium"}, \
                        f"Unexpected quality {result.quality} for {cc}"
                    assert result.population_projection is not None, \
                        f"No population projection for {cc}"

    def test_fetch_nso_country_ukraine(self) -> None:
        """Verify NSO supplement loads for Ukraine and produces low-quality result."""
        import json
        import tempfile

        ua_data = {
            "country_code": "UA",
            "country_name": "Ukraine",
            "source": "UN World Population Prospects 2024 (medium variant)",
            "source_url": "https://population.un.org/wpp/",
            "retrieved_date": "2026-03-15",
            "projection_variant": "medium",
            "base_year": 2023,
            "projections": {
                "2030": {"population": 36500000, "growth_rate": -0.008},
                "2050": {"population": 30100000, "growth_rate": -0.010},
                "2080": {"population": 23800000, "growth_rate": -0.007},
            },
            "median_age_2050": 48.2,
            "old_age_dependency_2050": 0.42,
            "quality_note": "Based on UN WPP 2024 medium variant",
        }
        with tempfile.TemporaryDirectory() as tmp:
            nso_path = __import__("pathlib").Path(tmp)
            (nso_path / "UA.json").write_text(json.dumps(ua_data))

            with EurostatProjectionsConnector() as connector:
                connector._nso_dir = nso_path
                connector._data_loaded = True
                supplements = connector._load_nso_supplements()
                connector._nso_supplements = supplements

                result = connector.fetch(50.45, 30.52, country_code="UA")
                assert result.quality == "low"
                assert result.population_projection is not None
                assert result.population_projection.projected_pop_2050 == 30_100_000

    def test_policy_proxy_all_in_scope_countries(self) -> None:
        """Policy stance is configured for all 23 in-scope countries."""
        with EurostatProjectionsConnector() as connector:
            connector._data_loaded = True

            from atoms_vs_ashes.connectors.eurostat_projections.models import (
                IN_SCOPE_ALL,
            )

            for cc in IN_SCOPE_ALL:
                result = connector.fetch(0.0, 0.0, country_code=cc)
                if result.policy_proxy:
                    assert result.policy_proxy.nuclear_policy_stance in {
                        "favourable", "neutral", "unfavourable",
                        "moratorium", "phaseout", "unknown",
                    }, f"Invalid policy stance for {cc}: {result.policy_proxy.nuclear_policy_stance}"
