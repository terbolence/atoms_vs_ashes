# man_hours: 3.0
"""Batch enrichment and DB persistence for the Copernicus DEM connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``Site.elevation_m``, ``SiteNaturalHazards``
(NH-04 columns), and ``SiteInfrastructureV2`` (NS-04 columns).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.copernicus_dem.models import (
    PRIMARY_CRITERION,
    SLOPE_CAUTION_DEG,
    SLOPE_FAIL_DEG,
    SOURCE_DESCRIPTION,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    DemResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteObservation,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.copernicus_dem.client import CopernicusDemConnector

log = get_logger(__name__)


def enrich_site(
    connector: CopernicusDemConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist DEM data for a single DB site."""
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
        log.info("dem_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elevation_m=float(site.elevation_m) if site.elevation_m is not None else None,
            max_slope_deg=float(cached.slope_angle_deg) if cached.slope_angle_deg is not None else None,
            slope_class=cached.slope_stability_class,
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site, result, run_id)
        log_raster_extraction(
            session,
            site_id=site_id,
            connector_slug="copernicus_dem",
            run_id=run_id,
            source_url=SOURCE_URL,
            extracted_values={
                "elevation_m": result.elevation.site_elevation_m,
                "slope_max_deg": result.slope.max_deg,
                "slope_mean_deg": result.slope.mean_deg,
                "slope_stability_class": result.slope_stability_class,
            },
            pixel_coords=(float(site.longitude), float(site.latitude)),
            resolution_m=30,
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            elevation_m=result.elevation.site_elevation_m,
            max_slope_deg=result.slope.max_deg,
            slope_class=result.slope_stability_class,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("dem_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: CopernicusDemConnector,
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

    _ensure_data_source(session)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("dem_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elevation_m=float(site.elevation_m) if site.elevation_m is not None else None,
                max_slope_deg=float(cached.slope_angle_deg) if cached.slope_angle_deg is not None else None,
                slope_class=cached.slope_stability_class,
                source=SOURCE_NAME,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(float(site.latitude), float(site.longitude))
            _persist_result(session, site, result, run_id)
            log_raster_extraction(
                session,
                site_id=site.site_id,
                connector_slug="copernicus_dem",
                run_id=run_id,
                source_url=SOURCE_URL,
                extracted_values={
                    "elevation_m": result.elevation.site_elevation_m,
                    "slope_max_deg": result.slope.max_deg,
                    "slope_mean_deg": result.slope.mean_deg,
                    "slope_stability_class": result.slope_stability_class,
                },
                pixel_coords=(float(site.longitude), float(site.latitude)),
                resolution_m=30,
            )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "dem_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                elevation_m=result.elevation.site_elevation_m,
                max_slope_deg=result.slope.max_deg,
                slope_class=result.slope_stability_class,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                elevation_m=result.elevation.site_elevation_m,
                max_slope_deg=result.slope.max_deg,
                slope_class=result.slope_stability_class,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("dem_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "dem_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "dem_batch_done", run_id=run_id,
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
    """Return cached NH row if slope data exists and is fresh."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.slope_angle_deg is not None and row.fetched_at:
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
        description=SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site: Site,
    result: DemResult,
    run_id: str,
) -> None:
    """Write DEM data to Site, SiteNaturalHazards, and SiteInfrastructureV2."""
    now = datetime.now(timezone.utc)

    # Update Site.elevation_m
    if result.elevation.site_elevation_m is not None:
        site.elevation_m = result.elevation.site_elevation_m

    # SiteNaturalHazards — NH-04 columns
    nh = session.get(SiteNaturalHazards, site.site_id)
    if nh is None:
        nh = SiteNaturalHazards(site_id=site.site_id)
        session.add(nh)

    nh.slope_angle_deg = result.slope.mean_deg
    nh.nh04_dem_cog_slope_max_deg = result.slope.max_deg
    nh.slope_stability_class = result.slope_stability_class
    nh.nh04_quality = "copernicus_dem_30m"
    nh.fetched_at = now
    nh.run_id = run_id

    comment_parts: list[str] = []
    elev = result.elevation
    if elev.site_elevation_m is not None:
        comment_parts.append(f"Elevation: {elev.site_elevation_m:.1f} m")
    if elev.min_m is not None and elev.max_m is not None:
        comment_parts.append(
            f"Range: {elev.min_m:.1f}–{elev.max_m:.1f} m "
            f"(relief {elev.relief_m:.1f} m)"
        )
    sl = result.slope
    if sl.mean_deg is not None:
        comment_parts.append(
            f"Slope: mean={sl.mean_deg:.1f}° max={sl.max_deg:.1f}° "
            f"p95={sl.p95_deg:.1f}°"
        )
    if sl.pct_above_15 is not None:
        comment_parts.append(f"{sl.pct_above_15:.1f}% > 15°, {sl.pct_above_30:.1f}% > 30°")
    tri = result.tri
    if tri.mean_tri is not None:
        comment_parts.append(f"TRI: mean {tri.mean_tri:.1f}, class {tri.tri_class}")
    comment_parts.append("Source: Copernicus DEM GLO-30 (30 m, EGM2008)")
    comment_parts.append("Note: DSM (includes canopy); conservative for slope stability")
    nh.nh04_comment = "; ".join(comment_parts)

    # SiteInfrastructureV2 — NS-04 columns (terrain suitability)
    infra = session.get(SiteInfrastructureV2, site.site_id)
    if infra is None:
        infra = SiteInfrastructureV2(site_id=site.site_id)
        session.add(infra)

    infra.ns04_quality = "copernicus_dem_30m"
    ns04_parts: list[str] = []
    if elev.std_m is not None:
        ns04_parts.append(f"Elevation std: {elev.std_m:.1f} m (earthworks proxy)")
    if sl.mean_deg is not None:
        ns04_parts.append(f"Mean slope: {sl.mean_deg:.1f}° (grading effort proxy)")
    if tri.mean_tri is not None:
        ns04_parts.append(f"TRI: {tri.mean_tri:.1f} ({tri.tri_class})")
    ns04_parts.append("Source: Copernicus DEM GLO-30")
    infra.ns04_comment = "; ".join(ns04_parts)

    # Observations for notable conditions
    if result.error:
        session.add(SiteObservation(
            site_id=site.site_id, criterion_id=PRIMARY_CRITERION,
            source_type="raster",
            observation=result.error,
            impact="negative" if result.slope.mean_deg is None else "neutral",
            confidence="low", run_id=run_id,
        ))

    if sl.mean_deg is not None and sl.mean_deg > SLOPE_FAIL_DEG:
        session.add(SiteObservation(
            site_id=site.site_id, criterion_id=PRIMARY_CRITERION,
            source_type="raster",
            observation=(
                f"Mean slope within 1 km buffer is {sl.mean_deg:.1f}° (> {SLOPE_FAIL_DEG}° threshold). "
                f"Max slope {sl.max_deg:.1f}°. "
                f"E-rule E3: FAIL — massive slope instability risk. "
                f"{sl.pct_above_30:.1f}% of terrain exceeds 30°. "
                f"Site-specific geotechnical investigation required (SSG-35 Table I-1 NH-04)."
            ),
            impact="blocking", confidence="high", run_id=run_id,
        ))
    elif sl.mean_deg is not None and sl.mean_deg > SLOPE_CAUTION_DEG:
        session.add(SiteObservation(
            site_id=site.site_id, criterion_id=PRIMARY_CRITERION,
            source_type="raster",
            observation=(
                f"Mean slope within 1 km buffer is {sl.mean_deg:.1f}° (> {SLOPE_CAUTION_DEG}° threshold). "
                f"Max slope {sl.max_deg:.1f}°. "
                f"E-rule E3: CAUTION — significant slope within nuclear island footprint. "
                f"{sl.pct_above_15:.1f}% of terrain exceeds 15°. "
                f"Detailed slope stability analysis recommended."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id=PRIMARY_CRITERION, source_type="raster",
        observation=f"DEM enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
