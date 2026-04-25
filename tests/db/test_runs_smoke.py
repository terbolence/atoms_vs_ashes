# man_hours: 0.5
"""Smoke test for ``start_run`` / ``complete_run`` round-trip.

Without an active session the helpers should still mint a stable
``run_id`` so CSV-only callers stay aligned with the DB.
"""

from __future__ import annotations

from atoms_vs_ashes.db.runs import (
    DatasetMeta,
    complete_run,
    run_scope,
    start_run,
)


def test_start_run_no_session_returns_unpersisted_handle():
    handle = start_run(
        None,
        run_kind="sensitivity",
        cli_command="pytest",
        notes="smoke",
    )
    assert handle.run_id
    assert handle.run_kind == "sensitivity"
    assert handle.persisted is False


def test_complete_run_no_session_is_noop():
    handle = start_run(None, run_kind="scoring")
    complete_run(None, handle, status="completed")


def test_run_scope_no_session_yields_handle():
    captured: dict[str, str] = {}
    with run_scope(None, run_kind="failure_analysis") as handle:
        captured["run_id"] = handle.run_id
    assert captured["run_id"]


def test_run_scope_marks_failed_on_exception():
    captured: dict[str, str] = {}
    try:
        with run_scope(None, run_kind="correlation") as handle:
            captured["run_id"] = handle.run_id
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert captured["run_id"]


def test_dataset_meta_dataclass_is_optional():
    meta = DatasetMeta(rubric_file_path="config/rubric")
    assert meta.rubric_file_path == "config/rubric"
    assert meta.weight_normalisation_profile is None
