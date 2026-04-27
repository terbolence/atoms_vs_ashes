# man_hours: 0.5
"""Round-trip tests for the singleton ``active_run_profile`` row (alembic 039).

Skipped when no live Postgres is reachable. The fixture snapshots the
DB row, runs the assertions, and restores the original on tear-down so
the test is non-destructive even when run against a populated dev DB.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.active_profile import (
    ACTIVE_PROFILE_ID,
    load_active_profile,
    save_active_profile,
)
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import ActiveRunProfile
from atoms_vs_ashes.runprofile.schema import RunProfile, ScopeBlock


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
        pytest.skip("Database not available for active_run_profile tests")
    if version is None or str(version) < "039":
        pytest.skip(
            f"Alembic revision {version!r} is below 039; "
            "run `alembic upgrade head` before re-running this test."
        )


@pytest.fixture
def restore_active_profile():
    """Snapshot the singleton row before the test and restore it after."""
    with session_scope() as session:
        row = session.get(ActiveRunProfile, ACTIVE_PROFILE_ID)
        original = dict(row.profile) if row else None
        original_updated_by = row.updated_by if row else None
    yield
    with session_scope() as session:
        row = session.get(ActiveRunProfile, ACTIVE_PROFILE_ID)
        if original is None:
            if row is not None:
                session.delete(row)
            return
        if row is None:
            session.add(
                ActiveRunProfile(
                    id=ACTIVE_PROFILE_ID,
                    profile=original,
                    updated_by=original_updated_by,
                )
            )
        else:
            row.profile = original
            row.updated_by = original_updated_by


def test_load_active_profile_returns_validated_runprofile():
    with session_scope() as session:
        profile = load_active_profile(session)
    assert isinstance(profile, RunProfile)
    assert profile.run_label  # alembic 039 seeded a non-empty label


def test_save_then_load_round_trips_jsonb(restore_active_profile):
    new_profile = RunProfile(
        run_label="round_trip_test",
        scope=ScopeBlock(countries=["RO"], smr_keys=["nuscale_voygr6"]),
        notes="written by tests/db/test_active_profile.py",
    )
    with session_scope() as session:
        save_active_profile(
            session, new_profile, updated_by="pytest:active_profile"
        )
    with session_scope() as session:
        reloaded = load_active_profile(session)
    assert reloaded.run_label == "round_trip_test"
    assert reloaded.scope.countries == ["RO"]
    assert reloaded.scope.smr_keys == ["nuscale_voygr6"]
    assert reloaded.notes == "written by tests/db/test_active_profile.py"


def test_save_active_profile_upserts_in_place(restore_active_profile):
    """Repeated saves must not insert a second row (singleton invariant)."""
    p1 = RunProfile(run_label="upsert_one", notes="1")
    p2 = RunProfile(run_label="upsert_two", notes="2")
    with session_scope() as session:
        save_active_profile(session, p1)
        save_active_profile(session, p2)
    with session_scope() as session:
        rows = session.execute(text("SELECT id FROM active_run_profile")).scalars().all()
        reloaded = load_active_profile(session)
    assert rows == [ACTIVE_PROFILE_ID]
    assert reloaded.run_label == "upsert_two"
    assert reloaded.notes == "2"


def test_singleton_check_constraint_rejects_other_ids(restore_active_profile):
    """Direct INSERT with id != 'active' must fail the CHECK constraint."""
    with pytest.raises(Exception):
        with session_scope() as session:
            session.execute(
                text(
                    "INSERT INTO active_run_profile (id, profile) "
                    "VALUES ('not_active', '{}'::jsonb)"
                )
            )


def test_save_preserves_complex_fields(restore_active_profile):
    p = RunProfile(
        run_label="complex_payload",
        fail_thresholds={"NH-02": {"E1": 4.5}, "NH-04": {"E3": 25.0}},
        scope=ScopeBlock(
            countries=["RO", "BG"],
            smr_keys=["nuscale_voygr6", "natrium_nominal"],
            site_status_in=["operating", "retired"],
        ),
        expert_override=True,
    )
    with session_scope() as session:
        save_active_profile(session, p)
    with session_scope() as session:
        reloaded = load_active_profile(session)
    assert reloaded.fail_thresholds == {
        "NH-02": {"E1": 4.5},
        "NH-04": {"E3": 25.0},
    }
    assert reloaded.scope.countries == ["BG", "RO"]
    assert reloaded.scope.smr_keys == ["natrium_nominal", "nuscale_voygr6"]
    assert reloaded.expert_override is True
