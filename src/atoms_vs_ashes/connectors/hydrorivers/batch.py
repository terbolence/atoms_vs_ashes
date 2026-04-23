# man_hours: 2.5
"""Batch enrichment and DB persistence for the HydroRIVERS connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.hydrorivers.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    RiverResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteInfrastructureV2, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.hydrorivers.client import HydroRiversConnector

log = get_logger(__name__)


def enrich_site(
    connector: HydroRiversConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist river data for a single DB site."""
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
        log.info("hydrorivers_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_river_km=float(cached.cooling_distance_km) if cached.cooling_distance_km else None,
            discharge_m3s=float(cached.cooling_flow_m3s) if cached.cooling_flow_m3s else None,
            source_type=cached.cooling_source_type,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            nearest_river_km=result.nearest_river_km,
            discharge_m3s=result.discharge_m3s,
            source_type=result.source_type,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("hydrorivers_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: HydroRiversConnector,
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
        "hydrorivers_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("hydrorivers_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                nearest_river_km=float(cached.cooling_distance_km) if cached.cooling_distance_km else None,
                discharge_m3s=float(cached.cooling_flow_m3s) if cached.cooling_flow_m3s else None,
                source_type=cached.cooling_source_type,
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
                "hydrorivers_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                nearest_river_km=result.nearest_river_km,
                discharge_m3s=result.discharge_m3s,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                nearest_river_km=result.nearest_river_km,
                discharge_m3s=result.discharge_m3s,
                source_type=result.source_type,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("hydrorivers_site_error", site_id=str(site.site_id), error=str(exc))
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
                "hydrorivers_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "hydrorivers_batch_done", run_id=run_id,
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
    """Return cached row if river data is fresh enough for this run."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row and row.cooling_source_type is not None and row.ns01_source == SOURCE_NAME:
        return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for HydroRIVERS."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "HydroRIVERS v10 — WWF/McGill/TNC. "
            "Global river network at 15 arc-second resolution (~500 m). "
            "Includes Strahler order, average discharge, and river connectivity."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: RiverResult,
    run_id: str,
) -> None:
    """Write river data to SiteInfrastructureV2 NS-01 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.cooling_source_type = result.source_type
    # See docs/post_processing/data_curation_methodology.md task 1 — keep the
    # HydroRIVERS reach id available even when the display name has been
    # resolved to a real river name.
    if result.river_id is not None:
        row.cooling_source_hyriv_id = int(result.river_id)
    row.cooling_source_name = result.river_name
    row.cooling_distance_km = result.nearest_river_km
    if result.discharge_m3s is not None:
        row.cooling_flow_m3s = result.discharge_m3s
    row.ns01_source = SOURCE_NAME
    row.ns01_quality = result.quality

    comment_parts: list[str] = []
    if result.nearest_river_km is not None:
        comment_parts.append(
            f"Nearest river: {result.river_name or 'unnamed'} "
            f"at {result.nearest_river_km:.1f} km"
        )
    if result.strahler_order is not None:
        comment_parts.append(f"Strahler order: {result.strahler_order}")
    if result.discharge_m3s is not None:
        comment_parts.append(f"Avg discharge: {result.discharge_m3s:.1f} m³/s")
    if result.cooling_viable:
        comment_parts.append("Cooling-viable (Strahler ≥ 3)")
    else:
        comment_parts.append("Below cooling threshold (Strahler < 3)")
    comment_parts.append("Source: HydroRIVERS v10 (WWF/McGill, 2019)")
    row.ns01_comment = "; ".join(comment_parts)

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=f"HydroRIVERS query note: {result.error}",
            impact="neutral", confidence="low", run_id=run_id,
        ))

    if not result.cooling_viable and result.nearest_river_km is not None:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"No cooling-viable river within {result.nearest_river_km:.1f} km. "
                f"Nearest water body is a {result.source_type or 'stream'} "
                f"(Strahler order {result.strahler_order}). "
                f"Site may require alternative cooling (cooling tower, seawater, lake)."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))

    # LL-022 plausibility guard: large plant matched to low-flow river
    site = session.get(Site, site_id)
    capacity_mw = float(site.installed_capacity_mw) if site and site.installed_capacity_mw else 0.0
    if capacity_mw > 100 and result.discharge_m3s is not None and result.discharge_m3s < 1.0:
        msg = (
            f"Implausible cooling match: {capacity_mw:.0f} MW plant matched to "
            f"river with only {result.discharge_m3s:.2f} m³/s average discharge "
            f"(Strahler {result.strahler_order}). Review nearest-river logic."
        )
        log.warning("hydrorivers_plausibility_guard", site_id=str(site_id), message=msg)
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=msg,
            impact="negative", confidence="high", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed river enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
        observation=f"HydroRIVERS enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
