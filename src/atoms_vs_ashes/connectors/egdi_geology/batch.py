# man_hours: 5.0
"""Batch enrichment and DB persistence for the EGDI geology connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteAttribute`` / ``DataQualityFlag`` tables.

Persists up to six SiteAttribute rows per site:
  NH-02 (faults), NH-03 (lithology/soil), NH-04 (rock type),
  NH-05 (mines + karst), NH-06 (boreholes + hydrogeology), RI-03 (aquifer).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.egdi_geology.models import (
    CRITERION_IDS,
    BatchResult,
    EgdiGeologyResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataQualityFlag, DataSource, Site, SiteAttribute
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


# ------------------------------------------------------------------
# Public entry points
# ------------------------------------------------------------------


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
    if cached is not None:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("egdi_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            quality=cached.value_json.get("quality") if cached.value_json else None,
            elapsed_ms=elapsed,
        )

    source_ids = _ensure_data_sources(session)

    try:
        result = connector.fetch_all(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        criteria = _persist_result(session, site_id, result, run_id, source_ids)
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
        _persist_error_flag(session, site_id, run_id, str(exc))
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
        if cached is not None:
            log.info("egdi_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                quality=cached.value_json.get("quality") if cached.value_json else None,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch_all(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            source_ids = _ensure_data_sources(session)
            criteria = _persist_result(
                session, site.site_id, result, run_id, source_ids,
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
            _persist_error_flag(session, site.site_id, run_id, str(exc))
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
) -> SiteAttribute | None:
    """Check if NH-02 attribute already exists for this site+run."""
    existing = (
        session.query(SiteAttribute)
        .filter_by(site_id=site_id, criterion_id="NH-02", run_id=run_id)
        .first()
    )
    if existing and existing.fetched_at:
        age = datetime.now(timezone.utc) - existing.fetched_at
        if age < timedelta(days=ttl_days):
            return existing
    return None


def _ensure_data_sources(session: Session) -> dict[str, uuid.UUID]:
    """Create or retrieve DataSource records for each EGDI layer group."""
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
    source_ids: dict[str, uuid.UUID],
) -> list[str]:
    """Write up to 6 SiteAttribute rows and quality flags.

    Returns list of criterion IDs that were written.
    """
    now = datetime.now(timezone.utc)
    written: list[str] = []

    # NH-02 — Fault activity
    fault_src = source_ids.get("egdi_hike_faults")
    fault_dist = None
    if result.faults:
        fault_dist = result.faults.nearest_fault_distance_km
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-02",
        value_numeric=fault_dist,
        value_json=result.faults.to_dict() if result.faults else None,
        source_id=fault_src, fetched_at=now, run_id=run_id,
    ))
    written.append("NH-02")
    if result.faults is None or result.faults.fault_count_within_buffer == 0:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="NH-02_faults",
            level="low" if result.faults else "insufficient",
            detail="No faults found within buffer — site may be outside HIKE coverage",
            run_id=run_id,
        ))

    # NH-03 — Soil type (lithology for liquefaction assessment)
    lith_src = source_ids.get("egdi_lithology")
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-03",
        value_text=result.lithology.lithology_class if result.lithology else None,
        value_json=result.lithology.to_dict() if result.lithology else None,
        source_id=lith_src, fetched_at=now, run_id=run_id,
    ))
    written.append("NH-03")
    if result.lithology is None or result.lithology.lithology_class is None:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="NH-03_lithology",
            level="low",
            detail="No lithology data returned from EGDI",
            run_id=run_id,
        ))

    # NH-04 — Soil/rock type (reuses lithology, tagged for slope stability)
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-04",
        value_text=result.lithology.rock_type if result.lithology else None,
        value_json=result.lithology.to_dict() if result.lithology else None,
        source_id=lith_src, fetched_at=now, run_id=run_id,
    ))
    written.append("NH-04")

    # NH-05 — Mining history + karst
    mine_src = source_ids.get("egdi_mines")
    nh05_json: dict[str, Any] = {}
    nh05_numeric: float | None = None
    if result.mines:
        nh05_json["mines"] = result.mines.to_dict()
        nh05_numeric = result.mines.nearest_mine_distance_km
    if result.karst:
        nh05_json["karst"] = result.karst.to_dict()
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-05",
        value_numeric=nh05_numeric,
        value_json=nh05_json or None,
        source_id=mine_src, fetched_at=now, run_id=run_id,
    ))
    written.append("NH-05")
    if result.karst and not result.karst.coverage_available:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="NH-05_karst",
            level="insufficient",
            detail="No EGDI karst data available for this country — S-03 OneGeology or national survey required",
            run_id=run_id,
        ))

    # NH-06 — Foundation (boreholes + hydrogeology)
    bh_src = source_ids.get("egdi_boreholes")
    nh06_json: dict[str, Any] = {}
    if result.boreholes:
        nh06_json["boreholes"] = result.boreholes.to_dict()
    if result.hydrogeology:
        nh06_json["hydrogeology"] = result.hydrogeology.to_dict()
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-06",
        value_json=nh06_json or None,
        source_id=bh_src, fetched_at=now, run_id=run_id,
    ))
    written.append("NH-06")
    if result.boreholes and result.boreholes.borehole_count_within_buffer == 0:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="NH-06_boreholes",
            level="insufficient",
            detail="No EGDI geotechnical boreholes within buffer — limited pilot coverage",
            run_id=run_id,
        ))

    # RI-03 — Aquifer characteristics
    hydro_src = source_ids.get("egdi_bgr_hydrogeology")
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="RI-03",
        value_text=result.hydrogeology.aquifer_type if result.hydrogeology else None,
        value_json=result.hydrogeology.to_dict() if result.hydrogeology else None,
        source_id=hydro_src, fetched_at=now, run_id=run_id,
    ))
    written.append("RI-03")
    if result.hydrogeology is None or result.hydrogeology.aquifer_type is None:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="RI-03_aquifer",
            level="low",
            detail="No aquifer type data returned from BGR hydrogeological map",
            run_id=run_id,
        ))

    # Overall quality flag
    if result.quality not in ("high", "medium"):
        session.add(DataQualityFlag(
            site_id=site_id, dataset="egdi_geology", dimension="completeness",
            level=result.quality,
            detail=result.error or f"Quality: {result.quality} — {len(result.layers_with_data)}/{len(result.layers_queried)} layers returned data",
            run_id=run_id,
        ))

    return written


def _persist_error_flag(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(DataQualityFlag(
        site_id=site_id, dataset="egdi_geology", dimension="availability",
        level="insufficient", detail=f"Enrichment failed: {error}", run_id=run_id,
    ))
