# man_hours: 2.5
"""Cross-profile analytics for the Phase 1.6 consolidated audit.

Pulls every ``composite_rankings`` profile currently in the target DB,
then produces stability metrics vs. the ``baseline`` profile:

- Scored-pair coverage (how many (site, SMR) pairs carry a numeric
  ``composite_score`` under a profile).
- Pct-based top-N (top-5 % / top-10 %) overlap and Jaccard with the
  baseline ranking, size-independent by design.
- Mean / max absolute composite-score drift across all pairs that
  are scored under *both* profiles.
- Per-category roll-up for the weight profiles
  (``w_<CAT>_plus_20`` / ``w_<CAT>_minus_20``).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import fmean

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, Site


@dataclass(frozen=True)
class ProfileRow:
    """Flat composite row used only by this analytics helper."""

    site_id: str
    smr_key: str
    composite_score: float | None
    country_code: str


TOP_PCTS: tuple[float, float] = (0.05, 0.10)


@dataclass
class ProfileStats:
    """Per-profile stability + drift block."""

    label: str
    total_rows: int
    scored_rows: int
    top5pct_size: int
    top10pct_size: int
    top5pct_overlap: int
    top10pct_overlap: int
    top5pct_jaccard: float
    top10pct_jaccard: float
    mean_abs_drift: float | None
    max_abs_drift: float | None
    pairs_drift_compared: int


@dataclass
class PhaseAnalytics:
    """Full analytics bundle consumed by the markdown writer."""

    baseline_label: str
    baseline_total_rows: int
    baseline_scored_rows: int
    baseline_top5pct_size: int = 0
    baseline_top10pct_size: int = 0
    baseline_top10pct_countries: dict[str, int] = field(default_factory=dict)
    profiles: list[ProfileStats] = field(default_factory=list)
    per_category_weight: list[tuple[str, float, int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_profile_rows(session: Session) -> dict[str, list[ProfileRow]]:
    """Return ``{weight_profile: [ProfileRow, ...]}`` for the whole table.

    Site → country is joined in-process to keep the SQL tiny; the
    merged DB has ≲ 500 sites so the join is free.
    """
    country_by_site = {
        sid: code
        for sid, code in session.execute(select(Site.site_id, Site.country_code)).all()
    }
    rows_by_profile: dict[str, list[ProfileRow]] = defaultdict(list)
    stmt = select(
        CompositeRanking.weight_profile,
        CompositeRanking.site_id,
        CompositeRanking.smr_key,
        CompositeRanking.composite_score,
    )
    for profile, site_id, smr_key, score in session.execute(stmt).all():
        rows_by_profile[profile].append(
            ProfileRow(
                site_id=site_id,
                smr_key=smr_key,
                composite_score=(float(score) if score is not None else None),
                country_code=country_by_site.get(site_id, "??"),
            )
        )
    return dict(rows_by_profile)


def _top_keys(rows: list[ProfileRow], n: int) -> list[tuple[str, str]]:
    """Return the top-N (site_id, smr_key) keys by score, desc."""
    scored = [r for r in rows if r.composite_score is not None]
    scored.sort(key=lambda r: r.composite_score, reverse=True)  # type: ignore[arg-type]
    return [(r.site_id, r.smr_key) for r in scored[:n]]


def _top_pct_size(rows: list[ProfileRow], pct: float) -> int:
    """Number of scored pairs to consider for the top-``pct`` slice."""
    scored = sum(1 for r in rows if r.composite_score is not None)
    return max(1, int(pct * scored)) if scored else 0


def _jaccard(a: list[tuple[str, str]], b: list[tuple[str, str]]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    inter = sa & sb
    return round(len(inter) / len(union), 4) if union else 0.0


def _drift(
    baseline: list[ProfileRow], profile: list[ProfileRow]
) -> tuple[float | None, float | None, int]:
    b_map = {
        (r.site_id, r.smr_key): r.composite_score
        for r in baseline
        if r.composite_score is not None
    }
    deltas: list[float] = []
    for r in profile:
        if r.composite_score is None:
            continue
        base = b_map.get((r.site_id, r.smr_key))
        if base is None:
            continue
        deltas.append(abs(r.composite_score - base))
    if not deltas:
        return None, None, 0
    return round(fmean(deltas), 4), round(max(deltas), 4), len(deltas)


def _country_counts(top20: list[tuple[str, str]], rows: list[ProfileRow]) -> dict[str, int]:
    by_key = {(r.site_id, r.smr_key): r.country_code for r in rows}
    out: dict[str, int] = defaultdict(int)
    for key in top20:
        out[by_key.get(key, "??")] += 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def compute_analytics(
    session: Session,
    baseline_label: str = "baseline",
) -> PhaseAnalytics:
    """Cross-profile analytics rollup used by the consolidated audit."""
    rows_by_profile = load_profile_rows(session)
    warnings: list[str] = []
    baseline_rows = rows_by_profile.get(baseline_label)
    if not baseline_rows:
        warnings.append(
            f"no rows found for weight_profile='{baseline_label}' in composite_rankings"
        )
        return PhaseAnalytics(
            baseline_label=baseline_label,
            baseline_total_rows=0,
            baseline_scored_rows=0,
            warnings=warnings,
        )

    baseline_scored = [r for r in baseline_rows if r.composite_score is not None]
    top5_size = _top_pct_size(baseline_rows, TOP_PCTS[0])
    top10_size = _top_pct_size(baseline_rows, TOP_PCTS[1])
    baseline_top5 = _top_keys(baseline_rows, top5_size)
    baseline_top10 = _top_keys(baseline_rows, top10_size)
    top10_countries = _country_counts(baseline_top10, baseline_rows)

    profile_stats: list[ProfileStats] = []
    for label, rows in sorted(rows_by_profile.items()):
        if label == baseline_label:
            continue
        p_top5_size = _top_pct_size(rows, TOP_PCTS[0])
        p_top10_size = _top_pct_size(rows, TOP_PCTS[1])
        top5 = _top_keys(rows, p_top5_size)
        top10 = _top_keys(rows, p_top10_size)
        mean_drift, max_drift, compared = _drift(baseline_rows, rows)
        scored_rows = sum(1 for r in rows if r.composite_score is not None)
        profile_stats.append(
            ProfileStats(
                label=label,
                total_rows=len(rows),
                scored_rows=scored_rows,
                top5pct_size=p_top5_size,
                top10pct_size=p_top10_size,
                top5pct_overlap=len(set(top5) & set(baseline_top5)),
                top10pct_overlap=len(set(top10) & set(baseline_top10)),
                top5pct_jaccard=_jaccard(top5, baseline_top5),
                top10pct_jaccard=_jaccard(top10, baseline_top10),
                mean_abs_drift=mean_drift,
                max_abs_drift=max_drift,
                pairs_drift_compared=compared,
            )
        )

    per_category = _per_category_weight_roll_up(profile_stats)

    return PhaseAnalytics(
        baseline_label=baseline_label,
        baseline_total_rows=len(baseline_rows),
        baseline_scored_rows=len(baseline_scored),
        baseline_top5pct_size=top5_size,
        baseline_top10pct_size=top10_size,
        baseline_top10pct_countries=top10_countries,
        profiles=profile_stats,
        per_category_weight=per_category,
        warnings=warnings,
    )


def _per_category_weight_roll_up(
    stats: list[ProfileStats],
) -> list[tuple[str, float, int]]:
    """Average mean-abs-drift + top-10 % overlap per NH/HI/RI/EP/NS bucket."""
    buckets: dict[str, list[ProfileStats]] = defaultdict(list)
    for s in stats:
        if not s.label.startswith("w_"):
            continue
        parts = s.label.split("_")
        if len(parts) < 3:
            continue
        cat = parts[1].upper()
        buckets[cat].append(s)
    out: list[tuple[str, float, int]] = []
    for cat, items in sorted(buckets.items()):
        drifts = [i.mean_abs_drift for i in items if i.mean_abs_drift is not None]
        overlap = [i.top10pct_overlap for i in items]
        if not drifts or not overlap:
            continue
        out.append((cat, round(fmean(drifts), 4), round(fmean(overlap))))
    return out
