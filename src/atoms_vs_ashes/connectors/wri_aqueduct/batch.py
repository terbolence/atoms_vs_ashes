# man_hours: 2.0
"""Batch enrichment and DB persistence for the WRI Aqueduct connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` NS-01 water stress columns.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.wri_aqueduct.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    WaterStressResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteInfrastructureV2, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.wri_aqueduct.client import WriAqueductConnector

log = get_logger(__name__)


def enrich_site(
    connector: WriAqueductConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist water stress data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_source(session)

    cached = _check_cache(session, site_id)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("aqueduct_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            water_stress_label=cached.water_stress_label,
            water_stress_score=float(cached.water_stress_score) if cached.water_stress_score else None,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            water_stress_label=result.water_stress_label,
            water_stress_score=result.water_stress_score,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("aqueduct_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: WriAqueductConnector,
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
        "aqueduct_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id)
        if cached:
            log.info("aqueduct_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                water_stress_label=cached.water_stress_label,
                water_stress_score=float(cached.water_stress_score) if cached.water_stress_score else None,
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
                "aqueduct_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                water_stress=result.water_stress_label,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                water_stress_label=result.water_stress_label,
                water_stress_score=result.water_stress_score,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("aqueduct_site_error", site_id=str(site.site_id), error=str(exc))
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
                "aqueduct_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "aqueduct_batch_done", run_id=run_id,
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
) -> SiteInfrastructureV2 | None:
    """Return cached row if water stress data already exists.

    "No Data" labels from a previous failed GDB load are *not* treated
    as cached — they must be re-queried now that GDB loading is fixed.
    """
    row = session.get(SiteInfrastructureV2, site_id)
    if row and row.water_stress_label is not None and row.water_stress_label != "No Data":
        return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for WRI Aqueduct."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "WRI Aqueduct 4.0 — World Resources Institute. "
            "Global water stress indicators at catchment level. "
            "Baseline water stress, depletion, and variability (2023)."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: WaterStressResult,
    run_id: str,
) -> None:
    """Write water stress data to SiteInfrastructureV2 columns."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.water_stress_score = result.water_stress_score
    row.water_stress_label = result.water_stress_label

    # Append water stress info to ns01_comment without overwriting river data
    stress_comment = (
        f"Water stress: {result.water_stress_label}"
        f" (score={result.water_stress_score:.3f})"
        if result.water_stress_score is not None
        else f"Water stress: {result.water_stress_label}"
    )
    if result.water_depletion is not None:
        stress_comment += f"; Depletion={result.water_depletion:.3f}"
    stress_comment += f"; Source: WRI Aqueduct 4.0 (2023)"

    if row.ns01_comment and SOURCE_NAME not in (row.ns01_source or ""):
        row.ns01_comment = row.ns01_comment + "; " + stress_comment
    else:
        row.ns01_comment = stress_comment

    if result.water_stress_label in ("High", "Extremely High"):
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"Site is in a {result.water_stress_label.lower()} water stress "
                f"catchment (WRI Aqueduct score={result.water_stress_score:.3f}). "
                f"Cooling water availability may be constrained; "
                f"competing demand from agriculture/industry is significant."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=f"WRI Aqueduct query note: {result.error}",
            impact="neutral", confidence="low", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed water stress enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
        observation=f"WRI Aqueduct enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
