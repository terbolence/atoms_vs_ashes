#!/usr/bin/env python
# man_hours: 3.8
"""Phase 1.6 sensitivity driver (refined).

End-to-end refined sensitivity analysis per
``.cursor/plans/phase_1.6_refined_sensitivity_8e58bf1f.plan.md``:

- Phase A — OAT importance CSV (``<stamp>_oat_importance.csv``).
- Phase B — regulatory matrix in ``composite_rankings`` (per-category
  ±20 % weights, Monte Carlo @ N=10000, threshold ±25 %, country-balance).
- Phase C — site banding CSV (``<stamp>_site_bands.csv``).

A consolidated markdown audit is written under
``audit/post_processing/06_scoring/`` alongside per-MC-stage audits.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_PROJECT_ROOT / ".env", override=False)

from atoms_vs_ashes.config import Settings  # noqa: E402
from atoms_vs_ashes.db.engine import init_engine, session_scope  # noqa: E402
from atoms_vs_ashes.db.runs import DatasetMeta, complete_run, start_run  # noqa: E402
from atoms_vs_ashes.logging import configure_logging, new_run_id  # noqa: E402
from atoms_vs_ashes.scoring._suite_importance import OATRunResult, run_oat_stage  # noqa: E402
from atoms_vs_ashes.scoring.suite import (  # noqa: E402
    DEFAULT_AUDIT_DIR,
    DEFAULT_RUBRIC_DIR,
    SensitivitySuiteConfig,
    SensitivitySuiteResult,
    run_sensitivity_suite,
)
from scripts._phase_1_6_analytics import compute_analytics  # noqa: E402
from scripts._phase_1_6_audit import write_consolidated_audit  # noqa: E402
from scripts._phase_1_6_driver_stages import (  # noqa: E402
    run_extended_from_args,
    run_national_from_args,
)

DEFAULT_REPORT_DIR = "report/output/sensitivity"

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

MC_ITERATION_STAGES: tuple[int, ...] = (10000,)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db-profile", choices=sorted(DB_PROFILES.keys()), default="merged")
    p.add_argument("--weight-profile-base", default="baseline")
    p.add_argument("--rubric-dir", default=DEFAULT_RUBRIC_DIR)
    p.add_argument("--audit-dir", default=str(DEFAULT_AUDIT_DIR))
    p.add_argument("--top-n-country", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-progress", action="store_true")
    p.add_argument(
        "--mc-stages", nargs="+", type=int,
        default=list(MC_ITERATION_STAGES),
        help="Monte Carlo iteration stages (default: 10000).",
    )
    p.add_argument("--skip-threshold", action="store_true")
    p.add_argument("--skip-oat", action="store_true")
    p.add_argument("--skip-national", action="store_true",
                   help="Skip national ranking sensitivity artefacts.")
    p.add_argument("--national-mc-rank-draws", type=int, default=None,
                   help="MC draws for national rank simulation (default: first MC stage).")
    p.add_argument("--min-national-pairs", type=int, default=3,
                   help="Minimum country×SMR pairs before national rank metrics are non-small-n.")
    p.add_argument("--skip-banding", action="store_true",
                   help="Skip the extended banding + national analysis stage.")
    p.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    p.add_argument("--no-figures", action="store_true")
    p.add_argument("--run-id", default=None)
    p.add_argument("--stamp", default=None,
                   help="Override the YYYYMMDD output stamp (default: today UTC).")
    return p.parse_args()


def _run_stage(cfg: SensitivitySuiteConfig, run_id: str) -> SensitivitySuiteResult:
    with session_scope() as session:
        return run_sensitivity_suite(session, cfg, run_id=run_id)


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _first_stage_cfg(
    args: argparse.Namespace, iterations: int, common: dict[str, object]
) -> SensitivitySuiteConfig:
    return SensitivitySuiteConfig(
        iterations=iterations,
        preset_label=None,
        include_weights=True,
        include_mc=True,
        include_country=True,
        include_threshold=not args.skip_threshold,
        **common,
    )


def _followup_cfg(
    iterations: int, common: dict[str, object]
) -> SensitivitySuiteConfig:
    return SensitivitySuiteConfig(
        iterations=iterations,
        preset_label=None,
        include_weights=False,
        include_mc=True,
        include_country=False,
        include_threshold=False,
        **common,
    )


def _run_pipeline(
    args: argparse.Namespace, run_id: str, common: dict[str, object]
) -> list[SensitivitySuiteResult]:
    stages: list[SensitivitySuiteResult] = []

    first_iters = args.mc_stages[0]
    _print(
        {
            "stage": 1,
            "message": "running first stage (weights + mc + country + threshold)",
            "iterations": first_iters,
            "run_id": run_id,
        }
    )
    stages.append(
        _run_stage(_first_stage_cfg(args, first_iters, common), run_id=run_id)
    )
    _print(stages[-1].to_dict())

    for iters in args.mc_stages[1:]:
        _print(
            {
                "stage": f"mc_{iters}",
                "message": "running additional Monte Carlo stage",
                "iterations": iters,
                "run_id": run_id,
            }
        )
        stages.append(_run_stage(_followup_cfg(iters, common), run_id=run_id))
        _print(stages[-1].to_dict())
    return stages


def _run_oat(
    args: argparse.Namespace, audit_dir: Path, run_id: str
) -> OATRunResult | None:
    if args.skip_oat:
        return None
    _print({"stage": "oat", "message": "running OAT importance (Phase A)"})
    with session_scope() as session:
        result = run_oat_stage(
            session,
            weight_profile_base=args.weight_profile_base,
            rubric_dir=args.rubric_dir,
            audit_dir=audit_dir,
            progress_enabled=not args.no_progress,
            run_id=run_id,
        )
    _print(
        {
            "stage": "oat",
            "csv_path": str(result.csv_path),
            "criteria_scored": result.criteria_scored,
            "top_criterion": result.top_criterion,
            "top_importance": result.top_importance,
        }
    )
    return result


def _open_run(args: argparse.Namespace, run_id: str):
    with session_scope() as run_session:
        return start_run(
            run_session,
            run_kind="sensitivity",
            cli_command=" ".join(sys.argv),
            run_id=run_id,
            dataset_meta=DatasetMeta(
                rubric_file_path=args.rubric_dir,
                weight_normalisation_profile=args.weight_profile_base,
            ),
        )


def main() -> int:
    args = _parse_args()

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    run_id = args.run_id or f"p16_{new_run_id()}"
    configure_logging(verbose=False, run_id=run_id)
    settings = Settings()
    init_engine(settings)

    audit_dir = Path(args.audit_dir)
    common: dict[str, object] = {
        "weight_profile_base": args.weight_profile_base,
        "rubric_dir": args.rubric_dir,
        "audit_dir": audit_dir,
        "seed": args.seed,
        "progress_enabled": not args.no_progress,
        "top_n_country": args.top_n_country,
    }

    stamp = args.stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    handle = _open_run(args, run_id)

    try:
        oat = _run_oat(args, audit_dir, run_id)
        stages = _run_pipeline(args, run_id, common)
        national = run_national_from_args(args, audit_dir, stamp, run_id)
        extended = run_extended_from_args(args, audit_dir, stamp, run_id, national)
    except Exception as exc:
        with session_scope() as fail_session:
            complete_run(fail_session, handle, status="failed", notes=f"err={exc!r}")
        raise

    with session_scope() as analytics_session:
        analytics = compute_analytics(
            analytics_session, baseline_label=args.weight_profile_base
        )
        consolidated = write_consolidated_audit(
            audit_dir,
            run_id,
            args.db_profile,
            stages,
            analytics,
            importance_csv=oat.csv_path if oat else None,
            bands_csv=extended.regional_bands_csv if extended else None,
            nuscale_bands_csv=extended.nuscale_bands_csv if extended else None,
            country_summary_csv=extended.country_summary_csv if extended else None,
            db_session=analytics_session,
        )
        complete_run(analytics_session, handle, status="completed")
    _print({
        "message": "phase_1_6_sensitivity_complete",
        "run_id": run_id,
        "stages": len(stages),
        "consolidated_audit": str(consolidated),
        "per_stage_audits": [str(s.audit_path) for s in stages],
        "importance_csv": str(oat.csv_path) if oat else None,
        "bands_csv": str(extended.regional_bands_csv) if extended else None,
        "regional_report_md": (
            str(extended.regional_report_md) if extended else None
        ),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
