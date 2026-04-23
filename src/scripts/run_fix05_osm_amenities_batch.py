#!/usr/bin/env python
# man_hours: 2.0
"""FIX-05: OSM EP-04 amenities batch re-enrichment.

Re-queries sites where hospital_count_epz is NULL — these are the ~310 sites
that received silent false-negative empty results from Overpass API disconnects
(LL-017). The fetch_amenities query and persistence logic are identical to the
EP-01 composite check (emergency_plan.py), but this script runs only the
amenity sub-query and persists only EP-04 columns.

Populates:
  site_emergency_planning: hospital_count_epz, prison_count_epz,
                           care_home_count_epz, ep04_quality, ep04_comment

Usage:
    python scripts/run_fix05_osm_amenities_batch.py [--dry-run] [--country CC,...]
                                                     [--no-skip-populated]
                                                     [--limit N]

Consent: Requires explicit user go-ahead (live API safety rule).
"""

from __future__ import annotations

import argparse
import random
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

import httpx

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm.client import OverpassClient
from atoms_vs_ashes.connectors.osm.models import OsmElement
from atoms_vs_ashes.db.models import DataSource, Site
from atoms_vs_ashes.logging import get_logger
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import Session, sessionmaker

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EPZ_RADIUS_M = 25_000.0
INTER_QUERY_DELAY_S = 30.0
JITTER_S = 8.0

SOURCE_NAME = "osm_amenities_fix05"
SOURCE_URL = "https://overpass-api.de/api/interpreter"
SOURCE_DESC = (
    "OpenStreetMap Overpass API — FIX-05 EP-04 amenities batch: hospitals, prisons, "
    "care homes, clinics within 25 km EPZ."
)

SPECIAL_POP_AMENITIES = ["hospital", "prison", "nursing_home", "clinic"]
EP04_COMMENT_MARKER = "Source: OSM Overpass [FIX-05 amenities]"

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_amenities(elements: list[OsmElement]) -> dict:
    """Aggregate amenity elements into EP-04 DB-ready fields."""
    counts: dict[str, int] = {}
    for el in elements:
        atype = el.tags.get("amenity", "other")
        counts[atype] = counts.get(atype, 0) + 1

    hospital_count = counts.get("hospital", 0) + counts.get("clinic", 0)
    prison_count = counts.get("prison", 0)
    care_home_count = counts.get("nursing_home", 0)
    total = len(elements)

    comment = (
        f"{hospital_count} hospital/clinic, "
        f"{prison_count} prison, "
        f"{care_home_count} care home within EPZ "
        f"(total {total} facilities). "
        f"{EP04_COMMENT_MARKER}"
    )

    quality = "medium"
    if total == 0:
        quality = "not_found"

    return {
        "hospital_count_epz": hospital_count,
        "prison_count_epz": prison_count,
        "care_home_count_epz": care_home_count,
        "quality": quality,
        "comment": comment[:1000],
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

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


def _needs_requery(
    session: Session, site_id: uuid.UUID, *, requery_zeros: bool = False,
) -> bool:
    """True if site needs an amenity query.

    Always true when hospital_count_epz is NULL.  When *requery_zeros* is set,
    also true for sites with all-zero counts that have the FIX-05 marker —
    these are likely false negatives from exhausted retries (LL-022).
    """
    row = session.execute(
        sa_text("""SELECT hospital_count_epz, prison_count_epz,
                          care_home_count_epz, ep04_comment
                   FROM site_emergency_planning
                   WHERE site_id = CAST(:sid AS uuid)"""),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return True
    if row["hospital_count_epz"] is None:
        return True
    if requery_zeros:
        comment = row.get("ep04_comment") or ""
        if EP04_COMMENT_MARKER in comment:
            total = (
                (row["hospital_count_epz"] or 0)
                + (row["prison_count_epz"] or 0)
                + (row["care_home_count_epz"] or 0)
            )
            if total == 0:
                return True
    return False


def _is_enriched(session: Session, site_id: uuid.UUID) -> bool:
    """True if site already has FIX-05 marker in ep04_comment."""
    row = session.execute(
        sa_text("""SELECT ep04_comment
                   FROM site_emergency_planning
                   WHERE site_id = CAST(:sid AS uuid)"""),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    return EP04_COMMENT_MARKER in (row.get("ep04_comment") or "")


def _persist_amenities(
    session: Session, site_id: uuid.UUID, data: dict, run_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    session.execute(sa_text("""
        INSERT INTO site_emergency_planning
            (site_id, hospital_count_epz, prison_count_epz, care_home_count_epz,
             ep04_quality, ep04_comment, fetched_at, run_id)
        VALUES
            (CAST(:sid AS uuid), :hospital_count_epz, :prison_count_epz,
             :care_home_count_epz, :ep04_quality, :ep04_comment, :now, :run_id)
        ON CONFLICT (site_id) DO UPDATE SET
            hospital_count_epz  = EXCLUDED.hospital_count_epz,
            prison_count_epz    = EXCLUDED.prison_count_epz,
            care_home_count_epz = EXCLUDED.care_home_count_epz,
            ep04_quality        = EXCLUDED.ep04_quality,
            ep04_comment        = EXCLUDED.ep04_comment,
            fetched_at          = EXCLUDED.fetched_at,
            run_id              = EXCLUDED.run_id
    """), {
        "sid": str(site_id),
        "hospital_count_epz": data["hospital_count_epz"],
        "prison_count_epz": data["prison_count_epz"],
        "care_home_count_epz": data["care_home_count_epz"],
        "ep04_quality": data["quality"],
        "ep04_comment": data["comment"],
        "now": now,
        "run_id": run_id,
    })


# ---------------------------------------------------------------------------
# Rate-limiting and retry helpers
# ---------------------------------------------------------------------------

_MAX_RETRIES = 5
_RETRY_MIN_WAIT_S = 60.0
_RETRY_MAX_WAIT_S = 300.0
_RETRYABLE_STATUSES = {429, 504, 408, 0}


def _is_retryable(client: OverpassClient) -> bool:
    return client._last_http_status in _RETRYABLE_STATUSES


def _wait_for_overpass_slot(client: OverpassClient, min_wait_s: float) -> None:
    """Wait at least *min_wait_s*, then poll /status for a free slot.

    Always enforces the minimum wait even when /status reports 'slots
    available'. Overpass 504s during global server overload occur
    independently of per-IP slot state.
    """
    log.info("fix05_backoff_sleep", wait_s=round(min_wait_s))
    time.sleep(min_wait_s)

    status_url = client._url.replace("/interpreter", "/status")
    try:
        resp = httpx.get(status_url, timeout=10)
        if resp.status_code == 200:
            body = resp.text
            if "slots available now" in body:
                log.info("fix05_slot_available")
                return
            for line in body.splitlines():
                if "Slot available after" in line and "in" in line:
                    parts = line.split("in ")
                    if parts:
                        try:
                            secs = int(parts[-1].replace(" seconds.", "").strip())
                            if secs > 0:
                                log.info("fix05_wait_slot", wait_s=secs)
                                time.sleep(secs + 2)
                        except (ValueError, IndexError):
                            pass
                    return
    except Exception:
        pass
    time.sleep(10)


def _query_with_retry(
    client: OverpassClient, lat: float, lon: float,
) -> list[OsmElement] | None:
    """Call fetch_amenities with exponential backoff on transient errors.

    Retries on 429, 504, timeouts (408), and disconnects (status 0).
    Always waits the full backoff period before retrying — slot polling
    is supplementary, not a substitute for the wait.

    Returns None (not []) when all retries are exhausted — callers must
    distinguish "API confirmed zero amenities" from "API never responded"
    (LL-017, LL-022).
    """
    elements: list[OsmElement] = []
    for attempt in range(_MAX_RETRIES + 1):
        elements = client.fetch_amenities(
            lat, lon, EPZ_RADIUS_M, SPECIAL_POP_AMENITIES,
        )
        if not _is_retryable(client):
            jitter = random.uniform(-JITTER_S, JITTER_S)
            time.sleep(max(2.0, INTER_QUERY_DELAY_S + jitter))
            return elements
        if attempt < _MAX_RETRIES:
            wait = min(_RETRY_MIN_WAIT_S * (2 ** attempt), _RETRY_MAX_WAIT_S)
            log.warning(
                "fix05_query_retry",
                attempt=attempt + 1,
                wait_s=round(wait),
                status=client._last_http_status,
            )
            _wait_for_overpass_slot(client, min_wait_s=wait)
            time.sleep(random.uniform(5, 15))
        else:
            log.error("fix05_query_exhausted", status=client._last_http_status, lat=lat, lon=lon)
    return None


# ---------------------------------------------------------------------------
# Plausibility guard (LL-022)
# ---------------------------------------------------------------------------

def _check_plausibility(
    site: Site, data: dict,
) -> str | None:
    """Return a warning message if the result looks implausible, else None."""
    total = (
        data["hospital_count_epz"]
        + data["prison_count_epz"]
        + data["care_home_count_epz"]
    )
    capacity = getattr(site, "installed_capacity_mw", None)
    if total == 0 and capacity is not None and float(capacity) > 50:
        return (
            f"Zero amenities within 25 km EPZ for a {capacity} MW plant — "
            f"may indicate a silent API failure (LL-022)"
        )
    return None


# ---------------------------------------------------------------------------
# Main batch loop
# ---------------------------------------------------------------------------

def run_batch(
    *,
    dry_run: bool = False,
    country_codes: list[str] | None = None,
    skip_populated: bool = True,
    requery_zeros: bool = False,
    limit: int | None = None,
    overpass_url: str | None = None,
) -> int:
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    client = OverpassClient(settings, overpass_url=overpass_url)

    run_id = f"fix05_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info("fix05_batch_start", run_id=run_id, dry_run=dry_run, requery_zeros=requery_zeros,
             overpass_url=client._url)

    query = session.query(Site)
    if country_codes:
        query = query.filter(Site.country_code.in_(country_codes))
    sites = query.order_by(Site.country_code, Site.name).all()

    if not sites:
        print("No sites found.", file=sys.stderr)
        return 0

    if not dry_run:
        _ensure_data_source(session)
        session.commit()

    ok_count = skip_count = err_count = plaus_warns = exhausted_count = 0
    exhausted_sites: list[str] = []
    t_start = time.monotonic()

    target_sites = []
    for site in sites:
        sid = site.site_id
        if skip_populated and _is_enriched(session, sid):
            skip_count += 1
            continue
        if not _needs_requery(session, sid, requery_zeros=requery_zeros):
            skip_count += 1
            continue
        target_sites.append(site)

    if limit is not None:
        target_sites = target_sites[:limit]

    total_target = len(target_sites)
    total_all = len(sites)

    print(
        f"\nFIX-05 OSM EP-04 amenities batch — {total_target} sites to query "
        f"(of {total_all} total, {skip_count} already populated), run_id={run_id}"
        + (" [DRY RUN]" if dry_run else "")
        + (" [REQUERY ZEROS]" if requery_zeros else ""),
        flush=True,
    )
    print(f"{'#':>4}  {'Country':>7}  {'Site':<40}  {'Hosp':>6}  {'Prison':>6}  {'Care':>6}  {'Total':>6}")
    print("-" * 90)

    for i, site in enumerate(target_sites):
        lat, lon = float(site.latitude), float(site.longitude)
        sid = site.site_id
        cc = site.country_code or "??"

        try:
            if not dry_run:
                elements = _query_with_retry(client, lat, lon)

                # LL-017/LL-022: None means all retries exhausted — do NOT
                # persist false-negative zeros.  Skip and track for re-query.
                if elements is None:
                    exhausted_count += 1
                    exhausted_sites.append(f"{cc} {site.name}")
                    label = "   EXHAUSTED" + " " * 18
                    log.warning(
                        "fix05_skip_exhausted",
                        site_id=str(sid),
                        site_name=site.name,
                        msg="All retries exhausted — skipping persistence to avoid false-negative zeros (LL-022)",
                    )
                    site_name = (site.name or "")[:40]
                    print(
                        f"{i+1:>4}  {cc:>7}  {site_name:<40}  {label}",
                        flush=True,
                    )
                    continue

                data = _parse_amenities(elements)
                _persist_amenities(session, sid, data, run_id)

                warning = _check_plausibility(site, data)
                if warning:
                    plaus_warns += 1
                    log.warning("fix05_plausibility", site_id=str(sid), msg=warning)

                hosp = data["hospital_count_epz"]
                prison = data["prison_count_epz"]
                care = data["care_home_count_epz"]
                total = hosp + prison + care
                label = f"{hosp:>6}  {prison:>6}  {care:>6}  {total:>6}"
            else:
                label = "   dry-run" + " " * 20

            ok_count += 1
        except Exception as exc:
            err_count += 1
            label = "   ERR" + " " * 24
            log.error("fix05_amenity_error", site_id=str(sid), error=str(exc))

        if not dry_run:
            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                log.error("fix05_commit_error", site_id=str(sid), error=str(exc))

        site_name = (site.name or "")[:40]
        print(
            f"{i+1:>4}  {cc:>7}  {site_name:<40}  {label}",
            flush=True,
        )

        if (i + 1) % 25 == 0:
            elapsed = time.monotonic() - t_start
            remaining = (total_target - i - 1) * (elapsed / (i + 1))
            log.info(
                "fix05_progress",
                completed=i + 1, total=total_target,
                ok=ok_count, errors=err_count,
                exhausted=exhausted_count, plausibility_warns=plaus_warns,
                elapsed_s=round(elapsed, 1),
                eta_min=round(remaining / 60, 1),
            )
            print(
                f"\n  --- Progress: {i+1}/{total_target} | elapsed {elapsed/60:.1f} min | "
                f"ETA ~{remaining/60:.1f} min | errors: {err_count} | "
                f"exhausted: {exhausted_count} | plausibility warns: {plaus_warns}\n",
                flush=True,
            )

    elapsed_total = time.monotonic() - t_start
    print(f"\n{'='*90}")
    print(f"FIX-05 pass complete in {elapsed_total/60:.1f} min | run_id={run_id}")
    print(f"  Processed:          {ok_count}")
    print(f"  Skipped (cached):   {skip_count}")
    print(f"  Exhausted (no persist): {exhausted_count}")
    print(f"  Errors:             {err_count}")
    print(f"  Plausibility warns: {plaus_warns}")
    if exhausted_sites:
        print(f"\n  Sites needing re-query:")
        for s in exhausted_sites:
            print(f"    - {s}")
    print(f"{'='*90}", flush=True)

    log.info(
        "fix05_batch_done", run_id=run_id,
        total_target=total_target, ok=ok_count,
        skip=skip_count, exhausted=exhausted_count, errors=err_count,
        plausibility_warns=plaus_warns,
        elapsed_s=round(elapsed_total, 1),
    )

    session.close()
    client.close()

    return exhausted_count


# ---------------------------------------------------------------------------
# Auto-retry wrapper
# ---------------------------------------------------------------------------

MAX_RETRY_PASSES = 5
RETRY_COOLDOWN_S = 120

def run_with_auto_retry(
    *,
    dry_run: bool = False,
    country_codes: list[str] | None = None,
    skip_populated: bool = True,
    requery_zeros: bool = False,
    limit: int | None = None,
    max_passes: int = MAX_RETRY_PASSES,
    cooldown_s: float = RETRY_COOLDOWN_S,
    overpass_url: str | None = None,
) -> None:
    """Run the batch, then automatically re-run for any exhausted sites.

    Repeats up to *max_passes* times (or until zero exhaustions remain).
    Waits *cooldown_s* between passes to let the Overpass API recover.
    """
    for pass_num in range(1, max_passes + 1):
        print(f"\n{'#'*90}")
        print(f"  FIX-05 — PASS {pass_num}/{max_passes}")
        print(f"{'#'*90}", flush=True)

        exhausted = run_batch(
            dry_run=dry_run,
            country_codes=country_codes,
            skip_populated=skip_populated,
            requery_zeros=requery_zeros,
            limit=limit,
            overpass_url=overpass_url,
        )

        if dry_run or exhausted == 0:
            print(f"\n  All sites processed — no exhausted sites remaining.", flush=True)
            break

        if pass_num < max_passes:
            print(
                f"\n  {exhausted} site(s) exhausted — cooling down {cooldown_s:.0f}s "
                f"before retry pass {pass_num + 1}...",
                flush=True,
            )
            log.info(
                "fix05_retry_cooldown",
                exhausted=exhausted, pass_num=pass_num,
                cooldown_s=cooldown_s,
            )
            time.sleep(cooldown_s)
        else:
            print(
                f"\n  {exhausted} site(s) still exhausted after {max_passes} passes. "
                f"Re-run later or use --requery-zeros.",
                flush=True,
            )

    print(f"\n{'#'*90}")
    print(f"  FIX-05 ALL PASSES COMPLETE")
    print(f"{'#'*90}", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-05: OSM EP-04 amenities batch — hospitals, prisons, care homes."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse CLI and connect to DB but do NOT call Overpass or write any rows.",
    )
    parser.add_argument(
        "--country", dest="countries", metavar="CC,...",
        help="Comma-separated ISO country codes to process (e.g. RO,PL). Default: all.",
    )
    parser.add_argument(
        "--no-skip-populated", dest="skip_populated", action="store_false", default=True,
        help="Re-run even for sites already enriched by a previous FIX-05 run.",
    )
    parser.add_argument(
        "--requery-zeros", action="store_true",
        help="Re-query sites that received all-zero counts from exhausted retries (LL-022).",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max number of sites to process (for validation batches).",
    )
    parser.add_argument(
        "--max-passes", type=int, default=MAX_RETRY_PASSES,
        help=f"Max retry passes for exhausted sites (default {MAX_RETRY_PASSES}).",
    )
    parser.add_argument(
        "--cooldown", type=float, default=RETRY_COOLDOWN_S,
        help=f"Seconds to wait between retry passes (default {RETRY_COOLDOWN_S}).",
    )
    parser.add_argument(
        "--overpass-url", default=None,
        help="Overpass API URL (default: https://overpass-api.de/api/interpreter). "
             "Mirrors: https://overpass.kumi.systems/api/interpreter",
    )
    args = parser.parse_args()

    country_codes = (
        [c.strip().upper() for c in args.countries.split(",")]
        if args.countries else None
    )
    run_with_auto_retry(
        dry_run=args.dry_run,
        country_codes=country_codes,
        skip_populated=args.skip_populated,
        requery_zeros=args.requery_zeros,
        limit=args.limit,
        max_passes=args.max_passes,
        cooldown_s=args.cooldown,
        overpass_url=args.overpass_url,
    )


if __name__ == "__main__":
    main()
