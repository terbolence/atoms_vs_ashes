# man_hours: 2.0
"""Batch enrichment and DB persistence for the S-09 GFMS connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.gfms.models import (
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    GfmsResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.gfms.client import GfmsConnector

log = get_logger(__name__)

_NH08_SOURCE_TYPE = "raster"
_NH09_SOURCE_TYPE = "raster"


def enrich_site(
    connector: GfmsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist GFMS flood data for a single DB site."""
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
        log.info("gfms_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            flood_susceptibility=cached.flood_zone_class,
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "gfms_site_complete",
            site_id=str(site_id), site_name=site.name,
            flood_susceptibility=result.flood_susceptibility,
            annual_prob=result.annual_flood_probability,
            pixel_lat=result.pixel_lat, pixel_lon=result.pixel_lon,
            elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            flood_susceptibility=result.flood_susceptibility,
            annual_flood_probability=result.annual_flood_probability,
            source=result.source,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("gfms_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: GfmsConnector,
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

    log.info(
        "gfms_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("gfms_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                flood_susceptibility=cached.flood_zone_class,
                source=SOURCE_NAME,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "gfms_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                flood_susceptibility=result.flood_susceptibility,
                annual_flood_probability=result.annual_flood_probability,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                flood_susceptibility=result.flood_susceptibility,
                annual_flood_probability=result.annual_flood_probability,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("gfms_site_error", site_id=str(site.site_id), error=str(exc))
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
                "gfms_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "gfms_batch_done", run_id=run_id,
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
    """Check if GFMS flood data is already cached for this site+run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.flood_zone_class is not None and row.fetched_at and row.run_id == run_id:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return row
    return None


def _ensure_data_source(session: Session) -> None:
    """Get or create the DataSource record for GFMS."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing is None:
        session.add(DataSource(
            name=SOURCE_NAME,
            url=SOURCE_URL,
            description=(
                "Global Flood Monitoring System (GFMS), University of Maryland ESSIC. "
                "NASA-funded experimental system. Binary flood detection grids at "
                "1/8° (~12 km) resolution, 3-hourly cadence, 2003–present. "
                "DRIVE hydrological model (VIC land surface + DRTR river routing) "
                "driven by GPM IMERG satellite precipitation."
            ),
            last_fetched=datetime.now(timezone.utc),
        ))
        session.flush()


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: GfmsResult,
    run_id: str,
) -> None:
    """Write GFMS flood data to SiteNaturalHazards NH-08 and NH-09 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # NH-09: River flooding (primary output)
    row.flood_zone_class = result.flood_susceptibility
    row.nh09_quality = result.quality
    nh09_parts: list[str] = [
        f"susceptibility={result.flood_susceptibility}",
        f"annual_prob={result.annual_flood_probability:.4f}",
        f"event_count={result.flood_event_count}",
        f"max_intensity={result.max_intensity_mm:.1f}mm",
        f"n_snapshots={result.n_snapshots_analysed}",
        f"period={result.analysis_period[0]}-{result.analysis_period[1]}",
        f"sampling={result.temporal_sampling}",
        f"source={SOURCE_NAME}",
    ]
    if result.dam_break_proxy:
        dbp = result.dam_break_proxy
        if dbp.anomalous_event_flag:
            nh09_parts.append(
                f"dam_break_proxy=anomalous(ratio={dbp.max_anomaly_ratio:.1f})"
            )
    row.nh09_comment = "; ".join(nh09_parts)

    # NH-08: Coastal flood proxy (always quality "low")
    row.nh08_quality = "low"
    if result.coastal_flood_proxy:
        cp = result.coastal_flood_proxy
        row.storm_surge_risk = "fluvial_proxy"
        nh08_comment = (
            f"GFMS coastal proxy: {cp.coastal_flood_events} flood events "
            f"at {result.pixel_lat:.4f}N, {result.pixel_lon:.4f}E "
            f"(coastal_dist≈{cp.coastal_distance_km:.1f}km). "
            "Fluvial signal only — storm surge not modelled."
        )
    else:
        nh08_comment = (
            "GFMS: site is inland (>20 km from coast). "
            "No coastal flood proxy available. "
            "GFMS models fluvial flooding only."
        )
    row.nh08_comment = nh08_comment

    row.fetched_at = now
    row.run_id = run_id

    # SiteObservation for error results
    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type=_NH09_SOURCE_TYPE,
            observation=f"GFMS flood enrichment error: {result.error}",
            impact="negative", confidence="low", run_id=run_id,
        ))

    # SiteObservation for high-susceptibility sites
    if result.flood_susceptibility == "high":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type=_NH09_SOURCE_TYPE,
            observation=(
                f"GFMS high flood susceptibility: annual probability "
                f"{result.annual_flood_probability:.1%}, "
                f"max intensity {result.max_intensity_mm:.0f} mm above threshold. "
                "Supplementary evidence for NH-09 ranking. "
                "Authoritative screening from S-08 EU Flood Risk Maps."
            ),
            impact="negative", confidence=result.quality, run_id=run_id,
        ))

    # SiteObservation for NH-08 (always — notes limitation)
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-08", source_type=_NH08_SOURCE_TYPE,
        observation=(
            "GFMS provides fluvial flood signal only — coastal storm surge, "
            "tsunami, and tidal flooding are not modelled. "
            "NH-08 assessment requires S-08 EU Flood Risk Maps (APSFR) "
            "and national marine agency data (N-05)."
        ),
        impact="neutral", confidence="high", run_id=run_id,
    ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-09", source_type=_NH09_SOURCE_TYPE,
        observation=f"GFMS flood enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
