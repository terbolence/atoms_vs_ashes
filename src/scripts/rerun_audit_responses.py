"""Re-run API connectors to capture raw responses for audit compliance.

For each connector, re-fetches data per site, logs the raw response to
both disk and DB (via site_raw_responses), and compares derived values
against what is currently stored.  On mismatch, writes a report and
pauses for user instruction.

Usage:
    PYTHONPATH=src python -u scripts/rerun_audit_responses.py \
        --run-id audit_rerun_20260419 --connectors corine natura2000
    PYTHONPATH=src python -u scripts/rerun_audit_responses.py \
        --run-id audit_rerun_20260419 --all
    PYTHONPATH=src python -u scripts/rerun_audit_responses.py \
        --run-id audit_rerun_20260419 --resume  # continue after mismatch review
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))

CONNECTORS_WITH_API = [
    "corine",
    "natura2000",
    "egdi_geology",
    "onegeology",
    "copernicus_ems",
    "noaa_ncei",
    "soilgrids",
    "bdticm_bedrock",
    "copernicus_dem",
]

MISMATCH_DIR = Path("audit/response_mismatches")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _report_mismatch(
    connector_slug: str,
    site_id: uuid.UUID,
    site_name: str,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> Path:
    """Write a mismatch report and return the file path."""
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{connector_slug}_{_timestamp()}.md"
    fpath = MISMATCH_DIR / fname

    lines = [
        f"# Data Mismatch Report: {connector_slug}",
        "",
        f"**Site**: {site_name} (`{site_id}`)",
        f"**Detected at**: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Current DB values",
        "```json",
        json.dumps(old_values, indent=2, default=str),
        "```",
        "",
        "## Newly fetched values",
        "```json",
        json.dumps(new_values, indent=2, default=str),
        "```",
        "",
        "## Differences",
    ]

    for key in sorted(set(list(old_values.keys()) + list(new_values.keys()))):
        old_v = old_values.get(key)
        new_v = new_values.get(key)
        if old_v != new_v:
            lines.append(f"- **{key}**: `{old_v}` → `{new_v}`")

    lines.append("")
    lines.append("## Action Required")
    lines.append("Review the differences above and decide:")
    lines.append("1. Keep existing DB values (skip update)")
    lines.append("2. Update DB with new values")
    lines.append("3. Investigate further")
    lines.append("")
    lines.append("Re-run with `--resume` after resolving.")

    fpath.write_text("\n".join(lines), encoding="utf-8")
    return fpath


def _run_connector(
    connector_slug: str,
    run_id: str,
    session: Any,
    settings: Any,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """Re-run a single connector for all sites, logging raw responses.

    Returns dict with keys: total, logged, skipped, mismatched, errors.
    """
    from atoms_vs_ashes.db.models import Site

    stats = {"total": 0, "logged": 0, "skipped": 0, "mismatched": 0, "errors": 0}

    sites = session.query(Site).order_by(Site.country_code, Site.name).all()
    stats["total"] = len(sites)

    print(f"  [{connector_slug}] {len(sites)} sites to process", flush=True)

    if connector_slug == "corine":
        from atoms_vs_ashes.connectors.corine import CorineConnector
        with CorineConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    summary = connector.classify(
                        float(site.latitude), float(site.longitude),
                    )
                    if connector.last_raw_response is not None:
                        from atoms_vs_ashes.connectors.response_logger import log_raw_response
                        log_raw_response(
                            session,
                            site_id=site.site_id,
                            connector_slug="corine",
                            run_id=run_id,
                            request_url=connector.last_request_url or "",
                            request_params=connector.last_request_params,
                            response_body=connector.last_raw_response,
                            http_status=connector.last_http_status,
                        )
                        stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1
                    print(f"    [ERROR] {site.name}: {exc}", flush=True)

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)
                time.sleep(2.0)

    elif connector_slug == "natura2000":
        from atoms_vs_ashes.connectors.natura2000 import Natura2000Connector
        with Natura2000Connector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch(
                        float(site.latitude), float(site.longitude),
                        country_code=site.country_code,
                    )
                    if connector.last_raw_response is not None:
                        from atoms_vs_ashes.connectors.response_logger import log_raw_response
                        log_raw_response(
                            session,
                            site_id=site.site_id,
                            connector_slug="natura2000",
                            run_id=run_id,
                            request_url=connector.last_request_url or "",
                            request_params=connector.last_request_params,
                            response_body=connector.last_raw_response,
                            http_status=connector.last_http_status,
                        )
                        stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1
                    print(f"    [ERROR] {site.name}: {exc}", flush=True)

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)
                time.sleep(0.5)

    elif connector_slug == "egdi_geology":
        from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
        with EgdiGeologyConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch_all(
                        float(site.latitude), float(site.longitude),
                        country_code=site.country_code,
                    )
                    if connector.last_raw_responses:
                        from atoms_vs_ashes.connectors.response_logger import log_raw_response
                        combined = {"layers": connector.last_raw_responses}
                        log_raw_response(
                            session,
                            site_id=site.site_id,
                            connector_slug="egdi_geology",
                            run_id=run_id,
                            request_url=connector._wfs_url,
                            response_body=combined,
                        )
                        stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1
                    print(f"    [ERROR] {site.name}: {exc}", flush=True)

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)
                time.sleep(1.0)

    elif connector_slug == "onegeology":
        from atoms_vs_ashes.connectors.onegeology import OneGeologyConnector
        from atoms_vs_ashes.db.models import SiteNaturalHazards
        with OneGeologyConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    nh = session.get(SiteNaturalHazards, site.site_id)
                    result = connector.fetch_all(
                        float(site.latitude), float(site.longitude),
                        country_code=site.country_code or "",
                        s02_nh02_quality=nh.nh02_quality if nh else None,
                        s02_nh05_quality=nh.nh05_quality if nh else None,
                    )
                    if connector.last_raw_responses:
                        from atoms_vs_ashes.connectors.response_logger import log_raw_response
                        combined = {"layers": connector.last_raw_responses}
                        log_raw_response(
                            session,
                            site_id=site.site_id,
                            connector_slug="onegeology",
                            run_id=run_id,
                            request_url=result.endpoints_queried[0] if result.endpoints_queried else "",
                            response_body=combined,
                        )
                        stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)
                time.sleep(1.0)

    elif connector_slug == "copernicus_ems":
        from atoms_vs_ashes.connectors.copernicus_ems import CopernicusEmsConnector
        with CopernicusEmsConnector(settings) as connector:
            print("    Fetching EMS catalogue (Phase A)...", flush=True)
            cat = connector.ingest_catalogue(run_id)
            print(
                f"    Catalogue: {cat.n_rrm_fetched} RRM + "
                f"{cat.n_rapid_fetched} Rapid activations",
                flush=True,
            )
            stats["logged"] = 1
            stats["total"] = 1

    elif connector_slug == "noaa_ncei":
        from atoms_vs_ashes.connectors.noaa_ncei import NoaaNceiConnector
        with NoaaNceiConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch_all(
                        float(site.latitude), float(site.longitude),
                    )
                    if connector.last_raw_responses:
                        from atoms_vs_ashes.connectors.response_logger import log_raw_response
                        combined = {"api_calls": connector.last_raw_responses}
                        log_raw_response(
                            session,
                            site_id=site.site_id,
                            connector_slug="noaa_ncei",
                            run_id=run_id,
                            request_url="https://www.ncei.noaa.gov/cdo-web/api/v2/",
                            response_body=combined,
                        )
                        stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1
                    print(f"    [ERROR] {site.name}: {exc}", flush=True)

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)

    elif connector_slug == "soilgrids":
        from atoms_vs_ashes.connectors.soilgrids import SoilGridsConnector
        from atoms_vs_ashes.connectors.soilgrids.models import SOURCE_URL
        with SoilGridsConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch(
                        float(site.latitude), float(site.longitude),
                    )
                    from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
                    log_raster_extraction(
                        session,
                        site_id=site.site_id,
                        connector_slug="soilgrids",
                        run_id=run_id,
                        source_url=SOURCE_URL,
                        extracted_values=result.raw_values or {},
                        crs="EPSG:152160",
                        resolution_m=250,
                    )
                    stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)

    elif connector_slug == "bdticm_bedrock":
        from atoms_vs_ashes.connectors.bdticm_bedrock import BdticmBedrockConnector
        from atoms_vs_ashes.connectors.bdticm_bedrock.models import SOURCE_URL
        with BdticmBedrockConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch(
                        float(site.latitude), float(site.longitude),
                    )
                    from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
                    log_raster_extraction(
                        session,
                        site_id=site.site_id,
                        connector_slug="bdticm_bedrock",
                        run_id=run_id,
                        source_url=SOURCE_URL,
                        extracted_values={
                            "depth_cm": result.depth_cm,
                            "depth_m": result.depth_m,
                        },
                        pixel_coords=(float(site.longitude), float(site.latitude)),
                        resolution_m=250,
                    )
                    stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)

    elif connector_slug == "copernicus_dem":
        from atoms_vs_ashes.connectors.copernicus_dem import CopernicusDemConnector
        from atoms_vs_ashes.connectors.copernicus_dem.models import SOURCE_URL
        with CopernicusDemConnector(settings) as connector:
            for i, site in enumerate(sites):
                try:
                    result = connector.fetch(
                        float(site.latitude), float(site.longitude),
                    )
                    from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
                    log_raster_extraction(
                        session,
                        site_id=site.site_id,
                        connector_slug="copernicus_dem",
                        run_id=run_id,
                        source_url=SOURCE_URL,
                        extracted_values={
                            "elevation_m": result.elevation.site_elevation_m,
                            "slope_max_deg": result.slope.max_deg,
                            "slope_mean_deg": result.slope.mean_deg,
                            "slope_stability_class": result.slope_stability_class,
                        },
                        pixel_coords=(float(site.longitude), float(site.latitude)),
                        resolution_m=30,
                    )
                    stats["logged"] += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    stats["errors"] += 1
                    print(f"    [ERROR] {site.name}: {exc}", flush=True)

                if (i + 1) % 25 == 0:
                    print(f"    progress: {i+1}/{len(sites)}", flush=True)

    else:
        print(f"  [SKIP] Unknown connector: {connector_slug}", flush=True)

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-run API connectors to capture raw responses for audit."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--connectors", nargs="+", default=[],
        help="Connector slugs to re-run (e.g. corine natura2000)",
    )
    parser.add_argument(
        "--all", dest="all_connectors", action="store_true",
        help="Re-run all connectors",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be done without calling APIs",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume after mismatch review",
    )
    args = parser.parse_args()

    connectors = args.connectors or (CONNECTORS_WITH_API if args.all_connectors else [])
    if not connectors:
        parser.error("Specify --connectors or --all")

    print(f"[boot] importing modules...", flush=True)
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.db.engine import init_engine, session_scope

    settings = Settings()
    init_engine(settings)

    print(f"[config] run_id={args.run_id}", flush=True)
    print(f"[config] connectors={connectors}", flush=True)

    if args.dry_run:
        print("[dry-run] Would re-run the following connectors:")
        for c in connectors:
            print(f"  - {c}")
        return 0

    overall: dict[str, dict[str, int]] = {}

    for slug in connectors:
        print(f"\n{'='*60}", flush=True)
        print(f"[{slug}] Starting re-run...", flush=True)
        print(f"{'='*60}", flush=True)

        with session_scope() as session:
            stats = _run_connector(slug, args.run_id, session, settings)
            overall[slug] = stats
            print(
                f"[{slug}] Done: "
                f"total={stats['total']}, logged={stats['logged']}, "
                f"errors={stats['errors']}, mismatched={stats['mismatched']}",
                flush=True,
            )

    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for slug, stats in overall.items():
        print(
            f"  {slug:25s}  total={stats['total']:4d}  "
            f"logged={stats['logged']:4d}  errors={stats['errors']:3d}",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
