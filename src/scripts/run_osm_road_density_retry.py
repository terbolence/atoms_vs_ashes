"""Retry the road_density Overpass query for all sites.

The main OSM audit run logged 6/7 query types successfully but
road_density consistently failed with 406 due to maxsize being too large.
This script retries only road_density and merges results into
site_raw_responses rows that already exist for each site.

Usage:
    PYTHONPATH=src python -u scripts/run_osm_road_density_retry.py
    PYTHONPATH=src python -u scripts/run_osm_road_density_retry.py --resume
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))

INTER_QUERY_DELAY_S = 25
INTER_QUERY_JITTER_S = 5
ROAD_RADIUS_M = 16_000


def _delay() -> None:
    jitter = random.uniform(-INTER_QUERY_JITTER_S, INTER_QUERY_JITTER_S)
    time.sleep(max(8, INTER_QUERY_DELAY_S + jitter))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Skip sites already logged")
    args = parser.parse_args()

    print("[boot] importing modules...", flush=True)
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.connectors.osm.client import OverpassClient, enable_raw_response_logging
    from atoms_vs_ashes.connectors.response_logger import log_raw_response
    from atoms_vs_ashes.db.engine import init_engine, session_scope
    from atoms_vs_ashes.db.models import Site
    from sqlalchemy import text

    settings = Settings()
    init_engine(settings)

    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw_responses" / "overpass"
    enable_raw_response_logging(raw_dir)

    run_id = "osm_road_density_retry_20260420"
    overpass_url = "https://overpass-api.de/api/interpreter"

    print(f"[config] run_id={run_id}", flush=True)
    print(f"[config] overpass_url={overpass_url}", flush=True)

    with session_scope() as session:
        sites = session.query(Site).order_by(Site.country_code, Site.name).all()
        site_list = [(s.site_id, s.name, float(s.latitude), float(s.longitude)) for s in sites]

    print(f"[info] {len(site_list)} sites to process", flush=True)

    already_done: set = set()
    if args.resume:
        with session_scope() as session:
            rows = session.execute(
                text("SELECT DISTINCT site_id FROM site_raw_responses WHERE connector_slug = 'osm_road_density' AND run_id = :rid"),
                {"rid": run_id},
            ).fetchall()
            already_done = {r[0] for r in rows}
        print(f"[resume] Skipping {len(already_done)} already-logged sites", flush=True)

    client = OverpassClient(
        settings=settings,
        overpass_url=overpass_url,
        retry_on_error=True,
    )

    total = len(site_list)
    logged = 0
    errors = 0
    t_global = time.monotonic()

    print(f"\n{'='*70}", flush=True)
    print(f"  Road density retry — {total} sites ({total - len(already_done)} remaining)", flush=True)
    print(f"{'='*70}\n", flush=True)

    for i, (site_id, name, lat, lon) in enumerate(site_list):
        if site_id in already_done:
            continue
        print(f"[{i+1:3d}/{total}] {name} ({lat:.4f}, {lon:.4f})", flush=True, end="")

        try:
            result = client.fetch_road_density(lat, lon, ROAD_RADIUS_M)
            road_body = {
                "type": "road_density",
                "data": result,
            }

            with session_scope() as session:
                log_raw_response(
                    session,
                    site_id=site_id,
                    connector_slug="osm_road_density",
                    run_id=run_id,
                    request_url=overpass_url,
                    response_body=road_body,
                    http_status=200 if not client.was_error else client._last_http_status,
                )
                session.commit()
            logged += 1
            total_km = result.get("total_km", "?")
            print(f"  — OK (total_km={total_km})", flush=True)

        except Exception as exc:
            errors += 1
            print(f"  — ERROR: {exc}", flush=True)

        if (i + 1) % 10 == 0:
            elapsed = time.monotonic() - t_global
            rate = logged / elapsed if elapsed > 0 else 0
            remaining = total - (i + 1)
            eta_s = remaining / rate if rate > 0 else 0
            print(
                f"  [progress] {i+1}/{total} | logged={logged} errors={errors} | "
                f"rate={rate*3600:.0f}/hr | ETA={eta_s/3600:.1f}h",
                flush=True,
            )

        _delay()

    elapsed_total = time.monotonic() - t_global
    print(f"\n{'='*70}", flush=True)
    print(f"  DONE — {logged} logged, {errors} errors ({elapsed_total/60:.1f} min)", flush=True)
    print(f"{'='*70}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
