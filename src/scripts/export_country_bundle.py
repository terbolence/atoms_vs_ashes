# man_hours: 0.5
"""Export one country narrative bundle as JSON.

Companion to ``export_site_bundle.py``. Read-only. Does not call any
external APIs. When the user asks "give me all data for this country",
this is the canonical entry point.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.reporting import build_country_bundle
from scripts._country_profile_query import resolve_runs


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("export_country_bundle")
    p.add_argument("--country-code", required=True, help="ISO-2 country code, e.g. RO")
    p.add_argument("--smr", default="nuscale_voygr6", help="SMR key (default nuscale_voygr6)")
    p.add_argument("--run-id", help="Scoring run_id; auto-resolved when omitted")
    p.add_argument(
        "--sensitivity-run-id",
        help="Sensitivity run_id; auto-resolved when omitted",
    )
    p.add_argument(
        "--sensitivity-stamp",
        default="20260425b",
        help="Report-output sensitivity pack stamp (default: 20260425b)",
    )
    p.add_argument(
        "--include-site-bundles",
        action="store_true",
        help="Embed the full per-site bundle for every site in the country",
    )
    p.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; stdout is used when omitted",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    init_engine(Settings())
    with session_scope() as session:
        scoring, sensitivity = resolve_runs(
            session, args.run_id, args.sensitivity_run_id,
        )
        payload = build_country_bundle(
            session,
            country_code=args.country_code,
            smr_key=args.smr,
            run_id=scoring,
            sensitivity_run_id=sensitivity,
            sensitivity_stamp=args.sensitivity_stamp,
            include_site_bundles=args.include_site_bundles,
        )

    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
