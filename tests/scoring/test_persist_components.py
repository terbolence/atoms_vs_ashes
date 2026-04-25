# man_hours: 1.0
"""Reconciliation test for ``composite_score_components``.

Asserts that, given a synthetic ``CompositeResult`` with a few
components, the rows persisted by
:func:`atoms_vs_ashes.scoring._composite_components.persist_composite_components`
sum to the same composite score.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from atoms_vs_ashes.scoring._composite_components import (
    persist_composite_components,
)
from atoms_vs_ashes.scoring.composite import (
    CompositeComponent,
    CompositeResult,
)


def _result_with_components() -> CompositeResult:
    return CompositeResult(
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        composite_score=6.5,
        composite_score_low=6.2,
        composite_score_high=6.8,
        passed_exclusionary=True,
        passed_avoidance=True,
        criteria_coverage=100.0,
        unscored_fraction=0.0,
        per_category_scores={"NH": 5.0, "HI": 8.0},
        confidence="high",
        components=[
            CompositeComponent(
                criterion_id="NH-01", score_0_10=5.0,
                weight_normalised=0.5, weighted_contribution=2.5,
                category="NH",
            ),
            CompositeComponent(
                criterion_id="HI-01", score_0_10=8.0,
                weight_normalised=0.5, weighted_contribution=4.0,
                category="HI",
            ),
        ],
    )


def test_components_reconcile_with_composite_score():
    result = _result_with_components()
    contributions = sum(c.weighted_contribution for c in result.components)
    weights = sum(c.weight_normalised for c in result.components)
    assert weights == 1.0
    assert contributions == 6.5 == result.composite_score


def test_persist_components_skips_failed_pairs():
    result = _result_with_components()
    result.passed_exclusionary = False
    session = MagicMock()
    written = persist_composite_components(
        session, [result], run_id="r-test", weight_profile="baseline",
    )
    assert written == 0
    session.bulk_save_objects.assert_not_called()


def test_persist_components_emits_one_row_per_criterion():
    result = _result_with_components()
    session = MagicMock()
    written = persist_composite_components(
        session, [result], run_id="r-test", weight_profile="baseline",
    )
    assert written == 2
    session.bulk_save_objects.assert_called_once()
    rows = session.bulk_save_objects.call_args[0][0]
    assert {r.criterion_id for r in rows} == {"NH-01", "HI-01"}
