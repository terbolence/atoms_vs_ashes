"""Run S-18 EFSM20 seismogenic faults enrichment.

Standalone script — bypasses the connectors barrel so rasterio/GDAL are never
imported (avoids Google-Drive GDAL filesystem scan hang).

Usage:
    .venv/bin/python scripts/run_efsm20_faults.py [OPTIONS]

Options:
    --run-id RUN_ID       Explicit run ID (auto-generated if omitted)
    --download            Download EFSM20 data from seismofaults.eu first
    --force-download      Re-download even if cached data exists
    --dry-run             Load data + run one sample query; do not write to DB
    --country CODE        Restrict to sites in this country (repeatable)
    --site-id UUID        Restrict to specific sites (repeatable)
    --all                 Enrich all sites (default when no filter given)
    --db-profile PROFILE  api (default) or llm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — standalone execution support
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

# Load env before any project imports
from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

# ---------------------------------------------------------------------------
# Direct imports — avoids barrel (connectors/__init__.py → rasterio hang)
# ---------------------------------------------------------------------------
from atoms_vs_ashes.connectors.efsm20_faults.client import Efsm20FaultsConnector
from atoms_vs_ashes.connectors.efsm20_faults.batch import enrich_batch
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.logging import configure_logging, new_run_id


_DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
}


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="S-18 EFSM20 seismogenic faults enrichment"
    )
    p.add_argument("--run-id", default=None)
    p.add_argument("--download", action="store_true",
                   help="Download EFSM20 data before enriching")
    p.add_argument("--force-download", action="store_true",
                   help="Force re-download even if cached data exists")
    p.add_argument("--dry-run", action="store_true",
                   help="Load index + sample query; do not write to DB")
    p.add_argument("--country", action="append", dest="country_codes",
                   metavar="CODE", help="Country ISO-2 code (repeatable)")
    p.add_argument("--site-id", action="append", dest="site_ids",
                   metavar="UUID", help="Site UUID (repeatable)")
    p.add_argument("--all", action="store_true", dest="enrich_all",
                   help="Enrich all sites")
    p.add_argument("--db-profile", choices=["api", "llm"], default="api")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    run_id = args.run_id or new_run_id()
    configure_logging(verbose=True, run_id=run_id)

    # Override DB name based on profile
    os.environ["POSTGRES_DB"] = _DB_PROFILES[args.db_profile]

    settings = Settings()
    print(f"[{_ts()}] === S-18 EFSM20 Fault Enrichment ===", flush=True)
    print(f"[{_ts()}] Run ID:     {run_id}", flush=True)
    print(f"[{_ts()}] DB profile: {args.db_profile} → {_DB_PROFILES[args.db_profile]}", flush=True)

    connector = Efsm20FaultsConnector(settings)

    # ------------------------------------------------------------------
    # Download phase
    # ------------------------------------------------------------------
    if args.download or args.force_download:
        print(f"[{_ts()}] Downloading EFSM20 data...", flush=True)
        files = connector.download(force=args.force_download)
        print(f"[{_ts()}] Download complete: {len(files)} file(s)", flush=True)
        for f in files:
            size_mb = Path(f).stat().st_size / 1024 / 1024 if Path(f).exists() else 0
            print(f"[{_ts()}]   {f}  ({size_mb:.1f} MB)", flush=True)
    elif not connector.data_exists():
        print(
            f"[{_ts()}] ERROR: EFSM20 data not found at {connector.data_dir}\n"
            f"[{_ts()}]        Re-run with --download to fetch from seismofaults.eu",
            flush=True,
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Dry run
    # ------------------------------------------------------------------
    if args.dry_run:
        print(f"[{_ts()}] Dry run — loading spatial index...", flush=True)
        ok = connector.health_check()
        print(f"[{_ts()}] Health check: {'OK' if ok else 'FAILED'}", flush=True)
        if ok:
            # Sample query: Vrancea seismic zone (Romania)
            result = connector.fetch(lat=45.70, lon=26.50)
            print(f"[{_ts()}] Sample fetch (45.70°N, 26.50°E — Vrancea, RO):", flush=True)
            print(json.dumps(result.to_dict(), indent=2, default=str), flush=True)
        connector.close()
        return

    # ------------------------------------------------------------------
    # Batch enrichment
    # ------------------------------------------------------------------
    init_engine(settings)

    site_ids: list[uuid.UUID] | None = None
    if args.site_ids:
        site_ids = [uuid.UUID(s) for s in args.site_ids]

    country_codes: list[str] | None = args.country_codes or None

    if not (args.enrich_all or site_ids or country_codes):
        print(
            f"[{_ts()}] ERROR: Specify --all, --site-id, or --country", flush=True
        )
        sys.exit(1)

    print(f"[{_ts()}] Loading EFSM20 spatial index...", flush=True)

    with session_scope() as session:
        result = enrich_batch(
            connector,
            session,
            run_id,
            site_ids=site_ids,
            country_codes=country_codes,
        )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print(f"\n[{_ts()}] === BATCH COMPLETE ===", flush=True)
    print(f"[{_ts()}] {result.summary_line()}", flush=True)
    print(f"[{_ts()}] Run ID: {run_id}", flush=True)

    print(f"\n--- Per-site results ---", flush=True)
    for s in result.per_site:
        icon = {"ok": "✓", "error": "✗", "cached": "⏭"}.get(s.status, "?")
        nearest = (
            f"{s.nearest_fault_km:.1f} km"
            if s.nearest_fault_km is not None
            else "N/A"
        )
        within = f"within_8km={'YES' if s.capable_within_8km else 'no'}" if s.capable_within_8km is not None else ""
        err = f" | ERROR: {s.error}" if s.error else ""
        print(
            f"  {icon} {s.site_name[:45]:<45} | {nearest:>9} | {within:<17} | {s.elapsed_ms:>5} ms{err}",
            flush=True,
        )

    ok_sites = [s for s in result.per_site if s.status == "ok" and s.nearest_fault_km is not None]
    if ok_sites:
        distances = [s.nearest_fault_km for s in ok_sites]
        print(f"\n--- Distance statistics ({len(distances)} sites) ---", flush=True)
        print(f"  Min:    {min(distances):.1f} km", flush=True)
        print(f"  Max:    {max(distances):.1f} km", flush=True)
        print(f"  Mean:   {sum(distances)/len(distances):.1f} km", flush=True)
        print(f"  Median: {sorted(distances)[len(distances)//2]:.1f} km", flush=True)
        within_8 = sum(1 for s in result.per_site if s.capable_within_8km)
        print(f"  Sites with capable fault within 8 km: {within_8}", flush=True)

    connector.close()
    print(f"\n[{_ts()}] Done.", flush=True)


if __name__ == "__main__":
    main()
