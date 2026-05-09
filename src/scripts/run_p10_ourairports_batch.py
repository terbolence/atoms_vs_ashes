# man_hours: 0.6
"""Run P10 OurAirports batch enrichment for all sites.

Usage:
    .venv/bin/python scripts/run_p10_ourairports_batch.py [--run-id RUN_ID]
    .venv/bin/python scripts/run_p10_ourairports_batch.py --requery-nulls
    .venv/bin/python scripts/run_p10_ourairports_batch.py --country RO,BG
    .venv/bin/python scripts/run_p10_ourairports_batch.py --site-id <UUID>
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from atoms_vs_ashes.connectors.ourairports import OurAirportsConnector
from atoms_vs_ashes.connectors.ourairports.batch import enrich_batch
from atoms_vs_ashes.db.engine import init_engine, session_scope


def main() -> None:
    parser = argparse.ArgumentParser(description="P10 OurAirports batch enrichment")
    parser.add_argument("--run-id", default=None, help="Run ID (auto-generated if omitted)")
    parser.add_argument(
        "--country", default=None,
        help="Comma-separated ISO country codes (e.g. RO,BG); enriches all sites in those countries.",
    )
    parser.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict enrichment to specific site UUIDs. Repeatable.",
    )
    parser.add_argument(
        "--requery-nulls", action="store_true",
        help="Bypass cache and only re-query sites whose HI-01 fields are NULL or low-quality.",
    )
    args = parser.parse_args()

    run_id = args.run_id or f"p10-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    site_ids: list[uuid.UUID] | None = None
    if args.site_id:
        site_ids = [uuid.UUID(s) for s in args.site_id]

    country_codes: list[str] | None = None
    if args.country:
        country_codes = [c.strip().upper() for c in args.country.split(",") if c.strip()]

    print(f"[{_ts()}] === P10 OurAirports Batch Enrichment ===")
    print(f"[{_ts()}] Run ID: {run_id}")

    # Step 1: Init DB
    print(f"[{_ts()}] Initialising database connection...")
    init_engine()

    # Step 2: Download + build index
    print(f"[{_ts()}] Creating OurAirports connector...")
    connector = OurAirportsConnector()

    print(f"[{_ts()}] Health check...")
    healthy = connector.health_check()
    print(f"[{_ts()}] Health check: {'OK' if healthy else 'FAILED'}")
    if not healthy:
        print(f"[{_ts()}] ERROR: OurAirports endpoint unreachable. Aborting.")
        sys.exit(1)

    print(f"[{_ts()}] Downloading airports.csv (if not cached)...")
    csv_path = connector.download()
    print(f"[{_ts()}] CSV path: {csv_path} ({csv_path.stat().st_size / 1024 / 1024:.1f} MB)")

    print(f"[{_ts()}] Building spatial index...")
    index = connector.load_index()
    print(f"[{_ts()}] Index: {index.airport_count} airports across {len(index.countries_loaded)} countries")

    # Step 3: Run batch
    print(f"[{_ts()}] Starting batch enrichment for all sites...")
    if args.requery_nulls:
        print(f"[{_ts()}] [REQUERY NULLS] only sites with NULL/low HI-01 will be re-fetched")
    with session_scope() as session:
        result = enrich_batch(
            connector, session, run_id,
            site_ids=site_ids,
            country_codes=country_codes,
            requery_nulls=args.requery_nulls,
        )

    # Step 4: Report
    print(f"\n[{_ts()}] === BATCH COMPLETE ===")
    print(f"[{_ts()}] {result.summary_line()}")
    print(f"[{_ts()}] Run ID: {run_id}")

    print(f"\n--- Per-site results ---")
    for s in result.per_site:
        status_icon = {"ok": "✅", "error": "❌", "cached": "⏭️"}.get(s.status, "?")
        nearest = f"{s.nearest_airport_km:.1f} km" if s.nearest_airport_km is not None else "N/A"
        name = s.nearest_airport_name or "N/A"
        quality = s.quality or "N/A"
        err = f" | ERROR: {s.error}" if s.error else ""
        print(
            f"  {status_icon} {s.site_name[:40]:<40} | nearest: {nearest:>10} | "
            f"{name[:30]:<30} | quality: {quality:<6} | {s.elapsed_ms:>5} ms{err}"
        )

    # Summary stats
    ok_sites = [s for s in result.per_site if s.status == "ok"]
    if ok_sites:
        distances = [s.nearest_airport_km for s in ok_sites if s.nearest_airport_km is not None]
        if distances:
            print(f"\n--- Distance statistics ---")
            print(f"  Min:    {min(distances):.1f} km")
            print(f"  Max:    {max(distances):.1f} km")
            print(f"  Mean:   {sum(distances) / len(distances):.1f} km")
            print(f"  Median: {sorted(distances)[len(distances) // 2]:.1f} km")

    connector.close()
    print(f"\n[{_ts()}] Done.")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


if __name__ == "__main__":
    main()
