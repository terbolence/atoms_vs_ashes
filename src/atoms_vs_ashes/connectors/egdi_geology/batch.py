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
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.egdi_geology.models import (
    BatchResult,
    EgdiGeologyResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteNaturalHazards,
    SiteObservation,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.egdi_geology.client import EgdiGeologyConnector

log = get_logger(__name__)

_SOURCE_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "egdi_hike_faults": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI HIKE pan-European fault database — fault proximity and activity",
    ),
    "egdi_lithology": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI surface lithology — soil/rock classification",
    ),
    "egdi_mines": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI mineral occurrences and coal heritage — mining proximity",
    ),
    "egdi_karst": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI karstified zones (CZ, IE) — subsidence hazard",
    ),
    "egdi_bgr_hydrogeology": (
        "https://maps.europe-geology.eu/wfs/",
        "BGR 1:1.5M hydrogeological map — aquifer type and groundwater bodies",
    ),
    "egdi_boreholes": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI geotechnical boreholes — foundation characterization",
    ),
}


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

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("egdi_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            quality=cached.nh02_quality,
            elapsed_ms=elapsed,
        )

    _ensure_data_sources(session)

    try:
        result = connector.fetch_all(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        criteria = _persist_result(session, site_id, result, run_id)
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
        _persist_error_observation(session, site_id, run_id, str(exc))
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

    _ensure_data_sources(session)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(
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
            criteria = _persist_result(
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
    if row and row.nh02_quality is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return row
    return None


def _ensure_data_sources(session: Session) -> dict[str, uuid.UUID]:
    ids: dict[str, uuid.UUID] = {}
    for name, (url, description) in _SOURCE_DESCRIPTIONS.items():
        existing = session.query(DataSource).filter_by(name=name).first()
        if existing:
            ids[name] = existing.source_id
        else:
            ds = DataSource(
                name=name, url=url, description=description,
                last_fetched=datetime.now(timezone.utc),
            )
            session.add(ds)
            session.flush()
            ids[name] = ds.source_id
    return ids


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
) -> list[str]:
    """Write geology data to SiteNaturalHazards + SiteRadiological columns."""
    now = datetime.now(timezone.utc)
    written: list[str] = []

    nh_row = session.get(SiteNaturalHazards, site_id)
    if nh_row is None:
        nh_row = SiteNaturalHazards(site_id=site_id)
        session.add(nh_row)

    # NH-02 — Fault activity
    if result.faults:
        nh_row.nearest_fault_km = result.faults.nearest_fault_distance_km
        if result.faults.nearest_fault_slip_rate_mm_yr is not None:
            nh_row.fault_slip_rate_mm_yr = result.faults.nearest_fault_slip_rate_mm_yr
    nh_row.nh02_quality = "low" if (result.faults is None or result.faults.fault_count_within_buffer == 0) else "medium"
    nh_row.nh02_source = "egdi_hike_faults"
    written.append("NH-02")
    if result.faults is None or result.faults.fault_count_within_buffer == 0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-02", source_type="api",
            observation="No faults found within buffer — site may be outside HIKE coverage",
            impact="neutral", confidence=nh_row.nh02_quality or "low", run_id=run_id,
        ))

    # NH-03 — Soil type (lithology); preserve existing Zhu liquefaction data
    if result.lithology and result.lithology.lithology_class:
        nh_row.soil_type = result.lithology.lithology_class
        if nh_row.liquefaction_suscept is None:
            nh_row.liquefaction_suscept = result.lithology.liquefaction_susceptibility
    egdi_nh03_quality = "low" if (result.lithology is None or result.lithology.lithology_class is None) else "medium"
    # See docs/post_processing/data_curation_methodology.md task 3 — provenance
    # belongs in nh03_source, evidence-confidence in nh03_quality.
    if nh_row.nh03_source is None:
        nh_row.nh03_source = "egdi_lithology"
    if nh_row.nh03_quality is None or nh_row.nh03_quality == "low":
        nh_row.nh03_quality = egdi_nh03_quality
    written.append("NH-03")

    # NH-04 — Slope stability (reuses lithology rock_type)
    if result.lithology and result.lithology.rock_type:
        nh_row.slope_stability_class = result.lithology.rock_type
    nh_row.nh04_quality = egdi_nh03_quality
    written.append("NH-04")

    # NH-05 — Mining history + karst
    if result.mines:
        nh_row.mining_void_present = result.mines.nearest_mine_distance_km is not None
    if result.karst:
        nh_row.karst_present = result.karst.coverage_available and result.karst.in_karst_zone
    nh_row.nh05_quality = "medium"
    written.append("NH-05")
    if result.karst and not result.karst.coverage_available:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-05", source_type="api",
            observation="No EGDI karst data available for this country — S-03 OneGeology or national survey required",
            impact="negative", confidence="low", run_id=run_id,
        ))

    # NH-06 — Foundation (boreholes + hydrogeology)
    if result.boreholes and result.boreholes.nearest_borehole_depth_m is not None:
        nh_row.depth_to_bedrock_m = result.boreholes.nearest_borehole_depth_m
    nh_row.nh06_quality = "low" if (result.boreholes and result.boreholes.borehole_count_within_buffer == 0) else "medium"
    written.append("NH-06")
    if result.boreholes and result.boreholes.borehole_count_within_buffer == 0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-06", source_type="api",
            observation="No EGDI geotechnical boreholes within buffer — limited pilot coverage",
            impact="negative", confidence="low", run_id=run_id,
        ))

    nh_row.fetched_at = now
    nh_row.run_id = run_id

    # RI-03 — Aquifer characteristics → SiteRadiological
    ri_row = session.get(SiteRadiological, site_id)
    if ri_row is None:
        ri_row = SiteRadiological(site_id=site_id)
        session.add(ri_row)
    if result.hydrogeology:
        ri_row.aquifer_type = result.hydrogeology.aquifer_type
    ri_row.ri03_quality = "low" if (result.hydrogeology is None or result.hydrogeology.aquifer_type is None) else "medium"
    ri_row.fetched_at = now
    ri_row.run_id = run_id
    written.append("RI-03")

    if result.quality not in ("high", "medium"):
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-02", source_type="api",
            observation=result.error or f"Quality: {result.quality} — {len(result.layers_with_data)}/{len(result.layers_queried)} layers returned data",
            impact="negative", confidence=result.quality, run_id=run_id,
        ))

    return written


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-02", source_type="api",
        observation=f"Enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
