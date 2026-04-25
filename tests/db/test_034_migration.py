# man_hours: 1.0
"""Verify Alembic revision 034 created every analytics table + enum.

Skipped when no live Postgres is reachable (mirrors the existing
``test_integration_db.py`` pattern). The test deliberately only
checks for table presence + enum types — re-validating the
``NOT VALID`` FKs against historical rows would require a populated
DB and is covered by the manual upgrade smoke step in the README.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope


EXPECTED_TABLES = (
    "runs",
    "dataset_snapshot",
    "composite_score_components",
    "site_bands",
    "country_rankings_summary",
    "country_site_rankings",
    "oat_importance",
    "weight_profile_stability",
    "threshold_sensitivity",
    "failure_outcomes",
    "failure_aggregates",
    "swing_weights",
    "criterion_correlations",
    "country_balance_check",
)


@pytest.fixture(scope="module", autouse=True)
def _init_db():
    try:
        init_engine(Settings())
        with session_scope() as session:
            session.execute(text("SELECT 1"))
            version = session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except Exception:
        pytest.skip("Database not available for migration test")
    if version is None or str(version) < "034":
        pytest.skip(
            f"Alembic revision {version!r} is below 034; "
            "run `alembic upgrade head` before re-running this test."
        )


def test_034_tables_present():
    with session_scope() as session:
        rows = session.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )).scalars().all()
        existing = set(rows)
        missing = [t for t in EXPECTED_TABLES if t not in existing]
        assert not missing, f"missing analytics tables: {missing}"


def test_034_run_kind_enum_present():
    with session_scope() as session:
        labels = session.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname='run_kind'"
        )).scalars().all()
        assert {
            "scoring", "sensitivity", "failure_analysis",
            "correlation", "swing_audit",
        }.issubset(set(labels))


def test_034_threshold_direction_enum_present():
    with session_scope() as session:
        labels = session.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname='threshold_direction'"
        )).scalars().all()
        assert {"plus_25", "minus_25"}.issubset(set(labels))


def test_034_runs_pk_shape():
    with session_scope() as session:
        col = session.execute(text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name='runs' AND column_name='run_id'"
        )).scalar_one_or_none()
        assert col is not None, "runs.run_id missing"
