# man_hours: 4.0
"""Batch enrichment and DB persistence for the WDPA connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` / ``SiteObservation`` /
``ScreeningVerdict`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.wdpa.models import (
    IUCN_STRICT,
    SOURCE_NAME,
    BatchResult,
    SiteEnrichmentSummary,
    WdpaResult,
)
from atoms_vs_ashes.db.models import (
    ScreeningVerdict,
    Site,
    SiteInfrastructureV2,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.wdpa.client import WdpaConnector

log = get_logger(__name__)

CRITERION_ID = "NS-08"
DEFAULT_API_URL = "https://api.protectedplanet.net"


def enrich_site(
    connector: WdpaConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist WDPA data for a single DB site."""
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
        log.info("wdpa_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        _persist_result(session, site_id, result, run_id)
        _persist_screening_verdict(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)

        log.info(
            "wdpa_site_complete",
            site_id=str(site_id), site_name=site.name,
            sensitivity=result.sensitivity_class,
            nearest_km=result.wdpa_nearest_distance_km,
            elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            sensitivity_class=result.sensitivity_class,
            nearest_distance_km=result.wdpa_nearest_distance_km,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"WDPA enrichment failed: {exc}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("wdpa_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: WdpaConnector,
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
        "wdpa_batch_start", run_id=run_id,
        total=batch.total_sites,
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("wdpa_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            _persist_result(session, site.site_id, result, run_id)
            _persist_screening_verdict(session, site.site_id, result, run_id)
            session.commit()

            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "wdpa_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                sensitivity=result.sensitivity_class,
                nearest_km=result.wdpa_nearest_distance_km,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                sensitivity_class=result.sensitivity_class,
                nearest_distance_km=result.wdpa_nearest_distance_km,
                source=result.source, elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("wdpa_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_ID,
                observation=f"WDPA enrichment failed: {exc}",
                run_id=run_id, confidence="low", impact="blocking",
            )
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "wdpa_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "wdpa_batch_done", run_id=run_id,
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
) -> SiteInfrastructureV2 | None:
    """Return cached row if WDPA data is fresh for this run."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None or row.wdpa_quality is None:
        return None
    if row.fetched_at and row.run_id == run_id:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    return ensure_data_source(
        session,
        name=SOURCE_NAME,
        url=DEFAULT_API_URL,
        description=(
            "WDPA Protected Planet REST API v4 — global protected area "
            "polygons for NS-08 ecological sensitivity assessment"
        ),
    )


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: WdpaResult,
    run_id: str,
) -> None:
    """Write WDPA data to SiteInfrastructureV2 WDPA columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.wdpa_nearest_distance_km = result.wdpa_nearest_distance_km
    row.wdpa_overlap = result.wdpa_overlap
    row.wdpa_sensitivity_class = result.sensitivity_class
    row.wdpa_result_json = result.to_dict()
    row.wdpa_quality = result.quality
    row.wdpa_source = SOURCE_NAME
    row.wdpa_comment = result.sensitivity_class
    row.fetched_at = now
    row.run_id = run_id

    if result.quality not in ("high",):
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=result.error or f"WDPA quality: {result.quality}",
            run_id=run_id,
            confidence=result.quality if result.quality != "insufficient" else "low",
            impact=(
                "negative" if result.quality == "low"
                else "blocking" if result.quality == "insufficient"
                else "neutral"
            ),
        )


def _persist_screening_verdict(
    session: Session,
    site_id: uuid.UUID,
    result: WdpaResult,
    run_id: str,
) -> None:
    """Write ScreeningVerdict rows for NS-08 avoidance checks.

    Uses all SMR designs from the database. NS-08 thresholds are
    reactor-independent, so all SMRs get the same verdict.
    """
    from atoms_vs_ashes.db.models import SmrDesign

    smr_designs = session.query(SmrDesign).all()
    if not smr_designs:
        log.warning("wdpa_no_smr_designs", site_id=str(site_id))
        return

    for smr in smr_designs:
        verdict, threshold, justification = _determine_verdict(result)

        measured = (
            f"{result.wdpa_nearest_distance_km:.2f} km"
            if result.wdpa_nearest_distance_km is not None else "N/A"
        )

        existing = (
            session.query(ScreeningVerdict)
            .filter_by(
                site_id=site_id,
                smr_key=smr.smr_key,
                criterion_id=CRITERION_ID,
                prompt_key="wdpa",
                run_id=run_id,
            )
            .first()
        )
        if existing:
            existing.verdict = verdict
            existing.threshold = threshold
            existing.justification = justification
            existing.measured_value = measured
            existing.confidence = result.quality
            existing.data_sources = [SOURCE_NAME]
        else:
            session.add(ScreeningVerdict(
                site_id=site_id,
                smr_key=smr.smr_key,
                criterion_id=CRITERION_ID,
                phase="exclusionary",
                prompt_key="wdpa",
                verdict=verdict,
                measured_value=measured,
                threshold=threshold,
                justification=justification,
                confidence=result.quality,
                data_sources=[SOURCE_NAME],
                run_id=run_id,
            ))


def _determine_verdict(
    result: WdpaResult,
) -> tuple[str, str, str]:
    """Determine screening verdict from WDPA result.

    Returns (verdict, threshold, justification).
    """
    if result.wdpa_overlap:
        overlap_ids = result.wdpa_overlap_ids[:3]
        nearest_cat = result.wdpa_nearest_iucn_category or "unknown"
        nearest_name = result.wdpa_nearest_name or "protected area"
        nearest_desig = result.wdpa_nearest_designation or ""

        if nearest_cat in IUCN_STRICT:
            return (
                "fail",
                "WDPA IUCN Ia/Ib overlap",
                f"Site overlaps with {nearest_name} (IUCN {nearest_cat}): "
                f"strict nature reserve / wilderness area. "
                f"Nuclear construction categorically incompatible.",
            )

        if "Ramsar" in nearest_desig or "World Heritage" in nearest_desig:
            return (
                "fail",
                "International designation overlap",
                f"Site overlaps with {nearest_name} ({nearest_desig}). "
                f"International designation carries highest regulatory protection.",
            )

        return (
            "fail",
            "Protected area overlap",
            f"Site overlaps with {nearest_name} "
            f"({nearest_desig}, IUCN {nearest_cat}). "
            f"Construction within a designated protected area is legally "
            f"incompatible in nearly all jurisdictions.",
        )

    nearest_km = result.wdpa_nearest_distance_km
    if nearest_km is not None and nearest_km < 2.0:
        nearest_cat = result.wdpa_nearest_iucn_category or ""
        nearest_name = result.wdpa_nearest_name or "protected area"

        if nearest_cat in IUCN_STRICT or result.wdpa_international_designation_count > 0:
            return (
                "fail",
                "<2 km from IUCN Ia/Ib or international PA",
                f"Site is {nearest_km:.2f} km from {nearest_name} "
                f"(IUCN {nearest_cat}). Buffer zone for "
                f"strictest-protection areas.",
            )

    if nearest_km is not None:
        return (
            "pass",
            "≥2 km from protected areas",
            f"Nearest protected area ({result.wdpa_nearest_name}) is "
            f"{nearest_km:.1f} km away. "
            f"Sensitivity class: {result.sensitivity_class}.",
        )

    return (
        "pass",
        "No protected areas within 25 km",
        "No WDPA-listed protected areas found within the 25 km search radius.",
    )
