#!/usr/bin/env python
# man_hours: 2.5
"""Audit site-area evidence and write recommended footprint values to CSV.

This script is read-only against the database. It produces an operator review
artifact that must be inspected before any consent-gated write is run.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from atoms_vs_ashes.analysis.site_area_db import (
    DEFAULT_DB,
    DEFAULT_LLM_DB,
    fetch_site_rows,
    load_manual_overrides,
    recommendations_from_rows,
    summarize_recommendations,
    write_recommendations_csv,
)


def default_output_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        PROJECT_ROOT
        / "audit"
        / "post_processing"
        / "06_scoring"
        / f"{stamp}_site_area_confidence.csv"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-name", default=DEFAULT_DB)
    parser.add_argument("--llm-db-name", default=DEFAULT_LLM_DB)
    parser.add_argument("--out", type=Path, default=default_output_path())
    parser.add_argument("--manual-overrides", type=Path)
    parser.add_argument("--site-id", action="append", dest="site_ids")
    parser.add_argument("--limit", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = fetch_site_rows(
        db_name=args.db_name,
        llm_db_name=args.llm_db_name,
        limit=args.limit,
        site_ids=args.site_ids,
    )
    recommendations = recommendations_from_rows(
        rows,
        manual_overrides=load_manual_overrides(args.manual_overrides),
    )
    write_recommendations_csv(recommendations, args.out)

    summary = summarize_recommendations(recommendations)
    print(f"Wrote {len(recommendations)} site-area audit rows to {args.out}")
    for key in sorted(summary):
        print(f"{key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
