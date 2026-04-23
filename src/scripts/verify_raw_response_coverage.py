"""Verify per-connector raw-response coverage for a given run_id.

For every slug listed in ``MANDATORY_LOGGING_CONNECTORS``, this script
counts the number of ``site_raw_responses`` rows tagged with the supplied
``--run-id`` and compares it to the number of sites that the connector is
expected to cover (default: every site in the DB).  Any connector with
< 100% coverage causes a non-zero exit, which means CI / cron orchestration
will fail when the rule isn't satisfied.

Usage:
    PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
        --run-id <run_id>

    PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
        --run-id <run_id> --json > coverage.json

    PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
        --run-id <run_id> --connectors osm population \
        --threshold 0.95

    # Per-connector run_ids via YAML manifest (overrides --run-id per slug):
    PYTHONPATH=src python -u scripts/verify_raw_response_coverage.py \
        --manifest audit/post_processing/raw_response_run_manifest.yml
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")


def _build_session() -> Any:
    """Create a SQLAlchemy session using project Settings."""
    from atoms_vs_ashes.db.engine import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    if engine is None:
        sys.exit(
            "ERROR: Could not initialise the database engine; check "
            "POSTGRES_HOST/USER/PASSWORD/DB env vars."
        )
    return sessionmaker(bind=engine, future=True)()


def _expected_site_ids(
    session: Any, country_codes: list[str] | None,
) -> list[Any]:
    from atoms_vs_ashes.db.models import Site

    q = session.query(Site.site_id)
    if country_codes:
        q = q.filter(Site.country_code.in_(country_codes))
    return [row[0] for row in q.all()]


def _logged_site_ids(
    session: Any, slug: str, run_id: str,
) -> list[Any]:
    from atoms_vs_ashes.db.models import SiteRawResponse

    q = (
        session.query(SiteRawResponse.site_id)
        .filter(SiteRawResponse.connector_slug == slug)
        .filter(SiteRawResponse.run_id == run_id)
        .distinct()
    )
    return [row[0] for row in q.all()]


def _disk_count(slug: str, run_id: str, project_root: Path) -> int:
    """Count files in ``data/raw_responses/<slug>/<run_id>/``."""
    folder = project_root / "data" / "raw_responses" / slug / run_id
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.glob("*.json") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run-id", required=False, default=None,
        help=(
            "Single run_id to inspect for every connector. "
            "Required unless --manifest covers all checked connectors."
        ),
    )
    parser.add_argument(
        "--manifest", type=Path, default=None,
        help=(
            "YAML file mapping connector_slug -> run_id. Overrides --run-id "
            "per slug. If a slug is missing, falls back to --run-id."
        ),
    )
    parser.add_argument(
        "--connectors", nargs="+", default=None,
        help="Subset of connector slugs to check (default: all registered)",
    )
    parser.add_argument(
        "--country-codes", nargs="+", default=None,
        help="Restrict expected site set to these country codes",
    )
    parser.add_argument(
        "--threshold", type=float, default=1.0,
        help="Min logged/expected ratio (0-1) before exiting non-zero",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit a machine-readable JSON report instead of human text",
    )
    parser.add_argument(
        "--allow-empty-disk", action="store_true",
        help=(
            "Don't fail when DB rows exist but the on-disk mirror is missing "
            "(useful for runs predating the dual-write)."
        ),
    )
    args = parser.parse_args()

    from atoms_vs_ashes.connectors import MANDATORY_LOGGING_CONNECTORS

    project_root = Path(__file__).resolve().parents[1]

    manifest_runs: dict[str, str] = {}
    if args.manifest:
        try:
            import yaml
        except ModuleNotFoundError:
            sys.exit(
                "ERROR: PyYAML is required for --manifest support; "
                "install with `pip install pyyaml`."
            )
        if not args.manifest.is_file():
            sys.exit(f"Manifest not found: {args.manifest}")
        loaded = yaml.safe_load(args.manifest.read_text()) or {}
        if not isinstance(loaded, dict):
            sys.exit(
                f"Manifest {args.manifest} must be a mapping of "
                "connector_slug -> run_id."
            )
        manifest_runs = {str(k): str(v) for k, v in loaded.items()}
        unknown_in_manifest = sorted(
            set(manifest_runs) - set(MANDATORY_LOGGING_CONNECTORS)
        )
        if unknown_in_manifest:
            sys.exit(
                "Manifest references unknown connector slug(s): "
                f"{', '.join(unknown_in_manifest)}"
            )

    if args.connectors:
        unknown = [
            c for c in args.connectors
            if c not in MANDATORY_LOGGING_CONNECTORS
        ]
        if unknown:
            sys.exit(f"Unknown connector slug(s): {', '.join(unknown)}")
        registry = {
            slug: MANDATORY_LOGGING_CONNECTORS[slug]
            for slug in args.connectors
        }
    else:
        registry = MANDATORY_LOGGING_CONNECTORS

    # Build slug -> run_id map. Manifest entries win; --run-id fills gaps.
    run_ids: dict[str, str | None] = {}
    for slug in registry:
        run_ids[slug] = manifest_runs.get(slug, args.run_id)
    missing_rid = [slug for slug, rid in run_ids.items() if not rid]
    if missing_rid:
        sys.exit(
            "ERROR: No run_id resolved for: "
            f"{', '.join(missing_rid)}. Pass --run-id and/or extend the "
            "manifest."
        )

    session = _build_session()
    try:
        expected = _expected_site_ids(session, args.country_codes)
    finally:
        # we'll reopen for each query loop to ensure isolation
        pass

    expected_set = {str(s) for s in expected}
    n_expected = len(expected_set)
    if n_expected == 0:
        sys.exit("No sites found in DB matching filter; aborting.")

    report: dict[str, dict[str, Any]] = {}
    overall_ok = True

    for slug, spec in sorted(registry.items()):
        rid = run_ids[slug]
        logged_ids = {str(s) for s in _logged_site_ids(session, slug, rid)}
        n_logged = len(logged_ids)
        missing_set = expected_set - logged_ids
        n_disk = _disk_count(slug, rid, project_root)

        ratio = (n_logged / n_expected) if n_expected else 0.0
        ratio_ok = ratio >= args.threshold

        disk_ok = n_disk >= n_logged
        if args.allow_empty_disk and n_disk == 0:
            disk_ok = True

        ok = ratio_ok and disk_ok
        if not ok:
            overall_ok = False

        report[slug] = {
            "run_id": rid,
            "logger_fn": spec["logger_fn"],
            "expected_sites": n_expected,
            "logged_sites": n_logged,
            "disk_files": n_disk,
            "missing_sites": sorted(missing_set)[:25],
            "missing_count": len(missing_set),
            "coverage_ratio": round(ratio, 4),
            "ok": ok,
            "reason": (
                None if ok
                else (
                    "below_threshold"
                    if not ratio_ok else "disk_mirror_short"
                )
            ),
        }

    if args.json:
        print(json.dumps({
            "run_id": args.run_id,
            "manifest": str(args.manifest) if args.manifest else None,
            "threshold": args.threshold,
            "country_codes": args.country_codes,
            "overall_ok": overall_ok,
            "connectors": report,
        }, indent=2))
    else:
        _print_human_report(
            args.run_id, args.manifest, n_expected, args.threshold,
            report, overall_ok,
        )

    return 0 if overall_ok else 2


def _print_human_report(
    run_id: str | None,
    manifest: Path | None,
    n_expected: int,
    threshold: float,
    report: dict[str, dict[str, Any]],
    overall_ok: bool,
) -> None:
    if manifest:
        print(f"Raw-response coverage from manifest={manifest}")
        if run_id:
            print(f"  (fallback --run-id={run_id})")
    else:
        print(f"Raw-response coverage for run_id={run_id}")
    print(f"Expected sites:  {n_expected}")
    print(f"Threshold:       {threshold:.0%}")
    print()
    header = (
        f"{'connector':<24} {'logger_fn':<22} {'run_id':<34} "
        f"{'logged':>7} {'disk':>5} {'missing':>8} {'ratio':>7}  status"
    )
    print(header)
    print("-" * len(header))

    for slug, info in report.items():
        status = "OK" if info["ok"] else f"FAIL ({info['reason']})"
        print(
            f"{slug:<24} {info['logger_fn']:<22} "
            f"{(info['run_id'] or '-'):<34} "
            f"{info['logged_sites']:>7} {info['disk_files']:>5} "
            f"{info['missing_count']:>8} "
            f"{info['coverage_ratio']:>7.2%}  {status}"
        )
        if not info["ok"] and info["missing_sites"]:
            preview = ", ".join(info["missing_sites"][:5])
            tail = "" if info["missing_count"] <= 5 else (
                f" (+{info['missing_count'] - 5} more)"
            )
            print(f"    missing site_ids: {preview}{tail}")

    print()
    print(f"Overall: {'PASS' if overall_ok else 'FAIL'}")


if __name__ == "__main__":
    sys.exit(main())
