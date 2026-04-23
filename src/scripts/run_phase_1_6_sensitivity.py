#!/usr/bin/env python
# man_hours: 3.0
"""Phase 1.6 sensitivity driver.

Executes the full sensitivity matrix required by
``.cursor/plans/siting_report_end_to_end_4a5dbb0d.plan.md`` §1.6:

- Per-category weight perturbation ±20 % — one profile pair per family
  (``w_NH_plus_20`` / ``w_NH_minus_20`` / ``w_HI_…`` / ``w_RI_…`` /
  ``w_EP_…`` / ``w_NS_…``). Uniform ±20 % scaling across every
  criterion is a renormalisation no-op so we perturb one family at a
  time instead.
- Monte Carlo @ N = 1000, 3000, 10000 (``mc_1000`` / ``mc_3000`` /
  ``mc_10000`` profiles).
- Threshold ±25 % (``threshold_plus_25`` / ``threshold_minus_25`` profiles).
- Country-balanced top-N check (``country_balanced`` profile).

All rows land in ``composite_rankings`` of the selected DB. A single
consolidated markdown audit report is written under
``audit/post_processing/06_scoring/`` alongside the per-MC-count audit
files emitted by :func:`run_sensitivity_suite`.

Example
-------
::

    python -m scripts.run_phase_1_6_sensitivity \\
        --db-profile merged \\
        --top-n-country 20

Runs against the merged DB (where baseline ``composite_rankings`` live)
and produces the full Phase 1.6 audit package.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_PROJECT_ROOT / ".env", override=False)

from atoms_vs_ashes.config import Settings  # noqa: E402
from atoms_vs_ashes.db.engine import init_engine, session_scope  # noqa: E402
from atoms_vs_ashes.logging import configure_logging, new_run_id  # noqa: E402
from atoms_vs_ashes.scoring.suite import (  # noqa: E402
    DEFAULT_AUDIT_DIR,
    DEFAULT_RUBRIC_DIR,
    SensitivitySuiteConfig,
    SensitivitySuiteResult,
    run_sensitivity_suite,
)
from scripts._phase_1_6_analytics import compute_analytics  # noqa: E402
from scripts._phase_1_6_audit import write_consolidated_audit  # noqa: E402

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

MC_ITERATION_STAGES: tuple[int, ...] = (1000, 3000, 10000)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db-profile",
        choices=sorted(DB_PROFILES.keys()),
        default="merged",
        help="Database profile (default: merged, where Phase 1.5 wrote baselines).",
    )
    parser.add_argument(
        "--weight-profile-base",
        default="baseline",
        help="Baseline weight profile to load composites from.",
    )
    parser.add_argument(
        "--rubric-dir", default=DEFAULT_RUBRIC_DIR, help="Scoring rubric directory."
    )
    parser.add_argument(
        "--audit-dir",
        default=str(DEFAULT_AUDIT_DIR),
        help="Audit output directory.",
    )
    parser.add_argument(
        "--top-n-country", type=int, default=20, help="Top-N for country balance check."
    )
    parser.add_argument("--seed", type=int, default=42, help="Monte Carlo seed.")
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar."
    )
    parser.add_argument(
        "--mc-stages",
        nargs="+",
        type=int,
        default=list(MC_ITERATION_STAGES),
        help="Monte Carlo iteration stages (default: 1000 3000 10000).",
    )
    parser.add_argument(
        "--skip-threshold",
        action="store_true",
        help="Skip the threshold ±25 %% direction (slowest stage).",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id (auto-generated if omitted).",
    )
    return parser.parse_args()


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

    stages = _run_pipeline(args, run_id, common)

    with session_scope() as analytics_session:
        analytics = compute_analytics(
            analytics_session, baseline_label=args.weight_profile_base
        )
    consolidated = write_consolidated_audit(
        audit_dir, run_id, args.db_profile, stages, analytics
    )
    _print(
        {
            "message": "phase_1_6_sensitivity_complete",
            "run_id": run_id,
            "stages": len(stages),
            "consolidated_audit": str(consolidated),
            "per_stage_audits": [str(s.audit_path) for s in stages],
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
