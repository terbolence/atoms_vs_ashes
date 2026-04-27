# man_hours: 2.0
"""Database diagnostics for the suitable-site scoring audit."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, RankingScore, ScreeningVerdict, Site


@dataclass(frozen=True)
class SuitabilityCounts:
    run_id: str
    weight_profile: str
    n_pairs: int
    n_sites: int
    n_countries: int
    pairs_pass_exclusionary: int
    pairs_pass_both: int
    sites_pass_exclusionary: int
    sites_pass_both: int
    countries_pass_exclusionary: int
    countries_pass_both: int
    pairs_hard_failed: int
    pairs_avoidance_flagged: int


@dataclass(frozen=True)
class CodeImpact:
    code: str
    phase: str
    verdict: str
    rows: int
    distinct_sites: int
    countries: int
    criteria: str


@dataclass(frozen=True)
class Ep01DisjunctImpact:
    bucket: str
    rows: int
    distinct_sites: int
    countries: int


@dataclass(frozen=True)
class CriterionScoreSummary:
    criterion_id: str
    rows: int
    unscored_rows: int
    insufficient_rows: int
    min_score: float | None
    median_score: float | None
    max_score: float | None


def resolve_latest_run_id(session: Session, weight_profile: str = "baseline") -> str | None:
    """Return the newest composite run for ``weight_profile``."""
    return session.execute(
        select(CompositeRanking.run_id)
        .where(CompositeRanking.weight_profile == weight_profile)
        .order_by(CompositeRanking.ranked_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def suitability_counts(
    session: Session,
    *,
    run_id: str,
    weight_profile: str = "baseline",
) -> SuitabilityCounts:
    rows = session.execute(
        select(
            CompositeRanking.site_id,
            CompositeRanking.passed_exclusionary,
            CompositeRanking.passed_avoidance,
            Site.country_code,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            (CompositeRanking.run_id == run_id)
            & (CompositeRanking.weight_profile == weight_profile)
        )
    ).all()
    sites = {sid for sid, *_rest in rows}
    countries = {str(cc) for *_flags, cc in rows}
    pass_excl_pairs = [(sid, cc) for sid, pe, _pa, cc in rows if pe]
    pass_both_pairs = [(sid, cc) for sid, pe, pa, cc in rows if pe and pa]
    return SuitabilityCounts(
        run_id=run_id,
        weight_profile=weight_profile,
        n_pairs=len(rows),
        n_sites=len(sites),
        n_countries=len(countries),
        pairs_pass_exclusionary=len(pass_excl_pairs),
        pairs_pass_both=len(pass_both_pairs),
        sites_pass_exclusionary=len({sid for sid, _ in pass_excl_pairs}),
        sites_pass_both=len({sid for sid, _ in pass_both_pairs}),
        countries_pass_exclusionary=len({str(cc) for _sid, cc in pass_excl_pairs}),
        countries_pass_both=len({str(cc) for _sid, cc in pass_both_pairs}),
        pairs_hard_failed=sum(1 for _sid, pe, _pa, _cc in rows if not pe),
        pairs_avoidance_flagged=sum(1 for _sid, pe, pa, _cc in rows if pe and not pa),
    )


def code_impacts(session: Session, *, run_id: str) -> list[CodeImpact]:
    rows = session.execute(
        select(
            ScreeningVerdict.prompt_key,
            ScreeningVerdict.phase,
            ScreeningVerdict.verdict,
            ScreeningVerdict.criterion_id,
            ScreeningVerdict.site_id,
            Site.country_code,
        )
        .join(Site, Site.site_id == ScreeningVerdict.site_id)
        .where(ScreeningVerdict.run_id == run_id)
    ).all()
    grouped: dict[tuple[str, str, str], dict[str, set | int]] = {}
    for prompt, phase, verdict, criterion, site_id, country in rows:
        code = str(prompt or criterion)
        key = (code, str(phase), str(verdict))
        item = grouped.setdefault(
            key, {"rows": 0, "sites": set(), "countries": set(), "criteria": set()}
        )
        item["rows"] = int(item["rows"]) + 1
        item["sites"].add(site_id)  # type: ignore[union-attr]
        item["countries"].add(str(country))  # type: ignore[union-attr]
        item["criteria"].add(str(criterion))  # type: ignore[union-attr]
    impacts = [
        CodeImpact(
            code=code,
            phase=phase,
            verdict=verdict,
            rows=int(item["rows"]),
            distinct_sites=len(item["sites"]),  # type: ignore[arg-type]
            countries=len(item["countries"]),  # type: ignore[arg-type]
            criteria="|".join(sorted(item["criteria"])),  # type: ignore[arg-type]
        )
        for (code, phase, verdict), item in grouped.items()
    ]
    return sorted(impacts, key=lambda r: (-r.rows, r.code, r.phase, r.verdict))


def ep01_disjunct_impacts(session: Session, *, run_id: str) -> list[Ep01DisjunctImpact]:
    rows = session.execute(
        select(ScreeningVerdict.measured_value, ScreeningVerdict.site_id, Site.country_code)
        .join(Site, Site.site_id == ScreeningVerdict.site_id)
        .where(
            (ScreeningVerdict.run_id == run_id)
            & (ScreeningVerdict.criterion_id == "EP-01")
            & (ScreeningVerdict.prompt_key == "E8")
        )
    ).all()
    grouped: dict[str, dict[str, set | int]] = {}
    for measured_raw, site_id, country in rows:
        bucket = _ep01_bucket(measured_raw)
        item = grouped.setdefault(bucket, {"rows": 0, "sites": set(), "countries": set()})
        item["rows"] = int(item["rows"]) + 1
        item["sites"].add(site_id)  # type: ignore[union-attr]
        item["countries"].add(str(country))  # type: ignore[union-attr]
    return [
        Ep01DisjunctImpact(
            bucket=bucket,
            rows=int(item["rows"]),
            distinct_sites=len(item["sites"]),  # type: ignore[arg-type]
            countries=len(item["countries"]),  # type: ignore[arg-type]
        )
        for bucket, item in sorted(grouped.items())
    ]


def _ep01_bucket(measured_raw: str | None) -> str:
    try:
        measured = json.loads(measured_raw or "{}")
    except json.JSONDecodeError:
        return "unparseable_measured_json"
    composite = measured.get("ep01_composite_score")
    trauma = measured.get("nearest_trauma_center_km")
    composite_fail = composite is not None and float(composite) < 30.0
    trauma_fail = trauma is not None and float(trauma) > 60.0
    if composite_fail and trauma_fail:
        return "both_disjuncts_triggered"
    if composite_fail:
        return "composite_score_lt_30"
    if trauma_fail:
        return "trauma_center_gt_60_km"
    if trauma is None:
        return "no_failure_or_missing_trauma_distance"
    return "no_failure"


def criterion_score_summaries(session: Session, *, run_id: str) -> list[CriterionScoreSummary]:
    by_criterion: dict[str, list[RankingScore]] = defaultdict(list)
    for row in session.execute(
        select(RankingScore).where(RankingScore.run_id == run_id)
    ).scalars():
        by_criterion[str(row.criterion_id)].append(row)
    return [
        _score_summary(cid, rows)
        for cid, rows in sorted(by_criterion.items())
    ]


def _score_summary(cid: str, rows: Iterable[RankingScore]) -> CriterionScoreSummary:
    items = list(rows)
    scores = sorted(float(r.score_0_10) for r in items if r.score_0_10 is not None)
    mid = scores[len(scores) // 2] if scores else None
    return CriterionScoreSummary(
        criterion_id=cid,
        rows=len(items),
        unscored_rows=sum(1 for r in items if r.quality_flag == "unscored"),
        insufficient_rows=sum(1 for r in items if r.confidence == "insufficient"),
        min_score=scores[0] if scores else None,
        median_score=mid,
        max_score=scores[-1] if scores else None,
    )
