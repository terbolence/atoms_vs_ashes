# man_hours: 1.0
"""Regression tests for the non-exclusionary composite scoring pool."""

from __future__ import annotations

import uuid

import pytest

from atoms_vs_ashes.db.models import RankingScore
from atoms_vs_ashes.scoring.composite import compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import Criterion, weight_normalisation
from atoms_vs_ashes.scoring.sensitivity import run_monte_carlo


def _criterion(
    criterion_id: str,
    phases: list[str],
    weight_factor: int,
) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        name=criterion_id,
        phases=phases,
        weight_factor=weight_factor,
        normalised_weight_pct=0.0,
    )


def _row(criterion_id: str, score: float) -> RankingScore:
    return RankingScore(
        site_id=uuid.uuid4(),
        smr_key="demo",
        criterion_id=criterion_id,
        score_0_10=score,
        score_low_0_10=score,
        score_high_0_10=score,
        weight_factor=5,
        weight_normalised=None,
        quality_flag="high",
        confidence="high",
        justification="{}",
        run_id="run-test",
    )


def test_weight_normalisation_excludes_exclusionary_criteria():
    bundle = {
        "NH-02": _criterion("NH-02", ["exclusionary", "ranking"], 10),
        "HI-01": _criterion("HI-01", ["avoidance", "ranking"], 5),
        "NS-02": _criterion("NS-02", ["ranking"], 5),
    }

    weights = weight_normalisation(bundle)

    assert set(weights) == {"HI-01", "NS-02"}
    assert weights["HI-01"] == pytest.approx(0.5)
    assert weights["NS-02"] == pytest.approx(0.5)


def test_composite_ignores_exclusionary_ranking_rows():
    site_id = uuid.uuid4()
    criteria = {
        "NH-02": _criterion("NH-02", ["exclusionary", "ranking"], 10),
        "HI-01": _criterion("HI-01", ["ranking"], 5),
    }

    result = compute_composite_for_site_smr(
        site_id=site_id,
        smr_key="demo",
        ranking_rows=[_row("NH-02", 10.0), _row("HI-01", 4.0)],
        verdicts=[],
        weights={"NH-02": 0.5, "HI-01": 0.5},
        criteria=criteria,
    )

    assert result.composite_score == pytest.approx(4.0)
    assert [c.criterion_id for c in result.components] == ["HI-01"]


def test_monte_carlo_filters_exclusionary_rows_with_criteria():
    criteria = {
        "NH-02": _criterion("NH-02", ["exclusionary", "ranking"], 10),
        "HI-01": _criterion("HI-01", ["ranking"], 5),
    }

    result = run_monte_carlo(
        uuid.uuid4(),
        "demo",
        [_row("NH-02", 10.0), _row("HI-01", 2.0)],
        [],
        {"NH-02": 0.5, "HI-01": 0.5},
        criteria,
        iterations=5,
    )

    assert result.mean == pytest.approx(2.0)
