# man_hours: 5.0
"""Batch enrichment and DB persistence for the EGDI geology connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteRadiological`` /
``SiteObservation`` tables.

Persists geology data to domain table columns:
  NH-02 (faults), NH-03 (lithology/soil), NH-04 (rock type),
  NH-05 (mines + karst), NH-06 (boreholes + hydrogeology),
  RI-03 (aquifer).
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.egdi_geology.models import (
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.egdi_geology.persistence import (
    check_cache,
    ensure_data_sources,
    persist_error_observation,
    persist_result,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.egdi_geology.client import EgdiGeologyConnector

log = get_logger(__name__)

_check_cache = check_cache
_ensure_data_sources = ensure_data_sources
_persist_result = persist_result
_persist_error_observation = persist_error_observation


def enrich_site(
    connector: EgdiGeologyConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist geology data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()

    cached = check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("egdi_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            quality=cached.nh02_quality,
            elapsed_ms=elapsed,
        )

    ensure_data_sources(session)

    try:
        result = connector.fetch_all(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        criteria = persist_result(session, site_id, result, run_id)
        if connector.last_raw_responses:
            combined = {"layers": connector.last_raw_responses}
            log_raw_response(
                session,
                site_id=site_id,
                connector_slug="egdi_geology",
                run_id=run_id,
                request_url=connector._wfs_url,
                response_body=combined,
            )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "egdi_site_complete", site_id=str(site_id), site_name=site.name,
            quality=result.quality, criteria_count=len(criteria), elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            criteria_written=criteria, quality=result.quality, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("egdi_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EgdiGeologyConnector,
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

    ensure_data_sources(session)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = check_cache(
            session, site.site_id, run_id, connector._cache_ttl_days,
        )
        if cached:
            log.info("egdi_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                quality=cached.nh02_quality,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch_all(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            criteria = persist_result(
                session, site.site_id, result, run_id,
            )
            if connector.last_raw_responses:
                combined = {"layers": connector.last_raw_responses}
                log_raw_response(
                    session,
                    site_id=site.site_id,
                    connector_slug="egdi_geology",
                    run_id=run_id,
                    request_url=connector._wfs_url,
                    response_body=combined,
                )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "egdi_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                quality=result.quality, criteria_count=len(criteria),
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                criteria_written=criteria, quality=result.quality,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("egdi_site_error", site_id=str(site.site_id), error=str(exc))
            persist_error_observation(session, site.site_id, run_id, str(exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "egdi_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

        time.sleep(connector._inter_request_delay)

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "egdi_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


