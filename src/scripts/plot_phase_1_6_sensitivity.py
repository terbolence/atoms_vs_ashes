#!/usr/bin/env python
# man_hours: 0.5
"""Render the four Phase 1.6 sensitivity figures from saved artefacts.

Inputs are the CSVs and consolidated audit markdown that
``run_phase_1_6_sensitivity`` already writes under
``audit/post_processing/06_scoring/``; outputs are PNGs under
``audit/post_processing/06_scoring/figures/<stamp>/``.

Requires the ``report_plots`` extra::

    pip install -e '.[report_plots]'

Example::

    python -m scripts.plot_phase_1_6_sensitivity \\
      --oat-csv   audit/post_processing/06_scoring/20260423_oat_importance.csv \\
      --bands-csv audit/post_processing/06_scoring/20260423_site_bands.csv \\
      --audit-md  audit/post_processing/06_scoring/20260423_phase1_6_sensitivity.md \\
      --out-dir   audit/post_processing/06_scoring/figures/20260423
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


DEFAULT_OAT_CSV = (
    "audit/post_processing/06_scoring/20260423_oat_importance.csv"
)
DEFAULT_BANDS_CSV = (
    "audit/post_processing/06_scoring/20260423_site_bands.csv"
)
DEFAULT_AUDIT_MD = (
    "audit/post_processing/06_scoring/20260423_phase1_6_sensitivity.md"
)
DEFAULT_OUT_DIR = "audit/post_processing/06_scoring/figures/20260423"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--oat-csv",
        default=DEFAULT_OAT_CSV,
        help="Path to the OAT importance CSV (default: 20260423 run).",
    )
    parser.add_argument(
        "--bands-csv",
        default=DEFAULT_BANDS_CSV,
        help="Path to the site-bands CSV (default: 20260423 run).",
    )
    parser.add_argument(
        "--audit-md",
        default=DEFAULT_AUDIT_MD,
        help="Path to the consolidated Phase 1.6 audit markdown.",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help="Directory where PNGs are written (created if missing).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        from scripts._phase_1_6_sensitivity_figures import save_all_figures
    except ImportError as exc:
        if "matplotlib" in str(exc).lower():
            print(
                "matplotlib is required. Install with: "
                "pip install -e '.[report_plots]'",
                file=sys.stderr,
            )
            return 2
        raise

    oat_csv = Path(args.oat_csv).resolve()
    bands_csv = Path(args.bands_csv).resolve()
    audit_md = Path(args.audit_md).resolve()
    out_dir = Path(args.out_dir).resolve()

    for label, path in (("oat-csv", oat_csv), ("bands-csv", bands_csv), ("audit-md", audit_md)):
        if not path.is_file():
            print(f"ERROR: {label} not found: {path}", file=sys.stderr)
            return 1

    paths = save_all_figures(
        out_dir,
        oat_csv=oat_csv,
        bands_csv=bands_csv,
        audit_md=audit_md,
    )
    payload = {
        "oat_top15": str(paths.oat_top15),
        "jaccard_by_profile": str(paths.jaccard_by_profile),
        "band_counts": str(paths.band_counts),
        "country_top10pct": str(paths.country_top10pct),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
