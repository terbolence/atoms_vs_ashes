# man_hours: 0.8
"""Tests for criterion activation registry integration in scoring."""

from __future__ import annotations

import uuid

import pytest

from atoms_vs_ashes.criterion_spec.activation import load_activation_registry
from atoms_vs_ashes.scoring.composite import compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import Criterion, weight_normalisation


def _criterion(
    criterion_id: str,
    phases: list[str],
    weight_factor: int,
    *,
    active: bool = True,
) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        name=criterion_id,
        phases=phases,
        weight_factor=weight_factor,
        normalised_weight_pct=0.0,
        active=active,
        inactive_reason=None if active else "test inactive",
        pending_implementation=None if active else "test connector",
        required_improvement=None if active else "IMP-TEST",
    )


def test_inactive_criterion_excluded_from_weight_normalisation():
    bundle = {
        "NS-02": _criterion("NS-02", ["ranking"], 5, active=True),
        "EP-05": _criterion("EP-05", ["ranking"], 5, active=False),
    }
    weights = weight_normalisation(bundle)
    assert set(weights) == {"NS-02"}
    assert weights["NS-02"] == pytest.approx(1.0)


def test_inactive_criterion_excluded_from_composite():
    site_id = uuid.uuid4()
    from atoms_vs_ashes.db.models import RankingScore

    criteria = {
        "NS-02": _criterion("NS-02", ["ranking"], 5, active=True),
        "EP-05": _criterion("EP-05", ["ranking"], 5, active=False),
    }
    weights = weight_normalisation(criteria)
    row_active = RankingScore(
        site_id=site_id,
        smr_key="demo",
        criterion_id="NS-02",
        score_0_10=7.0,
        score_low_0_10=7.0,
        score_high_0_10=7.0,
        weight_factor=5,
        weight_normalised=1.0,
        quality_flag="high",
        confidence="high",
        justification="{}",
        run_id="run-test",
    )
    row_inactive = RankingScore(
        site_id=site_id,
        smr_key="demo",
        criterion_id="EP-05",
        score_0_10=5.0,
        score_low_0_10=5.0,
        score_high_0_10=5.0,
        weight_factor=5,
        weight_normalised=None,
        quality_flag="unscored",
        confidence="insufficient",
        justification="{}",
        run_id="run-test",
    )
    result = compute_composite_for_site_smr(
        site_id=site_id,
        smr_key="demo",
        ranking_rows=[row_active, row_inactive],
        verdicts=[],
        weights=weights,
        criteria=criteria,
    )
    assert result.composite_score == pytest.approx(7.0)
    assert [c.criterion_id for c in result.components] == ["NS-02"]


def test_activation_registry_lists_seven_inactive():
    reg = load_activation_registry("config/scoring_specs")
    inactive = reg.inactive_ids()
    assert inactive == frozenset(
        {"EP-05", "HI-05", "HI-08", "NH-13", "NS-07", "NS-09", "NS-11"}
    )
    assert reg.entry_for("RI-01").active is True
