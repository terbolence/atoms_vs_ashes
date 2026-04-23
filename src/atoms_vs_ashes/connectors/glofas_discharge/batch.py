# man_hours: 2.5
"""Batch enrichment and DB persistence for the GloFAS discharge connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` NS-01 discharge columns.

GloFAS discharge data supplements the HydroRIVERS average discharge with
temporally resolved reanalysis statistics (mean, max, min, percentiles).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.glofas_discharge.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    DischargeResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteInfrastructureV2, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.glofas_discharge.client import GlofasDischargeConnector

log = get_logger(__name__)


def enrich_site(
    connector: GlofasDischargeConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist GloFAS discharge data for a single DB site."""
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
        log.info("glofas_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            mean_discharge_m3s=float(cached.cooling_flow_m3s) if cached.cooling_flow_m3s else None,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            mean_discharge_m3s=result.mean_discharge_m3s,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("glofas_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: GlofasDischargeConnector,
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
        "glofas_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id)
        if cached:
            log.info("glofas_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                mean_discharge_m3s=float(cached.cooling_flow_m3s) if cached.cooling_flow_m3s else None,
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
                "glofas_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                mean_discharge=result.mean_discharge_m3s,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                mean_discharge_m3s=result.mean_discharge_m3s,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("glofas_site_error", site_id=str(site.site_id), error=str(exc))
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
                "glofas_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "glofas_batch_done", run_id=run_id,
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
    """Return cached row if GloFAS discharge data already exists.

    Checks for the GloFAS marker in ns01_comment (not ns01_source,
    since GloFAS no longer overwrites the primary source — see LL-026).
    """
    row = session.get(SiteInfrastructureV2, site_id)
    if row and "GloFAS" in (row.ns01_comment or ""):
        return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for GloFAS."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "GloFAS v4 — Copernicus Emergency Management Service. "
            "Global river discharge reanalysis at 0.05° resolution. "
            "Historical period 1979–present via CDS API."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: DischargeResult,
    run_id: str,
) -> None:
    """Append GloFAS reanalysis discharge as supplementary metadata.

    Per LL-009 and LL-026, HydroRIVERS owns ``cooling_flow_m3s`` (the
    segment-level average discharge).  GloFAS is a 0.05° gridded product
    whose cell value can mis-represent main-channel discharge (LL-020
    spatial-grain mismatch).  We only fall back to GloFAS when
    HydroRIVERS has not yet populated the column.
    """
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    # Only fill cooling_flow_m3s when HydroRIVERS left it empty
    if row.cooling_flow_m3s is None and result.mean_discharge_m3s is not None:
        row.cooling_flow_m3s = result.mean_discharge_m3s
        row.ns01_source = SOURCE_NAME

    discharge_comment = []
    if result.mean_discharge_m3s is not None:
        discharge_comment.append(
            f"GloFAS mean discharge: {result.mean_discharge_m3s:.1f} m³/s"
        )
    if result.q10_discharge_m3s is not None:
        discharge_comment.append(f"Q10={result.q10_discharge_m3s:.1f}")
    if result.q90_discharge_m3s is not None:
        discharge_comment.append(f"Q90={result.q90_discharge_m3s:.1f}")
    discharge_comment.append("Source: GloFAS v4 reanalysis (CDS)")

    comment_str = "; ".join(discharge_comment)

    if row.ns01_comment and "GloFAS" not in row.ns01_comment:
        row.ns01_comment = row.ns01_comment + "; " + comment_str
    elif "GloFAS" in (row.ns01_comment or ""):
        pass  # don't duplicate
    else:
        row.ns01_comment = comment_str

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
            observation=f"GloFAS discharge query note: {result.error}",
            impact="neutral", confidence="low", run_id=run_id,
        ))

    if result.mean_discharge_m3s is not None and result.mean_discharge_m3s < 1.0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
            observation=(
                f"Very low river discharge at nearest grid point "
                f"(mean={result.mean_discharge_m3s:.2f} m³/s from GloFAS reanalysis). "
                f"Insufficient for once-through cooling of most reactor designs."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed discharge enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="raster",
        observation=f"GloFAS discharge enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
