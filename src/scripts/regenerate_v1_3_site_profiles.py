"""Refresh the 65 v1.03 site profiles (+ add Iernut) against the frozen
Phase 2 run identifiers.

For every existing ``<CC>_<slug>_site_bundle.json`` the script invokes
``build_country_profile_prototype`` in ``--site-only`` mode with the
canonical ``site_id`` taken from the bundle. ``--add`` lets callers
inject a brand-new profile (e.g. Iernut for feedback comment #60) by
passing ``COUNTRY:SITE NAME``.

Filled specialist blocks are preserved automatically by
``_preserve_filled_placeholders`` inside ``write_artifacts``; no
external preservation helper is required.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.build_country_profile_prototype import main as run_one


_DEFAULT_OUTPUT = Path(
    "report/version 1.03/output/report/chapters/05_country_and_site_profiles"
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("regenerate_v1_3_site_profiles")
    p.add_argument("--scoring-run-id", required=True)
    p.add_argument("--sensitivity-run-id", required=True)
    p.add_argument("--sensitivity-stamp", required=True)
    p.add_argument("--smr-key", default="nuscale_voygr6")
    p.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT)
    p.add_argument(
        "--add", action="append", default=[],
        help=(
            "Country:Site Name entry to add (e.g. 'RO:Iernut power station'). "
            "Used to inject sites not yet present in data/ as a "
            "<CC>_<slug>_site_bundle.json. May be repeated."
        ),
    )
    p.add_argument(
        "--limit", type=int, default=None,
        help="Optional cap for spot-check runs (process only first N bundles).",
    )
    return p


def _discover_existing(data_dir: Path) -> list[tuple[str, str]]:
    """Return ``(country_code, site_id)`` pairs for every existing
    site bundle JSON under ``data_dir``."""
    out: list[tuple[str, str]] = []
    for path in sorted(data_dir.glob("*_site_bundle.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ! skip {path.name}: {exc}", file=sys.stderr)
            continue
        site = payload.get("site") or {}
        meta = payload.get("metadata") or {}
        cc = site.get("country_code") or path.name[:2]
        sid = meta.get("site_id") or site.get("site_id")
        if cc and sid:
            out.append((cc, str(sid)))
    return out


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    data_dir = args.output_dir / "data"
    existing = _discover_existing(data_dir)
    if args.limit is not None:
        existing = existing[:args.limit]

    failures: list[str] = []
    for cc, site_id in existing:
        print(f"[site-profile] {cc} {site_id}")
        try:
            run_one([
                "--country-code", cc,
                "--site-id", site_id,
                "--site-only",
                "--smr-key", args.smr_key,
                "--scoring-run-id", args.scoring_run_id,
                "--sensitivity-run-id", args.sensitivity_run_id,
                "--sensitivity-stamp", args.sensitivity_stamp,
                "--output-dir", str(args.output_dir),
            ])
        except SystemExit as exc:
            if exc.code not in (0, None):
                failures.append(f"{cc}/{site_id}: SystemExit({exc.code})")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{cc}/{site_id}: {type(exc).__name__}: {exc}")

    for entry in args.add:
        if ":" not in entry:
            failures.append(f"--add invalid (missing ':'): {entry!r}")
            continue
        cc, _, site_name = entry.partition(":")
        cc = cc.strip().upper()
        site_name = site_name.strip()
        print(f"[site-profile +new] {cc} {site_name}")
        try:
            run_one([
                "--country-code", cc,
                "--site-name", site_name,
                "--site-only",
                "--smr-key", args.smr_key,
                "--scoring-run-id", args.scoring_run_id,
                "--sensitivity-run-id", args.sensitivity_run_id,
                "--sensitivity-stamp", args.sensitivity_stamp,
                "--output-dir", str(args.output_dir),
            ])
        except SystemExit as exc:
            if exc.code not in (0, None):
                failures.append(f"+{cc}/{site_name}: SystemExit({exc.code})")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"+{cc}/{site_name}: {type(exc).__name__}: {exc}")

    if failures:
        print("FAILURES:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(
        f"Refreshed {len(existing)} site profiles; "
        f"added {len(args.add)} new profile(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
