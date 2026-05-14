# man_hours: 0.6
"""Pure-unit tests for Results avoidance diagnostics."""

from __future__ import annotations

import json

import pytest

from atoms_vs_ashes.gui._results_data_avoidance_diag import (
    AvoidanceFlagRow,
    aggregate_diagnostics,
    margin_from_payload,
    required_relaxation_pct,
)
from atoms_vs_ashes.gui._results_render_diag_filters import (
    gap_df,
    near_miss_df,
    pareto_df,
    unlock_df,
)


def test_avoidance_margin_uses_threshold_metadata() -> None:
    measured = json.dumps({"grid_export_capacity_mw": 300})
    actual, threshold, units, pct = margin_from_payload(
        "NS-02", "A13", measured,
    )
    assert actual == pytest.approx(300.0)
    assert threshold == pytest.approx(462.0)
    assert units == "MW"
    assert pct == pytest.approx(35.0649, rel=1e-4)


def test_avoidance_aggregate_counts_distinct_sites() -> None:
    rows = [
        _row("s1", "NS-02", "A13", 10.0),
        _row("s1", "RI-05", "A12", 12.0),
        _row("s2", "NS-02", "A13", 7.0),
    ]
    diag = aggregate_diagnostics(rows, unlock_steps=(10.0,))
    assert diag.summary.n_failures == 3
    assert diag.summary.n_sites == 2
    assert diag.pareto[0].criterion_id == "NS-02"
    assert diag.pareto[0].n_sites == 2
    assert diag.unlocks


def test_required_relaxation_is_shared_with_exclusion_math() -> None:
    assert required_relaxation_pct(4.0, 5.0, "<") == pytest.approx(20.0)


def test_avoidance_pareto_df_limits_to_top_n() -> None:
    rows = [
        _row("a1", "NS-02", "A13", 4.0),
        _row("a2", "NS-02", "A13", 4.0),
        _row("b1", "RI-05", "A12", 3.0),
        _row("c1", "NH-09", "A20", 5.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = pareto_df(diag, top_n=2)
    assert list(df["criterion_id"])[0] == "NS-02"
    assert len(df) == 2


def test_avoidance_gap_df_uses_exact_near_miss_threshold() -> None:
    rows = [
        _row("s1", "NS-02", "A13", 8.0),
        _row("s2", "NS-02", "A13", 18.0),
        _row("s3", "NS-02", "A13", 30.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = gap_df(
        diag, top_n=5, max_gap=200.0, near_only=True,
        near_miss_gap_pct=15.0,
    )
    assert sorted(df["required_relaxation_pct"]) == [8.0]


def test_avoidance_gap_df_max_gap_caps_rows() -> None:
    rows = [
        _row("s1", "NS-02", "A13", 5.0),
        _row("s2", "NS-02", "A13", 40.0),
        _row("s3", "NS-02", "A13", 120.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = gap_df(
        diag, top_n=5, max_gap=50.0, near_only=False,
        near_miss_gap_pct=25.0,
    )
    assert sorted(df["required_relaxation_pct"]) == [5.0, 40.0]


def test_avoidance_unlock_df_selects_metric_column() -> None:
    rows = [
        _row("s1", "NS-02", "A13", 4.0),
        _row("s2", "NS-02", "A13", 6.0),
    ]
    diag = aggregate_diagnostics(rows, unlock_steps=(5.0, 10.0))
    failures_df = unlock_df(
        diag, top_n=5, metric="criterion_failures_resolved",
    )
    survivor_df = unlock_df(
        diag, top_n=5, metric="single_criterion_survivor_unlocks",
    )
    assert "n" in failures_df.columns
    assert "n" in survivor_df.columns
    failures_5 = failures_df[failures_df["step"] == "5%"]["n"].iat[0]
    assert failures_5 == 1


def test_avoidance_near_miss_uses_exact_threshold_no_silent_widening() -> None:
    rows = [
        _row("s1", "NS-02", "A13", 4.0),
        _row("s2", "NS-02", "A13", 12.0),
    ]
    diag = aggregate_diagnostics(rows)
    df = near_miss_df(diag, near_miss_gap_pct=10.0)
    assert sorted(df["relaxation_pct"]) == [4.0]


def _row(
    site_id: str, criterion_id: str, code: str, pct: float | None,
) -> AvoidanceFlagRow:
    return AvoidanceFlagRow(
        site_id=site_id, site_name=f"site-{site_id}", country_code="RO",
        smr_key="nuscale_voygr6", criterion_id=criterion_id,
        criterion_name=f"Criterion {criterion_id}", code=code,
        measured=None, threshold=None, units=None,
        required_relaxation_pct=pct, justification="test",
    )
