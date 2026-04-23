# man_hours: 2.5
"""Batch enrichment and DB persistence for the WOKAM karst connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.wokam_karst.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    KarstResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.wokam_karst.client import WokamKarstConnector

log = get_logger(__name__)


def enrich_site(
    connector: WokamKarstConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist karst data for a single DB site."""
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
        log.info("wokam_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            karst_present=cached.karst_present,
            karst_severity=cached.karst_severity,
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            karst_present=result.karst_present,
            karst_severity=result.karst_severity,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("wokam_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: WokamKarstConnector,
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
        "wokam_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("wokam_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                karst_present=cached.karst_present,
                karst_severity=cached.karst_severity,
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
                "wokam_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                karst_present=result.karst_present,
                karst_severity=result.karst_severity,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                karst_present=result.karst_present,
                karst_severity=result.karst_severity,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("wokam_site_error", site_id=str(site.site_id), error=str(exc))
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
                "wokam_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "wokam_batch_done", run_id=run_id,
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
    """Return cached row if karst data is fresh enough for this run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.karst_present is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for WOKAM."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "World Karst Aquifer Map (WOKAM) — BGR/IAH Karst Commission. "
            "Global 1:25M karst polygon dataset (2017). "
            "Classifies carbonate and evaporite karst aquifers."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: KarstResult,
    run_id: str,
) -> None:
    """Write karst data to SiteNaturalHazards NH-05 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    row.karst_present = result.karst_present
    row.karst_severity = result.karst_severity
    row.karst_formation_type = result.karst_formation_type
    row.nh05_quality = result.quality
    row.fetched_at = now
    row.run_id = run_id

    comment_parts: list[str] = []
    if result.karst_present:
        comment_parts.append(f"Site within WOKAM karst zone (polygon #{result.nearest_polygon_id})")
        comment_parts.append(f"Formation: {result.karst_formation_type}")
        comment_parts.append(f"Severity: {result.karst_severity}")
    else:
        if result.distance_to_nearest_km is not None:
            comment_parts.append(
                f"Nearest karst zone: {result.distance_to_nearest_km:.1f} km "
                f"(polygon #{result.nearest_polygon_id})"
            )
        else:
            comment_parts.append("No karst zone within search range")
    comment_parts.append("Source: WOKAM v1 (BGR/IAH, 2017), 1:25M scale")
    row.nh05_comment = "; ".join(comment_parts)

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=result.error,
            impact="negative" if not result.karst_present else "neutral",
            confidence="low", run_id=run_id,
        ))

    if result.karst_present and result.karst_severity == "high":
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"Site is within an evaporite/mixed karst zone (WOKAM). "
                f"E-rule E5 applies: evaporite karst with active dissolution "
                f"features is exclusionary (IAEA SSG-35 NH-05, NS-R-3 §3.12–3.14). "
                f"Detailed geotechnical investigation required."
            ),
            impact="negative", confidence="high", run_id=run_id,
        ))
    elif result.karst_present and result.karst_severity == "moderate":
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"Site is within a carbonate karst zone (WOKAM). "
                f"Carbonate karst requires detailed investigation but is not "
                f"automatically exclusionary. Screening-grade assessment only — "
                f"WOKAM is a 1:25M global product."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed karst enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
        observation=f"WOKAM karst enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
