#!/usr/bin/env python
# man_hours: 2.0
"""EP-02 road density re-query for sites with zero density (likely LL-017 false negatives).

The original EmergencyPlanCheck used OverpassClient *without* retry_on_error,
so disconnects produced {'density_km_per_km2': 0, 'total_road_km': 0} —
indistinguishable from a genuine empty result. This script re-queries those
sites with full retry/backoff logic and updates only EP-02 columns.

Populates (on site_emergency_planning):
    road_density_km_per_km2, total_road_km, has_motorway_access,
    ep02_quality, ep02_comment

Usage:
    python scripts/run_ep02_road_density_requery.py [--dry-run] [--limit N]
                                                     [--batch-size N]

Consent: Requires explicit user go-ahead (Overpass API, free, ~310 queries).
"""

from __future__ import annotations

import argparse
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import httpx

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm.client import OverpassClient
from atoms_vs_ashes.db.models import DataSource, Site, SiteEmergencyPlanning
from atoms_vs_ashes.logging import get_logger
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import Session, sessionmaker

log = get_logger(__name__)

EPZ_RADIUS_M = 25_000
INTER_QUERY_DELAY_S = 30.0
JITTER_S = 8.0

SOURCE_NAME = "osm_ep02_road_requery"
SOURCE_URL = "https://overpass-api.de/api/interpreter"
SOURCE_DESC = (
    "OpenStreetMap Overpass API — EP-02 road density re-query for sites "
    "affected by LL-017 silent false negatives (zero-density disconnect artefacts)."
)

EP02_REQUERY_MARKER = "Source: OSM Overpass [EP-02 requery]"

_MAX_RETRIES = 5
_RETRY_MIN_WAIT_S = 60.0
_RETRY_MAX_WAIT_S = 300.0
_RETRYABLE_STATUSES = {429, 504, 408, 0}


def _is_retryable(client: OverpassClient) -> bool:
    return client._last_http_status in _RETRYABLE_STATUSES


def _wait_for_overpass_slot(client: OverpassClient, min_wait_s: float) -> None:
    """Wait at least *min_wait_s*, then poll /status for a free slot.

    Unlike the previous version, this always enforces the minimum wait even
    when /status reports 'slots available'. The Overpass /status endpoint
    reports per-IP slot availability, but 504s during global server overload
    occur independently of slot state.
    """
    log.info("ep02_backoff_sleep", wait_s=round(min_wait_s))
    time.sleep(min_wait_s)

    status_url = client._url.replace("/interpreter", "/status")
    try:
        resp = httpx.get(status_url, timeout=10)
        if resp.status_code == 200:
            body = resp.text
            if "slots available now" in body:
                log.info("ep02_slot_available")
                return
            for line in body.splitlines():
                if "Slot available after" in line and "in" in line:
                    parts = line.split("in ")
                    if parts:
                        try:
                            secs = int(parts[-1].replace(" seconds.", "").strip())
                            if secs > 0:
                                log.info("ep02_wait_slot", wait_s=secs)
                                time.sleep(secs + 2)
                        except (ValueError, IndexError):
                            pass
                    return
    except Exception:
        pass
    time.sleep(10)


def _fetch_road_density_with_retry(
    client: OverpassClient,
    lat: float,
    lon: float,
    radius_m: float,
) -> dict | None:
    """Call fetch_road_density with exponential backoff on transient errors.

    Returns None if all retries are exhausted (caller should skip the site
    rather than persisting a false-negative zero).
    """
    for attempt in range(_MAX_RETRIES + 1):
        result = client.fetch_road_density(lat, lon, radius_m)
        if not _is_retryable(client):
            jitter = random.uniform(-JITTER_S, JITTER_S)
            time.sleep(max(2.0, INTER_QUERY_DELAY_S + jitter))
            return result
        if attempt < _MAX_RETRIES:
            wait = min(_RETRY_MIN_WAIT_S * (2 ** attempt), _RETRY_MAX_WAIT_S)
            log.warning(
                "ep02_query_retry",
                attempt=attempt + 1,
                wait_s=round(wait),
                status=client._last_http_status,
            )
            _wait_for_overpass_slot(client, min_wait_s=wait)
            time.sleep(random.uniform(5, 15))
        else:
            log.error("ep02_query_exhausted", status=client._last_http_status, lat=lat, lon=lon)
    return None


def _ensure_data_source(session: Session) -> None:
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if not existing:
        session.add(DataSource(
            name=SOURCE_NAME,
            url=SOURCE_URL,
            description=SOURCE_DESC,
            last_fetched=datetime.now(timezone.utc),
        ))
        session.flush()


def _find_zero_density_sites(session: Session) -> list[tuple]:
    """Return (site_id, name, country_code, latitude, longitude) for sites with zero road density."""
    rows = session.execute(sa_text("""
        SELECT s.site_id, s.name, s.country_code, s.latitude, s.longitude
        FROM sites s
        JOIN site_emergency_planning ep ON s.site_id = ep.site_id
        WHERE ep.road_density_km_per_km2 = 0
          AND (ep.total_road_km IS NULL OR ep.total_road_km = 0)
        ORDER BY s.country_code, s.name
    """)).fetchall()
    return rows


def _persist_road_density(
    session: Session,
    site_id: object,
    road_data: dict,
    run_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    density = road_data.get("density_km_per_km2", 0)
    total = road_data.get("total_road_km", 0)
    by_class = road_data.get("by_class_km", {})
    has_motorway = (by_class.get("motorway", 0) + by_class.get("trunk", 0)) > 0

    comment = (
        f"Road density {density:.3f} km/km², "
        f"{total:.1f} km total, "
        f"motorway/trunk: {'yes' if has_motorway else 'no'}. "
        f"{EP02_REQUERY_MARKER}"
    )

    session.execute(sa_text("""
        UPDATE site_emergency_planning
        SET road_density_km_per_km2 = :density,
            total_road_km = :total_road_km,
            has_motorway_access = :has_motorway,
            ep02_quality = :quality,
            ep02_comment = :comment,
            fetched_at = :now,
            run_id = :run_id
        WHERE site_id = CAST(:sid AS uuid)
    """), {
        "sid": str(site_id),
        "density": density,
        "total_road_km": total,
        "has_motorway": has_motorway,
        "quality": "medium",
        "comment": comment[:1000],
        "now": now,
        "run_id": run_id,
    })


def run_batch(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    batch_size: int = 20,
    overpass_url: str | None = None,
) -> None:
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    client = OverpassClient(settings, overpass_url=overpass_url)

    run_id = f"ep02_requery_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info("ep02_requery_start", run_id=run_id, dry_run=dry_run)

    sites = _find_zero_density_sites(session)
    if limit:
        sites = sites[:limit]

    if not sites:
        print("No sites with zero road density found.", file=sys.stderr)
        session.close()
        client.close()
        return

    if not dry_run:
        _ensure_data_source(session)
        session.commit()

    ok_count = err_count = skip_count = 0
    t_start = time.monotonic()

    print(
        f"\nEP-02 road density re-query — {len(sites)} sites, run_id={run_id}"
        + (" [DRY RUN]" if dry_run else ""),
        flush=True,
    )
    print(f"{'#':>4}  {'Country':>7}  {'Site':<40}  {'Density':>10}  {'Total km':>10}  {'Motorway':>10}")
    print("-" * 95)

    for i, row in enumerate(sites):
        site_id, name, cc, lat, lon = row
        lat, lon = float(lat), float(lon)
        site_name = (name or "")[:40]

        if dry_run:
            print(
                f"{i+1:>4}  {cc or '??':>7}  {site_name:<40}  {'dry-run':>10}  {'dry-run':>10}  {'dry-run':>10}",
                flush=True,
            )
            ok_count += 1
            continue

        try:
            road_data = _fetch_road_density_with_retry(client, lat, lon, EPZ_RADIUS_M)

            if road_data is None:
                skip_count += 1
                log.warning(
                    "ep02_skip_exhausted",
                    site_id=str(site_id), name=name, lat=lat, lon=lon,
                )
                print(
                    f"{i+1:>4}  {cc or '??':>7}  {site_name:<40}  {'SKIP':>10}  {'SKIP':>10}  {'SKIP':>10}",
                    flush=True,
                )
                continue

            density = road_data.get("density_km_per_km2", 0)
            total_km = road_data.get("total_road_km", 0)
            by_class = road_data.get("by_class_km", {})
            has_motorway = (by_class.get("motorway", 0) + by_class.get("trunk", 0)) > 0

            _persist_road_density(session, site_id, road_data, run_id)
            session.commit()
            ok_count += 1

            density_label = f"{density:.3f}"
            total_label = f"{total_km:.1f}"
            mway_label = "yes" if has_motorway else "no"

            print(
                f"{i+1:>4}  {cc or '??':>7}  {site_name:<40}  {density_label:>10}  {total_label:>10}  {mway_label:>10}",
                flush=True,
            )

        except Exception as exc:
            session.rollback()
            err_count += 1
            log.error("ep02_site_error", site_id=str(site_id), error=str(exc))
            print(
                f"{i+1:>4}  {cc or '??':>7}  {site_name:<40}  {'ERR':>10}  {'ERR':>10}  {'ERR':>10}",
                flush=True,
            )

        if (i + 1) % batch_size == 0:
            elapsed = time.monotonic() - t_start
            remaining = (len(sites) - i - 1) * (elapsed / (i + 1))
            print(
                f"\n  --- Progress: {i+1}/{len(sites)} | "
                f"elapsed {elapsed/60:.1f} min | ETA ~{remaining/60:.1f} min | "
                f"ok={ok_count} err={err_count} skipped={skip_count}\n",
                flush=True,
            )

    elapsed_total = time.monotonic() - t_start
    print(f"\n{'='*95}")
    print(f"EP-02 re-query complete in {elapsed_total/60:.1f} min | run_id={run_id}")
    print(f"  Processed: {ok_count}  |  Errors: {err_count}  |  Skipped (retry exhaustion): {skip_count}")
    print(f"{'='*95}", flush=True)

    log.info(
        "ep02_requery_done", run_id=run_id,
        total_sites=len(sites), ok=ok_count, errors=err_count,
        skipped=skip_count,
        elapsed_s=round(elapsed_total, 1),
    )

    session.close()
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EP-02: Re-query road density for sites with zero density (LL-017 fix)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List affected sites but do NOT call Overpass or write any rows.",
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Process only the first N sites (for validation batches).",
    )
    parser.add_argument(
        "--batch-size", type=int, default=20, metavar="N",
        help="Print progress summary every N sites (default: 20).",
    )
    parser.add_argument(
        "--overpass-url", default=None,
        help="Overpass API URL (default: https://overpass-api.de/api/interpreter). "
             "Mirrors: https://overpass.kumi.systems/api/interpreter",
    )
    args = parser.parse_args()

    run_batch(
        dry_run=args.dry_run,
        limit=args.limit,
        batch_size=args.batch_size,
        overpass_url=args.overpass_url,
    )


if __name__ == "__main__":
    main()
