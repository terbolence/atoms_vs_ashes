#!/usr/bin/env python
# man_hours: 1.25
"""Standalone extended-analysis CLI (Phase 1.6).

Reads existing ``composite_rankings`` rows (baseline + all 14
non-baseline profiles produced by
:mod:`run_phase_1_6_sensitivity`) and emits:

- Extended A–H bands at global and per-SMR scope.
- Per-country A–H bands (all-SMR and NuScale) with within-country
  percentile slices, so bands reflect national competitiveness.
- Country Jaccard-vs-baseline summary CSVs.
- Human-readable MD reports under ``report/output/sensitivity/<stamp>/``
  (one regional summary + one file per country).
- PNG figures (regional A–H counts, per-country top-10 bar charts).

No new baseline or scenario rows are written to the database.
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
from scripts._phase_1_6_extended_stages import (  # noqa: E402
    ExtendedStagesResult,
    run_extended_stages,
)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db-profile",
        choices=sorted(DB_PROFILES.keys()),
        default="merged",
        help="Database profile (default: merged).",
    )
    parser.add_argument(
        "--baseline-label",
        default="baseline",
        help="Baseline weight_profile label (default: 'baseline').",
    )
    parser.add_argument(
        "--audit-dir",
        default="audit/post_processing/06_scoring",
        help="Directory for raw CSV artefacts.",
    )
    parser.add_argument(
        "--report-dir",
        default="report/output/sensitivity",
        help="Root directory for human-readable reports; stamp subdir is appended.",
    )
    parser.add_argument(
        "--stamp",
        default=None,
        help="Override stamp (YYYYMMDD). Default: current UTC date.",
    )
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Skip PNG generation (useful when matplotlib isn't available).",
    )
    return parser.parse_args()


def _resolve_stamp(explicit: str | None) -> str:
    if explicit:
        return explicit
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _run(args: argparse.Namespace) -> ExtendedStagesResult:
    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    run_id = f"p16ext_{new_run_id()}"
    configure_logging(verbose=False, run_id=run_id)
    settings = Settings()
    init_engine(settings)

    stamp = _resolve_stamp(args.stamp)
    audit_dir = Path(args.audit_dir)
    report_dir = Path(args.report_dir) / stamp

    with session_scope() as session:
        handle = start_run(
            session,
            run_kind="extended_analysis",
            cli_command=" ".join(sys.argv),
            run_id=run_id,
            dataset_meta=DatasetMeta(
                weight_normalisation_profile=args.baseline_label,
            ),
        )
        try:
            result = run_extended_stages(
                session,
                baseline_label=args.baseline_label,
                audit_dir=audit_dir,
                report_dir=report_dir,
                stamp=stamp,
                generate_figures=not args.no_figures,
                run_id=run_id,
            )
        except Exception as exc:
            complete_run(session, handle, status="failed", notes=f"err={exc!r}")
            raise
        complete_run(session, handle, status="completed")
        return result


def _summary(result: ExtendedStagesResult) -> dict[str, object]:
    return {
        "regional_bands_csv": str(result.regional_bands_csv),
        "nuscale_bands_csv": str(result.nuscale_bands_csv),
        "per_smr_count": len(result.per_smr_bands_csvs),
        "per_country_count": len(result.per_country_bands_csvs),
        "per_country_nuscale_count": len(
            result.per_country_nuscale_bands_csvs
        ),
        "country_summary_csv": str(result.country_summary_csv)
        if result.country_summary_csv
        else None,
        "country_summary_nuscale_csv": str(result.country_summary_nuscale_csv)
        if result.country_summary_nuscale_csv
        else None,
        "regional_report_md": str(result.regional_report_md)
        if result.regional_report_md
        else None,
        "country_reports": {k: str(v) for k, v in result.country_report_mds.items()},
        "figures": {k: str(v) for k, v in result.figures.items()},
    }


def main() -> int:
    args = _parse_args()
    result = _run(args)
    print(json.dumps(_summary(result), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
