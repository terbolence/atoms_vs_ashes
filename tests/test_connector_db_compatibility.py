# man_hours: 4.0
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

_ALEMBIC_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"
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

            source_id = _ensure_data_source(session)
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

            _persist_result(session, site.site_id, result, run_id, source_id)
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

            source_ids = _ensure_data_sources(session)
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

            _persist_result(session, site.site_id, result, run_id, source_ids)
            session.flush()

            nh = session.get(SiteNaturalHazards, site.site_id)
            assert nh is not None, "SiteNaturalHazards row not created"
            assert nh.nearest_fault_km is not None

            ri = session.get(SiteRadiological, site.site_id)
            assert ri is not None, "SiteRadiological row not created"

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
