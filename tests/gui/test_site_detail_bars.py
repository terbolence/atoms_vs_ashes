# man_hours: 0.5
"""Unit tests for per-criterion bar merging (ranking + screening)."""

from __future__ import annotations

import uuid

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.gui._results_site_detail_bars import (
    SEMANTIC_AVOIDANCE,
    SEMANTIC_EXCLUSION,
    SEMANTIC_NO_RANK,
    SEMANTIC_UNSCORED,
    chart_semantic_legend_label,
    merge_criterion_bar_semantics,
)


def _rs(cid: str, score: float, *, quality_flag: str | None = None) -> RankingScore:
    return RankingScore(
        site_id=uuid.uuid4(),
        smr_key="x",
        criterion_id=cid,
        score_0_10=score,
        quality_flag=quality_flag,
        confidence="high",
        justification="",
        run_id="r1",
    )


def _sv(
    cid: str,
    *,
    phase: str,
    verdict: str,
) -> ScreeningVerdict:
    return ScreeningVerdict(
        site_id=uuid.uuid4(),
        smr_key="x",
        criterion_id=cid,
        phase=phase,
        prompt_key=None,
        verdict=verdict,
        justification="",
        confidence="high",
        run_id="r1",
    )


def test_merge_includes_missing_rank_with_screening_roles() -> None:
    ordered = ["NH-02", "NH-03", "HI-01"]
    ranking = [_rs("NH-03", 9.0), _rs("HI-01", 5.0)]
    verdicts = [
        _sv("NH-02", phase="avoidance", verdict="caution"),
    ]
    rows = merge_criterion_bar_semantics(
        ordered_ids=ordered,
        ranking=ranking,
        all_verdicts=verdicts,
    )
    by_id = {r[0]: r for r in rows}
    assert by_id["NH-02"][3] == SEMANTIC_AVOIDANCE
    assert by_id["NH-03"][2] == 9.0
    assert by_id["HI-01"][2] == 5.0


def test_merge_exclusion_over_avoidance_for_bar_colour() -> None:
    ordered = ["EP-01"]
    ranking = []
    verdicts = [
        _sv("EP-01", phase="exclusionary", verdict="fail"),
        _sv("EP-01", phase="avoidance", verdict="caution"),
    ]
    rows = merge_criterion_bar_semantics(
        ordered_ids=ordered,
        ranking=ranking,
        all_verdicts=verdicts,
    )
    assert rows[0][3] == SEMANTIC_EXCLUSION


def test_chart_semantic_legend_label_includes_full_family_names() -> None:
    assert chart_semantic_legend_label("nh") == "Natural hazards (NH)"
    assert chart_semantic_legend_label("NH") == "Natural hazards (NH)"
    assert chart_semantic_legend_label("ep") == "Emergency planning (EP)"
    assert chart_semantic_legend_label(SEMANTIC_EXCLUSION) == SEMANTIC_EXCLUSION


def test_merge_no_rank_when_no_score_no_screen() -> None:
    ordered = ["BF-01"]
    ranking = []
    verdicts = []
    rows = merge_criterion_bar_semantics(
        ordered_ids=ordered,
        ranking=ranking,
        all_verdicts=verdicts,
    )
    assert rows[0][3] == SEMANTIC_NO_RANK


def test_unscored_ranking_row_is_not_rendered_as_real_score() -> None:
    ordered = ["HI-07"]
    ranking = [_rs("HI-07", 5.0, quality_flag="unscored")]
    rows = merge_criterion_bar_semantics(
        ordered_ids=ordered,
        ranking=ranking,
        all_verdicts=[],
    )

    assert rows[0][2] is None
    assert rows[0][3] == SEMANTIC_UNSCORED
    assert chart_semantic_legend_label(SEMANTIC_UNSCORED) == "Unscored"
