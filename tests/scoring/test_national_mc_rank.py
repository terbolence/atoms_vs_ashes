# man_hours: 1.0
"""Unit tests for national Monte Carlo rank simulation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from atoms_vs_ashes.scoring._national_mc_rank import (
    run_national_mc_rank_simulation,
    write_national_mc_rank_csv,
)


@dataclass
class _RankingRowStub:
    site_id: str
    smr_key: str
    criterion_id: str
    score_0_10: float
    score_low_0_10: float | None = None
    score_high_0_10: float | None = None


@dataclass
class _VerdictStub:
    phase: str
    verdict: str


class _CriterionStub:
    participates_in_composite = True


def _row(site: str, score: float, lo=None, hi=None) -> _RankingRowStub:
    return _RankingRowStub(
        site_id=site, smr_key="ns", criterion_id="NS-01",
        score_0_10=score, score_low_0_10=lo, score_high_0_10=hi,
    )


def test_mc_rank_probabilities_are_deterministic() -> None:
    sites_rows = {
        ("a", "ns"): [_row("a", 8.0, 7.0, 9.0)],
        ("b", "ns"): [_row("b", 7.0, 6.0, 8.0)],
        ("c", "ns"): [_row("c", 6.0, 5.0, 7.0)],
    }
    countries = {pair: "RO" for pair in sites_rows}
    kwargs = dict(
        sites_rows=sites_rows,
        verdicts_by_pair={},
        country_by_pair=countries,
        weights={"NS-01": 1.0},
        criteria={"NS-01": _CriterionStub()},
        iterations=50,
        seed=123,
        min_pairs=3,
    )
    rows1 = run_national_mc_rank_simulation(**kwargs)
    rows2 = run_national_mc_rank_simulation(**kwargs)
    assert rows1 == rows2
    assert len(rows1) == 3
    assert all(r.iterations == 50 for r in rows1)
    assert all(0.0 <= r.p_rank_1 <= 1.0 for r in rows1)
    assert all(r.p_rank_1 <= r.p_rank_le_3 <= r.p_rank_le_5 for r in rows1)
    assert all(r.small_n is False for r in rows1)


def test_excluded_pairs_are_omitted() -> None:
    sites_rows = {
        ("a", "ns"): [_row("a", 8.0)],
        ("b", "ns"): [_row("b", 7.0)],
    }
    verdicts = {
        ("b", "ns"): [_VerdictStub(phase="exclusionary", verdict="fail")],
    }
    rows = run_national_mc_rank_simulation(
        sites_rows, verdicts, {("a", "ns"): "RO", ("b", "ns"): "RO"},
        weights={"NS-01": 1.0}, criteria={"NS-01": _CriterionStub()},
        iterations=5, seed=1,
    )
    assert [r.site_id for r in rows] == ["a"]
    assert rows[0].eligible_pair_count == 1
    assert rows[0].small_n is True


def test_iterations_must_be_positive() -> None:
    with pytest.raises(ValueError, match="iterations"):
        run_national_mc_rank_simulation(
            {}, {}, {}, weights={"NS-01": 1.0}, iterations=0,
        )


def test_write_mc_rank_csv(tmp_path) -> None:
    sites_rows = {("a", "ns"): [_row("a", 8.0)]}
    rows = run_national_mc_rank_simulation(
        sites_rows, {}, {("a", "ns"): "RO"},
        weights={"NS-01": 1.0}, criteria={"NS-01": _CriterionStub()},
        iterations=3, seed=1,
    )
    path = write_national_mc_rank_csv(tmp_path, rows, stamp="20260516")
    assert path.name == "20260516_national_mc_rank_distribution.csv"
    assert "p_rank_1" in path.read_text(encoding="utf-8").splitlines()[0]
