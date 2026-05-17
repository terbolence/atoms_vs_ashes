# man_hours: 1.5
"""Unit tests for the pure national ranking helpers.

Validates dense-rank-within-slice behaviour, deterministic tie-breaking,
small-n flag handling, and per-slice stability metrics (Spearman rho,
top-K Jaccard, top1 flip) without touching the DB or any sensitivity
suite plumbing.
"""

from __future__ import annotations

from atoms_vs_ashes.scoring._national_ranking import (
    DEFAULT_MIN_NATIONAL_PAIRS,
    UNKNOWN_COUNTRY,
    NationalRankDelta,
    ScoredPair,
    group_by_country_smr,
    rank_within_country_smr,
    slice_sizes,
    spearman_for_slice,
    spearman_rho_from_ranks,
    summarise_rank_deltas,
    topk_jaccard_for_slice,
)


def _pair(site: str, smr: str, country: str, score: float) -> ScoredPair:
    return ScoredPair(
        site_id=site, smr_key=smr, country_code=country, composite_score=score,
    )


class TestRankWithinCountrySmr:
    def test_dense_rank_within_each_country_smr_slice(self):
        pairs = [
            _pair("a", "ns", "RO", 7.0),
            _pair("b", "ns", "RO", 9.0),
            _pair("c", "ns", "RO", 5.0),
            _pair("d", "ns", "BG", 6.0),
            _pair("e", "ns", "BG", 8.0),
        ]
        ranks = rank_within_country_smr(pairs)
        assert ranks[("b", "ns")] == 1
        assert ranks[("a", "ns")] == 2
        assert ranks[("c", "ns")] == 3
        assert ranks[("e", "ns")] == 1
        assert ranks[("d", "ns")] == 2

    def test_each_smr_gets_its_own_slice(self):
        pairs = [
            _pair("a", "ns", "RO", 7.0),
            _pair("a", "xe", "RO", 4.0),
            _pair("b", "ns", "RO", 9.0),
            _pair("b", "xe", "RO", 5.0),
        ]
        ranks = rank_within_country_smr(pairs)
        assert ranks[("b", "ns")] == 1 and ranks[("a", "ns")] == 2
        assert ranks[("b", "xe")] == 1 and ranks[("a", "xe")] == 2

    def test_deterministic_tie_break_by_site_id_string(self):
        pairs = [
            _pair("zeta", "ns", "RO", 8.0),
            _pair("alpha", "ns", "RO", 8.0),
            _pair("mu", "ns", "RO", 8.0),
        ]
        ranks = rank_within_country_smr(pairs)
        assert ranks[("alpha", "ns")] == 1
        assert ranks[("mu", "ns")] == 2
        assert ranks[("zeta", "ns")] == 3

    def test_unscored_pairs_are_dropped(self):
        pairs = [
            _pair("a", "ns", "RO", 7.0),
            ScoredPair("b", "ns", "RO", None),  # type: ignore[arg-type]
        ]
        ranks = rank_within_country_smr(pairs)
        assert list(ranks) == [("a", "ns")]

    def test_blank_country_codes_route_to_unknown(self):
        pairs = [
            _pair("a", "ns", "", 5.0),
            _pair("b", "ns", None, 6.0),  # type: ignore[arg-type]
        ]
        grouped = group_by_country_smr(pairs)
        assert (UNKNOWN_COUNTRY, "ns") in grouped
        assert len(grouped[(UNKNOWN_COUNTRY, "ns")]) == 2


class TestSliceSizes:
    def test_counts_per_slice_ignore_unscored(self):
        pairs = [
            _pair("a", "ns", "RO", 5.0),
            _pair("b", "ns", "RO", 6.0),
            ScoredPair("c", "ns", "RO", None),  # type: ignore[arg-type]
            _pair("d", "ns", "BG", 7.0),
        ]
        sizes = slice_sizes(pairs)
        assert sizes[("RO", "ns")] == 2
        assert sizes[("BG", "ns")] == 1


class TestSummariseRankDeltas:
    def test_per_pair_and_per_slice_outputs_align(self):
        baseline = [
            _pair("a", "ns", "RO", 9.0),
            _pair("b", "ns", "RO", 7.0),
            _pair("c", "ns", "RO", 5.0),
        ]
        scenario = [
            _pair("a", "ns", "RO", 8.0),
            _pair("b", "ns", "RO", 9.0),
            _pair("c", "ns", "RO", 4.0),
        ]
        per_pair, per_slice = summarise_rank_deltas(baseline, scenario)
        deltas = {r.site_id: r.rank_delta for r in per_pair}
        assert deltas["a"] == 1  # was 1, now 2
        assert deltas["b"] == -1  # was 2, now 1
        assert deltas["c"] == 0
        assert len(per_slice) == 1
        slice_row = per_slice[0]
        assert slice_row.country_code == "RO"
        assert slice_row.smr_key == "ns"
        assert slice_row.n_pairs == 3
        assert slice_row.mean_abs_rank_delta == round((1 + 1 + 0) / 3, 4)
        assert slice_row.max_abs_rank_delta == 1
        assert slice_row.top1_changed is True
        assert slice_row.small_n is False

    def test_pairs_missing_in_one_ranking_drop_from_delta_only(self):
        baseline = [
            _pair("a", "ns", "RO", 9.0),
            _pair("b", "ns", "RO", 7.0),
            _pair("c", "ns", "RO", 5.0),
        ]
        scenario = [
            _pair("a", "ns", "RO", 8.0),
            _pair("b", "ns", "RO", 9.0),
            # "c" excluded in scenario (e.g. caught by an E-code)
        ]
        per_pair, _ = summarise_rank_deltas(baseline, scenario)
        row_c = next(r for r in per_pair if r.site_id == "c")
        assert row_c.baseline_rank == 3
        assert row_c.scenario_rank is None
        assert row_c.rank_delta is None
        assert row_c.score_delta is None

    def test_small_n_flag_uses_min_pairs_threshold(self):
        baseline = [_pair("a", "ns", "RO", 9.0), _pair("b", "ns", "RO", 7.0)]
        scenario = [_pair("a", "ns", "RO", 7.0), _pair("b", "ns", "RO", 9.0)]
        per_pair, per_slice = summarise_rank_deltas(
            baseline, scenario, min_pairs=3,
        )
        assert all(r.small_n is True for r in per_pair)
        assert per_slice[0].small_n is True
        # default threshold is 3; raise it to confirm wiring
        assert DEFAULT_MIN_NATIONAL_PAIRS == 3
        _, per_slice2 = summarise_rank_deltas(
            baseline, scenario, min_pairs=2,
        )
        assert per_slice2[0].small_n is False


class TestStabilityHelpers:
    def test_spearman_rho_identity_is_one(self):
        rows = [
            NationalRankDelta(
                country_code="RO", smr_key="ns", site_id=sid,
                baseline_rank=r, scenario_rank=r,
                baseline_score=10.0 - r, scenario_score=10.0 - r,
                eligible_pair_count=3, small_n=False,
            )
            for sid, r in (("a", 1), ("b", 2), ("c", 3))
        ]
        assert spearman_for_slice(rows) == 1.0

    def test_spearman_rho_inverted_is_minus_one(self):
        baseline = {"a": 1, "b": 2, "c": 3}
        scenario = {"a": 3, "b": 2, "c": 1}
        assert spearman_rho_from_ranks(baseline, scenario) == -1.0

    def test_spearman_returns_none_for_singletons(self):
        assert spearman_rho_from_ranks({"a": 1}, {"a": 1}) is None

    def test_topk_jaccard_for_slice_returns_overlap_fraction(self):
        rows = [
            NationalRankDelta(
                country_code="RO", smr_key="ns", site_id=sid,
                baseline_rank=br, scenario_rank=sr,
                baseline_score=None, scenario_score=None,
                eligible_pair_count=5, small_n=False,
            )
            for sid, br, sr in (
                ("a", 1, 2),
                ("b", 2, 1),
                ("c", 3, 3),
                ("d", 4, 5),
                ("e", 5, 4),
            )
        ]
        # top-3 baseline = {a,b,c}; top-3 scenario = {a,b,c}; jaccard = 1.0
        assert topk_jaccard_for_slice(rows, k=3) == 1.0
        # top-2 baseline = {a,b}; top-2 scenario = {a,b}; jaccard = 1.0
        assert topk_jaccard_for_slice(rows, k=2) == 1.0
        # top-1 baseline = {a}; top-1 scenario = {b}; jaccard = 0
        assert topk_jaccard_for_slice(rows, k=1) == 0.0
