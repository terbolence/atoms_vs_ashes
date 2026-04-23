# man_hours: 2.5
"""Batch enrichment and DB persistence for the EEA Industrial connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteHumanHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.eea_industrial.models import (
    CRITERION_IDS,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    IndustrialProximityResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteHumanHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.eea_industrial.client import EeaIndustrialConnector

log = get_logger(__name__)


def enrich_site(
    connector: EeaIndustrialConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist industrial proximity data for a single DB site."""
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
        log.info("eea_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_seveso_km=float(cached.nearest_seveso_km) if cached.nearest_seveso_km else None,
            nearest_industrial_km=float(cached.nearest_industrial_km) if cached.nearest_industrial_km else None,
            source=SOURCE_NAME, elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code or "",
        )
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            nearest_seveso_km=(
                result.chemical.nearest_facility_km
                if result.chemical and result.chemical.nearest_facility_km is not None
                else None
            ),
            nearest_industrial_km=(
                min(
                    (p.nearest_facility_km for p in [result.chemical, result.toxic, result.fire]
                     if p and p.nearest_facility_km is not None),
                    default=None,
                )
            ),
            nearest_toxic_km=(
                result.toxic.nearest_facility_km
                if result.toxic and result.toxic.nearest_facility_km is not None
                else None
            ),
            quality=result.quality,
            source=result.source,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("eea_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EeaIndustrialConnector,
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
        "eea_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("eea_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                source=SOURCE_NAME, elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code or "",
            )
            _persist_result(session, site.site_id, result, run_id)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "eea_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                quality=result.quality,
                facility_count=result.facility_count_total,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                quality=result.quality, source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("eea_site_error", site_id=str(site.site_id), error=str(exc))
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
                "eea_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "eea_batch_done", run_id=run_id,
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
) -> SiteHumanHazards | None:
    """Return cached row if industrial data is fresh enough for this run."""
    row = session.get(SiteHumanHazards, site_id)
    if row and row.hi02_quality is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for EEA Industrial."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "EEA Industrial Emissions Portal (E-PRTR / IED). "
            "Bulk facility dataset with coordinates, NACE codes, "
            "pollutant transfers, and SEVESO status flags. "
            "Covers EU-27 + EEA member states."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: IndustrialProximityResult,
    run_id: str,
) -> None:
    """Write industrial proximity data to SiteHumanHazards columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        row = SiteHumanHazards(site_id=site_id)
        session.add(row)

    # HI-02: Industrial explosions / chemical proximity
    if result.chemical:
        row.nearest_seveso_km = result.chemical.nearest_facility_km
        nearest_industrial = min(
            (p.nearest_facility_km for p in [result.chemical, result.toxic, result.fire]
             if p and p.nearest_facility_km is not None),
            default=None,
        )
        row.nearest_industrial_km = nearest_industrial

    row.hi02_quality = result.quality
    row.hi02_comment = _build_hi02_comment(result)

    # HI-03: Toxic releases
    if result.toxic:
        row.nearest_toxic_source_km = result.toxic.nearest_facility_km
    row.hi03_quality = result.quality
    row.hi03_comment = _build_hi03_comment(result)

    # HI-04: External fires / flammable storage
    if result.fire:
        row.nearest_flammable_storage_km = result.fire.nearest_facility_km
    row.hi04_quality = result.quality
    row.hi04_comment = _build_hi04_comment(result)

    row.fetched_at = now
    row.run_id = run_id

    # SiteObservation for non-EU countries (coverage gap)
    if result.quality == "insufficient":
        row.hi02_quality = "not_applicable"
        row.hi03_quality = "not_applicable"
        row.hi04_quality = "not_applicable"
        session.add(SiteObservation(
            site_id=site_id, criterion_id="HI-02", source_type="bulk_csv",
            observation=(
                f"E-PRTR/SEVESO register does not cover country {result.country_code}. "
                f"Industrial facility proximity cannot be assessed from EU registers. "
                f"OSM industrial land use may provide partial coverage."
            ),
            impact="negative", confidence="low", run_id=run_id,
        ))

    # SiteObservation for no facilities found in EU country
    if result.quality in ("high", "medium") and result.facility_count_total == 0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="HI-02", source_type="bulk_csv",
            observation=(
                f"No E-PRTR/SEVESO facilities found within {result.search_radius_km:.0f} km. "
                f"This may indicate a genuinely low industrial hazard density "
                f"or a data gap in the E-PRTR register."
            ),
            impact="neutral", confidence="medium", run_id=run_id,
        ))

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="HI-02", source_type="bulk_csv",
            observation=f"EEA industrial enrichment error: {result.error}",
            impact="negative", confidence="low", run_id=run_id,
        ))


def _build_hi02_comment(result: IndustrialProximityResult) -> str:
    """Build human-readable HI-02 comment."""
    parts: list[str] = []
    if result.chemical and result.chemical.nearest_facility_km is not None:
        parts.append(
            f"Nearest chemical/petrochemical: {result.chemical.nearest_facility_name} "
            f"at {result.chemical.nearest_facility_km:.1f} km"
        )
        if result.chemical.nearest_facility_tier:
            parts.append(f"(SEVESO {result.chemical.nearest_facility_tier} tier)")
        parts.append(f"Within 5 km: {result.chemical.count_within_5km}")
        parts.append(f"Within 10 km: {result.chemical.count_within_10km}")
    else:
        parts.append("No chemical/petrochemical facilities within search radius")
    parts.append(f"Source: EEA E-PRTR; quality: {result.quality}")
    return "; ".join(parts)


def _build_hi03_comment(result: IndustrialProximityResult) -> str:
    """Build human-readable HI-03 comment."""
    parts: list[str] = []
    if result.toxic and result.toxic.nearest_facility_km is not None:
        parts.append(
            f"Nearest toxic release source: {result.toxic.nearest_facility_name} "
            f"at {result.toxic.nearest_facility_km:.1f} km"
        )
        parts.append(f"Within 5 km: {result.toxic.count_within_5km}")
    else:
        parts.append("No toxic release sources within search radius")
    parts.append(f"Source: EEA E-PRTR; quality: {result.quality}")
    return "; ".join(parts)


def _build_hi04_comment(result: IndustrialProximityResult) -> str:
    """Build human-readable HI-04 comment."""
    parts: list[str] = []
    if result.fire and result.fire.nearest_facility_km is not None:
        parts.append(
            f"Nearest flammable storage: {result.fire.nearest_facility_name} "
            f"at {result.fire.nearest_facility_km:.1f} km"
        )
        parts.append(f"Within 2 km: {result.fire.count_within_2km}")
        parts.append(f"Within 5 km: {result.fire.count_within_5km}")
    else:
        parts.append("No flammable storage facilities within search radius")
    parts.append(f"Source: EEA E-PRTR; quality: {result.quality}")
    return "; ".join(parts)


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id="HI-02", source_type="bulk_csv",
        observation=f"EEA industrial enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
