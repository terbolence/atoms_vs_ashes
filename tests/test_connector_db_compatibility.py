# man_hours: 4.0
"""Verify that every connector's criterion_ids are seeded in the DB.

Two test layers:
1. Static: parse all Alembic seed migrations and compare against the
   CRITERION_IDS constants exported by each connector.
2. Live DB (skipped when no database): create a test site, call the
   connector's persist logic with mock data, and verify SiteAttribute
   rows are written without FK violations.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import types
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


# ---------------------------------------------------------------------------
# Helpers — collect CRITERION_IDS from all connectors
# ---------------------------------------------------------------------------

_CONNECTORS_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "atoms_vs_ashes"
    / "connectors"
)


_INGEST_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "atoms_vs_ashes"
    / "ingest"
)


def _scan_models_file(path: Path, name: str) -> tuple[str, ...] | None:
    """Extract CRITERION_IDS from a models.py file."""
    spec = importlib.util.spec_from_file_location(
        f"_tmp_{name}_models", path,
    )
    if spec is None or spec.loader is None:
        return None
    mod = types.ModuleType(spec.name)
    try:
        exec(compile(path.read_text(), path, "exec"), mod.__dict__)
    except Exception:
        text = path.read_text(encoding="utf-8")
        m = re.search(
            r'CRITERION_IDS\s*=\s*\(([^)]+)\)', text,
        )
        if m:
            return tuple(
                s.strip().strip('"').strip("'")
                for s in m.group(1).split(",")
                if s.strip()
            )
        return None

    cids = getattr(mod, "CRITERION_IDS", None)
    if cids is not None:
        return tuple(cids)
    return None


def _connector_criterion_ids() -> dict[str, tuple[str, ...]]:
    """Return {connector_name: CRITERION_IDS} for every connector that
    declares a CRITERION_IDS constant in its models module.
    Also scans ingest/models.py for non-connector persistence modules."""
    result: dict[str, tuple[str, ...]] = {}

    for subdir in sorted(_CONNECTORS_DIR.iterdir()):
        models_path = subdir / "models.py"
        if not models_path.is_file():
            continue
        cids = _scan_models_file(models_path, subdir.name)
        if cids is not None:
            result[subdir.name] = cids

    ingest_models = _INGEST_DIR / "models.py"
    if ingest_models.is_file():
        cids = _scan_models_file(ingest_models, "ingest")
        if cids is not None:
            result["ingest"] = cids

    return result


# ===================================================================
# Static tests — no DB required
# ===================================================================


class TestCriteriaSeedCompleteness:
    """Every criterion_id written by a connector must exist in Alembic seeds."""

    _seeded = _seeded_criterion_ids()
    _connectors = _connector_criterion_ids()

    def test_at_least_one_connector_found(self):
        assert len(self._connectors) >= 5, (
            f"Expected at least 5 modules with CRITERION_IDS, found: "
            f"{list(self._connectors.keys())}"
        )

    def test_all_criterion_ids_are_seeded(self):
        missing: dict[str, list[str]] = {}
        for name, ids in self._connectors.items():
            not_seeded = [cid for cid in ids if cid not in self._seeded]
            if not_seeded:
                missing[name] = not_seeded

        assert not missing, (
            "Connectors reference criterion_ids that are NOT seeded in any "
            f"Alembic migration:\n"
            + "\n".join(
                f"  {name}: {ids}" for name, ids in missing.items()
            )
            + "\n\nFix: add a seed migration for these criteria."
        )

    @pytest.mark.parametrize(
        "connector_name,criterion_ids",
        [
            pytest.param(name, ids, id=name)
            for name, ids in _connector_criterion_ids().items()
        ],
    )
    def test_per_connector_coverage(self, connector_name, criterion_ids):
        not_seeded = [cid for cid in criterion_ids if cid not in self._seeded]
        assert not not_seeded, (
            f"Connector '{connector_name}' uses criterion_ids {not_seeded} "
            f"which are not seeded in Alembic migrations."
        )

    def test_seed_migration_has_all_46_criteria(self):
        """All 46 criteria from requirements/05_siting_criteria.md
        should be present in the combined seed data."""
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
    without FK violations on criterion_id."""

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
        """S-01: create a test site, persist mock SeismicHazardResult,
        verify 3 SiteAttribute rows (NH-01, NH-03, NH-04)."""
        from atoms_vs_ashes.connectors.seismic_hazard.batch import _persist_result, _ensure_data_source
        from atoms_vs_ashes.connectors.seismic_hazard.models import SeismicHazardResult
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteAttribute, Country

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

            attrs = (
                session.query(SiteAttribute)
                .filter_by(site_id=site.site_id, run_id=run_id)
                .all()
            )
            written_cids = {a.criterion_id for a in attrs}
            assert {"NH-01", "NH-03", "NH-04"} <= written_cids, (
                f"Expected NH-01, NH-03, NH-04; got {written_cids}"
            )

            session.rollback()

    def test_egdi_geology_persist_succeeds(self):
        """S-02: create a test site, persist mock EgdiGeologyResult,
        verify 6 SiteAttribute rows (NH-02..NH-06, RI-03)."""
        from atoms_vs_ashes.connectors.egdi_geology.batch import _persist_result, _ensure_data_sources
        from atoms_vs_ashes.connectors.egdi_geology.models import (
            EgdiGeologyResult,
            FaultAssessment,
            LithologyAssessment,
        )
        from atoms_vs_ashes.db.engine import session_scope
        from atoms_vs_ashes.db.models import Site, SiteAttribute

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

            attrs = (
                session.query(SiteAttribute)
                .filter_by(site_id=site.site_id, run_id=run_id)
                .all()
            )
            written_cids = {a.criterion_id for a in attrs}
            assert {"NH-02", "NH-03", "NH-04", "NH-05", "NH-06", "RI-03"} <= written_cids, (
                f"Expected all 6 EGDI criteria; got {written_cids}"
            )

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
