# man_hours: 1.5
"""Unit tests for ``run_oat_importance_national``.

Builds a tiny synthetic two-country fixture with a single criterion
that matters in one country and not in the other, then checks that
the national OAT importance reflects that local difference (which a
global / regional OAT cannot capture).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pytest

from atoms_vs_ashes.scoring._national_oat import (
    NationalOATImportance,
    run_oat_importance_national,
)
from atoms_vs_ashes.scoring._suite_national_oat import (
    _ordered_rows,
    write_national_oat_csv,
)


# ---------------------------------------------------------------------------
# Synthetic doubles (no DB / no rubric YAML required)
# ---------------------------------------------------------------------------


@dataclass
class _RankingRowStub:
    """Mimics ``RankingScore`` fields read by the composite engine."""

    site_id: str
    smr_key: str
    criterion_id: str
    score_0_10: float
    score_low_0_10: float | None = None
    score_high_0_10: float | None = None
    quality_flag: str | None = None
    confidence: str = "high"


class _CriterionStub:
    """Minimal ``Criterion`` surface used by ``compute_composite_for_site_smr``."""

    def __init__(self, cid: str):
        self.criterion_id = cid
        self.name = cid
        self.phase = "ranking"
        self.is_exclusionary = False
        self.is_avoidance = False
        self.is_ranking = True
        self.participates_in_composite = True


def _criteria(*cids: str) -> dict[str, _CriterionStub]:
    return {cid: _CriterionStub(cid) for cid in cids}


def _row(
    site: str, smr: str, cid: str, score: float,
) -> _RankingRowStub:
    return _RankingRowStub(
        site_id=site, smr_key=smr, criterion_id=cid, score_0_10=score,
    )


# ---------------------------------------------------------------------------
# Fixture: two countries, two ranking criteria.
# In RO: NH dominates the order (sites differ on NH, agree on NS).
# In BG: NS dominates the order (sites differ on NS, agree on NH).
# A global OAT would average both effects and dilute them.
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_pairs():
    criteria = _criteria("NH-01", "NS-01")
    weights = {"NH-01": 0.5, "NS-01": 0.5}
    sites_rows: dict[tuple, list[_RankingRowStub]] = {
        # Romania: NH differs (5/7/9), NS constant (6). The descending NH
        # order is intentionally the reverse of the site-id tie-break order.
        ("ro_a", "ns"): [_row("ro_a", "ns", "NH-01", 5.0),
                         _row("ro_a", "ns", "NS-01", 6.0)],
        ("ro_b", "ns"): [_row("ro_b", "ns", "NH-01", 7.0),
                         _row("ro_b", "ns", "NS-01", 6.0)],
        ("ro_c", "ns"): [_row("ro_c", "ns", "NH-01", 9.0),
                         _row("ro_c", "ns", "NS-01", 6.0)],
        # Bulgaria: NS differs (5/7/9), NH constant (6), again reversing
        # the deterministic tie-break order after NS is dropped.
        ("bg_a", "ns"): [_row("bg_a", "ns", "NH-01", 6.0),
                         _row("bg_a", "ns", "NS-01", 5.0)],
        ("bg_b", "ns"): [_row("bg_b", "ns", "NH-01", 6.0),
                         _row("bg_b", "ns", "NS-01", 7.0)],
        ("bg_c", "ns"): [_row("bg_c", "ns", "NH-01", 6.0),
                         _row("bg_c", "ns", "NS-01", 9.0)],
    }
    verdicts_by_pair: dict[tuple, list] = {pair: [] for pair in sites_rows}
    country_by_pair = {
        ("ro_a", "ns"): "RO", ("ro_b", "ns"): "RO", ("ro_c", "ns"): "RO",
        ("bg_a", "ns"): "BG", ("bg_b", "ns"): "BG", ("bg_c", "ns"): "BG",
    }
    return (
        sites_rows, verdicts_by_pair, country_by_pair, weights, criteria,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_national_oat_picks_up_country_specific_drivers(synthetic_pairs):
    sites_rows, verdicts, country_by_pair, weights, criteria = synthetic_pairs
    rows = run_oat_importance_national(
        sites_rows, verdicts, country_by_pair,
        weights=weights, criteria=criteria, min_pairs=2,
    )
    by_key = {(r.country_code, r.smr_key, r.criterion_id): r for r in rows}

    # In RO dropping NH-01 collapses the rank-driving criterion → all sites
    # tie on the constant NS-01 score, so deltas should be > 0.
    ro_nh = by_key[("RO", "ns", "NH-01")]
    assert ro_nh.mean_abs_rank_change > 0
    assert ro_nh.pairs_compared == 3
    assert ro_nh.eligible_pair_count == 3
    assert ro_nh.small_n is False

    # In RO dropping NS-01 changes nothing about RO ordering (NS was flat).
    ro_ns = by_key[("RO", "ns", "NS-01")]
    assert ro_ns.mean_abs_rank_change == 0.0

    # Mirror in BG: NS-01 drives the order; NH-01 drop is a no-op.
    bg_ns = by_key[("BG", "ns", "NS-01")]
    bg_nh = by_key[("BG", "ns", "NH-01")]
    assert bg_ns.mean_abs_rank_change > 0
    assert bg_nh.mean_abs_rank_change == 0.0


def test_importance_score_normalised_by_eligible_pool(synthetic_pairs):
    sites_rows, verdicts, country_by_pair, weights, criteria = synthetic_pairs
    rows = run_oat_importance_national(
        sites_rows, verdicts, country_by_pair,
        weights=weights, criteria=criteria, min_pairs=2,
    )
    for r in rows:
        assert 0.0 <= r.importance_score <= 1.0
        if r.eligible_pair_count > 0:
            assert (
                r.importance_score
                == round(r.mean_abs_rank_change / r.eligible_pair_count, 4)
            )


def test_small_n_flag_threshold(synthetic_pairs):
    sites_rows, verdicts, country_by_pair, weights, criteria = synthetic_pairs
    rows = run_oat_importance_national(
        sites_rows, verdicts, country_by_pair,
        weights=weights, criteria=criteria, min_pairs=10,
    )
    assert rows, "should emit rows even when every slice is small_n"
    assert all(r.small_n is True for r in rows)


def test_csv_round_trip(tmp_path, synthetic_pairs):
    sites_rows, verdicts, country_by_pair, weights, criteria = synthetic_pairs
    rows = run_oat_importance_national(
        sites_rows, verdicts, country_by_pair,
        weights=weights, criteria=criteria, min_pairs=2,
    )
    csv_path = write_national_oat_csv(
        tmp_path, rows, criteria, stamp="20260516",
    )
    assert csv_path.exists()
    assert csv_path.name == "20260516_national_oat_importance.csv"
    contents = csv_path.read_text(encoding="utf-8").splitlines()
    header = contents[0].split(",")
    assert "country_code" in header
    assert "smr_key" in header
    assert "criterion_id" in header
    assert "importance_score" in header


def test_ordered_rows_sort_is_deterministic(synthetic_pairs):
    sites_rows, verdicts, country_by_pair, weights, criteria = synthetic_pairs
    rows = run_oat_importance_national(
        sites_rows, verdicts, country_by_pair,
        weights=weights, criteria=criteria, min_pairs=2,
    )
    ordered = _ordered_rows(rows, criteria)
    keys = [(r["country_code"], r["smr_key"]) for r in ordered]
    # Country×SMR runs contiguous; within each, higher importance first.
    assert keys == sorted(keys)
