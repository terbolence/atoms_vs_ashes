# man_hours: 0.5
"""Pure-unit tests for the Results run picker preferred-run policy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from atoms_vs_ashes.gui._results_run_picker import (
    _newest_completed_run_id,
    _preferred_run_id,
)
from atoms_vs_ashes.gui._results_runs_list import RunSummary

_BASE = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)


def _make_run(
    run_id: str,
    *,
    status: str = "completed",
    minutes_after: int = 0,
    run_kind: str = "scoring",
) -> RunSummary:
    started = _BASE + timedelta(minutes=minutes_after)
    completed = started + timedelta(minutes=1) if status == "completed" else None
    return RunSummary(
        run_id=run_id,
        run_kind=run_kind,
        status=status,
        started_at=started,
        completed_at=completed,
    )


def test_no_runs_returns_none_and_preserves_seen() -> None:
    pick, seen = _preferred_run_id(
        [], current_pick="anything", last_seen_latest="prev",
    )
    assert pick is None
    assert seen == "prev"


def test_initial_load_selects_newest_completed_and_records_it() -> None:
    runs = [
        _make_run("r3", minutes_after=30),
        _make_run("r2", minutes_after=20),
        _make_run("r1", minutes_after=10),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick=None, last_seen_latest=None,
    )
    assert pick == "r3"
    assert seen == "r3"


def test_user_pick_of_older_run_is_preserved_when_no_new_run() -> None:
    runs = [
        _make_run("r3", minutes_after=30),
        _make_run("r2", minutes_after=20),
        _make_run("r1", minutes_after=10),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick="r1", last_seen_latest="r3",
    )
    assert pick == "r1"
    assert seen == "r3"


def test_newer_completed_run_overrides_older_user_pick() -> None:
    runs = [
        _make_run("r4", minutes_after=40),
        _make_run("r3", minutes_after=30),
        _make_run("r2", minutes_after=20),
        _make_run("r1", minutes_after=10),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick="r1", last_seen_latest="r3",
    )
    assert pick == "r4"
    assert seen == "r4"


def test_stale_pick_falls_back_to_newest_completed() -> None:
    runs = [
        _make_run("r3", minutes_after=30),
        _make_run("r2", minutes_after=20),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick="dropped_off", last_seen_latest="r3",
    )
    assert pick == "r3"
    assert seen == "r3"


def test_no_completed_runs_falls_back_to_newest_overall() -> None:
    runs = [
        _make_run("r2", status="running", minutes_after=20),
        _make_run("r1", status="failed", minutes_after=10),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick=None, last_seen_latest=None,
    )
    assert pick == "r2"
    assert seen is None


def test_no_completed_runs_preserves_user_pick_when_in_set() -> None:
    runs = [
        _make_run("r2", status="running", minutes_after=20),
        _make_run("r1", status="failed", minutes_after=10),
    ]
    pick, seen = _preferred_run_id(
        runs, current_pick="r1", last_seen_latest=None,
    )
    assert pick == "r1"
    assert seen is None


def test_newest_completed_skips_failed_runs() -> None:
    runs = [
        _make_run("r3", status="failed", minutes_after=30),
        _make_run("r2", minutes_after=20),
        _make_run("r1", minutes_after=10),
    ]
    assert _newest_completed_run_id(runs) == "r2"


def test_repeat_call_with_unchanged_latest_keeps_user_pick() -> None:
    runs = [
        _make_run("r3", minutes_after=30),
        _make_run("r2", minutes_after=20),
        _make_run("r1", minutes_after=10),
    ]
    first_pick, first_seen = _preferred_run_id(
        runs, current_pick=None, last_seen_latest=None,
    )
    assert first_pick == "r3"
    user_pick = "r1"
    second_pick, second_seen = _preferred_run_id(
        runs, current_pick=user_pick, last_seen_latest=first_seen,
    )
    assert second_pick == "r1"
    assert second_seen == "r3"
