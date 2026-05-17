# man_hours: 1.0
"""Driver-stage helpers for ``run_phase_1_6_sensitivity``."""

from __future__ import annotations

import json
from pathlib import Path

from atoms_vs_ashes.db.engine import session_scope
from scripts._phase_1_6_extended_stages import (
    ExtendedStagesResult,
    run_extended_stages,
)
from scripts._phase_1_6_national_sensitivity import (
    NationalSensitivityStageResult,
    run_national_sensitivity_stage,
)


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def run_extended_from_args(
    args,
    audit_dir: Path,
    stamp: str,
    run_id: str,
    national: NationalSensitivityStageResult | None = None,
) -> ExtendedStagesResult | None:
    """Run extended banding/country reports from parsed CLI args."""
    if args.skip_banding:
        return None
    _print({
        "stage": "extended",
        "message": "running extended banding + national analysis (Phase C)",
    })
    report_dir = Path(args.report_dir) / stamp
    with session_scope() as session:
        result = run_extended_stages(
            session, baseline_label=args.weight_profile_base,
            audit_dir=audit_dir, report_dir=report_dir, stamp=stamp,
            generate_figures=not args.no_figures, run_id=run_id,
            national_country_figures=(
                national.country_figures if national is not None else None
            ),
        )
    _print({
        "stage": "extended",
        "regional_bands_csv": str(result.regional_bands_csv),
        "nuscale_bands_csv": str(result.nuscale_bands_csv),
        "country_report_count": len(result.country_report_mds),
        "regional_report_md": str(result.regional_report_md),
    })
    return result


def run_national_from_args(
    args, audit_dir: Path, stamp: str, run_id: str,
) -> NationalSensitivityStageResult | None:
    """Run national rank sensitivity from parsed CLI args."""
    if args.skip_national:
        return None
    draws = (
        args.national_mc_rank_draws
        if args.national_mc_rank_draws is not None
        else args.mc_stages[0]
    )
    if draws <= 0:
        raise ValueError("--national-mc-rank-draws must be >= 1")
    if args.min_national_pairs <= 0:
        raise ValueError("--min-national-pairs must be >= 1")
    _print({
        "stage": "national_sensitivity",
        "message": "running national rank sensitivity",
        "iterations": draws,
        "min_pairs": args.min_national_pairs,
    })
    with session_scope() as session:
        result = run_national_sensitivity_stage(
            session,
            run_id=run_id,
            baseline_label=args.weight_profile_base,
            rubric_dir=args.rubric_dir,
            audit_dir=audit_dir,
            report_dir=Path(args.report_dir) / stamp,
            stamp=stamp,
            iterations=draws,
            seed=args.seed,
            min_pairs=args.min_national_pairs,
            progress_enabled=not args.no_progress,
        )
    _print({"stage": "national_sensitivity", **result.to_dict()})
    return result


__all__ = ["run_extended_from_args", "run_national_from_args"]
