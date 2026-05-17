# man_hours: 1.35
"""National-OAT importance stage for the Phase 1.6 driver.

Mirrors :mod:`_suite_importance` but produces per-(country, SMR,
criterion) rows. Writes ``<stamp>_national_oat_importance.csv`` next
to the existing OAT artefact and optionally persists rows via a
caller-supplied writer (kept loose so the DB schema can land
independently in a separate step).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from sqlalchemy.orm import Session

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._national_oat import (
    NationalOATImportance,
    run_oat_importance_national,
)
from atoms_vs_ashes.scoring._national_ranking import DEFAULT_MIN_NATIONAL_PAIRS
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring._suite_persist import load_pairs
from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    load_rubric_bundle,
    weight_normalisation,
)

log = get_logger(__name__)

NATIONAL_OAT_CSV_FIELDS = (
    "country_code",
    "smr_key",
    "criterion_id",
    "family",
    "criterion_name",
    "mean_abs_rank_change",
    "importance_score",
    "pairs_compared",
    "eligible_pair_count",
    "small_n",
)

NationalOATWriter = Callable[
    [Session | None, str | None, Sequence[NationalOATImportance]], int,
]


@dataclass
class NationalOATRunResult:
    """Summary of one national-OAT stage run."""

    rows_total: int
    slices_total: int
    criteria_scored: int
    csv_path: Path


def _ordered_rows(
    importances: Sequence[NationalOATImportance],
    criteria: dict[str, Criterion],
) -> list[dict[str, object]]:
    rows = [
        {
            "country_code": imp.country_code,
            "smr_key": imp.smr_key,
            "criterion_id": imp.criterion_id,
            "family": imp.family,
            "criterion_name": (
                criteria[imp.criterion_id].name
                if imp.criterion_id in criteria else ""
            ),
            "mean_abs_rank_change": imp.mean_abs_rank_change,
            "importance_score": imp.importance_score,
            "pairs_compared": imp.pairs_compared,
            "eligible_pair_count": imp.eligible_pair_count,
            "small_n": imp.small_n,
        }
        for imp in importances
    ]
    rows.sort(
        key=lambda r: (
            str(r["country_code"]),
            str(r["smr_key"]),
            -float(r["importance_score"] or 0),
            str(r["criterion_id"]),
        )
    )
    return rows


def write_national_oat_csv(
    audit_dir: Path,
    importances: Sequence[NationalOATImportance],
    criteria: dict[str, Criterion],
    *,
    stamp: str | None = None,
) -> Path:
    """Write the national OAT importance CSV and return its path."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp_value = stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{stamp_value}_national_oat_importance.csv"
    rows = _ordered_rows(importances, criteria)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=NATIONAL_OAT_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)  # type: ignore[arg-type]
    return path


def run_national_oat_stage(
    session: Session,
    *,
    weight_profile_base: str,
    rubric_dir: str,
    audit_dir: Path,
    progress_enabled: bool = True,
    run_id: str | None = None,
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
    stamp: str | None = None,
    scope=None,
    db_writer: NationalOATWriter | None = None,
) -> NationalOATRunResult:
    """End-to-end national OAT stage; loads pairs, ranks per slice, writes CSV.

    ``db_writer`` is an optional callable that persists the rows; when
    omitted the stage is CSV-only. The signature matches
    ``persist_national_oat_importance(session, run_id, rows) -> int``
    so the DB-step plug-in is a one-liner.
    """
    bundle = load_rubric_bundle(rubric_dir)
    weights = weight_normalisation(bundle, profile=weight_profile_base)
    rows_by_pair, verdicts_by_pair, country_by_pair = load_pairs(
        session, weight_profile_base=weight_profile_base, scope=scope,
    )

    ranking_ids = [
        cid for cid, c in bundle.items()
        if c.participates_in_composite and cid in weights
    ]

    with ProgressReporter(
        total=len(ranking_ids),
        description="National OAT (zero-out per criterion, per country×SMR)",
        enabled=progress_enabled,
    ) as reporter:
        importances = run_oat_importance_national(
            rows_by_pair,
            verdicts_by_pair,
            country_by_pair,
            weights=weights,
            criteria=bundle,
            min_pairs=min_pairs,
            progress_cb=reporter.advance,
        )

    csv_path = write_national_oat_csv(
        audit_dir, importances, bundle, stamp=stamp,
    )

    if db_writer is not None:
        db_writer(session, run_id, importances)

    slices = {(imp.country_code, imp.smr_key) for imp in importances}
    log.info(
        "national_oat_stage_complete",
        rows=len(importances),
        slices=len(slices),
        csv_path=str(csv_path),
    )
    return NationalOATRunResult(
        rows_total=len(importances),
        slices_total=len(slices),
        criteria_scored=len(ranking_ids),
        csv_path=csv_path,
    )


__all__ = [
    "NATIONAL_OAT_CSV_FIELDS",
    "NationalOATRunResult",
    "NationalOATWriter",
    "run_national_oat_stage",
    "write_national_oat_csv",
]
