"""Capture raw Overpass API responses for audit compliance.

Thin wrapper around :func:`atoms_vs_ashes.connectors.osm.batch.enrich_audit_responses`,
which is the canonical implementation.  The connector itself is responsible
for dual-writing raw responses to ``site_raw_responses`` (DB) and
``data/raw_responses/osm/<run_id>/<site_id>.json`` (disk) — see
``.cursor/rules/raw-response-logging.mdc``.

Usage:
    PYTHONPATH=src python -u scripts/run_osm_audit_responses.py
    PYTHONPATH=src python -u scripts/run_osm_audit_responses.py --run-id my_run
    PYTHONPATH=src python -u scripts/run_osm_audit_responses.py --resume --run-id osm_audit_20260420
    PYTHONPATH=src python -u scripts/run_osm_audit_responses.py --overpass-url https://overpass.kumi.systems/api/interpreter
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture raw Overpass API responses for audit."
    )
    parser.add_argument(
        "--run-id",
        default=f"osm_audit_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
    )
    parser.add_argument(
        "--overpass-url",
        default="https://overpass-api.de/api/interpreter",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip sites that already have responses for this run_id",
    )
    args = parser.parse_args()

    print("[boot] importing modules...", flush=True)
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.connectors.osm.batch import enrich_audit_responses
    from atoms_vs_ashes.connectors.osm.client import OverpassClient
    from atoms_vs_ashes.db.engine import init_engine, session_scope

    settings = Settings()
    init_engine(settings)

    print(f"[config] run_id={args.run_id}", flush=True)
    print(f"[config] overpass_url={args.overpass_url}", flush=True)

    client = OverpassClient(
        settings=settings,
        overpass_url=args.overpass_url,
        retry_on_error=True,
    )

    with session_scope() as session:
        summary = enrich_audit_responses(
            client,
            session,
            run_id=args.run_id,
            skip_already_logged=args.resume,
        )

    print(
        f"DONE — total={summary['total']} logged={summary['logged']} "
        f"errors={summary['errors']} skipped={summary['skipped']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
