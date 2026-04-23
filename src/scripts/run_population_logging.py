"""Run the PopulationConnector over every site and dual-write raw responses.

There is no ``atoms-vs-ashes enrich population`` CLI subcommand — population
is normally consumed indirectly by RI-04/RI-06/EP-01.  This thin wrapper
exists to satisfy the mandatory raw-response logging contract introduced in
``.cursor/rules/raw-response-logging.mdc`` by exercising
``connectors.population.batch.enrich_batch`` directly.

Each site fires up to ~3 Overpass queries plus an optional GeoNames REST
lookup; the population batch helper drains the OverpassClient's per-site
accumulator and dual-writes one ``site_raw_responses`` row per site to
both Postgres and ``data/raw_responses/population/<run_id>/<site_id>.json``.

Usage:
    PYTHONPATH=src python -u scripts/run_population_logging.py \
        --run-id audit_postlogging_20260421
    PYTHONPATH=src python -u scripts/run_population_logging.py \
        --run-id <id> --country RO BG
    PYTHONPATH=src python -u scripts/run_population_logging.py \
        --run-id <id> --site-id <uuid>
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        default=f"population_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        help="run_id tag for site_raw_responses + disk path",
    )
    parser.add_argument(
        "--country", dest="country_codes",
        nargs="+", default=None,
        help="Restrict to ISO-3166-1 alpha-2 country codes",
    )
    parser.add_argument(
        "--site-id", dest="site_ids",
        nargs="+", default=None,
        help="Restrict to specific site UUIDs",
    )
    args = parser.parse_args()

    print(f"[boot] run_id={args.run_id}", flush=True)

    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.connectors.population import (
        PopulationConnector,
        enrich_batch,
    )
    from atoms_vs_ashes.db.engine import init_engine, session_scope

    settings = Settings()
    init_engine(settings)

    site_ids = [uuid.UUID(s) for s in args.site_ids] if args.site_ids else None
    country_codes = list(args.country_codes) if args.country_codes else None

    with PopulationConnector(settings) as conn, session_scope() as session:
        results = enrich_batch(
            conn,
            session,
            args.run_id,
            site_ids=site_ids,
            country_codes=country_codes,
        )

    print(
        f"DONE — sites_completed={len(results)} run_id={args.run_id}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
