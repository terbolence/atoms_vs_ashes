# man_hours: 0.75
"""Merge ranking scores + screening phases into one per-criterion bar table."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.db.models_scoring_definitions import (
    CompiledScoringSnapshot,
    ScoringRunSnapshot,
)


def load_bundle_criterion_ids_ordered(
    session: Session, run_id: str, smr_key: str,
) -> list[str] | None:
    """Return criterion IDs from the compiled snapshot bundle for ``smr_key``."""
    link = session.get(ScoringRunSnapshot, run_id)
    if link is None:
        return None
    snap = session.get(CompiledScoringSnapshot, link.snapshot_id)
    if snap is None or not snap.bundles_by_smr:
        return None
    bundles: dict = snap.bundles_by_smr
    bundle = bundles.get(smr_key)
    if bundle is None and len(bundles) == 1:
        bundle = next(iter(bundles.values()))
    if not bundle:
        return None
    return list(bundle.keys())


def fallback_criterion_ids(
    ranking: list[RankingScore],
    verdicts: list[ScreeningVerdict],
) -> list[str]:
    ids = {str(r.criterion_id) for r in ranking} | {
        str(v.criterion_id) for v in verdicts
    }
    return sorted(ids)


def _family(criterion_id: str) -> str:
    head = criterion_id.split("-", 1)[0]
    return head.lower()[:2] if head else "??"


def _screening_highlight(
    verdicts: list[ScreeningVerdict],
) -> str | None:
    """Worst actionable screening role for one criterion (for bar colouring)."""
    if any(
        v.phase == "exclusionary" and v.verdict == "fail"
        for v in verdicts
    ):
        return "exclusion"
    if any(
        v.phase == "avoidance"
        and v.verdict in ("fail", "caution")
        for v in verdicts
    ):
        return "avoidance"
    return None


SEMANTIC_EXCLUSION = "Exclusion"
SEMANTIC_AVOIDANCE = "Avoidance"
SEMANTIC_NO_RANK = "No 0–10 score"

# Two-letter prefixes from criterion IDs (e.g. NH-02 → nh) → legend text for charts.
_FAMILY_LEGEND_LABELS: dict[str, str] = {
    "bf": "Basic filters (BF)",
    "nh": "Natural hazards (NH)",
    "hi": "Human-induced hazards (HI)",
    "ri": "Radiological impact (RI)",
    "ep": "Emergency planning (EP)",
    "ns": "Non-safety & site (NS)",
}


def chart_semantic_legend_label(semantic: str) -> str:
    """Map rubric family code or screening token to a human-readable legend label."""
    if semantic in (SEMANTIC_EXCLUSION, SEMANTIC_AVOIDANCE, SEMANTIC_NO_RANK):
        return semantic
    key = semantic.strip().lower()
    return _FAMILY_LEGEND_LABELS.get(key, semantic)


def merge_criterion_bar_semantics(
    *,
    ordered_ids: list[str],
    ranking: list[RankingScore],
    all_verdicts: list[ScreeningVerdict],
) -> list[tuple[str, str, float | None, str]]:
    """Return rows ``(criterion_id, family, score_or_none, semantic_legend_key)``."""
    rank_map = {str(r.criterion_id): r for r in ranking}
    by_cid: dict[str, list[ScreeningVerdict]] = defaultdict(list)
    for v in all_verdicts:
        by_cid[str(v.criterion_id)].append(v)
    out: list[tuple[str, str, float | None, str]] = []
    for cid in ordered_ids:
        fam = _family(cid)
        rv = rank_map.get(cid)
        vs = by_cid.get(cid, [])
        if rv is not None and rv.score_0_10 is not None:
            out.append(
                (
                    cid,
                    fam,
                    float(rv.score_0_10),
                    fam,
                )
            )
            continue
        hl = _screening_highlight(vs)
        if hl == "exclusion":
            out.append((cid, fam, None, SEMANTIC_EXCLUSION))
        elif hl == "avoidance":
            out.append((cid, fam, None, SEMANTIC_AVOIDANCE))
        else:
            out.append((cid, fam, None, SEMANTIC_NO_RANK))
    return out


__all__ = [
    "SEMANTIC_AVOIDANCE",
    "SEMANTIC_EXCLUSION",
    "SEMANTIC_NO_RANK",
    "chart_semantic_legend_label",
    "fallback_criterion_ids",
    "load_bundle_criterion_ids_ordered",
    "merge_criterion_bar_semantics",
]
