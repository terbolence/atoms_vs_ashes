# man_hours: 1.5
"""OAT (one-at-a-time) importance orchestrator for Phase 1.6.

Loads baseline pairs + rubric weights, runs :func:`run_oat_importance`
with a progress bar, and writes a CSV artefact (columns
``criterion_id``, ``family``, ``mean_abs_rank_change``,
``importance_score``, ``pairs_compared``) under the audit directory.

The plan asks for a Parquet artefact, but ``pyarrow`` is not a project
dependency; CSV keeps the tabular schema identical, costs no install
footprint, and is trivially reloaded via ``pandas.read_csv``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import persist_oat_importance
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring._suite_persist import load_pairs
from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    load_rubric_bundle,
    weight_normalisation,
)
from atoms_vs_ashes.scoring.sensitivity import (
    OATImportance,
    run_oat_importance,
)

log = get_logger(__name__)

IMPORTANCE_CSV_FIELDS = (
    "criterion_id",
    "family",
    "criterion_name",
    "mean_abs_rank_change",
    "importance_score",
    "pairs_compared",
)


@dataclass
class OATRunResult:
    """Summary of an OAT importance run (machine-readable)."""

    criteria_scored: int
    pairs_compared: int
    top_criterion: str | None
    top_importance: float
    csv_path: Path


class _ImportanceRow:
    """Adapter exposing the field names :func:`persist_oat_importance` expects."""

    __slots__ = (
        "criterion_id", "family", "criterion_name",
        "mean_abs_rank_change", "importance_score", "pairs_compared",
    )

    def __init__(
        self, imp: OATImportance, criteria: dict[str, Criterion]
    ) -> None:
        self.criterion_id = imp.criterion_id
        self.family = imp.family
        self.criterion_name = (
            criteria[imp.criterion_id].name if imp.criterion_id in criteria else ""
        )
        self.mean_abs_rank_change = imp.mean_abs_rank_change
        self.importance_score = imp.importance_score
        self.pairs_compared = imp.pairs_compared


def _ordered_rows(
    importances: dict[str, OATImportance],
    criteria: dict[str, Criterion],
) -> list[dict[str, object]]:
    rows = [
        {
            "criterion_id": imp.criterion_id,
            "family": imp.family,
            "criterion_name": criteria[imp.criterion_id].name
            if imp.criterion_id in criteria
            else "",
            "mean_abs_rank_change": imp.mean_abs_rank_change,
            "importance_score": imp.importance_score,
            "pairs_compared": imp.pairs_compared,
        }
        for imp in importances.values()
    ]
    rows.sort(key=lambda r: float(r["importance_score"]), reverse=True)
    return rows


def write_importance_csv(
    audit_dir: Path,
    importances: dict[str, OATImportance],
    criteria: dict[str, Criterion],
) -> Path:
    """Write the ordered importance table and return its path."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{stamp}_oat_importance.csv"
    rows = _ordered_rows(importances, criteria)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=IMPORTANCE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)  # type: ignore[arg-type]
    return path


def run_oat_stage(
    session: Session,
    *,
    weight_profile_base: str,
    rubric_dir: str,
    audit_dir: Path,
    progress_enabled: bool = True,
    run_id: str | None = None,
) -> OATRunResult:
    """Execute the OAT importance stage end-to-end and write the CSV."""
    bundle = load_rubric_bundle(rubric_dir)
    weights = weight_normalisation(bundle, profile=weight_profile_base)
    rows_by_pair, verdicts_by_pair, _country = load_pairs(
        session, weight_profile_base=weight_profile_base
    )

    ranking_ids = [
        cid for cid, c in bundle.items()
        if c.participates_in_composite and cid in weights
    ]
    with ProgressReporter(
        total=len(ranking_ids),
        description="OAT importance (zero-out per criterion)",
        enabled=progress_enabled,
    ) as reporter:
        importances = run_oat_importance(
            rows_by_pair,
            verdicts_by_pair,
            weights=weights,
            criteria=bundle,
            progress_cb=reporter.advance,
        )

    csv_path = write_importance_csv(audit_dir, importances, bundle)
    top = next(iter(_ordered_rows(importances, bundle)), None)
    persist_oat_importance(
        session, run_id=run_id,
        rows=[_ImportanceRow(imp, bundle) for imp in importances.values()],
    )

    log.info(
        "oat_stage_complete",
        criteria=len(importances),
        csv_path=str(csv_path),
    )
    return OATRunResult(
        criteria_scored=len(importances),
        pairs_compared=next(iter(importances.values())).pairs_compared
        if importances
        else 0,
        top_criterion=top["criterion_id"] if top else None,  # type: ignore[index]
        top_importance=float(top["importance_score"]) if top else 0.0,  # type: ignore[index]
        csv_path=csv_path,
    )
