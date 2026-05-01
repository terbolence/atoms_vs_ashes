# man_hours: 2.0
"""DB reads for the hand-pick shortlist + avoidance annex report.

``CountrySiteRanking`` rows are keyed by **sensitivity** ``run_id``;
``CompositeRanking`` / ``ScreeningVerdict`` rows for a scoring pass use
**scoring** ``run_id``.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, ScreeningVerdict, Site
from atoms_vs_ashes.db.queries import top_n_per_country

AVOIDANCE_TRIGGER_VERDICTS = frozenset({"caution", "fail"})


def avoidance_annex_includes_row(*, phase: str, verdict: str) -> bool:
    """True when this verdict row counts as an avoidance trigger (matches composite gate)."""
    return phase == "avoidance" and verdict in AVOIDANCE_TRIGGER_VERDICTS


def _composite_flags_stmt(
    *,
    scoring_run_id: str,
    weight_profile: str,
    site_ids: list[uuid.UUID],
    smr_key: str,
):
    return (
        select(
            CompositeRanking.site_id,
            CompositeRanking.smr_key,
            CompositeRanking.passed_exclusionary,
            CompositeRanking.passed_avoidance,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.rank_position,
        )
        .where(
            CompositeRanking.run_id == scoring_run_id,
            CompositeRanking.weight_profile == weight_profile,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.site_id.in_(site_ids),
        )
    )


def load_shortlist_grouped(
    session: Session,
    *,
    sensitivity_run_id: str,
    scoring_run_id: str,
    smr_key: str,
    top_n: int,
    weight_profile: str = "baseline",
) -> dict[str, list[dict[str, Any]]]:
    """Top ``top_n`` sites per country (sensitivity ranks) enriched with composite pass flags."""
    flat = top_n_per_country(
        session,
        run_id=sensitivity_run_id,
        smr_key=smr_key,
        n=top_n,
        qualification_mode="normal",
    )
    if not flat:
        return {}
    site_ids = list({r["site_id"] for r in flat})
    comp_rows = session.execute(
        _composite_flags_stmt(
            scoring_run_id=scoring_run_id,
            weight_profile=weight_profile,
            site_ids=site_ids,
            smr_key=smr_key,
        )
    ).all()
    comp_by_site: dict[uuid.UUID, dict[str, Any]] = {}
    for row in comp_rows:
        comp_by_site[row.site_id] = dict(row._mapping)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in flat:
        cc = str(r["country_code"])
        comp = comp_by_site.get(r["site_id"], {})
        merged = {
            **r,
            "passed_exclusionary": comp.get("passed_exclusionary"),
            "passed_avoidance": comp.get("passed_avoidance"),
            "composite_ranking_score": comp.get("composite_score"),
            "composite_ranking_low": comp.get("composite_score_low"),
            "composite_ranking_high": comp.get("composite_score_high"),
            "rank_position": comp.get("rank_position"),
        }
        grouped[cc].append(merged)
    return {k: grouped[k] for k in sorted(grouped)}


def load_full_pass_pairs(
    session: Session,
    *,
    scoring_run_id: str,
    smr_key: str,
    weight_profile: str = "baseline",
) -> list[dict[str, Any]]:
    """All (site, smr) with exclusionary pass and avoidance pass."""
    stmt = (
        select(
            Site.country_code,
            Site.name.label("site_name"),
            Site.site_id,
            CompositeRanking.smr_key,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.rank_position,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            CompositeRanking.run_id == scoring_run_id,
            CompositeRanking.weight_profile == weight_profile,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.passed_exclusionary.is_(True),
            CompositeRanking.passed_avoidance.is_(True),
        )
        .order_by(Site.country_code, Site.name)
    )
    return [dict(r._mapping) for r in session.execute(stmt).all()]


def load_avoidance_flagged_pairs(
    session: Session,
    *,
    scoring_run_id: str,
    smr_key: str,
    weight_profile: str = "baseline",
) -> list[dict[str, Any]]:
    """Sites that pass exclusionary but fail avoidance (same gate as ``passed_avoidance``)."""
    stmt = (
        select(
            Site.country_code,
            Site.name.label("site_name"),
            Site.site_id,
            CompositeRanking.smr_key,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.rank_position,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            CompositeRanking.run_id == scoring_run_id,
            CompositeRanking.weight_profile == weight_profile,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.passed_exclusionary.is_(True),
            CompositeRanking.passed_avoidance.is_(False),
        )
        .order_by(Site.country_code, Site.name)
    )
    return [dict(r._mapping) for r in session.execute(stmt).all()]


def load_avoidance_verdicts_for_pairs(
    session: Session,
    *,
    scoring_run_id: str,
    pairs: list[tuple[uuid.UUID, str]],
) -> dict[tuple[uuid.UUID, str], list[dict[str, Any]]]:
    """Per (site_id, smr_key), all avoidance-phase trigger rows for the scoring run."""
    if not pairs:
        return {}
    site_ids = {sid for sid, _ in pairs}
    smr_keys = {sk for _, sk in pairs}
    rows = session.execute(
        select(ScreeningVerdict)
        .where(
            ScreeningVerdict.run_id == scoring_run_id,
            ScreeningVerdict.phase == "avoidance",
            ScreeningVerdict.verdict.in_(tuple(AVOIDANCE_TRIGGER_VERDICTS)),
            ScreeningVerdict.site_id.in_(site_ids),
            ScreeningVerdict.smr_key.in_(smr_keys),
        )
        .order_by(
            ScreeningVerdict.site_id,
            ScreeningVerdict.smr_key,
            ScreeningVerdict.criterion_id,
            ScreeningVerdict.prompt_key,
        )
    ).scalars().all()
    pair_set = set(pairs)
    out: dict[tuple[uuid.UUID, str], list[dict[str, Any]]] = defaultdict(list)
    for v in rows:
        key = (v.site_id, str(v.smr_key))
        if key not in pair_set:
            continue
        out[key].append(
            {
                "criterion_id": v.criterion_id,
                "phase": v.phase,
                "verdict": v.verdict,
                "measured_value": v.measured_value,
                "threshold": v.threshold,
                "measured_value_numeric": (
                    float(v.measured_value_numeric)
                    if v.measured_value_numeric is not None
                    else None
                ),
                "threshold_numeric": (
                    float(v.threshold_numeric)
                    if v.threshold_numeric is not None
                    else None
                ),
                "measured_units": v.measured_units,
                "justification": v.justification,
                "confidence": v.confidence,
                "data_sources": list(v.data_sources) if v.data_sources else None,
                "prompt_key": v.prompt_key,
            }
        )
    return dict(out)


__all__ = [
    "AVOIDANCE_TRIGGER_VERDICTS",
    "avoidance_annex_includes_row",
    "load_avoidance_flagged_pairs",
    "load_avoidance_verdicts_for_pairs",
    "load_full_pass_pairs",
    "load_shortlist_grouped",
]
