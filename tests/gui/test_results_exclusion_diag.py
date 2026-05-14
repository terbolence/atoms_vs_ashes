# man_hours: 0.95
"""Pure-unit tests for Results exclusionary diagnostics."""

from __future__ import annotations

import json

import pytest

from atoms_vs_ashes.gui._results_data_exclusion_diag import (
    ExclusionFailureRow,
    aggregate_diagnostics,
    margin_from_payload,
    required_relaxation_pct,
)
from atoms_vs_ashes.gui._results_render_diag_filters import (
    gap_df,
    near_miss_df,
    near_miss_rows,
    pareto_df,
    unlock_df,
)


def test_required_relaxation_is_direction_aware() -> None:
    assert required_relaxation_pct(12.0, 10.0, ">") == pytest.approx(20.0)
    assert required_relaxation_pct(9.0, 10.0, "<") == pytest.approx(10.0)
    assert required_relaxation_pct(10.0, 10.0, ">=") == pytest.approx(0.0)
    assert required_relaxation_pct(8.0, 10.0, ">") == pytest.approx(0.0)
    assert required_relaxation_pct(1.0, 0.0, ">") is None
    assert required_relaxation_pct(1.0, 2.0, "==") is None


def test_margin_from_payload_uses_threshold_metadata() -> None:
    measured = json.dumps({"nearest_fault_km": 4.5})
    _, threshold, units, pct = margin_from_payload(
        "NH-02", "E1", measured,
    )
    assert threshold == pytest.approx(8.0)
    assert units == "km"
    assert pct == pytest.approx(43.75)


def test_margin_from_payload_handles_safety_floor() -> None:
    measured = json.dumps({"score_0_10": 4.5, "pass_mark": 5.0})
    actual, threshold, units, pct = margin_from_payload(
        "NH-02", "E1:floor", measured,
    )
    assert actual == pytest.approx(4.5)
    assert threshold == pytest.approx(5.0)
    assert units is None
    assert pct == pytest.approx(10.0)


def test_aggregate_counts_distinct_sites_per_criterion() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 10.0),
        _row("s1", "NH-02", "E1b", 12.0),
        _row("s2", "NH-02", "E1", 7.0),
    ]
    diag = aggregate_diagnostics(rows)
    assert diag.summary.n_failures == 3
    assert diag.summary.n_sites == 2
    assert diag.pareto[0].n_sites == 2
    assert diag.pareto[0].n_pairs == 2
    assert diag.pareto[0].n_failures == 3


def test_unlock_curve_distinguishes_resolved_from_survivor_unlocks() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 4.0),
        _row("s2", "NH-02", "E1", 6.0),
        _row("s2", "EP-01", "E9", 2.0),
    ]
    diag = aggregate_diagnostics(rows, unlock_steps=(5.0, 10.0))
    nh_5 = _unlock(diag, "NH-02", 5.0)
    nh_10 = _unlock(diag, "NH-02", 10.0)
    assert nh_5.criterion_failures_resolved == 1
    assert nh_5.single_criterion_survivor_unlocks == 1
    assert nh_10.criterion_failures_resolved == 2
    assert nh_10.single_criterion_survivor_unlocks == 1


def test_pareto_df_limits_to_top_n() -> None:
    rows = [
        _row("a1", "NH-02", "E1", 4.0),
        _row("a2", "NH-02", "E1", 4.0),
        _row("b1", "NH-03", "E2", 3.0),
        _row("c1", "EP-01", "E9", 5.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = pareto_df(diag, top_n=2)
    assert list(df["criterion_id"]) == ["NH-02", "EP-01"]
    assert len(df) == 2


def test_pareto_df_with_top_n_zero_is_empty() -> None:
    rows = [_row("a1", "NH-02", "E1", 4.0)]
    diag = aggregate_diagnostics(rows)
    assert pareto_df(diag, top_n=0).empty


def test_gap_df_uses_exact_near_miss_threshold() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 8.0),
        _row("s2", "NH-02", "E1", 18.0),
        _row("s3", "NH-02", "E1", 30.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = gap_df(
        diag, top_n=5, max_gap=200.0, near_only=True,
        near_miss_gap_pct=15.0,
    )
    assert sorted(df["required_relaxation_pct"]) == [8.0]


def test_gap_df_max_gap_caps_rows() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 5.0),
        _row("s2", "NH-02", "E1", 40.0),
        _row("s3", "NH-02", "E1", 120.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = gap_df(
        diag, top_n=5, max_gap=50.0, near_only=False,
        near_miss_gap_pct=25.0,
    )
    assert sorted(df["required_relaxation_pct"]) == [5.0, 40.0]


def test_gap_df_top_n_restricts_criteria() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 4.0),
        _row("s2", "NH-02", "E1", 6.0),
        _row("s3", "NH-03", "E2", 3.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = gap_df(
        diag, top_n=1, max_gap=200.0, near_only=False,
        near_miss_gap_pct=25.0,
    )
    assert set(df["criterion"]).issubset({"NH-02 — Criterion NH-02"})


def test_unlock_df_selects_metric_column() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 4.0),
        _row("s2", "NH-02", "E1", 6.0),
        _row("s2", "EP-01", "E9", 2.0),
    ]
    diag = aggregate_diagnostics(rows, unlock_steps=(5.0, 10.0))
    failures_df = unlock_df(
        diag, top_n=5, metric="criterion_failures_resolved",
    )
    survivor_df = unlock_df(
        diag, top_n=5, metric="single_criterion_survivor_unlocks",
    )
    nh_5_failures = failures_df[
        failures_df["criterion"].str.startswith("NH-02")
        & (failures_df["step"] == "5%")
    ]["n"].iat[0]
    nh_5_survivors = survivor_df[
        survivor_df["criterion"].str.startswith("NH-02")
        & (survivor_df["step"] == "5%")
    ]["n"].iat[0]
    assert nh_5_failures == 1
    assert nh_5_survivors == 1


def test_near_miss_uses_exact_threshold_no_silent_widening() -> None:
    rows = [
        _row("s1", "NH-02", "E1", 4.0),
        _row("s2", "NH-02", "E1", 12.0),
        _row("s3", "NH-02", "E1", 20.0),
    ]
    diag = aggregate_diagnostics(rows)
    rows_within = near_miss_rows(diag, near_miss_gap_pct=10.0)
    assert {r.site_name for r in rows_within} == {"site-s1"}
    df = near_miss_df(diag, near_miss_gap_pct=10.0)
    assert sorted(df["relaxation_pct"]) == [4.0]


def _row(
    site_id: str, criterion_id: str, code: str, pct: float | None,
) -> ExclusionFailureRow:
    return ExclusionFailureRow(
        site_id=site_id, site_name=f"site-{site_id}", country_code="RO",
        smr_key="nuscale_voygr6", criterion_id=criterion_id,
        criterion_name=f"Criterion {criterion_id}", code=code,
        measured=None, threshold=None, units=None,
        required_relaxation_pct=pct, justification="test",
    )


def _unlock(diag, criterion_id: str, step: float):
    prefix = f"{criterion_id} "
    return next(
        r for r in diag.unlocks
        if r.criterion_label.startswith(prefix) and r.step_pct == step
    )
