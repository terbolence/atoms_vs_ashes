#!/usr/bin/env python
# man_hours: 2.0
"""FIX-06: NS-01 cooling source re-enrichment.

Re-runs the three NS-01 cooling connectors in the correct order
(per LL-009 execution order):

  1. HydroRIVERS  — nearest-river match with prefer-higher-Strahler logic
  2. GloFAS       — supplementary reanalysis discharge (no longer overwrites)
  3. WRI Aqueduct — water stress from GDB (fixes 100% null issue)

All three connectors use locally cached data (shapefiles, NetCDF, GDB),
so **no live API calls** are made.

Usage:
    python scripts/run_fix06_ns01_cooling.py --dry-run
    python scripts/run_fix06_ns01_cooling.py --dry-run --limit 5
    python scripts/run_fix06_ns01_cooling.py --requery-nulls
    python scripts/run_fix06_ns01_cooling.py --country RO,BG

Consent: Requires explicit user go-ahead for writes (no external APIs).
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def _snapshot_before(session: Session, site_id: uuid.UUID) -> dict:
    """Capture pre-run NS-01 values for before/after comparison."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return {}
    return {
        "cooling_source_type": row.cooling_source_type,
        "cooling_source_name": row.cooling_source_name,
        "cooling_distance_km": float(row.cooling_distance_km) if row.cooling_distance_km else None,
        "cooling_flow_m3s": float(row.cooling_flow_m3s) if row.cooling_flow_m3s else None,
        "ns01_source": row.ns01_source,
        "water_stress_label": row.water_stress_label,
        "water_stress_score": float(row.water_stress_score) if row.water_stress_score else None,
    }


def _needs_requery(session: Session, site_id: uuid.UUID) -> bool:
    """True if site has stale or broken NS-01 data that should be re-queried.

    Matches sites where:
    - GloFAS overwrote cooling_flow_m3s (ns01_source == 'glofas_discharge')
    - WRI Aqueduct returned 'No Data'
    - cooling_flow_m3s is NULL
    """
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return True
    if row.ns01_source == "glofas_discharge":
        return True
    if row.water_stress_label == "No Data" or row.water_stress_label is None:
        return True
    if row.cooling_flow_m3s is None:
        return True
    return False


def _clear_ns01_for_rerun(session: Session, site_id: uuid.UUID) -> None:
    """Reset NS-01 columns so connectors write fresh values."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return
    row.cooling_source_type = None
    row.cooling_source_name = None
    row.cooling_distance_km = None
    row.cooling_flow_m3s = None
    row.ns01_source = None
    row.ns01_quality = None
    row.ns01_comment = None
    row.water_stress_score = None
    row.water_stress_label = None


def run_batch(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    country_codes: list[str] | None = None,
    requery_nulls: bool = False,
) -> None:
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    run_id = f"fix06_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info("fix06_batch_start", run_id=run_id, dry_run=dry_run, requery_nulls=requery_nulls)

    # Build site list
    query = session.query(Site)
    if country_codes:
        query = query.filter(Site.country_code.in_(country_codes))
    sites = query.order_by(Site.country_code, Site.name).all()

    if requery_nulls:
        sites = [s for s in sites if _needs_requery(session, s.site_id)]

    if limit:
        sites = sites[:limit]

    if not sites:
        print("No sites to process.", file=sys.stderr)
        return

    print(
        f"\nFIX-06 NS-01 cooling re-enrichment — {len(sites)} sites, run_id={run_id}"
        + (" [DRY RUN]" if dry_run else ""),
        flush=True,
    )

    if dry_run:
        print(f"\n{'#':>4}  {'CC':>3}  {'Site':<40}  {'ns01_source':<16}  {'flow_m3s':>10}  {'stress':<16}  {'requery'}")
        print("-" * 110)
        for i, site in enumerate(sites):
            row = session.get(SiteInfrastructureV2, site.site_id)
            ns01_src = (row.ns01_source or "—") if row else "—"
            flow = f"{float(row.cooling_flow_m3s):.1f}" if row and row.cooling_flow_m3s else "NULL"
            stress = (row.water_stress_label or "NULL") if row else "NULL"
            needs = _needs_requery(session, site.site_id)
            print(
                f"{i+1:>4}  {site.country_code or '??':>3}  {(site.name or '')[:40]:<40}  "
                f"{ns01_src:<16}  {flow:>10}  {stress:<16}  {'YES' if needs else 'no'}",
                flush=True,
            )
        print(f"\nDry run complete. {len(sites)} sites would be processed.")
        session.close()
        return

    # ---- Initialize connectors (all local, no API calls) ----
    from atoms_vs_ashes.connectors.hydrorivers.client import HydroRiversConnector
    from atoms_vs_ashes.connectors.glofas_discharge.client import GlofasDischargeConnector
    from atoms_vs_ashes.connectors.wri_aqueduct.client import WriAqueductConnector

    from atoms_vs_ashes.connectors.hydrorivers.batch import enrich_site as hr_enrich
    from atoms_vs_ashes.connectors.glofas_discharge.batch import enrich_site as gf_enrich
    from atoms_vs_ashes.connectors.wri_aqueduct.batch import enrich_site as aq_enrich

    hr_conn = HydroRiversConnector(settings)
    gf_conn = GlofasDischargeConnector(settings)
    aq_conn = WriAqueductConnector(settings)

    print(f"\n{'#':>4}  {'CC':>3}  {'Site':<35}  {'river':<20}  {'flow_m3s':>10}  {'stress':<16}  {'status'}")
    print("-" * 115)

    ok = err = 0
    t_start = time.monotonic()
    snapshots: list[dict] = []

    for i, site in enumerate(sites):
        sid = site.site_id
        before = _snapshot_before(session, sid)

        # Reset NS-01 columns for clean re-enrichment
        _clear_ns01_for_rerun(session, sid)
        session.flush()

        site_ok = True
        try:
            # Step 1: HydroRIVERS
            hr_result = hr_enrich(hr_conn, sid, session, run_id)
            if hr_result.status == "error":
                log.warning("fix06_hydrorivers_error", site_id=str(sid), error=hr_result.error)

            # Step 2: GloFAS (supplementary — won't overwrite HydroRIVERS)
            gf_result = gf_enrich(gf_conn, sid, session, run_id)
            if gf_result.status == "error":
                log.warning("fix06_glofas_error", site_id=str(sid), error=gf_result.error)

            # Step 3: WRI Aqueduct
            aq_result = aq_enrich(aq_conn, sid, session, run_id)
            if aq_result.status == "error":
                log.warning("fix06_aqueduct_error", site_id=str(sid), error=aq_result.error)

            session.commit()
        except Exception as exc:
            session.rollback()
            site_ok = False
            log.error("fix06_site_error", site_id=str(sid), error=str(exc))

        after = _snapshot_before(session, sid)
        snapshots.append({
            "site_name": site.name,
            "country": site.country_code,
            "before": before,
            "after": after,
        })

        if site_ok:
            ok += 1
        else:
            err += 1

        river = (after.get("cooling_source_name") or "—")[:20]
        flow = f"{after['cooling_flow_m3s']:.1f}" if after.get("cooling_flow_m3s") else "NULL"
        stress = after.get("water_stress_label") or "NULL"
        status = "ok" if site_ok else "ERR"

        print(
            f"{i+1:>4}  {site.country_code or '??':>3}  {(site.name or '')[:35]:<35}  "
            f"{river:<20}  {flow:>10}  {stress:<16}  {status}",
            flush=True,
        )

        if (i + 1) % 25 == 0:
            elapsed = time.monotonic() - t_start
            remaining = (len(sites) - i - 1) * (elapsed / (i + 1))
            print(
                f"\n  --- Progress: {i+1}/{len(sites)} | elapsed {elapsed/60:.1f} min | "
                f"ETA ~{remaining/60:.1f} min | ok={ok} err={err}\n",
                flush=True,
            )

    elapsed_total = time.monotonic() - t_start
    print(f"\n{'='*115}")
    print(f"FIX-06 complete in {elapsed_total:.1f}s | run_id={run_id}")
    print(f"  Processed: {ok} ok, {err} errors out of {len(sites)} sites")

    # Print before/after summary for changed sites
    changed = [s for s in snapshots if s["before"] != s["after"]]
    if changed:
        print(f"\n  Changed sites: {len(changed)}/{len(snapshots)}")
        print(f"  {'Site':<35}  {'Before flow':>12}  {'After flow':>12}  {'Before stress':<16}  {'After stress':<16}")
        print("  " + "-" * 100)
        for s in changed[:20]:
            b_flow = f"{s['before'].get('cooling_flow_m3s', 0):.1f}" if s["before"].get("cooling_flow_m3s") else "NULL"
            a_flow = f"{s['after'].get('cooling_flow_m3s', 0):.1f}" if s["after"].get("cooling_flow_m3s") else "NULL"
            b_stress = s["before"].get("water_stress_label") or "NULL"
            a_stress = s["after"].get("water_stress_label") or "NULL"
            print(f"  {(s['site_name'] or '')[:35]:<35}  {b_flow:>12}  {a_flow:>12}  {b_stress:<16}  {a_stress:<16}")
        if len(changed) > 20:
            print(f"  ... and {len(changed) - 20} more")

    print(f"{'='*115}", flush=True)

    hr_conn.close()
    gf_conn.close()
    aq_conn.close()
    session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-06: Re-enrich NS-01 cooling sources (HydroRIVERS → GloFAS → WRI Aqueduct)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List sites and current NS-01 values. No DB writes.",
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="Process only the first N sites (for testing).",
    )
    parser.add_argument(
        "--country", dest="countries", metavar="CC,...",
        help="Comma-separated ISO country codes (e.g. RO,BG). Default: all.",
    )
    parser.add_argument(
        "--requery-nulls", action="store_true",
        help="Only re-run sites with stale/broken NS-01 data.",
    )
    args = parser.parse_args()

    country_codes = (
        [c.strip().upper() for c in args.countries.split(",")]
        if args.countries else None
    )
    run_batch(
        dry_run=args.dry_run,
        limit=args.limit,
        country_codes=country_codes,
        requery_nulls=args.requery_nulls,
    )


if __name__ == "__main__":
    main()
