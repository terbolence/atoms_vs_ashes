# man_hours: 2.0
"""Batch enrichment and DB persistence for the SEVESO III connector.

Delegates to the EEA Industrial batch module for the actual persistence
logic, since both connectors write to the same SiteHumanHazards columns.
The SEVESO connector adds Minerva + national data to the facility index
before running the batch.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.eea_industrial.batch import (
    _build_hi02_comment,
    _build_hi03_comment,
    _build_hi04_comment,
    _check_cache,
    _ensure_data_source as _ensure_eea_data_source,
    _persist_error_observation,
    _persist_result,
)
from atoms_vs_ashes.connectors.seveso.models import (
    MINERVA_SOURCE,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.seveso.client import SevesoConnector

log = get_logger(__name__)


def enrich_site(
    connector: SevesoConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist SEVESO proximity data for a single DB site."""
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
        log.info("seveso_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_seveso_km=float(cached.nearest_seveso_km) if cached.nearest_seveso_km else None,
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
            quality=result.quality,
            source=result.source,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("seveso_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: SevesoConnector,
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
        "seveso_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("seveso_cache_hit", site_id=str(site.site_id))
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
                "seveso_site_complete",
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
            log.error("seveso_site_error", site_id=str(site.site_id), error=str(exc))
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
                "seveso_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "seveso_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Data source helpers
# ------------------------------------------------------------------

def _ensure_data_sources(session: Session) -> None:
    """Get or create DataSource records for SEVESO sources."""
    _ensure_eea_data_source(session)

    for name, url, desc in [
        (
            SOURCE_NAME,
            SOURCE_URL,
            "SEVESO III unified facility database — E-PRTR + JRC Minerva + national registers.",
        ),
        (
            MINERVA_SOURCE,
            "https://minerva.jrc.ec.europa.eu/",
            "JRC Minerva/eNACER SEVESO establishment register. "
            "SEVESO-specific data with upper/lower tier classification.",
        ),
    ]:
        existing = session.query(DataSource).filter_by(name=name).first()
        if not existing:
            session.add(DataSource(
                name=name,
                url=url,
                description=desc,
                last_fetched=datetime.now(timezone.utc),
            ))
    session.flush()
