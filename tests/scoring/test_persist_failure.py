# man_hours: 1.0
"""Reconciliation test for the failure-analysis writers.

Validates that the long-form rows produced by
``scripts._phase_1_6_failure_db.persist_breakdown`` match the
counts in the synthetic :class:`FailureBreakdown` they are derived
from. Uses ``MagicMock`` for the SQLAlchemy session so the test
runs without a live DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    PairOutcome,
    SmrStat,
)
from scripts._phase_1_6_failure_db import persist_breakdown


def _synthetic_breakdown() -> FailureBreakdown:
    site_a, site_b = uuid.uuid4(), uuid.uuid4()
    pairs = [
        PairOutcome(
            site_id=site_a, smr_key="nuscale_voygr6", country_code="RO",
            bucket="survived", hard_criteria=(), floor_criteria=(),
        ),
        PairOutcome(
            site_id=site_b, smr_key="nuscale_voygr6", country_code="RO",
            bucket="hard_only", hard_criteria=("NH-04",), floor_criteria=(),
        ),
    ]
    return FailureBreakdown(
        total_pairs=2,
        survived=1,
        hard_only=1,
        floor_only=0,
        both=0,
        n_distinct_sites=2,
        n_distinct_smrs=1,
        per_criterion=[
            CriterionStat("NH-04", "Seismic", hard_pairs=1, floor_pairs=0,
                          union_pairs=1, intersection_pairs=0),
        ],
        per_country=[
            CountryStat("RO", n_sites=2, n_pairs=2, survived=1,
                        hard_only=1, floor_only=0, both=0,
                        n_sites_with_survivor=1),
        ],
        per_smr=[
            SmrStat("nuscale_voygr6", n_pairs=2, survived=1,
                    hard_only=1, floor_only=0, both=0),
        ],
        pair_outcomes=pairs,
        multi_failure_histogram={1: 1},
    )


def test_persist_breakdown_emits_outcomes_and_aggregates():
    breakdown = _synthetic_breakdown()
    session = MagicMock()
    n_out, n_aggs = persist_breakdown(
        session,
        run_id="r-test",
        breakdown=breakdown,
        country_by_site={p.site_id: p.country_code for p in breakdown.pair_outcomes},
    )
    assert n_out == 2
    assert n_aggs > 0
    aggregate_call = session.bulk_save_objects.call_args_list[1]
    rows = aggregate_call[0][0]
    axes = {r.axis for r in rows}
    assert "summary" in axes
    assert "criterion" in axes
    assert "country" in axes
    assert "smr" in axes
    assert "multi_failure_histogram" in axes


def test_persist_breakdown_no_session_is_noop():
    out, aggs = persist_breakdown(
        None, run_id=None, breakdown=_synthetic_breakdown(),
    )
    assert (out, aggs) == (0, 0)
