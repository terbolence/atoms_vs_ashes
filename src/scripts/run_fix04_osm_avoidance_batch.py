#!/usr/bin/env python
# man_hours: 3.0
"""FIX-04: OSM avoidance batch enrichment — military, HV power, EM transmitters.

Populates:
  site_human_hazards:  nearest_military_km, nearest_military_name, military_count,
                       hi06_quality, hi06_comment,
                       nearest_transmitter_km, transmitter_type, transmitter_count,
                       hi07_quality, hi07_comment
  site_infrastructure_v2: nearest_hv_line_km, nearest_substation_km, hv_line_count,
                           substation_count, hv_line_voltage_kv, ns02_quality, ns02_comment

Usage:
    python scripts/run_fix04_osm_avoidance_batch.py [--dry-run] [--country CC,...]
                                                     [--skip-populated]

Consent: User gave explicit go-ahead 2026-04-17.
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
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MILITARY_RADIUS_KM = 25.0
POWER_RADIUS_KM = 50.0
TRANSMITTER_RADIUS_KM = 25.0
INTER_QUERY_DELAY_S = 12.0
JITTER_S = 3.0
RATE_LIMIT_WAIT_S = 60.0

SOURCE_NAME = "osm_avoidance_fix04"
SOURCE_URL = "https://overpass-api.de/api/interpreter"
SOURCE_DESC = (
    "OpenStreetMap Overpass API — FIX-04 avoidance batch: military proximity (HI-06/A5/A6), "
    "HV power infrastructure (NS-02/A13), EM transmitters (HI-07)."
)

MILITARY_CRITERION_ID = "HI-06"
POWER_CRITERION_ID = "NS-02"
TRANSMITTER_CRITERION_ID = "HI-07"

HI06_COMMENT_MARKER = "Source: OSM Overpass [FIX-04 military]"
HI07_COMMENT_MARKER = "Source: OSM Overpass [FIX-04 transmitter]"
NS02_COMMENT_MARKER = "Source: OSM Overpass [FIX-04 power]"

# Military tag classifications
_MILITARY_A5_TAGS = frozenset({
    "range", "training_area", "barracks", "base", "airfield", "checkpoint",
})
_MILITARY_A6_TAGS = frozenset({
    "bunker", "ammunition", "nuclear_explosion_site", "danger_area",
})


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_military(
    site_lat: float, site_lon: float, elements: list[OsmElement]
) -> dict:
    """Aggregate OSM military elements into DB-ready fields."""
    if not elements:
        return {
            "nearest_military_km": None,
            "nearest_military_name": None,
            "military_count": 0,
            "quality": "not_found",
            "comment": f"No military features found within {MILITARY_RADIUS_KM:.0f} km. {HI06_COMMENT_MARKER}",
        }

    valid = [el for el in elements if el.lat is not None and el.lon is not None]
    if not valid:
        return {
            "nearest_military_km": None,
            "nearest_military_name": None,
            "military_count": len(elements),
            "quality": "low",
            "comment": f"{len(elements)} elements returned but lacked coordinates. {HI06_COMMENT_MARKER}",
        }

    nearest: OsmElement | None = None
    nearest_km = float("inf")
    for el in valid:
        d = haversine_km(site_lat, site_lon, el.lat, el.lon)
        if d < nearest_km:
            nearest_km = d
            nearest = el

    name = (nearest.tags.get("name") or nearest.tags.get("operator") or "") if nearest else ""
    mil_tag = (nearest.tags.get("military") or nearest.tags.get("landuse") or "") if nearest else ""
    a_class = "A5" if mil_tag in _MILITARY_A5_TAGS else "A6" if mil_tag in _MILITARY_A6_TAGS else "A5"

    comment = (
        f"Nearest military: {name or 'unnamed'} ({mil_tag}), {nearest_km:.1f} km [{a_class}]. "
        f"Total features within {MILITARY_RADIUS_KM:.0f} km: {len(valid)}. "
        f"{HI06_COMMENT_MARKER}"
    )
    quality = "high" if nearest_km < 5 else "medium"

    return {
        "nearest_military_km": round(nearest_km, 2),
        "nearest_military_name": (name[:200] if name else None),
        "military_count": len(valid),
        "quality": quality,
        "comment": comment[:1000],
    }


def _parse_power(
    site_lat: float, site_lon: float, elements: list[OsmElement]
) -> dict:
    """Aggregate OSM power elements into DB-ready HV line / substation fields."""
    if not elements:
        return {
            "nearest_hv_line_km": None,
            "nearest_substation_km": None,
            "hv_line_count": 0,
            "substation_count": 0,
            "hv_line_voltage_kv": None,
            "quality": "not_found",
            "comment": f"No HV power features found within {POWER_RADIUS_KM:.0f} km. {NS02_COMMENT_MARKER}",
        }

    valid = [el for el in elements if el.lat is not None and el.lon is not None]

    lines = [el for el in valid if el.tags.get("power") == "line"]
    substations = [el for el in valid if el.tags.get("power") == "substation"]

    def nearest(items: list[OsmElement]) -> tuple[float | None, OsmElement | None]:
        best_d: float | None = None
        best_el: OsmElement | None = None
        for el in items:
            if el.lat is None or el.lon is None:
                continue
            d = haversine_km(site_lat, site_lon, el.lat, el.lon)
            if best_d is None or d < best_d:
                best_d = d
                best_el = el
        return best_d, best_el

    line_km, nearest_line = nearest(lines)
    sub_km, nearest_sub = nearest(substations)

    # Parse voltage of nearest HV line
    voltage_kv: int | None = None
    if nearest_line:
        v_raw = nearest_line.tags.get("voltage", "")
        if v_raw:
            # voltage tag may be "220000" or "220000;110000"
            for part in v_raw.split(";"):
                try:
                    v = int(part.strip()) // 1000
                    if v >= 110:
                        voltage_kv = v
                        break
                except ValueError:
                    pass

    sub_name = (
        nearest_sub.tags.get("name") or nearest_sub.tags.get("operator", "")
        if nearest_sub else ""
    )

    parts = []
    if line_km is not None:
        parts.append(f"Nearest HV line: {line_km:.1f} km" + (f" ({voltage_kv} kV)" if voltage_kv else ""))
    if sub_km is not None:
        parts.append(f"Nearest substation: {sub_name or 'unnamed'}, {sub_km:.1f} km")
    parts.append(f"HV lines: {len(lines)}, substations: {len(substations)}")
    parts.append(NS02_COMMENT_MARKER)

    quality = "medium"
    if line_km is not None and line_km < 10 and sub_km is not None and sub_km < 20:
        quality = "high"
    if line_km is None and sub_km is None:
        quality = "not_found"

    return {
        "nearest_hv_line_km": round(line_km, 2) if line_km is not None else None,
        "nearest_substation_km": round(sub_km, 2) if sub_km is not None else None,
        "hv_line_count": len(lines),
        "substation_count": len(substations),
        "hv_line_voltage_kv": voltage_kv,
        "quality": quality,
        "comment": "; ".join(parts)[:1000],
    }


def _parse_transmitters(
    site_lat: float, site_lon: float, elements: list[OsmElement]
) -> dict:
    """Aggregate OSM transmitter elements into DB-ready fields."""
    if not elements:
        return {
            "nearest_transmitter_km": None,
            "transmitter_type": None,
            "transmitter_count": 0,
            "quality": "not_found",
            "comment": f"No transmitters/masts found within {TRANSMITTER_RADIUS_KM:.0f} km. {HI07_COMMENT_MARKER}",
        }

    valid = [el for el in elements if el.lat is not None and el.lon is not None]
    if not valid:
        return {
            "nearest_transmitter_km": None,
            "transmitter_type": None,
            "transmitter_count": len(elements),
            "quality": "low",
            "comment": f"{len(elements)} elements lacked coordinates. {HI07_COMMENT_MARKER}",
        }

    nearest: OsmElement | None = None
    nearest_km = float("inf")
    for el in valid:
        d = haversine_km(site_lat, site_lon, el.lat, el.lon)
        if d < nearest_km:
            nearest_km = d
            nearest = el

    tx_type = (
        nearest.tags.get("tower:type")
        or nearest.tags.get("man_made")
        or "mast"
        if nearest else "mast"
    )

    comment = (
        f"Nearest transmitter: {tx_type}, {nearest_km:.1f} km. "
        f"Total within {TRANSMITTER_RADIUS_KM:.0f} km: {len(valid)}. "
        f"{HI07_COMMENT_MARKER}"
    )

    return {
        "nearest_transmitter_km": round(nearest_km, 2),
        "transmitter_type": tx_type[:100],
        "transmitter_count": len(valid),
        "quality": "medium",
        "comment": comment[:500],
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


def _check_hh_comment(session: Session, site_id: uuid.UUID, marker: str) -> bool:
    """Return True if site_human_hazards has a comment containing *marker*."""
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("SELECT hi06_comment, hi07_comment FROM site_human_hazards WHERE site_id = CAST(:sid AS uuid)"),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    for col in ("hi06_comment", "hi07_comment"):
        val = row.get(col) or ""
        if marker in val:
            return True
    return False


def _is_enriched_military(session: Session, site_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("SELECT hi06_comment FROM site_human_hazards WHERE site_id = CAST(:sid AS uuid)"),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    return HI06_COMMENT_MARKER in (row.get("hi06_comment") or "")


def _is_enriched_power(session: Session, site_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("SELECT ns02_comment FROM site_infrastructure_v2 WHERE site_id = CAST(:sid AS uuid)"),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    return NS02_COMMENT_MARKER in (row.get("ns02_comment") or "")


def _is_enriched_transmitter(session: Session, site_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("SELECT hi07_comment FROM site_human_hazards WHERE site_id = CAST(:sid AS uuid)"),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    return HI07_COMMENT_MARKER in (row.get("hi07_comment") or "")


def _persist_military(
    session: Session, site_id: uuid.UUID, data: dict, run_id: str,
) -> None:
    from sqlalchemy import text as sa_text
    now = datetime.now(timezone.utc)
    session.execute(sa_text("""
        INSERT INTO site_human_hazards (site_id, nearest_military_km, nearest_military_name,
            military_count, hi06_quality, hi06_comment, fetched_at, run_id)
        VALUES (CAST(:sid AS uuid), :nearest_military_km, :nearest_military_name, :military_count,
                :hi06_quality, :hi06_comment, :now, :run_id)
        ON CONFLICT (site_id) DO UPDATE SET
            nearest_military_km   = EXCLUDED.nearest_military_km,
            nearest_military_name = EXCLUDED.nearest_military_name,
            military_count        = EXCLUDED.military_count,
            hi06_quality          = EXCLUDED.hi06_quality,
            hi06_comment          = EXCLUDED.hi06_comment,
            fetched_at            = EXCLUDED.fetched_at,
            run_id                = EXCLUDED.run_id
    """), {
        "sid": str(site_id),
        "nearest_military_km": data["nearest_military_km"],
        "nearest_military_name": data["nearest_military_name"],
        "military_count": data["military_count"],
        "hi06_quality": data["quality"],
        "hi06_comment": data["comment"],
        "now": now,
        "run_id": run_id,
    })


def _persist_transmitter(
    session: Session, site_id: uuid.UUID, data: dict, run_id: str,
) -> None:
    from sqlalchemy import text as sa_text
    now = datetime.now(timezone.utc)
    session.execute(sa_text("""
        INSERT INTO site_human_hazards (site_id, nearest_transmitter_km, transmitter_type,
            transmitter_count, hi07_quality, hi07_comment, fetched_at, run_id)
        VALUES (CAST(:sid AS uuid), :nearest_transmitter_km, :transmitter_type, :transmitter_count,
                :hi07_quality, :hi07_comment, :now, :run_id)
        ON CONFLICT (site_id) DO UPDATE SET
            nearest_transmitter_km = EXCLUDED.nearest_transmitter_km,
            transmitter_type       = EXCLUDED.transmitter_type,
            transmitter_count      = EXCLUDED.transmitter_count,
            hi07_quality           = EXCLUDED.hi07_quality,
            hi07_comment           = EXCLUDED.hi07_comment,
            fetched_at             = EXCLUDED.fetched_at,
            run_id                 = EXCLUDED.run_id
    """), {
        "sid": str(site_id),
        "nearest_transmitter_km": data["nearest_transmitter_km"],
        "transmitter_type": data["transmitter_type"],
        "transmitter_count": data["transmitter_count"],
        "hi07_quality": data["quality"],
        "hi07_comment": data["comment"],
        "now": now,
        "run_id": run_id,
    })


def _persist_power(
    session: Session, site_id: uuid.UUID, data: dict, run_id: str,
) -> None:
    from sqlalchemy import text as sa_text
    now = datetime.now(timezone.utc)
    session.execute(sa_text("""
        INSERT INTO site_infrastructure_v2 (site_id, nearest_hv_line_km, nearest_substation_km,
            hv_line_count, substation_count, hv_line_voltage_kv, ns02_quality, ns02_comment,
            fetched_at, run_id)
        VALUES (CAST(:sid AS uuid), :nearest_hv_line_km, :nearest_substation_km, :hv_line_count,
                :substation_count, :hv_line_voltage_kv, :ns02_quality, :ns02_comment, :now, :run_id)
        ON CONFLICT (site_id) DO UPDATE SET
            nearest_hv_line_km   = EXCLUDED.nearest_hv_line_km,
            nearest_substation_km = EXCLUDED.nearest_substation_km,
            hv_line_count        = EXCLUDED.hv_line_count,
            substation_count     = EXCLUDED.substation_count,
            hv_line_voltage_kv   = EXCLUDED.hv_line_voltage_kv,
            ns02_quality         = EXCLUDED.ns02_quality,
            ns02_comment         = EXCLUDED.ns02_comment,
            fetched_at           = EXCLUDED.fetched_at,
            run_id               = EXCLUDED.run_id
    """), {
        "sid": str(site_id),
        "nearest_hv_line_km": data["nearest_hv_line_km"],
        "nearest_substation_km": data["nearest_substation_km"],
        "hv_line_count": data["hv_line_count"],
        "substation_count": data["substation_count"],
        "hv_line_voltage_kv": data["hv_line_voltage_kv"],
        "ns02_quality": data["quality"],
        "ns02_comment": data["comment"],
        "now": now,
        "run_id": run_id,
    })


# ---------------------------------------------------------------------------
# Rate-limiting and retry helpers
# ---------------------------------------------------------------------------

_MAX_RETRIES = 6
_BACKOFF_BASE_S = 45.0
_BACKOFF_CAP_S = 180.0
_RETRYABLE_STATUSES = {429, 504, 408, 0}


def _is_retryable(client: OverpassClient) -> bool:
    """True if the last query failed with a transient/retryable error."""
    return client._last_http_status in _RETRYABLE_STATUSES


def _wait_for_overpass_slot(client: OverpassClient, max_wait_s: float) -> None:
    """Poll Overpass /status until a query slot is available or *max_wait_s* expires."""
    status_url = client._url.replace("/interpreter", "/status")
    deadline = time.monotonic() + max_wait_s
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(status_url, timeout=5)
            if resp.status_code == 200:
                text = resp.text
                if "slots available now" in text:
                    log.info("fix04_slot_available")
                    time.sleep(2)
                    return
                for line in text.splitlines():
                    if "Slot available after" in line and "in" in line:
                        parts = line.split("in ")
                        if parts:
                            try:
                                secs = int(parts[-1].replace(" seconds.", "").strip())
                                sleep_for = min(secs + 2, deadline - time.monotonic())
                                if sleep_for > 0:
                                    log.info("fix04_wait_slot", wait_s=round(sleep_for))
                                    time.sleep(sleep_for)
                                return
                            except (ValueError, IndexError):
                                pass
        except Exception:
            pass
        time.sleep(10)


def _query_with_retry(fetch_fn, client: OverpassClient, lat: float, lon: float, radius_km: float) -> list:
    """Call *fetch_fn* with exponential backoff on transient errors.

    Retries on 429, 504, timeouts (408), and disconnects (status 0).
    Polls Overpass /status before each retry to wait for an available slot.
    Returns the element list; on total failure returns [] and logs a warning.
    """
    for attempt in range(_MAX_RETRIES + 1):
        elements = fetch_fn(lat, lon, radius_km=radius_km)
        if not _is_retryable(client):
            jitter = random.uniform(-JITTER_S, JITTER_S)
            time.sleep(max(2.0, INTER_QUERY_DELAY_S + jitter))
            return elements
        if attempt < _MAX_RETRIES:
            wait = min(_BACKOFF_BASE_S * (2 ** attempt), _BACKOFF_CAP_S)
            log.warning(
                "fix04_query_retry",
                attempt=attempt + 1,
                wait_s=round(wait),
                status=client._last_http_status,
            )
            _wait_for_overpass_slot(client, max_wait_s=wait)
            time.sleep(random.uniform(2, 8))
        else:
            log.error("fix04_query_exhausted", status=client._last_http_status, lat=lat, lon=lon)
    return elements


# ---------------------------------------------------------------------------
# Main batch loop
# ---------------------------------------------------------------------------

def _needs_requery_military(session: Session, site_id: uuid.UUID) -> bool:
    """True if site has marker but null distance (likely false negative from disconnect)."""
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("""SELECT nearest_military_km, military_count, hi06_comment
                   FROM site_human_hazards WHERE site_id = CAST(:sid AS uuid)"""),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    comment = row.get("hi06_comment") or ""
    if HI06_COMMENT_MARKER not in comment:
        return False
    return row["nearest_military_km"] is None and (row["military_count"] or 0) == 0


def _needs_requery_power(session: Session, site_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("""SELECT nearest_hv_line_km, nearest_substation_km, hv_line_count,
                          substation_count, ns02_comment
                   FROM site_infrastructure_v2 WHERE site_id = CAST(:sid AS uuid)"""),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    comment = row.get("ns02_comment") or ""
    if NS02_COMMENT_MARKER not in comment:
        return False
    return (row["nearest_hv_line_km"] is None and row["nearest_substation_km"] is None
            and (row["hv_line_count"] or 0) == 0 and (row["substation_count"] or 0) == 0)


def _needs_requery_transmitter(session: Session, site_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text
    row = session.execute(
        sa_text("""SELECT nearest_transmitter_km, transmitter_count, hi07_comment
                   FROM site_human_hazards WHERE site_id = CAST(:sid AS uuid)"""),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    comment = row.get("hi07_comment") or ""
    if HI07_COMMENT_MARKER not in comment:
        return False
    return row["nearest_transmitter_km"] is None and (row["transmitter_count"] or 0) == 0


def run_batch(
    *,
    dry_run: bool = False,
    country_codes: list[str] | None = None,
    skip_populated: bool = True,
    requery_nulls: bool = False,
) -> None:
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    client = OverpassClient(settings)

    run_id = f"fix04_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info("fix04_batch_start", run_id=run_id, dry_run=dry_run, requery_nulls=requery_nulls)

    query = session.query(Site)
    if country_codes:
        query = query.filter(Site.country_code.in_(country_codes))
    sites = query.order_by(Site.country_code, Site.name).all()

    if not sites:
        print("No sites found.", file=sys.stderr)
        return

    if not dry_run:
        _ensure_data_source(session)
        session.commit()

    # Counters
    mil_ok = mil_skip = mil_err = 0
    pwr_ok = pwr_skip = pwr_err = 0
    tx_ok = tx_skip = tx_err = 0
    t_start = time.monotonic()

    print(
        f"\nFIX-04 OSM avoidance batch — {len(sites)} sites, run_id={run_id}"
        + (" [DRY RUN]" if dry_run else "")
        + (" [REQUERY NULLS]" if requery_nulls else ""),
        flush=True,
    )
    print(f"{'#':>4}  {'Country':>7}  {'Site':<40}  {'Military':>10}  {'HV line':>10}  {'Transmit':>10}")
    print("-" * 95)

    for i, site in enumerate(sites):
        lat, lon = float(site.latitude), float(site.longitude)
        sid = site.site_id
        cc = site.country_code or "??"

        mil_cached = skip_populated and _is_enriched_military(session, sid)
        pwr_cached = skip_populated and _is_enriched_power(session, sid)
        tx_cached = skip_populated and _is_enriched_transmitter(session, sid)

        if requery_nulls:
            if mil_cached and _needs_requery_military(session, sid):
                mil_cached = False
            if pwr_cached and _needs_requery_power(session, sid):
                pwr_cached = False
            if tx_cached and _needs_requery_transmitter(session, sid):
                tx_cached = False

        all_cached = mil_cached and pwr_cached and tx_cached
        if all_cached:
            mil_skip += 1
            pwr_skip += 1
            tx_skip += 1
            continue

        mil_label = pwr_label = tx_label = "skip"

        # --- Military ---
        if mil_cached:
            mil_skip += 1
            mil_label = "cached"
        else:
            try:
                if not dry_run:
                    elements = _query_with_retry(client.fetch_military_areas, client, lat, lon, MILITARY_RADIUS_KM)
                    mil_data = _parse_military(lat, lon, elements)
                    _persist_military(session, sid, mil_data, run_id)
                    mil_km = mil_data["nearest_military_km"]
                    mil_label = f"{mil_km:.1f} km" if mil_km is not None else "none"
                else:
                    mil_label = "dry-run"
                mil_ok += 1
            except Exception as exc:
                mil_err += 1
                mil_label = "ERR"
                log.error("fix04_military_error", site_id=str(sid), error=str(exc))

        # --- Power infrastructure ---
        if pwr_cached:
            pwr_skip += 1
            pwr_label = "cached"
        else:
            try:
                if not dry_run:
                    elements = _query_with_retry(client.fetch_power_infrastructure, client, lat, lon, POWER_RADIUS_KM)
                    pwr_data = _parse_power(lat, lon, elements)
                    _persist_power(session, sid, pwr_data, run_id)
                    hv_km = pwr_data["nearest_hv_line_km"]
                    pwr_label = f"{hv_km:.1f} km" if hv_km is not None else "none"
                else:
                    pwr_label = "dry-run"
                pwr_ok += 1
            except Exception as exc:
                pwr_err += 1
                pwr_label = "ERR"
                log.error("fix04_power_error", site_id=str(sid), error=str(exc))

        # --- Transmitters ---
        if tx_cached:
            tx_skip += 1
            tx_label = "cached"
        else:
            try:
                if not dry_run:
                    elements = _query_with_retry(client.fetch_transmitters, client, lat, lon, TRANSMITTER_RADIUS_KM)
                    tx_data = _parse_transmitters(lat, lon, elements)
                    _persist_transmitter(session, sid, tx_data, run_id)
                    tx_km = tx_data["nearest_transmitter_km"]
                    tx_label = f"{tx_km:.1f} km" if tx_km is not None else "none"
                else:
                    tx_label = "dry-run"
                tx_ok += 1
            except Exception as exc:
                tx_err += 1
                tx_label = "ERR"
                log.error("fix04_transmitter_error", site_id=str(sid), error=str(exc))

        # Commit per-site
        if not dry_run:
            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                log.error("fix04_commit_error", site_id=str(sid), error=str(exc))

        site_name = (site.name or "")[:40]
        print(
            f"{i+1:>4}  {cc:>7}  {site_name:<40}  {mil_label:>10}  {pwr_label:>10}  {tx_label:>10}",
            flush=True,
        )

        # Progress summary every 25 sites
        if (i + 1) % 25 == 0:
            elapsed = time.monotonic() - t_start
            remaining = (len(sites) - i - 1) * (elapsed / (i + 1))
            log.info(
                "fix04_progress",
                completed=i + 1, total=len(sites),
                mil_ok=mil_ok, pwr_ok=pwr_ok, tx_ok=tx_ok,
                errors=mil_err + pwr_err + tx_err,
                elapsed_s=round(elapsed, 1),
                eta_min=round(remaining / 60, 1),
            )
            print(
                f"\n  --- Progress: {i+1}/{len(sites)} | elapsed {elapsed/60:.1f} min | "
                f"ETA ~{remaining/60:.1f} min | errors: mil={mil_err} pwr={pwr_err} tx={tx_err}\n",
                flush=True,
            )

    elapsed_total = time.monotonic() - t_start
    print(f"\n{'='*95}")
    print(f"FIX-04 complete in {elapsed_total/60:.1f} min | run_id={run_id}")
    print(f"  Military:     {mil_ok} processed, {mil_skip} cached, {mil_err} errors")
    print(f"  Power:        {pwr_ok} processed, {pwr_skip} cached, {pwr_err} errors")
    print(f"  Transmitters: {tx_ok} processed, {tx_skip} cached, {tx_err} errors")
    print(f"{'='*95}", flush=True)

    log.info(
        "fix04_batch_done", run_id=run_id,
        total_sites=len(sites),
        mil_ok=mil_ok, mil_skip=mil_skip, mil_err=mil_err,
        pwr_ok=pwr_ok, pwr_skip=pwr_skip, pwr_err=pwr_err,
        tx_ok=tx_ok, tx_skip=tx_skip, tx_err=tx_err,
        elapsed_s=round(elapsed_total, 1),
    )

    session.close()
    client.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-04: OSM avoidance batch — military, HV power, transmitters."
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
        help="Re-run even for sites already enriched by a previous FIX-04 run.",
    )
    parser.add_argument(
        "--requery-nulls", action="store_true",
        help="Re-query sites where data was stored as null (likely false negatives from disconnects).",
    )
    args = parser.parse_args()

    country_codes = [c.strip().upper() for c in args.countries.split(",")] if args.countries else None
    run_batch(
        dry_run=args.dry_run,
        country_codes=country_codes,
        skip_populated=args.skip_populated,
        requery_nulls=args.requery_nulls,
    )


if __name__ == "__main__":
    main()
