# man_hours: 1.0
"""Regression tests for the non-exclusionary composite scoring pool."""

from __future__ import annotations

import uuid

import pytest

from atoms_vs_ashes.db.models import RankingScore
from atoms_vs_ashes.scoring.composite import compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    weight_basis_resolution,
    weight_normalisation,
)
from atoms_vs_ashes.scoring.sensitivity import run_monte_carlo


def _criterion(
    criterion_id: str,
    phases: list[str],
    weight_factor: int,
    *,
    weight_factors: dict[str, int] | None = None,
    weight_basis_source: dict[str, str] | None = None,
) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        name=criterion_id,
        phases=phases,
        weight_factor=weight_factor,
        normalised_weight_pct=0.0,
        weight_factors=weight_factors,
        weight_basis_source=weight_basis_source,
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


def test_weight_normalisation_named_basis_uses_weight_factors_table():
    bundle = {
        "HI-01": _criterion(
            "HI-01",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 8},
            weight_basis_source={"epri": "EPRI Site Selection Guide §4.2"},
        ),
        "NS-02": _criterion(
            "NS-02",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 2},
        ),
    }

    baseline_weights = weight_normalisation(bundle)
    assert baseline_weights["HI-01"] == pytest.approx(0.5)
    assert baseline_weights["NS-02"] == pytest.approx(0.5)

    epri_weights = weight_normalisation(bundle, basis="epri")
    assert epri_weights["HI-01"] == pytest.approx(8 / 10)
    assert epri_weights["NS-02"] == pytest.approx(2 / 10)


def test_weight_normalisation_named_basis_falls_back_to_baseline_when_missing(
    caplog: pytest.LogCaptureFixture,
):
    bundle = {
        "HI-01": _criterion(
            "HI-01",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 8},
        ),
        "NS-02": _criterion(
            "NS-02",
            ["ranking"],
            5,
            weight_factors=None,
        ),
    }

    with caplog.at_level("WARNING", logger="atoms_vs_ashes.scoring.rubric"):
        weights = weight_normalisation(bundle, basis="epri")

    assert weights["HI-01"] == pytest.approx(8 / 13)
    assert weights["NS-02"] == pytest.approx(5 / 13)
    assert any(
        "weight_factors['epri']" in record.message and "NS-02" in record.message
        for record in caplog.records
    )


def test_weight_basis_resolution_reports_per_criterion_provenance():
    bundle = {
        "HI-01": _criterion(
            "HI-01",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 8},
        ),
        "NS-02": _criterion("NS-02", ["ranking"], 5, weight_factors=None),
    }

    resolved = weight_basis_resolution(bundle, basis="epri")

    assert resolved["HI-01"] == (8, "epri")
    assert resolved["NS-02"] == (5, "baseline")


def test_weight_normalisation_combines_perturbation_with_basis():
    bundle = {
        "HI-01": _criterion(
            "HI-01",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 8},
        ),
        "NS-02": _criterion(
            "NS-02",
            ["ranking"],
            5,
            weight_factors={"baseline": 5, "epri": 2},
        ),
    }

    baseline_w_plus = weight_normalisation(bundle, profile="w_plus_20")
    epri_w_plus = weight_normalisation(bundle, profile="w_plus_20", basis="epri")

    assert baseline_w_plus["HI-01"] == pytest.approx(0.5)
    assert epri_w_plus["HI-01"] == pytest.approx(0.8)


def test_weight_factors_invalid_value_rejected():
    with pytest.raises(ValueError, match=r"weight_factors\['epri'\] = 11"):
        Criterion(
            criterion_id="HI-01",
            name="Aircraft Crash",
            phases=["ranking"],
            weight_factor=5,
            normalised_weight_pct=0.0,
            weight_factors={"baseline": 5, "epri": 11},
        )


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
