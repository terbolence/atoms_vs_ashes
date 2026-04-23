# man_hours: 2.5
"""Batch enrichment and DB persistence for the EFSM20 faults connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.efsm20_faults.models import (
    CRITERION_ID,
    E1_THRESHOLD_KM,
    SEARCH_RADIUS_KM,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    FaultResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.efsm20_faults.client import Efsm20FaultsConnector

log = get_logger(__name__)


def enrich_site(
    connector: Efsm20FaultsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist fault data for a single DB site."""
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
        log.info("efsm20_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_fault_km=float(cached.nearest_fault_km) if cached.nearest_fault_km else None,
            capable_within_8km=(
                cached.nearest_fault_km is not None
                and float(cached.nearest_fault_km) < E1_THRESHOLD_KM
            ),
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
            nearest_fault_km=result.nearest_fault_km,
            capable_within_8km=result.capable_fault_within_8km,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("efsm20_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: Efsm20FaultsConnector,
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
        "efsm20_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("efsm20_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                nearest_fault_km=(
                    float(cached.nearest_fault_km)
                    if cached.nearest_fault_km else None
                ),
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
                "efsm20_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                nearest_fault_km=result.nearest_fault_km,
                capable_within_8km=result.capable_fault_within_8km,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                nearest_fault_km=result.nearest_fault_km,
                capable_within_8km=result.capable_fault_within_8km,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("efsm20_site_error", site_id=str(site.site_id), error=str(exc))
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
                "efsm20_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "efsm20_batch_done", run_id=run_id,
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
    """Return cached row if fault data is fresh enough for this run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.nh02_source == SOURCE_NAME and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for EFSM20."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "European Fault-Source Model 2020 (EFSM20) — EFEHR/INGV. "
            "GeoJSON fault traces with activity class, slip rate, and fault type. "
            "Covers Euro-Mediterranean region. CC BY 4.0."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: FaultResult,
    run_id: str,
) -> None:
    """Write fault data to SiteNaturalHazards NH-02 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    row.nearest_fault_km = result.nearest_fault_km
    row.fault_name = result.fault_name
    row.fault_slip_rate_mm_yr = result.fault_slip_rate_mm_yr
    row.nh02_source = result.source
    row.nh02_quality = result.quality
    row.fetched_at = now
    row.run_id = run_id

    is_no_fault = result.fault_name == "none_in_search_radius"

    comment_parts: list[str] = []
    if is_no_fault:
        comment_parts.append(
            f"No EFSM20 seismogenic faults within {SEARCH_RADIUS_KM:.0f} km "
            f"search radius — site is on a stable tectonic platform"
        )
    elif result.nearest_fault_km is not None:
        comment_parts.append(
            f"Nearest capable fault: {result.nearest_fault_km:.1f} km"
        )
        if result.fault_name:
            comment_parts.append(f"Name: {result.fault_name}")
        if result.fault_activity_class:
            comment_parts.append(f"Activity: {result.fault_activity_class}")
        if result.fault_type:
            comment_parts.append(f"Type: {result.fault_type}")
        if result.fault_slip_rate_mm_yr is not None:
            comment_parts.append(
                f"Slip rate: {result.fault_slip_rate_mm_yr:.2f} mm/yr"
            )
        comment_parts.append(
            f"Total faults within 50 km: {result.faults_within_50km} "
            f"({result.capable_faults_within_50km} capable)"
        )
    else:
        comment_parts.append("No faults found within 50 km search radius")

    comment_parts.append("Source: EFSM20 (EFEHR/INGV, 2022)")
    row.nh02_comment = "; ".join(comment_parts)

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=result.error,
            impact="negative",
            confidence="low", run_id=run_id,
        ))

    if result.capable_fault_within_8km:
        obs_text = (
            f"Capable fault within {E1_THRESHOLD_KM} km (E-rule E1). "
            f"Nearest capable fault: {result.fault_name or 'unnamed'} at "
            f"{result.nearest_fault_km:.1f} km "
            f"(activity: {result.fault_activity_class}). "
        )
        if result.within_rupture_zone:
            obs_text += (
                "Site is within estimated surface rupture zone "
                f"(< {1.0} km from fault trace). "
            )
        obs_text += (
            "IAEA SSG-9 Rev.1 §3.8–3.22: capable faults within 8 km "
            "of a nuclear installation require detailed investigation. "
            "This is a screening-grade assessment; site-specific "
            "paleoseismological studies are required."
        )
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=obs_text,
            impact="negative", confidence="high", run_id=run_id,
        ))
    elif is_no_fault:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"No EFSM20 seismogenic faults within {SEARCH_RADIUS_KM:.0f} km. "
                f"Site is located on a stable tectonic platform with no mapped "
                f"Quaternary-active fault sources. "
                f"E-rule E1 satisfied for fault proximity."
            ),
            impact="positive", confidence="high", run_id=run_id,
        ))
    elif (
        result.nearest_fault_km is not None
        and result.capable_faults_within_50km == 0
    ):
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
            observation=(
                f"No capable (active/possibly active) faults within 50 km. "
                f"Nearest fault of any class: {result.fault_name or 'unnamed'} "
                f"at {result.nearest_fault_km:.1f} km "
                f"(activity: {result.fault_activity_class}). "
                f"E-rule E1 satisfied for fault proximity."
            ),
            impact="positive", confidence="high", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed fault enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="vector",
        observation=f"EFSM20 fault enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
