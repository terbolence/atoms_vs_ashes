# man_hours: 1.0
"""Batch enrichment and DB persistence for the BDTICM bedrock connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.bdticm_bedrock.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    BedrockResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.bdticm_bedrock.client import BdticmBedrockConnector

log = get_logger(__name__)


def enrich_site(
    connector: BdticmBedrockConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist depth-to-bedrock for a single DB site."""
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
        log.info("bdticm_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            depth_m=float(cached.depth_to_bedrock_m) if cached.depth_to_bedrock_m else None,
            source=SOURCE_NAME,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        log_raster_extraction(
            session,
            site_id=site_id,
            connector_slug="bdticm_bedrock",
            run_id=run_id,
            source_url=SOURCE_URL,
            extracted_values={
                "depth_cm": result.depth_cm,
                "depth_m": result.depth_m,
            },
            pixel_coords=(float(site.longitude), float(site.latitude)),
            resolution_m=250,
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            depth_m=result.depth_m,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("bdticm_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: BdticmBedrockConnector,
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
            if nh is None or nh.depth_to_bedrock_m is None:
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
                log.info("bdticm_cache_hit", site_id=str(site.site_id))
                batch.skipped_cached += 1
                elapsed_ms = int((time.monotonic() - site_start) * 1000)
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name, status="cached",
                    depth_m=float(cached.depth_to_bedrock_m) if cached.depth_to_bedrock_m else None,
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
                connector_slug="bdticm_bedrock",
                run_id=run_id,
                source_url=SOURCE_URL,
                extracted_values={
                    "depth_cm": result.depth_cm,
                    "depth_m": result.depth_m,
                },
                pixel_coords=(float(site.longitude), float(site.latitude)),
                resolution_m=250,
            )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "bdticm_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                depth_m=result.depth_m,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                depth_m=result.depth_m,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("bdticm_site_error", site_id=str(site.site_id), error=str(exc))
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
                "bdticm_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "bdticm_batch_done", run_id=run_id,
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
    if row and row.depth_to_bedrock_m is not None and row.fetched_at:
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
            "SoilGrids v1 (2017-03) absolute depth to bedrock (BDTICM), 250 m resolution. "
            "Ensemble ML prediction (Random Forest + GBT) from ~2.9 M profile/borehole observations. "
            "Shangguan et al. (2017) J. Adv. Model. Earth Syst., 9, 65-88."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: BedrockResult,
    run_id: str,
) -> None:
    """Write depth-to-bedrock to SiteNaturalHazards NH-06 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # Only overwrite if currently NULL (LL-009 multi-source coordination)
    if result.depth_m is not None and row.depth_to_bedrock_m is None:
        row.depth_to_bedrock_m = result.depth_m

    if result.depth_m is not None:
        if row.nh06_quality is None or row.nh06_quality in ("low", "insufficient"):
            row.nh06_quality = "medium"

    comment = (
        f"DTB: {result.depth_cm} cm ({result.depth_m} m); "
        f"Source: BDTICM 250 m (Shangguan et al. 2017)"
    ) if result.depth_m is not None else f"BDTICM: {result.error}"

    if row.nh06_comment:
        row.nh06_comment = row.nh06_comment + " | BDTICM: " + comment
    else:
        row.nh06_comment = comment

    row.fetched_at = now
    row.run_id = run_id

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
            observation=result.error,
            impact="negative" if result.depth_m is None else "neutral",
            confidence="low", run_id=run_id,
        ))

    if result.depth_m is not None and result.depth_m < 5.0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
            observation=(
                f"Shallow bedrock detected: {result.depth_m} m. "
                f"Excavation difficulties may arise for deep foundations and underground structures. "
                f"Site-specific geotechnical investigation recommended (SSG-9 Rev.1 §4.1–4.12)."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
        observation=f"BDTICM bedrock enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
