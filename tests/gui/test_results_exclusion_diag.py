# man_hours: 0.75
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
