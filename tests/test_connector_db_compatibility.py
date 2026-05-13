# man_hours: 4.1
"""Verify that connector persist logic writes to the new domain tables.

Two test layers:
1. Static: parse all Alembic seed migrations and confirm all 46 criteria
   are seeded.
2. Live DB (skipped when no database): create a test site, call the
   connector's persist logic with mock data, and verify domain-table
   rows are written without FK violations.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers — extract seeded criterion IDs from Alembic migrations
# ---------------------------------------------------------------------------

_ALEMBIC_DIR = Path(__file__).resolve().parents[1] / "src" / "alembic" / "versions"
_CRITERION_ID_RE = re.compile(r'"criterion_id"\s*:\s*"([A-Z]{1,2}-\d{2})"')


def _seeded_criterion_ids() -> set[str]:
    """Scan all Alembic migration files for criterion_id seed values."""
    ids: set[str] = set()
    for path in sorted(_ALEMBIC_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        ids.update(_CRITERION_ID_RE.findall(text))
    return ids


# ===================================================================
# Static tests — no DB required
# ===================================================================


class TestCriteriaSeedCompleteness:
    """All 46 criteria from requirements must be seeded in Alembic."""

    _seeded = _seeded_criterion_ids()

    def test_seed_migration_has_all_46_criteria(self):
        expected = set()
        for prefix, count in [("NH", 14), ("HI", 8), ("RI", 6), ("EP", 5), ("NS", 13)]:
            for i in range(1, count + 1):
                expected.add(f"{prefix}-{i:02d}")
        not_found = expected - self._seeded
        assert not not_found, (
            f"Criteria from requirements doc not seeded: {sorted(not_found)}"
        )

    def test_no_duplicate_seeds_across_migrations(self):
        """Each criterion_id should appear in exactly one migration."""
        seen: dict[str, list[str]] = {}
        for path in sorted(_ALEMBIC_DIR.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for cid in _CRITERION_ID_RE.findall(text):
                seen.setdefault(cid, []).append(path.name)
        duplicates = {cid: files for cid, files in seen.items() if len(files) > 1}
        assert not duplicates, (
            f"Criterion IDs seeded in multiple migrations: {duplicates}"
        )


# ===================================================================
# Live-DB integration tests — skipped when database is unavailable
# ===================================================================


class TestConnectorPersistLiveDB:
    """Verify that connector persist functions can write to a real DB
    without FK violations on the new domain tables."""

    @pytest.fixture(autouse=True)
    def _require_db(self):
        """Skip entire class when database is not reachable."""
        try:
            from atoms_vs_ashes.config import Settings
            from atoms_vs_ashes.db.engine import init_engine, session_scope

            settings = Settings()
            init_engine(settings)
            from sqlalchemy import text
            with session_scope() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            pytest.skip("Database not available for live integration tests")

    def test_seismic_hazard_persist_succeeds(self):
        """S-01: persist mock SeismicHazardResult, verify SiteNaturalHazards columns."""
        from atoms_vs_ashes.connectors.seismic_hazard.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.seismic_hazard.models import SeismicHazardResult
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteNaturalHazards

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-seismic-001"

            result = SeismicHazardResult(
                lat=44.1456,
                lon=23.1234,
                pga_475yr=0.25,
                source="test_mock",
                quality="high",
                grid_distance_km=2.5,
                vs30_reference=760.0,
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            nh = session.get(SiteNaturalHazards, site.site_id)
            assert nh is not None, "SiteNaturalHazards row not created"
            assert nh.pga_475yr_g is not None
            assert nh.nh01_quality == "high"
            assert nh.run_id == run_id

            session.rollback()

    def test_egdi_geology_persist_succeeds(self):
        """S-02: persist mock EgdiGeologyResult, verify SiteNaturalHazards
        and SiteRadiological columns."""
        from atoms_vs_ashes.connectors.egdi_geology.batch import _persist_result, _ensure_data_sources
        from atoms_vs_ashes.connectors.egdi_geology.models import (
            EgdiGeologyResult,
            FaultAssessment,
            LithologyAssessment,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteNaturalHazards, SiteRadiological

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_sources(session)
            run_id = "test-egdi-001"

            result = EgdiGeologyResult(
                lat=44.14,
                lon=23.12,
                layers_queried=["faults", "lithology"],
                layers_with_data=["faults", "lithology"],
                quality="medium",
                faults=FaultAssessment(
                    nearest_fault_distance_km=12.0,
                    fault_count_within_buffer=2,
                    nearest_fault_type="normal",
                    nearest_fault_activity="potentially_active",
                ),
                lithology=LithologyAssessment(
                    lithology_class="clay",
                    rock_type="sedimentary",
                    engineering_soil_group="fine_grained",
                ),
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            nh = session.get(SiteNaturalHazards, site.site_id)
            assert nh is not None, "SiteNaturalHazards row not created"
            assert nh.nearest_fault_km is not None

            ri = session.get(SiteRadiological, site.site_id)
            assert ri is not None, "SiteRadiological row not created"

            session.rollback()

    def test_wdpa_persist_succeeds(self):
        """S-15: persist mock WdpaResult, verify SiteInfrastructureV2 WDPA columns."""
        from atoms_vs_ashes.connectors.wdpa.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.wdpa.models import WdpaResult
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "UA", "Ukraine")
            site = _ensure_test_site(session, "UA")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-wdpa-001"

            result = WdpaResult(
                lat=45.50,
                lon=29.60,
                country_code="UA",
                country_iso3="UKR",
                is_eu_member=False,
                wdpa_overlap=False,
                wdpa_nearest_distance_km=2.8,
                wdpa_nearest_site_id=166899,
                wdpa_nearest_name="Kyliiske Mouth",
                wdpa_nearest_designation="Ramsar Site",
                wdpa_nearest_iucn_category="Not Reported",
                wdpa_sites_within_5km=1,
                wdpa_sites_within_16km=2,
                wdpa_sites_within_25km=2,
                sensitivity_class="moderate",
                quality="high",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None, "SiteInfrastructureV2 row not created"
            assert infra.wdpa_quality == "high"
            assert infra.wdpa_overlap is False
            assert infra.wdpa_sensitivity_class == "moderate"
            assert infra.run_id == run_id

            session.rollback()

    def test_worldcover_persist_succeeds(self):
        """S-36: persist mock WorldCover metrics, verify SiteInfrastructureV2 NS-04/NS-05 columns."""
        from atoms_vs_ashes.connectors.worldcover.batch import (
            _ensure_data_source,
            _persist_result,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "TR", "Turkey")
            site = _ensure_test_site(session, "TR")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-worldcover-001"

            metrics = {
                "buildable_area_ha": 78.3,
                "dominant_land_class": "211",
                "dominant_land_label": "Cropland",
                "dominant_class_pct": 52.0,
                "favourable_land_pct": 55.0,
                "moderate_land_pct": 30.0,
                "unfavourable_land_pct": 15.0,
                "natural_seminatural_ha": 35.0,
            }

            _persist_result(session, site.site_id, metrics, run_id)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None, "SiteInfrastructureV2 row not created"
            assert infra.dominant_land_class == "211"
            assert float(infra.dominant_class_pct) == pytest.approx(52.0, abs=0.1)
            assert float(infra.buildable_area_ha) == pytest.approx(78.3, abs=0.1)
            assert infra.ns04_quality == "medium"
            assert infra.ns05_quality == "worldcover_10m"
            assert infra.run_id == run_id

            session.rollback()

    def test_eu_flood_risk_persist_succeeds(self):
        """S-08/P14: persist mock EuFloodRiskResult, verify SiteNaturalHazards
        NH-08 and NH-09 columns including A11 avoidance data."""
        from atoms_vs_ashes.connectors.eu_flood_risk.batch import _persist_result, _ensure_data_sources
        from atoms_vs_ashes.connectors.eu_flood_risk.models import (
            ApsfrDesignation,
            EuFloodRiskResult,
            FloodDepthProfile,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteNaturalHazards, SiteObservation

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_sources(session)
            run_id = "test-flood-001"

            depth = FloodDepthProfile(
                depth_rp10_m=0.0,
                depth_rp20_m=0.0,
                depth_rp50_m=0.0,
                depth_rp75_m=0.12,
                depth_rp100_m=0.45,
                depth_rp200_m=1.20,
                depth_rp500_m=2.85,
                max_depth_m=2.85,
                depth_class_rp100=1,
                tile_id="N42E025",
            )
            apsfr = ApsfrDesignation(
                apsfr_id="RO_APSFR_123",
                country_code="RO",
                probability_scenario="medium",
                source_type="river",
                unit_of_management="Danube Lower",
                reporting_cycle=2,
            )
            result = EuFloodRiskResult(
                lat=44.14,
                lon=23.12,
                flood_depth=depth,
                apsfr=[apsfr],
                hazard_class="avoidance",
                screening_flags=["A14", "A15", "A11"],
                flood_exposure_class="low",
                flood_return_period_threshold=75,
                sources=["jrc_glofas_flood_hazard_v2.1.2", "eea_apsfr_v3.0"],
                quality="high",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            nh = session.get(SiteNaturalHazards, site.site_id)
            assert nh is not None, "SiteNaturalHazards row not created"
            assert nh.flood_zone_class == "avoidance"
            assert nh.nh09_quality == "high"
            assert nh.nh08_quality == "high"
            assert nh.run_id == run_id

            obs = (
                session.query(SiteObservation)
                .filter_by(site_id=site.site_id, run_id=run_id)
                .all()
            )
            a11_obs = [o for o in obs if "A11" in (o.observation or "")]
            assert len(a11_obs) >= 1, "A11 SiteObservation not written"

            session.rollback()

    def test_corine_land_cover_persist_succeeds(self):
        """P12: persist mock CORINE buildable metrics, verify SiteInfrastructureV2 NS-04/NS-05 columns."""
        from atoms_vs_ashes.connectors.corine.batch import (
            _ensure_data_source,
            _persist_result,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-corine-001"

            metrics = {
                "buildable_area_ha": 95.5,
                "dominant_land_class": "211",
                "dominant_land_label": "Non-irrigated arable land",
                "dominant_class_pct": 45.2,
                "favourable_land_pct": 60.0,
                "moderate_land_pct": 25.0,
                "unfavourable_land_pct": 15.0,
                "natural_seminatural_ha": 42.3,
            }

            _persist_result(session, site.site_id, metrics, run_id)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None, "SiteInfrastructureV2 row not created"
            assert infra.dominant_land_class == "211"
            assert float(infra.dominant_class_pct) == pytest.approx(45.2, abs=0.1)
            assert float(infra.favourable_land_pct) == pytest.approx(60.0, abs=0.1)
            assert float(infra.buildable_area_ha) == pytest.approx(95.5, abs=0.1)
            assert infra.ns04_quality == "high"
            assert infra.ns05_quality == "corine_proxy"
            assert infra.run_id == run_id

            session.rollback()

    def test_corine_does_not_overwrite_fix03_buildable_area(self):
        """P12 must not overwrite buildable_area_ha if FIX-03 already set it."""
        from atoms_vs_ashes.connectors.corine.batch import (
            _ensure_data_source,
            _persist_result,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)

            # Simulate FIX-03 having already set buildable_area_ha
            infra = SiteInfrastructureV2(
                site_id=site.site_id,
                buildable_area_ha=120.0,
                ns05_quality="osm_polygon",
                ns05_comment="OSM industrial polygon area",
            )
            session.add(infra)
            session.flush()

            metrics = {
                "buildable_area_ha": 85.0,
                "dominant_land_class": "211",
                "dominant_land_label": "Non-irrigated arable land",
                "dominant_class_pct": 50.0,
                "favourable_land_pct": 60.0,
                "moderate_land_pct": 25.0,
                "unfavourable_land_pct": 15.0,
                "natural_seminatural_ha": 30.0,
            }

            _persist_result(session, site.site_id, metrics, "test-corine-002")
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            # buildable_area_ha should remain at 120.0 (FIX-03 value)
            assert float(infra.buildable_area_ha) == pytest.approx(120.0, abs=0.1)
            # But NS-04 fields should be updated
            assert infra.dominant_land_class == "211"
            assert infra.ns04_quality == "high"
            # ns05_comment should have CORINE ref appended
            assert "CORINE ref" in infra.ns05_comment

            session.rollback()

    def test_osm_transport_persist_succeeds(self):
        """P11: persist mock TransportResult, verify SiteInfrastructureV2 NS-03 columns."""
        from atoms_vs_ashes.connectors.osm.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.osm.models import (
            HighwayResult,
            RailwayResult,
            TransportResult,
            WaterwayResult,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-transport-001"

            result = TransportResult(
                lat=45.27,
                lon=27.96,
                highway=HighwayResult(
                    nearest_highway_km=2.5,
                    nearest_highway_type="motorway",
                    highway_heavy_haul=True,
                    element_count=3,
                ),
                railway=RailwayResult(
                    nearest_rail_km=0.8,
                    nearest_mainline_rail_km=0.8,
                    rail_siding_present=True,
                    rail_gauge_mm=1435,
                    rail_heavy_haul=True,
                    element_count=5,
                ),
                waterway=WaterwayResult(
                    nearest_waterway_km=4.2,
                    nearest_waterway_name="Dunărea",
                    waterway_cemt_class="VIc",
                    waterway_barge_capable=True,
                    element_count=2,
                ),
                heavy_haul_capable=True,
                heavy_haul_confidence="high",
                quality="high",
            )

            _persist_result(session, site.site_id, result, run_id, "RO")
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None, "SiteInfrastructureV2 row not created"
            assert float(infra.nearest_highway_km) == pytest.approx(2.5, abs=0.1)
            assert float(infra.nearest_rail_km) == pytest.approx(0.8, abs=0.1)
            assert float(infra.nearest_waterway_km) == pytest.approx(4.2, abs=0.1)
            assert infra.heavy_haul_capable is True
            assert infra.ns03_quality == "high"
            assert infra.ns03_comment is not None
            assert "motorway" in infra.ns03_comment
            assert infra.run_id == run_id

            session.rollback()

    def test_ghsl_pop_persist_succeeds(self):
        """S-20: persist mock GhslPopResult, verify SiteRadiological and
        SiteEmergencyPlanning columns."""
        from atoms_vs_ashes.connectors.ghsl_pop.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.ghsl_pop.models import (
            GhslPopResult,
            NearestCity,
            RingPopulation,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteEmergencyPlanning, SiteRadiological

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-ghsl-001"

            result = GhslPopResult(
                lat=44.14,
                lon=23.12,
                rings=[
                    RingPopulation(radius_km=5, pop_total=5000, area_km2=78.54, pop_density=63.66),
                    RingPopulation(radius_km=16, pop_total=50000, area_km2=804.25, pop_density=62.17),
                    RingPopulation(radius_km=25, pop_total=120000, area_km2=1963.50, pop_density=61.12),
                    RingPopulation(radius_km=80, pop_total=800000, area_km2=20106.19, pop_density=39.79),
                ],
                nearest_city=NearestCity(
                    name="Craiova", population=290_000, distance_km=45.2,
                ),
                pop_growth_rate_pct=-0.15,
                quality="medium",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            ri = session.get(SiteRadiological, site.site_id)
            assert ri is not None, "SiteRadiological row not created"
            assert ri.pop_density_5km is not None
            assert float(ri.pop_density_5km) == pytest.approx(63.66, abs=0.1)
            assert ri.pop_total_5km == 5000
            assert ri.pop_total_80km == 800000
            assert ri.nearest_city_name == "Craiova"
            assert ri.nearest_city_pop == 290_000
            assert ri.ri04_quality == "ghsl_pop_100m_r2023a"
            assert ri.run_id == run_id

            ep = session.get(SiteEmergencyPlanning, site.site_id)
            assert ep is not None, "SiteEmergencyPlanning row not created"
            assert ep.ep01_population_score is not None
            assert ep.run_id == run_id

            session.rollback()

    def test_eurostat_gisco_persist_succeeds(self):
        """S-16: persist mock EurostatGiscoResult, verify SiteRadiological RI-05 columns."""
        from atoms_vs_ashes.connectors.eurostat_gisco.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.eurostat_gisco.models import (
            CityProximityResult,
            EurostatGiscoResult,
            NearbyCityRecord,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteRadiological

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-gisco-001"

            result = EurostatGiscoResult(
                lat=44.14,
                lon=23.12,
                country_code="RO",
                city_proximity=CityProximityResult(
                    nearest_city_name="Craiova",
                    nearest_city_code="RO003C",
                    nearest_city_distance_km=45.2,
                    nearest_city_population=269_506,
                    nearest_city_country="RO",
                    cities_within_25km=0,
                    cities_within_80km=1,
                    largest_city_within_80km_name="Craiova",
                    largest_city_within_80km_population=269_506,
                    settlement_hierarchy="rural",
                    nearby_cities=[
                        NearbyCityRecord(
                            city_code="RO003C", city_name="Craiova",
                            country_code="RO", distance_km=45.2,
                            population=269_506,
                        ),
                    ],
                ),
                quality="high",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            ri = session.get(SiteRadiological, site.site_id)
            assert ri is not None, "SiteRadiological row not created"
            assert ri.nearest_city_name == "Craiova"
            assert ri.nearest_city_pop == 269_506
            assert float(ri.nearest_city_50k_km) == pytest.approx(45.2, abs=0.1)
            assert ri.ri05_quality == "gisco_urau_2021"
            assert ri.ri05_comment is not None
            assert "Craiova" in ri.ri05_comment
            assert "settlement hierarchy" in ri.ri05_comment.lower()
            assert ri.run_id == run_id

            session.rollback()

    def test_geonames_dump_persist_succeeds(self):
        """GeoNames dump: extended_data merge + RI-05 gap-fill vs skip when GISCO present."""
        from atoms_vs_ashes.connectors.geonames_dump.batch import (
            _maybe_update_ri05_main,
            _merge_extended_data,
        )
        from atoms_vs_ashes.connectors.geonames_dump.models import (
            EXTENDED_DATA_KEY,
            NearestGeonamesResult,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteRadiological

        nearest = NearestGeonamesResult(
            geoname_id=680_334,
            name="Constanța",
            population=250_000,
            country_code="RO",
            distance_km=120.5,
            feature_code="PPLA2",
        )
        run_id = "test-geonames-dump-001"

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            site.extended_data = {"keep_marker": True}
            session.flush()

            _merge_extended_data(session, site, nearest, dump_date="2026-01-15")
            session.flush()
            session.refresh(site)
            assert site.extended_data.get("keep_marker") is True
            assert EXTENDED_DATA_KEY in site.extended_data
            assert site.extended_data[EXTENDED_DATA_KEY]["name"] == "Constanța"
            assert site.extended_data[EXTENDED_DATA_KEY]["geoname_id"] == 680_334

            updated = _maybe_update_ri05_main(
                session, site.site_id, nearest, run_id, overwrite=False,
            )
            assert updated is True
            session.flush()
            ri = session.get(SiteRadiological, site.site_id)
            assert ri is not None
            assert ri.nearest_city_name == "Constanța"
            assert ri.ri05_quality == "geonames_c5k"

            skipped = _maybe_update_ri05_main(
                session, site.site_id, nearest, run_id, overwrite=False,
            )
            assert skipped is False

            assert (
                _maybe_update_ri05_main(
                    session, site.site_id, nearest, run_id + "b", overwrite=True,
                )
                is True
            )
            ri2 = session.get(SiteRadiological, site.site_id)
            assert ri2.run_id == run_id + "b"

            session.rollback()

    def test_entso_e_persist_with_per_unit_match(self):
        """S-13: persist EntsoEResult with per-unit match, verify site-level capacity."""
        from atoms_vs_ashes.connectors.entso_e.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.entso_e.matcher import MatchResult
        from atoms_vs_ashes.connectors.entso_e.models import (
            CapacityMetrics,
            EntsoEResult,
            GenerationUnit,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-entsoe-001"

            matched_unit = GenerationUnit(
                unit_name="Rovinari Group 3",
                unit_eic="ROV3",
                psr_type="B05",
                psr_name="Fossil Hard coal",
                installed_mw=330.0,
            )
            result = EntsoEResult(
                lat=44.14,
                lon=23.12,
                country_code="RO",
                bidding_zone_eic="10YRO-TEL------P",
                bidding_zone_name="Romania (RO)",
                capacity=CapacityMetrics(
                    total_installed_mw=19500.0,
                    nuclear_installed_mw=1300.0,
                    has_nuclear_precedent=True,
                    smr_capacity_ratio=0.024,
                ),
                per_unit_match=MatchResult(
                    matched=True,
                    capacity_mw=330.0,
                    unit_count=1,
                    best_score=85.0,
                    matched_units=[matched_unit],
                ),
                nuclear_readiness="excellent",
                reference_year=2025,
                quality="high",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None, "SiteInfrastructureV2 row not created"
            assert infra.grid_export_capacity_mw is not None
            assert float(infra.grid_export_capacity_mw) == pytest.approx(330.0, abs=1.0)
            assert infra.ns02_quality == "high"
            assert infra.ns02_comment is not None
            assert "per-unit match" in infra.ns02_comment
            assert infra.run_id == run_id

            session.rollback()

    def test_entso_e_persist_gem_fallback(self):
        """S-13: persist EntsoEResult without match, verify GEM fallback."""
        from atoms_vs_ashes.connectors.entso_e.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.entso_e.models import (
            CapacityMetrics,
            EntsoEResult,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-entsoe-002"

            result = EntsoEResult(
                lat=44.14,
                lon=23.12,
                country_code="RO",
                bidding_zone_eic="10YRO-TEL------P",
                bidding_zone_name="Romania (RO)",
                capacity=CapacityMetrics(
                    total_installed_mw=19500.0,
                ),
                nuclear_readiness="excellent",
                reference_year=2025,
                quality="medium",
            )

            _persist_result(session, site.site_id, result, run_id, installed_capacity_mw=660.0)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None
            assert float(infra.grid_export_capacity_mw) == pytest.approx(660.0, abs=1.0)
            assert "GEM" in infra.ns02_comment
            assert infra.run_id == run_id

            session.rollback()

    def test_entso_e_persist_no_match_no_gem(self):
        """S-13: no per-unit match and no GEM -> grid_export_capacity_mw is NULL."""
        from atoms_vs_ashes.connectors.entso_e.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.entso_e.models import (
            CapacityMetrics,
            EntsoEResult,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            _ensure_data_source(session)
            run_id = "test-entsoe-003"

            result = EntsoEResult(
                lat=44.14,
                lon=23.12,
                country_code="RO",
                bidding_zone_eic="10YRO-TEL------P",
                bidding_zone_name="Romania (RO)",
                capacity=CapacityMetrics(total_installed_mw=19500.0),
                nuclear_readiness="excellent",
                reference_year=2025,
                quality="medium",
            )

            _persist_result(session, site.site_id, result, run_id)
            session.flush()

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None
            assert infra.grid_export_capacity_mw is None
            assert "not determined" in infra.ns02_comment

            session.rollback()

    def test_earth_engine_persist_succeeds(self):
        """S-06: mock EarthEngineResult → domain tables + multi-source JSON."""
        from atoms_vs_ashes.connectors.earth_engine.batch import _persist_result
        from atoms_vs_ashes.connectors.earth_engine.fusion import FusionConfig
        from atoms_vs_ashes.connectors.earth_engine.models import (
            EarthEngineResult,
            GeeBuiltUpResult,
            GeeFireResult,
            GeeTerrainResult,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import (
            SiteEmergencyPlanning,
            SiteInfrastructureV2,
            SiteNaturalHazards,
        )

        with session_scope() as session:
            _ensure_country(session, "RO", "Romania")
            site = _ensure_test_site(session, "RO")
            session.flush()

            run_id = "test-gee-persist-001"
            result = EarthEngineResult(
                lat=44.14,
                lon=23.12,
                terrain=GeeTerrainResult(
                    slope_max_deg=15.2,
                    slope_mean_deg=5.1,
                    slope_p95_deg=12.0,
                    relief_range_m=80.0,
                    relief_16km_m=220.0,
                    mountain_barrier_score=0.15,
                    terrain_class="moderate",
                    grading_class="moderate",
                    drainage_class="moderate",
                    roughness_class="moderate",
                    quality="high",
                ),
                fire=GeeFireResult(
                    modis_burn_count_25yr=2,
                    fire_recurrence_class="rare",
                    modis_burn_fraction_mean=0.04,
                    quality="medium",
                ),
                built_up=GeeBuiltUpResult(
                    built_fraction_dw=0.25,
                    demolition_class="moderate",
                    quality="high",
                ),
            )
            _persist_result(
                session,
                site.site_id,
                result,
                run_id,
                fusion_cfg=FusionConfig(),
                terrain_skipped=False,
            )
            session.flush()

            nh = session.get(SiteNaturalHazards, site.site_id)
            assert nh is not None
            assert nh.nh04_gee_slope_max_deg is not None
            assert nh.nh04_cross_source_summary is not None
            assert nh.nh13_gee_modis_burn_months is not None
            assert nh.nh13_cross_source_summary is not None

            infra = session.get(SiteInfrastructureV2, site.site_id)
            assert infra is not None
            assert infra.ns04_gee_terrain_class is not None
            assert infra.ns04_cross_source_summary is not None
            assert infra.ns06_gee_built_fraction is not None
            assert infra.ns06_cross_source_summary is not None

            ep = session.get(SiteEmergencyPlanning, site.site_id)
            assert ep is not None
            assert ep.ep03_gee_relief_16km_m is not None
            assert ep.ep03_cross_source_summary is not None

            session.rollback()


# ---------------------------------------------------------------------------
# Shared live-DB helpers
# ---------------------------------------------------------------------------

def _ensure_country(session, code: str, name: str) -> None:
    from atoms_vs_ashes.db.models import Country
    existing = session.get(Country, code)
    if not existing:
        session.add(Country(country_code=code, country_name=name))
        session.flush()


def _ensure_test_site(session, country_code: str):
    from atoms_vs_ashes.db.models import Site
    import uuid

    site = Site(
        site_id=uuid.uuid4(),
        name="__test_connector_db_compat__",
        country_code=country_code,
        country_name="Romania",
        latitude=44.1456,
        longitude=23.1234,
    )
    session.add(site)
    return site
