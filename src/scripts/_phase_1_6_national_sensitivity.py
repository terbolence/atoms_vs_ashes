# man_hours: 1.5
"""National sensitivity stage for the Phase 1.6 driver."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import persist_national_oat_importance
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._national_mc_rank import (
    persist_and_write_national_mc_rank,
    run_national_mc_rank_simulation,
)
from atoms_vs_ashes.scoring._national_ranking import DEFAULT_MIN_NATIONAL_PAIRS
from atoms_vs_ashes.scoring._national_sensitivity import (
    NationalProfileSensitivityResult,
    compute_national_profile_sensitivity,
)
from atoms_vs_ashes.scoring._suite_national_oat import (
    NationalOATRunResult,
    run_national_oat_stage,
)
from atoms_vs_ashes.scoring._suite_persist import load_pairs
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle, weight_normalisation
from scripts._phase_1_6_figures_national_sensitivity import (
    build_national_sensitivity_figures,
)

log = get_logger(__name__)


@dataclass(frozen=True)
class NationalSensitivityStageResult:
    """Machine-readable output of the national sensitivity stage."""

    oat: NationalOATRunResult
    profile: NationalProfileSensitivityResult
    mc_rank_csv: Path
    mc_rank_rows: int
    figures: dict[str, Path]
    country_figures: dict[str, Path]

    def to_dict(self) -> dict[str, object]:
        return {
            "national_oat_csv": str(self.oat.csv_path),
            "national_oat_rows": self.oat.rows_total,
            "national_profile_rank_csv": str(self.profile.rank_csv),
            "national_profile_summary_csv": str(self.profile.summary_csv),
            "national_profile_rank_rows": self.profile.per_pair_rows,
            "national_profile_summary_rows": self.profile.summary_rows,
            "national_mc_rank_csv": str(self.mc_rank_csv),
            "national_mc_rank_rows": self.mc_rank_rows,
            "national_figures": {k: str(v) for k, v in self.figures.items()},
            "national_country_figures": {
                k: str(v) for k, v in self.country_figures.items()
            },
        }


def run_national_sensitivity_stage(
    session: Session,
    *,
    run_id: str,
    baseline_label: str,
    rubric_dir: str,
    audit_dir: Path,
    stamp: str,
    iterations: int,
    seed: int,
    report_dir: Path | None = None,
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS,
    progress_enabled: bool = True,
) -> NationalSensitivityStageResult:
    """Run national OAT, profile rank deltas, and MC rank simulation."""
    oat = run_national_oat_stage(
        session,
        weight_profile_base=baseline_label,
        rubric_dir=rubric_dir,
        audit_dir=audit_dir,
        progress_enabled=progress_enabled,
        run_id=run_id,
        min_pairs=min_pairs,
        stamp=stamp,
        db_writer=persist_national_oat_importance,
    )
    profile = compute_national_profile_sensitivity(
        session,
        sensitivity_run_id=run_id,
        baseline_label=baseline_label,
        audit_dir=audit_dir,
        stamp=stamp,
        min_pairs=min_pairs,
        persist=True,
    )

    bundle = load_rubric_bundle(rubric_dir)
    weights = weight_normalisation(bundle, profile=baseline_label)
    rows_by_pair, verdicts_by_pair, country_by_pair = load_pairs(
        session, weight_profile_base=baseline_label,
    )
    mc_rows = run_national_mc_rank_simulation(
        rows_by_pair,
        verdicts_by_pair,
        country_by_pair,
        weights=weights,
        criteria=bundle,
        iterations=iterations,
        seed=seed,
        min_pairs=min_pairs,
    )
    mc_csv = persist_and_write_national_mc_rank(
        session, run_id=run_id, audit_dir=audit_dir, rows=mc_rows, stamp=stamp,
    )
    figures: dict[str, Path] = {}
    country_figures: dict[str, Path] = {}
    if report_dir is not None:
        figures, country_figures = build_national_sensitivity_figures(
            summary_csv=profile.summary_csv,
            oat_csv=oat.csv_path,
            mc_csv=mc_csv,
            figures_dir=report_dir / "national" / "figures",
        )
    log.info(
        "national_sensitivity_stage_complete",
        oat_rows=oat.rows_total,
        profile_rows=profile.per_pair_rows,
        mc_rows=len(mc_rows),
        figures=len(figures),
        country_figures=len(country_figures),
    )
    return NationalSensitivityStageResult(
        oat=oat,
        profile=profile,
        mc_rank_csv=mc_csv,
        mc_rank_rows=len(mc_rows),
        figures=figures,
        country_figures=country_figures,
    )


__all__ = [
    "NationalSensitivityStageResult",
    "run_national_sensitivity_stage",
]
