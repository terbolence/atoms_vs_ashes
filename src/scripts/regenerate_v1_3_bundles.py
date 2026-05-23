"""Refresh all v1.03 country + site bundles, ledgers, and feedback_rerun
country bundles against the frozen Phase 2 run identifiers.

Phase 2 of the v1.03 feedback resolution plan post-processes three
frozen database runs without re-scoring:

* ``--scoring-run-id``      composite_rankings parent run
* ``--sensitivity-run-id``  national-sensitivity child run (50k iter)
* ``--sensitivity-stamp``   report-output sensitivity-pack stamp

The script only touches **data** payloads (JSON bundles and the
``<CC>_site_ledger.csv`` files). Markdown/figures stay frozen until
Phase 3 reruns ``build_country_profile_prototype.py``. Bundles are
discovered by glob so adding a new site (e.g. Iernut in Phase 3) is a
one-line addition.

Outputs:

* ``<chapter5>/data/<CC>_country_bundle.json``  - one per country in
  ``--countries``.
* ``<chapter5>/data/<CC>_<slug>_site_bundle.json``  - one per existing
  site bundle (refreshed in place; new ones must be added by Phase 3).
* ``<chapter5>/data/<CC>_site_ledger.csv``  - one per country.
* ``<feedback-rerun>/<CC>_country_bundle.json``  - one per code listed
  in ``--feedback-rerun-countries``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.reporting import build_country_bundle, build_site_bundle


_DEFAULT_CHAPTER5 = Path(
    "report/version 1.03/output/report/chapters/05_country_and_site_profiles"
)
_DEFAULT_FEEDBACK_RERUN = Path(
    "report/version 1.03/output/report/bundles/feedback_rerun_20260509"
)

_DEFAULT_COUNTRIES = (
    "AT", "BA", "BG", "BY", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)

_DEFAULT_FEEDBACK_RERUN_COUNTRIES = (
    "AL", "AT", "BA", "BG", "BY", "CZ", "HR", "HU", "LV", "MD",
    "ME", "MK", "PL", "RO", "RS", "SI", "SK", "TR", "UA", "XK",
)

_LEDGER_COLS = (
    "national_rank", "name", "passed_exclusionary",
    "passed_avoidance", "composite_score", "composite_score_low",
    "composite_score_high", "national_band",
    "national_top10pct_hit_rate", "criteria_coverage",
    "avg_confidence", "installed_capacity_mw",
    "latitude", "longitude",
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("regenerate_v1_3_bundles")
    p.add_argument("--scoring-run-id", required=True)
    p.add_argument("--sensitivity-run-id", required=True)
    p.add_argument("--sensitivity-stamp", required=True)
    p.add_argument("--smr-key", default="nuscale_voygr6")
    p.add_argument(
        "--chapter5-root", type=Path, default=_DEFAULT_CHAPTER5,
        help="Root of v1.03 Chapter 5 country/site profiles directory.",
    )
    p.add_argument(
        "--feedback-rerun-root", type=Path, default=_DEFAULT_FEEDBACK_RERUN,
        help="Root of feedback_rerun country bundles directory.",
    )
    p.add_argument(
        "--countries", nargs="+", default=list(_DEFAULT_COUNTRIES),
        help="ISO-2 codes for the 17 in-scope countries.",
    )
    p.add_argument(
        "--feedback-rerun-countries", nargs="+",
        default=list(_DEFAULT_FEEDBACK_RERUN_COUNTRIES),
        help="ISO-2 codes for the 20 feedback_rerun bundles.",
    )
    return p


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def _write_ledger_csv(path: Path, sites: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_LEDGER_COLS), lineterminator="\n")
        writer.writeheader()
        for row in sites:
            writer.writerow({col: row.get(col) for col in _LEDGER_COLS})


def _existing_site_bundle_ids(data_dir: Path, cc: str) -> list[tuple[Path, uuid.UUID]]:
    """Return ``(path, site_id)`` for every existing site-bundle JSON
    under ``data_dir`` belonging to country ``cc``.

    The function reads the existing JSON so we do not need any external
    slug-to-uuid mapping. Adding a new site means dropping in its bundle
    JSON before running Phase 2 (Phase 3 does this for Iernut).
    """
    matches: list[tuple[Path, uuid.UUID]] = []
    for path in sorted(data_dir.glob(f"{cc}_*_site_bundle.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ! skip {path.name}: {exc}", file=sys.stderr)
            continue
        sid = (payload.get("metadata") or {}).get("site_id")
        if not sid:
            print(f"  ! skip {path.name}: no metadata.site_id", file=sys.stderr)
            continue
        try:
            matches.append((path, uuid.UUID(str(sid))))
        except ValueError as exc:
            print(f"  ! skip {path.name}: bad site_id ({exc})", file=sys.stderr)
    return matches


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    init_engine(Settings())

    chapter5 = args.chapter5_root.resolve()
    data_dir = chapter5 / "data"
    feedback_root = args.feedback_rerun_root.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    feedback_root.mkdir(parents=True, exist_ok=True)

    country_total = len(args.countries)
    site_total = 0
    feedback_total = 0

    with session_scope() as session:
        for cc in args.countries:
            print(f"[country] {cc}")
            country_bundle = build_country_bundle(
                session, country_code=cc, smr_key=args.smr_key,
                run_id=args.scoring_run_id,
                sensitivity_run_id=args.sensitivity_run_id,
                sensitivity_stamp=args.sensitivity_stamp,
            )
            _write_json(data_dir / f"{cc}_country_bundle.json", country_bundle)
            _write_ledger_csv(
                data_dir / f"{cc}_site_ledger.csv",
                country_bundle.get("sites", []),
            )
            for site_path, site_id in _existing_site_bundle_ids(data_dir, cc):
                site_bundle = build_site_bundle(
                    session, site_id=site_id, smr_key=args.smr_key,
                    run_id=args.scoring_run_id,
                    sensitivity_run_id=args.sensitivity_run_id,
                    sensitivity_stamp=args.sensitivity_stamp,
                )
                _write_json(site_path, site_bundle)
                site_total += 1

        for cc in args.feedback_rerun_countries:
            print(f"[feedback_rerun] {cc}")
            try:
                bundle = build_country_bundle(
                    session, country_code=cc, smr_key=args.smr_key,
                    run_id=args.scoring_run_id,
                    sensitivity_run_id=args.sensitivity_run_id,
                    sensitivity_stamp=args.sensitivity_stamp,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  ! {cc} feedback_rerun bundle failed: {exc}", file=sys.stderr)
                continue
            _write_json(
                feedback_root / f"{cc}_country_bundle.json", bundle,
            )
            feedback_total += 1

    print(
        f"Refreshed {country_total} country bundles, {site_total} site "
        f"bundles, {country_total} ledger CSVs, and {feedback_total} "
        f"feedback_rerun bundles."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
