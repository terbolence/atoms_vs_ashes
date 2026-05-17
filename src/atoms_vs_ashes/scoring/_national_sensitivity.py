# man_hours: 2.7
"""National rank-delta analytics over persisted sensitivity profiles.

This module is an additive Phase 1.6 layer: it reads already-persisted
``composite_rankings`` baseline + non-baseline profiles, recomputes
national ranks within each ``(country_code, smr_key)`` slice, and emits
per-pair deltas plus per-slice summaries.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import (
    persist_national_rank_sensitivity,
    persist_national_sensitivity_summary,
)
from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._national_ranking import (
    DEFAULT_MIN_NATIONAL_PAIRS,
    NationalRankDelta,
    NationalSliceSummary,
    ScoredPair,
    summarise_rank_deltas,
)
from atoms_vs_ashes.scoring._suite_persist import _resolve_baseline_run_id

log = get_logger(__name__)

RANK_CSV_FIELDS = (
    "country_code",
    "smr_key",
    "weight_profile",
    "scenario_family",
    "site_id",
    "baseline_national_rank",
    "scenario_national_rank",
    "rank_delta",
    "baseline_score",
    "scenario_score",
    "score_delta",
    "eligible_pair_count",
    "small_n",
)

SUMMARY_CSV_FIELDS = (
    "country_code",
    "smr_key",
    "weight_profile",
    "scenario_family",
    "n_pairs",
    "mean_abs_rank_delta",
    "max_abs_rank_delta",
    "spearman_rho",
    "top1_changed",
    "top3_jaccard",
    "top5_jaccard",
    "small_n",
)


@dataclass(frozen=True)
class NationalProfileSensitivityResult:
    """Paths and row counts from one profile-sensitivity run."""

    rank_csv: Path
    summary_csv: Path
    per_pair_rows: int
    summary_rows: int
    profiles: tuple[str, ...]


def scenario_family(weight_profile: str) -> str:
    """Classify profile labels for reporting and DB rows."""
    if weight_profile.startswith("w_") and weight_profile != "w_swing":
        return "weight"
    if weight_profile == "w_swing":
        return "swing"
    if weight_profile.startswith("threshold_"):
        return "threshold"
    if weight_profile.startswith("mc_"):
        return "mc_summary"
    if weight_profile == "country_balanced":
        return "country_balanced"
    return "other"


def _rows_to_pairs(rows: list[tuple]) -> list[ScoredPair]:
    out: list[ScoredPair] = []
    for site_id, smr_key, country, score in rows:
        if score is None:
            continue
        out.append(ScoredPair(
            site_id=site_id,
            smr_key=str(smr_key),
            country_code=str(country or "??"),
            composite_score=float(score),
        ))
    return out


def _load_profile_pairs(
    session: Session,
    *,
    weight_profile: str,
    run_id: str | None = None,
    smr_key: str | None = None,
) -> list[ScoredPair]:
    stmt = (
        select(
            CompositeRanking.site_id,
            CompositeRanking.smr_key,
            Site.country_code,
            CompositeRanking.composite_score,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(CompositeRanking.weight_profile == weight_profile)
    )
    if run_id is not None:
        stmt = stmt.where(CompositeRanking.run_id == run_id)
    if smr_key is not None:
        stmt = stmt.where(CompositeRanking.smr_key == smr_key)
    return _rows_to_pairs(session.execute(stmt).all())


def _available_profiles(
    session: Session,
    *,
    sensitivity_run_id: str,
    baseline_label: str,
) -> list[str]:
    rows = session.execute(
        select(CompositeRanking.weight_profile)
        .where(CompositeRanking.run_id == sensitivity_run_id)
        .where(CompositeRanking.weight_profile != baseline_label)
        .distinct()
        .order_by(CompositeRanking.weight_profile)
    ).all()
    return [str(r[0]) for r in rows]


def _rank_row_dict(
    row: NationalRankDelta, *, weight_profile: str, family: str,
) -> dict[str, object]:
    return {
        "country_code": row.country_code,
        "smr_key": row.smr_key,
        "weight_profile": weight_profile,
        "scenario_family": family,
        "site_id": row.site_id,
        "baseline_national_rank": row.baseline_rank,
        "scenario_national_rank": row.scenario_rank,
        "rank_delta": row.rank_delta,
        "baseline_score": row.baseline_score,
        "scenario_score": row.scenario_score,
        "score_delta": row.score_delta,
        "eligible_pair_count": row.eligible_pair_count,
        "small_n": row.small_n,
    }


def _summary_row_dict(
    row: NationalSliceSummary, *, weight_profile: str, family: str,
) -> dict[str, object]:
    return {
        "country_code": row.country_code,
        "smr_key": row.smr_key,
        "weight_profile": weight_profile,
        "scenario_family": family,
        "metric": "profile_rank_delta",
        "criterion_id": None,
        "family": family,
        "n_pairs": row.n_pairs,
        "mean_abs_rank_delta": row.mean_abs_rank_delta,
        "max_abs_rank_delta": row.max_abs_rank_delta,
        "spearman_rho": row.spearman_rho,
        "top1_changed": row.top1_changed,
        "top3_jaccard": row.top3_jaccard,
        "top5_jaccard": row.top5_jaccard,
        "small_n": row.small_n,
        "extra": {"scenario_family": family},
    }


def write_national_profile_sensitivity_csvs(
    audit_dir: Path,
    rank_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    *,
    stamp: str | None = None,
) -> tuple[Path, Path]:
    """Write rank-delta and summary CSVs."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp_value = stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    rank_path = audit_dir / f"{stamp_value}_national_rank_sensitivity.csv"
    summary_path = audit_dir / f"{stamp_value}_national_sensitivity_summary.csv"
    with rank_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RANK_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rank_rows)
    with summary_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_CSV_FIELDS)
        writer.writeheader()
        writer.writerows([
            {k: row.get(k, "") for k in SUMMARY_CSV_FIELDS}
            for row in summary_rows
        ])
    return rank_path, summary_path


def compute_national_profile_sensitivity(
    session: Session,
    *,
    sensitivity_run_id: str,
    baseline_label: str = "baseline",
    scoring_run_id: str | None = None,
    audit_dir: Path | None = None,
    stamp: str | None = None,
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
    profiles: list[str] | tuple[str, ...] | None = None,
    smr_key: str | None = None,
    persist: bool = True,
) -> NationalProfileSensitivityResult:
    """Compute national rank deltas for persisted non-baseline profiles."""
    baseline_run_id = scoring_run_id or _resolve_baseline_run_id(
        session, weight_profile_base=baseline_label,
    )
    baseline_pairs = _load_profile_pairs(
        session, weight_profile=baseline_label, run_id=baseline_run_id,
        smr_key=smr_key,
    )
    profile_labels = list(profiles) if profiles is not None else _available_profiles(
        session, sensitivity_run_id=sensitivity_run_id,
        baseline_label=baseline_label,
    )

    rank_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for profile in profile_labels:
        scenario_pairs = _load_profile_pairs(
            session, weight_profile=profile, run_id=sensitivity_run_id,
            smr_key=smr_key,
        )
        if not scenario_pairs:
            continue
        family = scenario_family(profile)
        per_pair, per_slice = summarise_rank_deltas(
            baseline_pairs, scenario_pairs, min_pairs=min_pairs,
        )
        rank_dicts = [
            _rank_row_dict(row, weight_profile=profile, family=family)
            for row in per_pair
        ]
        summary_dicts = [
            _summary_row_dict(row, weight_profile=profile, family=family)
            for row in per_slice
        ]
        rank_rows.extend(rank_dicts)
        summary_rows.extend(summary_dicts)
        if persist:
            persist_national_rank_sensitivity(
                session, run_id=sensitivity_run_id,
                weight_profile=profile, rows=per_pair, scenario_family=family,
            )

    if persist:
        persist_national_sensitivity_summary(
            session, run_id=sensitivity_run_id, rows=summary_rows,
        )

    out_dir = audit_dir or Path("audit/post_processing/06_scoring")
    rank_csv, summary_csv = write_national_profile_sensitivity_csvs(
        out_dir, rank_rows, summary_rows, stamp=stamp,
    )
    log.info(
        "national_profile_sensitivity_complete",
        profiles=profile_labels,
        rank_rows=len(rank_rows),
        summary_rows=len(summary_rows),
    )
    return NationalProfileSensitivityResult(
        rank_csv=rank_csv,
        summary_csv=summary_csv,
        per_pair_rows=len(rank_rows),
        summary_rows=len(summary_rows),
        profiles=tuple(profile_labels),
    )


__all__ = [
    "NationalProfileSensitivityResult", "compute_national_profile_sensitivity",
    "scenario_family", "write_national_profile_sensitivity_csvs",
]
