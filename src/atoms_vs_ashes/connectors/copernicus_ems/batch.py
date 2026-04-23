# man_hours: 3.0
"""Batch enrichment and DB persistence for the Copernicus EMS connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.copernicus_ems.models import (
    CRITERION_IDS,
    SOURCE_COMBINED,
    SOURCE_RAPID,
    SOURCE_RRM,
    BatchResult,
    FlashFloodAssessment,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.copernicus_ems.client import CopernicusEmsConnector

log = get_logger(__name__)


def enrich_site(
    connector: CopernicusEmsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Assess and persist flash flood data for a single DB site."""
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
        log.info("ems_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            source=SOURCE_COMBINED,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.assess_site(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        _log_ems_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)

        status = "ok" if result.susceptibility is not None else "no_data"
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status=status,
            susceptibility=result.susceptibility,
            n_events=result.n_events_within_buffer,
            source=result.source,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_ems_raw(session, connector, site_id, run_id, None, error=str(exc))
        except Exception as log_exc:
            log.warning("ems_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("ems_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: CopernicusEmsConnector,
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

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("ems_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                source=SOURCE_COMBINED,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.assess_site(
                float(site.latitude), float(site.longitude),
            )
            _persist_result(session, site.site_id, result, run_id)
            _log_ems_raw(session, connector, site.site_id, run_id, result)
            session.commit()

            if result.susceptibility is not None:
                batch.succeeded += 1
                status = "ok"
            else:
                batch.no_data += 1
                status = "no_data"

            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "ems_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                susceptibility=result.susceptibility,
                n_events=result.n_events_within_buffer,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status=status,
                susceptibility=result.susceptibility,
                n_events=result.n_events_within_buffer,
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("ems_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_ems_raw(session, connector, site.site_id, run_id, None, error=str(exc))
            except Exception as log_exc:
                log.warning("ems_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "ems_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                no_data=batch.no_data,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "ems_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        no_data=batch.no_data,
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
    """Check if NH-09 EMS data is already cached for this site+run.

    Uses nh09_comment containing 'cems' as the cache indicator since
    the flood_zone_class column is shared with S-08 EU Flood Risk.
    """
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.nh09_comment and "cems" in row.nh09_comment.lower() and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> None:
    """Ensure DataSource provenance record exists."""
    existing = session.query(DataSource).filter_by(name=SOURCE_COMBINED).first()
    if existing is None:
        session.add(DataSource(
            name=SOURCE_COMBINED,
            url="https://emergency.copernicus.eu/",
            description=(
                "Copernicus Emergency Management Service — "
                "RRM + Rapid Mapping flood activation catalogue. "
                "Flash flood susceptibility derived from historical activation footprints."
            ),
            last_fetched=datetime.now(timezone.utc),
        ))
        session.flush()


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: FlashFloodAssessment,
    run_id: str,
) -> None:
    """Write flash flood data to SiteNaturalHazards NH-09 columns.

    Appends CEMS data to existing NH-09 comment rather than overwriting,
    since S-08 EU Flood Risk may have already written to this row.
    """
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # NH-09: Append flash flood data (don't overwrite S-08 data)
    nh09_parts: list[str] = []
    if row.nh09_comment:
        nh09_parts.append(row.nh09_comment)
    nh09_parts.append(f"CEMS flash flood: {result.susceptibility or 'no_data'}")
    if result.n_events_within_buffer > 0:
        nh09_parts.append(f"Events within {50}km: {result.n_events_within_buffer}")
    if result.distance_to_nearest_km is not None:
        nh09_parts.append(f"Nearest activation: {result.distance_to_nearest_km:.1f} km")
    row.nh09_comment = "; ".join(nh09_parts)

    # NH-08: Coastal proxies
    nh08_parts: list[str] = []
    if row.nh08_comment:
        nh08_parts.append(row.nh08_comment)
    if result.nh08_seiche_proxy:
        nh08_parts.append(f"CEMS seiche proxy: {result.nh08_seiche_proxy}")
    if result.nh08_tidal_proxy:
        nh08_parts.append(f"CEMS tidal proxy: {result.nh08_tidal_proxy}")
    if result.nh08_wave_proxy:
        nh08_parts.append(f"CEMS wave proxy: {result.nh08_wave_proxy}")
    if nh08_parts and not row.nh08_comment:
        nh08_parts.append("Priority 2 proxy — national marine agency data (N-05) is authoritative")
    if nh08_parts:
        row.nh08_comment = "; ".join(nh08_parts)

    row.fetched_at = now
    row.run_id = run_id

    # SiteObservation for quality tracking
    if result.quality == "insufficient":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="api",
            observation=(
                f"No Copernicus EMS flood activation data within "
                f"{50} km. Flash flood susceptibility cannot be "
                f"assessed from this source. "
                f"S-08 EU Flood Risk Maps and S-09 GFMS provide "
                f"complementary flood data."
            ),
            impact="neutral", confidence="low", run_id=run_id,
        ))

    if result.susceptibility == "high":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="api",
            observation=(
                f"Site intersects or is very close to a historical "
                f"Copernicus EMS flood activation footprint "
                f"({result.nearest_activation_code}). "
                f"Flash flood susceptibility classified as HIGH. "
                f"IAEA NS-G-3.5 §3.10–3.18 requires flash flood assessment."
            ),
            impact="negative", confidence="high", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-09", source_type="api",
        observation=f"Copernicus EMS enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))


def _log_ems_raw(
    session: Session,
    connector: CopernicusEmsConnector,
    site_id: uuid.UUID,
    run_id: str,
    result: FlashFloodAssessment | None,
    *,
    error: str | None = None,
) -> None:
    """Persist the per-site EMS assessment to ``site_raw_responses``.

    Copernicus EMS does not make a per-site network call: each site is
    assessed locally against the in-memory catalogue ingested by Phase A.
    The raw response we persist is therefore the assessment payload plus a
    catalogue digest (URLs + counts) that lets an auditor reproduce the
    decision deterministically.
    """
    body: dict[str, Any] = {
        "type": "copernicus_ems_assessment",
        "catalogue": {
            "rrm_api_url": getattr(connector, "_rrm_api_url", None),
            "rapid_api_url": getattr(connector, "_rapid_api_url", None),
            "n_rrm": len(getattr(connector, "_rrm_activations", []) or []),
            "n_rapid": len(getattr(connector, "_rapid_activations", []) or []),
            "n_centroids": len(getattr(connector, "_footprint_centroids", []) or []),
            "site_buffer_km": getattr(connector, "_site_buffer_km", None),
            "categories": getattr(connector, "_categories", None),
        },
    }
    if result is not None:
        body["assessment"] = {
            "lat": result.lat,
            "lon": result.lon,
            "susceptibility": result.susceptibility,
            "distance_to_nearest_km": result.distance_to_nearest_km,
            "n_events_within_buffer": result.n_events_within_buffer,
            "nearest_activation_code": result.nearest_activation_code,
            "nearest_activation_date": (
                str(result.nearest_activation_date)
                if result.nearest_activation_date is not None else None
            ),
            "footprints_intersecting": [
                {
                    "activation_code": fp.activation_code,
                    "activation_date": str(fp.activation_date) if fp.activation_date else None,
                    "distance_km": fp.distance_km,
                    "category": fp.category,
                }
                for fp in (result.footprints_intersecting or [])
            ],
            "source": result.source,
            "quality": result.quality,
            "error": result.error,
        }
    if error is not None:
        body["error"] = error

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="copernicus_ems",
        run_id=run_id,
        request_url=getattr(connector, "_rrm_api_url", "") or "",
        response_body=body,
        http_status=200 if (result is not None and error is None) else None,
    )
