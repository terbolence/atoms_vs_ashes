# man_hours: 2.0
"""Batch enrichment and DB persistence for the SoilGrids connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.soilgrids.models import (
    CRITERION_IDS,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    SiteEnrichmentSummary,
    SoilGridsResult,
)
from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.soilgrids.client import SoilGridsConnector

log = get_logger(__name__)


def enrich_site(
    connector: SoilGridsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist SoilGrids data for a single DB site."""
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
        log.info("soilgrids_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            soil_type=cached.soil_type,
            bearing_capacity_kpa=float(cached.bearing_capacity_kpa) if cached.bearing_capacity_kpa else None,
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        log_raster_extraction(
            session,
            site_id=site_id,
            connector_slug="soilgrids",
            run_id=run_id,
            source_url=SOURCE_URL,
            extracted_values=result.raw_values or {},
            crs="EPSG:152160",
            resolution_m=250,
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            soil_type=result.soil_type,
            bearing_capacity_kpa=result.bearing_capacity_kpa,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("soilgrids_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: SoilGridsConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    requery_nulls: bool = False,
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

    if requery_nulls:
        null_site_ids = set()
        for site in sites:
            nh = session.get(SiteNaturalHazards, site.site_id)
            if nh is None or nh.soil_type is None:
                null_site_ids.add(site.site_id)
        sites = [s for s in sites if s.site_id in null_site_ids]

    batch.total_sites = len(sites)
    if not sites:
        return batch

    _ensure_data_source(session)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        if not requery_nulls:
            cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
            if cached:
                log.info("soilgrids_cache_hit", site_id=str(site.site_id))
                batch.skipped_cached += 1
                elapsed_ms = int((time.monotonic() - site_start) * 1000)
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name, status="cached",
                    soil_type=cached.soil_type,
                    source=SOURCE_NAME,
                    elapsed_ms=elapsed_ms,
                ))
                continue

        try:
            result = connector.fetch(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            log_raster_extraction(
                session,
                site_id=site.site_id,
                connector_slug="soilgrids",
                run_id=run_id,
                source_url=SOURCE_URL,
                extracted_values=result.raw_values or {},
                crs="EPSG:152160",
                resolution_m=250,
            )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "soilgrids_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                soil_type=result.soil_type,
                bearing_kpa=result.bearing_capacity_kpa,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                soil_type=result.soil_type,
                bearing_capacity_kpa=result.bearing_capacity_kpa,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("soilgrids_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 10 == 0:
            log.info(
                "soilgrids_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "soilgrids_batch_done", run_id=run_id,
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
) -> SiteNaturalHazards | None:
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.soil_type is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "ISRIC SoilGrids v2.0 — global soil property maps at 250 m resolution. "
            "Queried via OGC WCS 2.0.1 for clay/sand/silt/bulk-density. "
            "Soil type classified via USDA texture triangle; bearing capacity "
            "estimated via simplified Terzaghi/Meyerhof correlation."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: SoilGridsResult,
    run_id: str,
) -> None:
    """Write SoilGrids data to SiteNaturalHazards NH-03/NH-06 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # NH-03: soil_type — only overwrite if currently NULL (LL-009 multi-source coordination)
    if result.soil_type and row.soil_type is None:
        row.soil_type = result.soil_type

    # NH-06: bearing_capacity — only overwrite if currently NULL
    if result.bearing_capacity_kpa and row.bearing_capacity_kpa is None:
        row.bearing_capacity_kpa = result.bearing_capacity_kpa

    # Quality: upgrade if we have data, don't downgrade existing.
    # See docs/post_processing/data_curation_methodology.md task 3 — provenance
    # tag goes in nh03_source, the enum stays in nh03_quality.
    if result.soil_type:
        quality = "medium"
        if row.nh03_source is None:
            row.nh03_source = "soilgrids"
        if row.nh03_quality is None or row.nh03_quality in ("low", "insufficient"):
            row.nh03_quality = quality
        if row.nh06_quality is None or row.nh06_quality in ("low", "insufficient"):
            row.nh06_quality = quality

    comment_parts: list[str] = []
    if result.clay_pct is not None:
        comment_parts.append(f"Clay {result.clay_pct:.1f}%, Sand {result.sand_pct:.1f}%, Silt {result.silt_pct:.1f}%")
    if result.soil_type:
        comment_parts.append(f"USDA class: {result.soil_type}")
    if result.bearing_capacity_kpa:
        comment_parts.append(f"Bearing capacity (screening proxy): {result.bearing_capacity_kpa:.0f} kPa")
    if result.bulk_density_gcm3:
        comment_parts.append(f"Bulk density: {result.bulk_density_gcm3:.2f} g/cm³")
    comment_parts.append("Source: ISRIC SoilGrids v2.0 (250 m)")

    if row.nh06_comment:
        row.nh06_comment = row.nh06_comment + " | SoilGrids: " + "; ".join(comment_parts)
    else:
        row.nh06_comment = "; ".join(comment_parts)

    row.fetched_at = now
    row.run_id = run_id

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-03", source_type="wcs",
            observation=result.error,
            impact="negative" if result.soil_type is None else "neutral",
            confidence="low", run_id=run_id,
        ))

    if result.bearing_capacity_kpa and result.bearing_capacity_kpa < 75:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-06", source_type="wcs",
            observation=(
                f"Screening bearing capacity is low ({result.bearing_capacity_kpa:.0f} kPa). "
                f"Site-specific geotechnical investigation required (SSG-9 Rev.1 §4.1–4.12)."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-03", source_type="wcs",
        observation=f"SoilGrids enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
