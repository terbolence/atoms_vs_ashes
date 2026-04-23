# man_hours: 2.0
"""Batch enrichment and DB persistence for S-11 NOAA NCEI connector.

Writes to SiteNaturalHazards (NH-10, NH-11, NH-12 columns) and
SiteObservation (rich JSON detail). Each site is committed independently
for isolation; failures on one site do not block others.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.noaa_ncei.models import (
    CONNECTOR_SLUG,
    SOURCE_GHCND,
    SOURCE_GSOM,
    SOURCE_IBTRACS,
    SOURCE_URLS,
    BatchResult,
    NoaaNceiResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.noaa_ncei.client import NoaaNceiConnector

log = get_logger(__name__)

_CRITERION_NH10 = "NH-10"
_CRITERION_NH11 = "NH-11"
_CRITERION_NH12 = "NH-12"


def enrich_site(
    connector: NoaaNceiConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist meteorological hazard data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_sources(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("ncei_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="cached",
            quality=cached.nh10_quality,
            max_wind_ms=(
                float(cached.max_wind_speed_ms)
                if cached.max_wind_speed_ms is not None else None
            ),
            max_precip_mm=(
                float(cached.extreme_precip_mm)
                if cached.extreme_precip_mm is not None else None
            ),
            record_tmax_c=(
                float(cached.extreme_temp_max_c)
                if cached.extreme_temp_max_c is not None else None
            ),
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch_all(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        if connector.last_raw_responses:
            combined = {"api_calls": connector.last_raw_responses}
            log_raw_response(
                session,
                site_id=site_id,
                connector_slug="noaa_ncei",
                run_id=run_id,
                request_url="https://www.ncei.noaa.gov/cdo-web/api/v2/",
                response_body=combined,
            )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "ncei_site_complete",
            site_id=str(site_id),
            site_name=site.name,
            quality=result.quality,
            station=(result.station.name if result.station else None),
            elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="ok",
            quality=result.quality,
            station_name=result.station.name if result.station else None,
            station_distance_km=result.station_distance_km,
            max_wind_ms=(
                result.wind.max_gust_ms if result.wind else None
            ),
            max_precip_mm=(
                result.precipitation.max_daily_precip_mm if result.precipitation else None
            ),
            record_tmax_c=(
                result.temperature.record_tmax_c if result.temperature else None
            ),
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("ncei_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="error",
            error=str(exc),
            elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: NoaaNceiConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
    """Enrich multiple sites with per-site commit isolation and progress logging."""
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

    _ensure_data_sources(session)

    log.info(
        "ncei_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("ncei_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="cached",
                quality=cached.nh10_quality,
                max_wind_ms=(
                    float(cached.max_wind_speed_ms)
                    if cached.max_wind_speed_ms is not None else None
                ),
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch_all(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            if connector.last_raw_responses:
                combined = {"api_calls": connector.last_raw_responses}
                log_raw_response(
                    session,
                    site_id=site.site_id,
                    connector_slug="noaa_ncei",
                    run_id=run_id,
                    request_url="https://www.ncei.noaa.gov/cdo-web/api/v2/",
                    response_body=combined,
                )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "ncei_site_complete",
                site_id=str(site.site_id),
                site_name=site.name,
                index=i + 1,
                total=len(sites),
                quality=result.quality,
                station=(result.station.name if result.station else None),
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="ok",
                quality=result.quality,
                station_name=result.station.name if result.station else None,
                station_distance_km=result.station_distance_km,
                max_wind_ms=result.wind.max_gust_ms if result.wind else None,
                max_precip_mm=(
                    result.precipitation.max_daily_precip_mm
                    if result.precipitation else None
                ),
                record_tmax_c=(
                    result.temperature.record_tmax_c if result.temperature else None
                ),
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("ncei_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="error",
                error=str(exc),
                elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "ncei_batch_progress",
                completed=i + 1,
                total=len(sites),
                succeeded=batch.succeeded,
                failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "ncei_batch_done",
        run_id=run_id,
        total=batch.total_sites,
        succeeded=batch.succeeded,
        failed=batch.failed,
        cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ---------------------------------------------------------------------------
# Cache check
# ---------------------------------------------------------------------------

def _check_cache(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    ttl_days: int,
) -> SiteNaturalHazards | None:
    """Return the cached SiteNaturalHazards row if it's fresh for this run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.fetched_at and row.run_id == run_id:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            if row.nh10_quality is not None or row.nh12_quality is not None:
                return row
    return None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: NoaaNceiResult,
    run_id: str,
) -> None:
    """Write meteorological hazard data to SiteNaturalHazards + SiteObservation."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # NH-10: Extreme winds (max gust), tornadoes, tropical storms
    row.max_wind_speed_ms = (
        result.wind.max_gust_ms if result.wind and result.wind.max_gust_ms else None
    )
    row.nh10_quality = result.quality
    nh10_comment_parts = []
    if result.station:
        nh10_comment_parts.append(
            f"Station: {result.station.name} ({result.station_distance_km:.1f} km away)"
        )
    if result.wind and result.wind.max_gust_ms is not None:
        nh10_comment_parts.append(
            f"Max gust: {result.wind.max_gust_ms:.1f} m/s ({result.wind.source_datatype})"
        )
    if result.tornado and result.tornado.events_per_year is not None:
        nh10_comment_parts.append(
            f"Tornado rate: {result.tornado.events_per_year:.2f}/yr (WT10)"
        )
    if result.tropical_storms:
        nh10_comment_parts.append(
            f"Tropical storms within 500km: {result.tropical_storms.storms_within_500km} "
            f"(IBTrACS v04r01, {result.tropical_storms.analysis_period})"
        )
    if result.quality_notes:
        nh10_comment_parts.append("Quality: " + "; ".join(result.quality_notes[:2]))
    nh10_comment_parts.append(f"Sources: {', '.join(result.sources)}")
    row.nh10_comment = " | ".join(nh10_comment_parts)[:2000]

    # NH-11: Extreme precipitation and hail
    row.extreme_precip_mm = (
        result.precipitation.max_daily_precip_mm
        if result.precipitation and result.precipitation.max_daily_precip_mm is not None
        else None
    )
    row.nh11_quality = result.quality
    nh11_parts = []
    if result.precipitation and result.precipitation.max_daily_precip_mm is not None:
        nh11_parts.append(
            f"Max daily precip: {result.precipitation.max_daily_precip_mm:.1f} mm"
        )
    if result.hail and result.hail.events_per_year is not None:
        nh11_parts.append(f"Hail rate: {result.hail.events_per_year:.2f}/yr (WT05)")
    if result.station:
        nh11_parts.append(f"Station: {result.station.name}")
    nh11_parts.append(f"record_years={result.record_years}")
    row.nh11_comment = " | ".join(nh11_parts)[:2000]

    # NH-12: Temperature extremes
    row.extreme_temp_max_c = (
        result.temperature.record_tmax_c
        if result.temperature and result.temperature.record_tmax_c is not None
        else None
    )
    row.extreme_temp_min_c = (
        result.temperature.record_tmin_c
        if result.temperature and result.temperature.record_tmin_c is not None
        else None
    )
    row.nh12_quality = result.quality
    nh12_parts = []
    if result.temperature:
        if result.temperature.record_tmax_c is not None:
            nh12_parts.append(f"Record TMAX: {result.temperature.record_tmax_c:.1f}°C")
        if result.temperature.record_tmin_c is not None:
            nh12_parts.append(f"Record TMIN: {result.temperature.record_tmin_c:.1f}°C")
    if result.station:
        nh12_parts.append(f"Station: {result.station.name}")
    row.nh12_comment = " | ".join(nh12_parts)[:2000]

    row.fetched_at = now
    row.run_id = run_id

    # Store full JSON in SiteObservation for rich downstream consumption
    full_json = json.dumps(result.to_dict(), default=str)
    session.add(SiteObservation(
        site_id=site_id,
        criterion_id=_CRITERION_NH10,
        source_type="api",
        observation_class="data_json",
        observation=full_json,
        confidence=result.quality,
        run_id=run_id,
    ))

    # Write quality-flag observation if quality is low/insufficient
    if result.quality in ("low", "insufficient") and result.quality_notes:
        session.add(SiteObservation(
            site_id=site_id,
            criterion_id=_CRITERION_NH10,
            source_type="api",
            observation_class="quality_flag",
            observation=(
                f"NOAA NCEI data quality: {result.quality}. "
                + " ".join(result.quality_notes)
            ),
            impact="negative" if result.quality == "insufficient" else "neutral",
            confidence="high",
            run_id=run_id,
        ))


def _persist_error_observation(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    error: str,
) -> None:
    """Write an error observation for a failed NCEI enrichment."""
    session.add(SiteObservation(
        site_id=site_id,
        criterion_id=_CRITERION_NH10,
        source_type="api",
        observation=f"NOAA NCEI enrichment failed: {error}",
        impact="blocking",
        confidence="low",
        run_id=run_id,
    ))


def _ensure_data_sources(session: Session) -> None:
    """Get or create DataSource records for GHCND, GSOM, and IBTrACS."""
    for source_name, url in SOURCE_URLS.items():
        existing = session.query(DataSource).filter_by(name=source_name).first()
        if not existing:
            descriptions = {
                SOURCE_GHCND: (
                    "NOAA NCEI Global Historical Climatology Network – Daily (GHCN-D). "
                    "Daily temperature, precipitation, wind speed, and weather-type "
                    "flag observations from 100,000+ stations worldwide."
                ),
                SOURCE_GSOM: (
                    "NOAA NCEI Global Summary of the Month (GSOM). Pre-computed monthly "
                    "climate statistics including extreme temperature and precipitation."
                ),
                SOURCE_IBTRACS: (
                    "NOAA NCEI International Best Track Archive for Climate Stewardship "
                    "(IBTrACS v04r01). Global tropical cyclone best-track positions, "
                    "including Mediterranean medicanes."
                ),
            }
            session.add(DataSource(
                name=source_name,
                url=url,
                description=descriptions.get(source_name, ""),
                last_fetched=datetime.now(timezone.utc),
            ))
    session.flush()
