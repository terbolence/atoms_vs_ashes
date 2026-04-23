#!/usr/bin/env python3
# man_hours: 1.0
"""Fix 08: Fill transport gap columns (nearest_highway_km, nearest_rail_km,
nearest_waterway_km) via Overpass for sites where ANY of the three is NULL.

Uses the existing P11 transport enrichment stack (connectors/osm/batch.py,
parsers.py) but targets ONLY the NULL-column sites and enforces hardened
backoff (60 s minimum) to avoid the LL-017/LL-018 false-negative pattern.

Populates:
  site_infrastructure_v2: nearest_highway_km, nearest_rail_km,
                           nearest_waterway_km, heavy_haul_capable,
                           ns03_quality, ns03_comment, fetched_at, run_id

Usage:
    python scripts/run_fix08_transport_gaps.py [--dry-run] [--limit N]
                                               [--overpass-url URL]

Consent: Requires explicit user go-ahead (live API safety rule).
"""

from __future__ import annotations

import argparse
import random
import socket
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
from atoms_vs_ashes.connectors.osm.batch import _fetch_transport, _persist_result, _ensure_data_source
from atoms_vs_ashes.connectors.osm.client import OverpassClient, enable_raw_response_logging

enable_raw_response_logging(PROJECT_ROOT / "data" / "raw_responses" / "overpass")
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import Session, sessionmaker

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INTER_QUERY_DELAY_S = 35.0
JITTER_S = 8.0

_MAX_RETRIES = 5
_RETRY_MIN_WAIT_S = 60.0
_RETRY_MAX_WAIT_S = 300.0
# 406 = temporary IP ban from Overpass (occurs after repeated 429/504 storms).
# batch._query_with_retry only retries on 429; 406 slips through as empty
# results which are then persisted as NULL.  Must be caught at the fix08 level.
_RETRYABLE_STATUSES = {429, 504, 408, 0, 406}
# Longer minimum wait when the server has issued an IP ban (406).
_IP_BAN_WAIT_S = 600.0  # 10 minutes
# Wait time when a DNS/network error is detected (transient network blip).
_NETWORK_ERROR_WAIT_S = 120.0  # 2 minutes


def _is_dns_error(exc: BaseException) -> bool:
    """Return True if this exception is a DNS resolution or network-level failure."""
    if isinstance(exc, (socket.gaierror, OSError)):
        return True
    msg = str(exc).lower()
    return any(
        phrase in msg
        for phrase in (
            "nodename nor servname",
            "name or service not known",
            "temporary failure in name resolution",
            "network is unreachable",
            "connection refused",
            "errno 8",
        )
    )


# ---------------------------------------------------------------------------
# Rate-limiting helpers (same pattern as fix05 — always enforce full backoff)
# ---------------------------------------------------------------------------

def _wait_for_overpass_slot(client: OverpassClient, min_wait_s: float) -> None:
    """Wait at least *min_wait_s*, then poll /status for a free slot."""
    log.info("fix08_backoff_sleep", wait_s=round(min_wait_s))
    time.sleep(min_wait_s)

    status_url = client._url.replace("/interpreter", "/status")
    try:
        resp = httpx.get(status_url, timeout=10)
        if resp.status_code == 200:
            body = resp.text
            if "slots available now" in body:
                log.info("fix08_slot_available")
                return
            for line in body.splitlines():
                if "Slot available after" in line and "in" in line:
                    parts = line.split("in ")
                    if parts:
                        try:
                            secs = int(parts[-1].replace(" seconds.", "").strip())
                            if secs > 0:
                                log.info("fix08_wait_slot", wait_s=secs)
                                time.sleep(secs + 2)
                        except (ValueError, IndexError):
                            pass
                    return
    except Exception:
        pass
    time.sleep(10)


def _transport_with_retry(
    client: OverpassClient,
    lat: float,
    lon: float,
    country_code: str,
):
    """Run transport fetch with hardened exponential backoff.

    Returns a TransportResult on success, or None when all retries are
    exhausted (LL-017 guard — callers must NOT persist on None).

    406 handling (LL-018 extension):
    batch._query_with_retry only retries on 429; HTTP 406 (IP ban) slips
    through as empty results.  We detect 406 via client._last_http_status
    after _fetch_transport returns and apply an extended IP-ban cooldown.
    """
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = _fetch_transport(
                client, lat, lon,
                country_code=country_code,
                highway_radius_km=10.0,
                railway_radius_km=15.0,
                waterway_radius_km=10.0,
            )
            last_status = client._last_http_status

            if last_status not in _RETRYABLE_STATUSES:
                jitter = random.uniform(-JITTER_S, JITTER_S)
                time.sleep(max(2.0, INTER_QUERY_DELAY_S + jitter))
                return result

            # Retryable status detected (including 406 IP ban)
            if attempt < _MAX_RETRIES:
                if last_status == 406:
                    wait = _IP_BAN_WAIT_S
                    log.warning(
                        "fix08_ip_ban_detected",
                        attempt=attempt + 1,
                        wait_s=round(wait),
                        msg="HTTP 406 = IP ban from overpass-api.de. "
                            "Consider --overpass-url https://overpass.kumi.systems/api/interpreter",
                    )
                else:
                    wait = min(_RETRY_MIN_WAIT_S * (2 ** attempt), _RETRY_MAX_WAIT_S)
                    log.warning(
                        "fix08_query_retry",
                        attempt=attempt + 1,
                        wait_s=round(wait),
                        status=last_status,
                    )
                _wait_for_overpass_slot(client, min_wait_s=wait)
                time.sleep(random.uniform(5, 15))
            else:
                log.error(
                    "fix08_query_exhausted",
                    lat=lat, lon=lon, status=last_status,
                )
        except Exception as exc:
            if attempt < _MAX_RETRIES:
                if _is_dns_error(exc):
                    # Network-level failure (DNS blip, unreachable host).
                    # HTTPX reconnects automatically — just give the network 2 min.
                    wait = _NETWORK_ERROR_WAIT_S
                    log.warning(
                        "fix08_network_error_retry",
                        attempt=attempt + 1,
                        wait_s=round(wait),
                        error=str(exc),
                        msg="DNS/network failure — waiting 2 min for recovery",
                    )
                else:
                    wait = min(_RETRY_MIN_WAIT_S * (2 ** attempt), _RETRY_MAX_WAIT_S)
                    log.warning(
                        "fix08_exception_retry",
                        attempt=attempt + 1,
                        wait_s=round(wait),
                        error=str(exc),
                    )
                time.sleep(wait)
                time.sleep(random.uniform(5, 15))
            else:
                log.error("fix08_exception_exhausted", lat=lat, lon=lon, error=str(exc))
    return None


# ---------------------------------------------------------------------------
# Target-site selection
# ---------------------------------------------------------------------------

def _get_null_sites(session: Session) -> list[Site]:
    """Return sites where any transport column is NULL."""
    null_ids = session.execute(
        sa_text(
            """
            SELECT s.site_id
            FROM   sites s
            LEFT JOIN site_infrastructure_v2 iv ON iv.site_id = s.site_id
            WHERE  iv.nearest_highway_km IS NULL
               OR  iv.nearest_rail_km    IS NULL
               OR  iv.nearest_waterway_km IS NULL
            ORDER BY s.country_code, s.name
            """
        )
    ).scalars().all()

    if not null_ids:
        return []
    return (
        session.query(Site)
        .filter(Site.site_id.in_(null_ids))
        .order_by(Site.country_code, Site.name)
        .all()
    )


# ---------------------------------------------------------------------------
# Main batch
# ---------------------------------------------------------------------------

# How many consecutive outer-level 504 retries before pausing the entire batch.
_OVERLOAD_PAUSE_AFTER = 5
_OVERLOAD_PAUSE_S = 1800.0  # 30 minutes

# Mirror rotation: cycle to next mirror after this many consecutive 504 outer retries.
_MIRROR_ROTATE_AFTER = 3
_MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


def run_batch(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    overpass_url: str | None = None,
) -> int:
    """Returns number of sites that were exhausted (not persisted)."""
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    client = OverpassClient(settings, overpass_url=overpass_url)

    run_id = f"fix08_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info(
        "fix08_batch_start", run_id=run_id, dry_run=dry_run,
        overpass_url=client._url,
        overload_pause_after=_OVERLOAD_PAUSE_AFTER,
        overload_pause_s=_OVERLOAD_PAUSE_S,
    )

    target_sites = _get_null_sites(session)
    if limit is not None:
        target_sites = target_sites[:limit]

    total_target = len(target_sites)

    if not target_sites:
        print("[fix08] No transport-gap sites found — all columns populated.", flush=True)
        session.close()
        client.close()
        return 0

    if not dry_run:
        _ensure_data_source(session)
        session.commit()

    print(
        f"\nFIX-08 transport gaps — {total_target} sites with NULL columns, run_id={run_id}"
        + (" [DRY RUN]" if dry_run else ""),
        flush=True,
    )
    print(
        f"{'#':>4}  {'CC':>4}  {'Site':<40}  {'Hwy km':>8}  {'Rail km':>8}  {'WW km':>8}  {'Status'}"
    )
    print("-" * 100)

    ok_count = skip_count = err_count = exhausted_count = 0
    # Tracks consecutive outer-level 504 retry events (fix08_query_retry).
    # Reset to 0 on any success; rotates mirror at _MIRROR_ROTATE_AFTER,
    # pauses for 30 min at _OVERLOAD_PAUSE_AFTER.
    consecutive_overload = 0
    mirror_index = 0  # index into _MIRRORS; may be overridden by --overpass-url
    # Build the effective mirror list: if a specific URL was passed, prepend it.
    effective_mirrors = list(_MIRRORS)
    if overpass_url and overpass_url not in effective_mirrors:
        effective_mirrors.insert(0, overpass_url)
    elif overpass_url and overpass_url in effective_mirrors:
        mirror_index = effective_mirrors.index(overpass_url)
    t_start = time.monotonic()

    for i, site in enumerate(target_sites):
        lat = float(site.latitude)
        lon = float(site.longitude)
        cc = site.country_code or "??"
        site_name = (site.name or "")[:40]

        if dry_run:
            print(f"{i+1:>4}  {cc:>4}  {site_name:<40}  dry-run", flush=True)
            ok_count += 1
            continue

        # --- Sustained-overload guard ---
        # Snapshot the client status before the call; after the call, check if
        # the outer retry was triggered (status 504 on the last attempt).
        pre_status = client._last_http_status

        result = _transport_with_retry(client, lat, lon, cc)
        post_status = client._last_http_status

        # If the result is None OR the last HTTP status indicates a timeout,
        # we count it as an overload event.
        is_overload_event = (result is None and post_status == 504) or (
            result is not None and post_status == 504
        )

        if is_overload_event:
            consecutive_overload += 1
            log.warning(
                "fix08_overload_event",
                consecutive=consecutive_overload,
                rotate_threshold=_MIRROR_ROTATE_AFTER,
                pause_threshold=_OVERLOAD_PAUSE_AFTER,
            )
            # Rotate mirror after _MIRROR_ROTATE_AFTER consecutive 504s.
            if consecutive_overload % _MIRROR_ROTATE_AFTER == 0 and len(effective_mirrors) > 1:
                mirror_index = (mirror_index + 1) % len(effective_mirrors)
                new_url = effective_mirrors[mirror_index]
                client._url = new_url
                log.warning(
                    "fix08_mirror_rotate",
                    new_url=new_url,
                    consecutive=consecutive_overload,
                    msg="Switching Overpass mirror due to sustained 504s",
                )
                print(
                    f"\n  *** MIRROR ROTATE: switching to {new_url} after "
                    f"{consecutive_overload} consecutive 504s ***\n",
                    flush=True,
                )
        else:
            consecutive_overload = 0  # success or non-504 failure resets the streak

        if consecutive_overload >= _OVERLOAD_PAUSE_AFTER:
            log.warning(
                "fix08_sustained_overload_pause",
                consecutive=consecutive_overload,
                pause_s=round(_OVERLOAD_PAUSE_S),
                msg=f"Server consistently returning 504 — pausing {_OVERLOAD_PAUSE_S/60:.0f} min",
            )
            print(
                f"\n  *** SERVER OVERLOAD: {consecutive_overload} consecutive 504 retries. "
                f"Pausing {_OVERLOAD_PAUSE_S/60:.0f} min to let it recover... ***\n",
                flush=True,
            )
            time.sleep(_OVERLOAD_PAUSE_S)
            consecutive_overload = 0
            log.info("fix08_overload_pause_done", resuming_at=site_name)

        if result is None:
            exhausted_count += 1
            log.warning(
                "fix08_skip_exhausted",
                site_id=str(site.site_id),
                site_name=site.name,
                msg="All retries exhausted — skipping persistence (LL-017 guard)",
            )
            print(
                f"{i+1:>4}  {cc:>4}  {site_name:<40}  {'':>8}  {'':>8}  {'':>8}  EXHAUSTED",
                flush=True,
            )
            continue

        try:
            _persist_result(session, site.site_id, result, run_id, cc)
            session.commit()
            ok_count += 1

            hw = result.highway.nearest_highway_km
            rw = result.railway.nearest_rail_km
            ww = result.waterway.nearest_waterway_km
            hw_s = f"{hw:.1f}" if hw is not None else "None"
            rw_s = f"{rw:.1f}" if rw is not None else "None"
            ww_s = f"{ww:.1f}" if ww is not None else "None"
            print(
                f"{i+1:>4}  {cc:>4}  {site_name:<40}  {hw_s:>8}  {rw_s:>8}  {ww_s:>8}",
                flush=True,
            )
        except Exception as exc:
            session.rollback()
            err_count += 1
            log.error("fix08_persist_error", site_id=str(site.site_id), error=str(exc))
            print(
                f"{i+1:>4}  {cc:>4}  {site_name:<40}  {'':>8}  {'':>8}  {'':>8}  ERR: {exc}",
                flush=True,
            )

        if (i + 1) % 25 == 0:
            elapsed = time.monotonic() - t_start
            remaining = (total_target - i - 1) * (elapsed / (i + 1))
            log.info(
                "fix08_progress",
                completed=i + 1, total=total_target,
                ok=ok_count, exhausted=exhausted_count, errors=err_count,
                consecutive_overload=consecutive_overload,
                elapsed_s=round(elapsed, 1),
                eta_min=round(remaining / 60, 1),
            )
            print(
                f"\n  --- {i+1}/{total_target} | {elapsed/60:.1f} min elapsed | "
                f"ETA ~{remaining/60:.1f} min | ok={ok_count} exhausted={exhausted_count} "
                f"err={err_count} overload_streak={consecutive_overload}\n",
                flush=True,
            )

    elapsed_total = time.monotonic() - t_start
    print(f"\n{'='*100}")
    print(f"FIX-08 pass complete in {elapsed_total/60:.1f} min | run_id={run_id}")
    print(f"  OK:        {ok_count}")
    print(f"  Exhausted: {exhausted_count}")
    print(f"  Errors:    {err_count}")
    print(f"{'='*100}", flush=True)

    log.info(
        "fix08_batch_done", run_id=run_id,
        total=total_target, ok=ok_count,
        exhausted=exhausted_count, errors=err_count,
        elapsed_s=round(elapsed_total, 1),
    )

    session.close()
    client.close()
    return exhausted_count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-08: Fill transport gap columns via Overpass."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Connect to DB but do NOT call Overpass or write any rows.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max sites to process (for validation batches).",
    )
    parser.add_argument(
        "--overpass-url", default=None,
        help="Overpass API URL. Mirrors: https://overpass.kumi.systems/api/interpreter",
    )
    args = parser.parse_args()

    run_batch(
        dry_run=args.dry_run,
        limit=args.limit,
        overpass_url=args.overpass_url,
    )


if __name__ == "__main__":
    main()
