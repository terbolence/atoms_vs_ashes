# man_hours: 6.2
"""Batch enrichment and DB persistence for P11 OSM transport access.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` (NS-03 columns).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.osm.models import (
    LOW_OSM_COVERAGE_COUNTRIES,
    TRANSPORT_CRITERION_ID,
    TRANSPORT_SOURCE_DESCRIPTION,
    TRANSPORT_SOURCE_NAME,
    TRANSPORT_SOURCE_URL,
    TransportBatchResult,
    TransportResult,
    TransportSiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.osm.parsers import (
    TRANSPORT_NS03_COMMENT_MARKER,
    assess_heavy_haul,
    build_ns03_comment,
    classify_highways,
    classify_railways,
    classify_waterways,
    determine_quality,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteInfrastructureV2,
    SiteObservation,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.osm.client import OverpassClient

log = get_logger(__name__)

_CACHE_TTL_DAYS = 30
_BATCH_INTER_QUERY_DELAY_S = 5.0


def enrich_site(
    client: OverpassClient,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
    *,
    highway_radius_km: float = 10.0,
    railway_radius_km: float = 15.0,
    waterway_radius_km: float = 10.0,
) -> TransportSiteEnrichmentSummary:
    """Fetch and persist transport access data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return TransportSiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_source(session)

    cached = _check_cache(session, site_id, run_id)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("transport_cache_hit", site_id=str(site_id))
        return TransportSiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_highway_km=_to_float(cached.nearest_highway_km),
            nearest_rail_km=_to_float(cached.nearest_rail_km),
            nearest_waterway_km=_to_float(cached.nearest_waterway_km),
            heavy_haul_capable=cached.heavy_haul_capable,
            source=TRANSPORT_SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = _fetch_transport(
            client, float(site.latitude), float(site.longitude),
            country_code=site.country_code or "",
            highway_radius_km=highway_radius_km,
            railway_radius_km=railway_radius_km,
            waterway_radius_km=waterway_radius_km,
        )
        _persist_result(session, site_id, result, run_id, site.country_code or "")
        _log_osm_raw(session, client, site_id, run_id, scope="transport")
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return TransportSiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            nearest_highway_km=result.highway.nearest_highway_km,
            nearest_rail_km=result.railway.nearest_rail_km,
            nearest_waterway_km=result.waterway.nearest_waterway_km,
            heavy_haul_capable=result.heavy_haul_capable,
            quality=result.quality,
            source=result.source,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_osm_raw(session, client, site_id, run_id, scope="transport", error=str(exc))
        except Exception as log_exc:
            log.warning("osm_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("transport_site_error", site_id=str(site_id), error=str(exc))
        return TransportSiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    client: OverpassClient,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    highway_radius_km: float = 10.0,
    railway_radius_km: float = 15.0,
    waterway_radius_km: float = 10.0,
) -> TransportBatchResult:
    """Enrich multiple sites with per-site commit isolation and progress logging."""
    batch = TransportBatchResult(run_id=run_id)
    batch_start = time.monotonic()

    query = session.query(Site)
    if site_ids is not None:
        if not site_ids:
            return batch
        query = query.filter(Site.site_id.in_(site_ids))
    elif country_codes is not None:
        query = query.filter(Site.country_code.in_(country_codes))

    sites = query.order_by(Site.country_code, Site.name).all()
    batch.total_sites = len(sites)
    if not sites:
        return batch

    _ensure_data_source(session)

    log.info(
        "transport_batch_start",
        run_id=run_id,
        total_sites=len(sites),
        expected_queries=len(sites) * 3,
        estimated_minutes=round(len(sites) * 15 / 60, 1),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id)
        if cached:
            log.info("transport_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(TransportSiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                nearest_highway_km=_to_float(cached.nearest_highway_km),
                nearest_rail_km=_to_float(cached.nearest_rail_km),
                nearest_waterway_km=_to_float(cached.nearest_waterway_km),
                heavy_haul_capable=cached.heavy_haul_capable,
                source=TRANSPORT_SOURCE_NAME,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = _fetch_transport(
                client, float(site.latitude), float(site.longitude),
                country_code=site.country_code or "",
                highway_radius_km=highway_radius_km,
                railway_radius_km=railway_radius_km,
                waterway_radius_km=waterway_radius_km,
            )
            _persist_result(session, site.site_id, result, run_id, site.country_code or "")
            _log_osm_raw(session, client, site.site_id, run_id, scope="transport")
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "transport_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                nearest_highway_km=result.highway.nearest_highway_km,
                nearest_rail_km=result.railway.nearest_rail_km,
                heavy_haul=result.heavy_haul_capable,
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(TransportSiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                nearest_highway_km=result.highway.nearest_highway_km,
                nearest_rail_km=result.railway.nearest_rail_km,
                nearest_waterway_km=result.waterway.nearest_waterway_km,
                heavy_haul_capable=result.heavy_haul_capable,
                quality=result.quality,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("transport_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_osm_raw(session, client, site.site_id, run_id, scope="transport", error=str(exc))
            except Exception as log_exc:
                log.warning("osm_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(TransportSiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "transport_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                cached=batch.skipped_cached,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "transport_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Core fetch logic
# ------------------------------------------------------------------

_MAX_QUERY_RETRIES = 3
_RETRY_BACKOFF_BASE_S = 15.0
_RETRY_BACKOFF_CAP_S = 90.0


def _query_with_retry(
    client: OverpassClient,
    fetch_fn,
    lat: float,
    lon: float,
    *,
    radius_km: float,
) -> list:
    """Execute a fetch method with retry on 429 rate limiting."""
    for attempt in range(_MAX_QUERY_RETRIES + 1):
        elements = fetch_fn(lat, lon, radius_km=radius_km)
        if not client.was_rate_limited:
            return elements
        if attempt < _MAX_QUERY_RETRIES:
            wait = min(
                _RETRY_BACKOFF_BASE_S * (2 ** attempt),
                _RETRY_BACKOFF_CAP_S,
            )
            log.warning(
                "transport_rate_limited",
                attempt=attempt + 1,
                wait_s=round(wait),
                lat=lat, lon=lon,
            )
            client._wait_for_slot(wait)
    return elements


def _fetch_transport(
    client: OverpassClient,
    lat: float,
    lon: float,
    *,
    country_code: str = "",
    highway_radius_km: float = 10.0,
    railway_radius_km: float = 15.0,
    waterway_radius_km: float = 10.0,
) -> TransportResult:
    """Fetch all transport data in ONE Overpass query and aggregate into a TransportResult.

    Uses ``client.fetch_transport_combined`` to issue a single union query
    covering highways, railways and waterways.  This is 3× more efficient than
    the previous three-query approach and dramatically reduces 504 incidence on
    public mirrors.
    """
    client.reset_raw_call_log()
    hw_elements, rw_elements, ww_elements = client.fetch_transport_combined(
        lat, lon,
        highway_radius_km=highway_radius_km,
        railway_radius_km=railway_radius_km,
        waterway_radius_km=waterway_radius_km,
    )

    highway = classify_highways(lat, lon, hw_elements)
    railway = classify_railways(lat, lon, rw_elements, country_code=country_code)
    waterway = classify_waterways(lat, lon, ww_elements)

    capable, confidence = assess_heavy_haul(highway, railway, waterway)

    result = TransportResult(
        lat=lat,
        lon=lon,
        highway=highway,
        railway=railway,
        waterway=waterway,
        heavy_haul_capable=capable,
        heavy_haul_confidence=confidence,
    )
    result.quality = determine_quality(result, country_code)
    return result


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------

def _check_cache(
    session: Session,
    site_id: uuid.UUID,
    _run_id: str,
) -> SiteInfrastructureV2 | None:
    """Return cached infra row if P11 transport was persisted recently.

    Rows are identified by ``ns03_comment`` containing the OSM provenance marker
    (not by ``run_id``), so a new CLI run can resume after an interrupted batch
    without re-querying Overpass for completed sites.
    """
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return None
    if not row.ns03_comment or TRANSPORT_NS03_COMMENT_MARKER not in row.ns03_comment:
        return None
    if row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=_CACHE_TTL_DAYS):
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for OSM transport."""
    existing = session.query(DataSource).filter_by(name=TRANSPORT_SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=TRANSPORT_SOURCE_NAME,
        url=TRANSPORT_SOURCE_URL,
        description=TRANSPORT_SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: TransportResult,
    run_id: str,
    country_code: str = "",
) -> None:
    """Write transport data to SiteInfrastructureV2 and SiteObservation."""
    now = datetime.now(timezone.utc)

    infra = session.get(SiteInfrastructureV2, site_id)
    if infra is None:
        infra = SiteInfrastructureV2(site_id=site_id)
        session.add(infra)

    # Merge-only: never overwrite a non-NULL column with NULL.
    # This prevents API failures (200 + 0 elements) from wiping good data.
    if infra.nearest_highway_km is None:
        infra.nearest_highway_km = result.highway.nearest_highway_km
    if infra.nearest_rail_km is None:
        infra.nearest_rail_km = result.railway.nearest_rail_km
    if infra.nearest_waterway_km is None:
        infra.nearest_waterway_km = result.waterway.nearest_waterway_km
    if infra.heavy_haul_capable is None:
        infra.heavy_haul_capable = result.heavy_haul_capable
    infra.ns03_quality = result.quality
    infra.ns03_comment = build_ns03_comment(result)
    infra.fetched_at = now
    infra.run_id = run_id

    _write_observations(session, site_id, result, run_id, country_code)


def _write_observations(
    session: Session,
    site_id: uuid.UUID,
    result: TransportResult,
    run_id: str,
    country_code: str = "",
) -> None:
    """Write SiteObservation records for notable transport conditions."""
    hw = result.highway
    rw = result.railway
    ww = result.waterway

    if hw.nearest_highway_km is None or hw.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"No motorway/trunk/primary highway found within 10 km. "
                f"Detail: {hw.error or 'no elements returned'}"
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))

    if rw.nearest_rail_km is None or rw.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"No railway found within 15 km. "
                f"Detail: {rw.error or 'no elements returned'}"
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))

    if ww.nearest_waterway_km is None or ww.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"No navigable waterway found within 10 km. "
                f"Normal for inland sites not near major rivers."
            ),
            impact="neutral", confidence="high", run_id=run_id,
        ))

    if result.heavy_haul_capable is None:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                "Heavy-haul transport capability could not be determined. "
                "Former coal plant logistics access is not penalized without "
                "explicit negative route evidence; manual route confirmation "
                "is recommended."
            ),
            impact="neutral", confidence="low", run_id=run_id,
        ))

    if result.heavy_haul_capable is False:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                "Heavy-haul transport capability is explicitly negative across "
                "the available OSM road, rail, and waterway indicators."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))

    if rw.rail_siding_present:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                "Rail siding or spur found within 1 km of site. "
                "Strong indicator of existing heavy transport infrastructure "
                "(typical for coal plant sites)."
            ),
            impact="positive", confidence="high", run_id=run_id,
        ))

    total_elements = hw.element_count + rw.element_count + ww.element_count
    if total_elements < 2:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"OSM data appears sparse for this location "
                f"(only {total_elements} transport elements returned across all queries). "
                f"Results should be treated with low confidence."
            ),
            impact="neutral", confidence="low", run_id=run_id,
        ))

    if (
        country_code.upper() in LOW_OSM_COVERAGE_COUNTRIES
        and rw.nearest_rail_km is not None
        and rw.nearest_rail_km < 5.0
    ):
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"Site is in {country_code.upper()} (known lower OSM railway coverage). "
                f"Rail proximity of {rw.nearest_rail_km:.1f} km should be validated "
                f"against national railway data."
            ),
            impact="neutral", confidence="low", run_id=run_id,
        ))

    cc_upper = country_code.upper()
    if (
        cc_upper in {"UA", "BY", "EE", "LV", "LT", "AM"}
        and rw.nearest_rail_km is not None
        and rw.nearest_rail_km < 5.0
    ):
        session.add(SiteObservation(
            site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID,
            source_type="api",
            observation=(
                f"Nearest rail is within 5 km in broad-gauge country ({cc_upper}). "
                f"Gauge: {rw.rail_gauge_mm or 1520} mm. "
                f"Cross-border heavy-haul logistics may require gauge-change facilities."
            ),
            impact="neutral", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation when transport enrichment fails."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=TRANSPORT_CRITERION_ID, source_type="api",
        observation=f"Transport access enrichment failed: {error}",
        impact="negative", confidence="low", run_id=run_id,
    ))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_float(val: Any) -> float | None:
    """Safely convert a DB numeric to float."""
    if val is None:
        return None
    return float(val)


def _log_osm_raw(
    session: Session,
    client: OverpassClient,
    site_id: uuid.UUID,
    run_id: str,
    *,
    scope: str,
    error: str | None = None,
) -> None:
    """Persist this site's accumulated Overpass calls to site_raw_responses.

    Combines every per-call entry from ``client.consume_raw_call_log()`` into
    a single ``response_body`` dict keyed by ``calls`` so the disk file and
    DB row contain the full Overpass dialogue for the site.
    """
    calls = client.consume_raw_call_log()
    if not calls and error is None:
        return

    body: dict[str, Any] = {
        "scope": scope,
        "calls": calls,
    }
    if error is not None:
        body["error"] = error

    last_status = calls[-1]["http_status"] if calls else None
    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="osm",
        run_id=run_id,
        request_url=getattr(client, "_url", ""),
        response_body=body,
        http_status=last_status,
    )


# ------------------------------------------------------------------
# Audit-style multi-query capture
# ------------------------------------------------------------------

_AUDIT_QUERY_TYPES = (
    "road_density",
    "amenities",
    "transport_combined",
    "military",
    "power_infrastructure",
    "transmitters",
    "airports",
)
_AUDIT_AMENITY_TYPES = (
    "hospital", "clinic", "prison", "nursing_home", "social_facility",
)
_AUDIT_EPZ_RADIUS_M = 25_000
_AUDIT_ROAD_RADIUS_M = 16_000


def enrich_audit_responses(
    client: OverpassClient,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    inter_query_delay_s: float = 20.0,
    inter_query_jitter_s: float = 5.0,
    skip_already_logged: bool = True,
) -> dict[str, int]:
    """Run all audit query types per site and dual-write raw responses.

    This is the canonical replacement for the standalone audit script and
    must be called instead of any future ad-hoc raw-capture script.  Every
    site gets exactly one ``site_raw_responses`` row whose ``response_body``
    contains the union of all Overpass query bodies.

    Returns a small summary dict: ``{"total": N, "logged": N, "errors": N,
    "skipped": N}``.
    """
    from sqlalchemy import text

    summary = {"total": 0, "logged": 0, "errors": 0, "skipped": 0}

    query = session.query(Site)
    if site_ids is not None:
        if not site_ids:
            return summary
        query = query.filter(Site.site_id.in_(site_ids))
    sites = query.order_by(Site.country_code, Site.name).all()
    summary["total"] = len(sites)
    if not sites:
        return summary

    already_done: set[uuid.UUID] = set()
    if skip_already_logged:
        rows = session.execute(
            text(
                "SELECT DISTINCT site_id FROM site_raw_responses "
                "WHERE connector_slug = 'osm' AND run_id = :rid"
            ),
            {"rid": run_id},
        ).fetchall()
        already_done = {r[0] for r in rows}

    for site in sites:
        if site.site_id in already_done:
            summary["skipped"] += 1
            continue

        client.reset_raw_call_log()
        per_query: list[dict[str, Any]] = []
        try:
            lat = float(site.latitude)
            lon = float(site.longitude)
            country_code = site.country_code or ""

            for qt in _AUDIT_QUERY_TYPES:
                try:
                    per_query.append(
                        _run_audit_query(client, qt, lat, lon, country_code=country_code)
                    )
                except Exception as exc:
                    per_query.append({"type": qt, "error": str(exc)})
                _audit_delay(inter_query_delay_s, inter_query_jitter_s)

            log_raw_response(
                session,
                site_id=site.site_id,
                connector_slug="osm",
                run_id=run_id,
                request_url=getattr(client, "_url", ""),
                response_body={
                    "scope": "audit",
                    "query_types": list(_AUDIT_QUERY_TYPES),
                    "results": per_query,
                    "calls": client.consume_raw_call_log(),
                },
                http_status=200 if all("error" not in r for r in per_query) else None,
            )
            session.commit()
            summary["logged"] += 1
        except Exception as exc:
            session.rollback()
            log.error("osm_audit_site_error", site_id=str(site.site_id), error=str(exc))
            summary["errors"] += 1

    return summary


def _run_audit_query(
    client: OverpassClient,
    qt: str,
    lat: float,
    lon: float,
    *,
    country_code: str,
) -> dict[str, Any]:
    """Dispatch a single audit query type and summarise the result."""
    if qt == "road_density":
        return {"type": qt, "data": client.fetch_road_density(lat, lon, _AUDIT_ROAD_RADIUS_M)}
    if qt == "amenities":
        elements = client.fetch_amenities(lat, lon, _AUDIT_EPZ_RADIUS_M, list(_AUDIT_AMENITY_TYPES))
        return {"type": qt, "count": len(elements)}
    if qt == "transport_combined":
        hw, rw, ww = client.fetch_transport_combined(lat, lon)
        h = classify_highways(lat, lon, hw)
        r = classify_railways(lat, lon, rw, country_code=country_code)
        w = classify_waterways(lat, lon, ww)
        return {
            "type": qt,
            "data": {
                "nearest_highway_km": h.nearest_highway_km,
                "nearest_rail_km": r.nearest_rail_km,
                "nearest_waterway_km": w.nearest_waterway_km,
            },
        }
    if qt == "military":
        return {"type": qt, "count": len(client.fetch_military_areas(lat, lon))}
    if qt == "power_infrastructure":
        return {"type": qt, "count": len(client.fetch_power_infrastructure(lat, lon))}
    if qt == "transmitters":
        return {"type": qt, "count": len(client.fetch_transmitters(lat, lon))}
    if qt == "airports":
        return {"type": qt, "count": len(client.fetch_airports(lat, lon))}
    raise ValueError(f"Unknown audit query type: {qt}")


def _audit_delay(base: float, jitter: float) -> None:
    """Sleep between Overpass calls to respect fair-use limits."""
    import random as _random

    time.sleep(max(5.0, base + _random.uniform(-jitter, jitter)))
