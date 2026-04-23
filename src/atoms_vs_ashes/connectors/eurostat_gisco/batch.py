# man_hours: 3.0
"""Batch enrichment and DB persistence for the Eurostat GISCO connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteRadiological`` (RI-05) / ``SiteObservation``.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.eurostat_gisco.models import (
    CRITERION_IDS,
    SOURCE_DESCRIPTION,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    EurostatGiscoResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteObservation,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.eurostat_gisco.client import EurostatGiscoConnector

log = get_logger(__name__)


def enrich_site(
    connector: EurostatGiscoConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist Eurostat GISCO city data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_source(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("gisco_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_city_name=cached.nearest_city_name,
            nearest_city_distance_km=(
                float(cached.nearest_city_50k_km) if cached.nearest_city_50k_km else None
            ),
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        _log_gisco_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            nearest_city_name=result.nearest_city_name,
            nearest_city_distance_km=result.nearest_city_distance_km,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_gisco_raw(session, connector, site_id, run_id, None, error=str(exc))
        except Exception as log_exc:
            log.warning("gisco_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("gisco_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EurostatGiscoConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
    """Enrich multiple sites with per-site commit isolation."""
    batch = BatchResult(run_id=run_id)
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

    if not connector.data_loaded():
        log.info("gisco_batch_loading_data")
        connector.load_data()

    log.info(
        "gisco_batch_start", run_id=run_id, total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("gisco_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                nearest_city_name=cached.nearest_city_name,
                source=SOURCE_NAME,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            _log_gisco_raw(session, connector, site.site_id, run_id, result)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "gisco_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                nearest_city=result.nearest_city_name,
                distance_km=result.nearest_city_distance_km,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                nearest_city_name=result.nearest_city_name,
                nearest_city_distance_km=result.nearest_city_distance_km,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("gisco_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_gisco_raw(
                    session, connector, site.site_id, run_id,
                    None, error=str(exc),
                )
            except Exception as log_exc:
                log.warning("gisco_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "gisco_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "gisco_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------

def _check_cache(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    ttl_days: int,
) -> SiteRadiological | None:
    """Return cached row if RI-05 data is fresh enough."""
    row = session.get(SiteRadiological, site_id)
    if (
        row
        and row.nearest_city_name is not None
        and row.ri05_quality == "gisco_urau_2021"
        and row.fetched_at
    ):
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get-or-create the DataSource record for Eurostat GISCO."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EurostatGiscoResult,
    run_id: str,
) -> None:
    """Write city proximity data to SiteRadiological (RI-05)."""
    now = datetime.now(timezone.utc)

    ri = session.get(SiteRadiological, site_id)
    if ri is None:
        ri = SiteRadiological(site_id=site_id)
        session.add(ri)

    if result.city_proximity:
        cp = result.city_proximity
        ri.nearest_city_50k_km = cp.nearest_city_distance_km
        ri.nearest_city_name = cp.nearest_city_name
        ri.nearest_city_pop = cp.nearest_city_population
        ri.ri05_quality = "gisco_urau_2021"
        ri.ri05_comment = _build_ri05_comment(result)

    ri.fetched_at = now
    ri.run_id = run_id

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="RI-05", source_type="api",
            observation=result.error,
            impact="negative" if result.nearest_city_name is None else "neutral",
            confidence="low", run_id=run_id,
        ))

    if result.city_proximity and not result.city_proximity.nearest_city_name:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="RI-05", source_type="api",
            observation=(
                "No city with population >50,000 found within 100 km. "
                "Site may be in a very remote area. "
                "Source: Eurostat GISCO Urban Audit 2021."
            ),
            impact="neutral", confidence="medium", run_id=run_id,
        ))


def _build_ri05_comment(result: EurostatGiscoResult) -> str:
    """Build a structured comment for the RI-05 quality column."""
    parts: list[str] = []
    cp = result.city_proximity
    if not cp:
        return "No city proximity data available"

    if cp.nearest_city_name:
        parts.append(
            f"Nearest city >50k: {cp.nearest_city_name} "
            f"({cp.nearest_city_population:,} pop) "
            f"at {cp.nearest_city_distance_km:.1f} km"
        )
    else:
        parts.append("No city >50k within search radius")

    parts.append(f"Cities >50k within 25 km: {cp.cities_within_25km}")
    parts.append(f"Cities >50k within 80 km: {cp.cities_within_80km}")
    parts.append(f"Settlement hierarchy: {cp.settlement_hierarchy}")
    parts.append("Source: Eurostat GISCO Urban Audit 2021 + urb_cpop1")
    return "; ".join(parts)


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write a blocking observation when enrichment fails entirely."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id="RI-05", source_type="api",
        observation=f"Eurostat GISCO enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))


def _log_gisco_raw(
    session: Session,
    connector: EurostatGiscoConnector,
    site_id: uuid.UUID,
    run_id: str,
    result: EurostatGiscoResult | None,
    *,
    error: str | None = None,
) -> None:
    """Persist the per-site GISCO assessment to ``site_raw_responses``.

    Eurostat GISCO does not make a per-site network call: the cities
    catalogue is downloaded once during Phase A and queried locally for
    each site.  We therefore log the assessment payload alongside a digest
    of the loaded catalogue (totals + thresholds) so an auditor can
    reproduce the proximity calculation deterministically.
    """
    cities = getattr(connector, "_cities", None) or []
    threshold = getattr(connector, "_city_min_population", None)
    body: dict[str, Any] = {
        "type": "eurostat_gisco_assessment",
        "catalogue": {
            "gisco_base_url": getattr(connector, "_gisco_base_url", None),
            "eurostat_api_url": getattr(connector, "_eurostat_api_url", None),
            "n_cities_total": len(cities),
            "n_cities_above_threshold": sum(
                1 for c in cities
                if c.population is not None and threshold is not None
                and c.population >= threshold
            ),
            "city_min_population": threshold,
            "city_search_radius_km": getattr(
                connector, "_city_search_radius_km", None,
            ),
        },
    }
    if result is not None:
        body["assessment"] = result.to_dict()
    if error is not None:
        body["error"] = error

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="eurostat_gisco",
        run_id=run_id,
        request_url=getattr(connector, "_eurostat_api_url", "") or SOURCE_URL,
        response_body=body,
        http_status=200 if (result is not None and error is None) else None,
    )
