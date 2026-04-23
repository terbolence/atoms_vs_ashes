# man_hours: 3.0
"""Batch enrichment and DB persistence for the GHSL GHS-POP connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteRadiological`` / ``SiteEmergencyPlanning``
/ ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.ghsl_pop.models import (
    CAUTION_POP_DENSITY_5KM,
    CRITERION_IDS,
    SOURCE_DESCRIPTION,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    GhslPopResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteEmergencyPlanning,
    SiteObservation,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.ghsl_pop.client import GhslPopConnector

log = get_logger(__name__)


def enrich_site(
    connector: GhslPopConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist GHSL population data for a single DB site."""
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
        log.info("ghsl_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            pop_density_5km=float(cached.pop_density_5km) if cached.pop_density_5km else None,
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
            pop_density_5km=result.pop_density_5km,
            nearest_city_name=(
                result.nearest_city.name if result.nearest_city else None
            ),
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("ghsl_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: GhslPopConnector,
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
        "ghsl_batch_start", run_id=run_id, total_sites=len(sites),
        expected_api_calls=0,
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("ghsl_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                pop_density_5km=float(cached.pop_density_5km) if cached.pop_density_5km else None,
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
                "ghsl_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                pop_density_5km=result.pop_density_5km,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                pop_density_5km=result.pop_density_5km,
                nearest_city_name=(
                    result.nearest_city.name if result.nearest_city else None
                ),
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("ghsl_site_error", site_id=str(site.site_id), error=str(exc))
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
                "ghsl_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "ghsl_batch_done", run_id=run_id,
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
) -> SiteRadiological | None:
    """Return cached row if population data is fresh enough."""
    row = session.get(SiteRadiological, site_id)
    if row and row.pop_density_5km is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get-or-create the DataSource record for GHSL GHS-POP."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: GhslPopResult,
    run_id: str,
) -> None:
    """Write population data to SiteRadiological and SiteEmergencyPlanning."""
    now = datetime.now(timezone.utc)

    # --- SiteRadiological (RI-04, RI-05, RI-06) ---
    ri = session.get(SiteRadiological, site_id)
    if ri is None:
        ri = SiteRadiological(site_id=site_id)
        session.add(ri)

    ri.pop_density_5km = result.pop_density_5km
    ri.pop_density_16km = result.pop_density_16km
    ri.pop_density_25km = result.pop_density_25km
    ri.pop_density_80km = result.pop_density_80km
    ri.pop_total_5km = result.pop_total_5km
    ri.pop_total_16km = result.pop_total_16km
    ri.pop_total_25km = result.pop_total_25km
    ri.pop_total_80km = result.pop_total_80km
    ri.ri04_quality = "ghsl_pop_100m_r2023a"
    ri.ri04_comment = _build_ri04_comment(result)

    if result.nearest_city:
        ri.nearest_city_50k_km = result.nearest_city.distance_km
        ri.nearest_city_name = result.nearest_city.name
        ri.nearest_city_pop = result.nearest_city.population
        ri.ri05_quality = "ghsl_pop_100m_r2023a"

    if result.pop_growth_rate_pct is not None:
        ri.pop_growth_rate_pct = result.pop_growth_rate_pct
        ri.ri06_quality = "ghsl_pop_100m_r2023a"
        ri.ri06_comment = "CAGR 2020→2030 from GHS-POP R2023A multi-epoch data"

    ri.fetched_at = now
    ri.run_id = run_id

    # --- SiteEmergencyPlanning (EP-01 population component) ---
    ep = session.get(SiteEmergencyPlanning, site_id)
    if ep is None:
        ep = SiteEmergencyPlanning(site_id=site_id)
        session.add(ep)

    pop_5km = result.pop_total_5km
    if pop_5km is not None:
        # EP-01 population score: inverse relationship — lower population = higher score
        # Scale: 0 (very high pop) to 100 (very low pop)
        # Thresholds: <1000 = 100, <5000 = 80, <20000 = 60, <50000 = 40, else 20
        if pop_5km < 1_000:
            ep01_pop_score = 100.0
        elif pop_5km < 5_000:
            ep01_pop_score = 80.0
        elif pop_5km < 20_000:
            ep01_pop_score = 60.0
        elif pop_5km < 50_000:
            ep01_pop_score = 40.0
        else:
            ep01_pop_score = 20.0
        ep.ep01_population_score = ep01_pop_score
        ep.ep01_quality = "ghsl_pop_100m_r2023a"
        ep.ep01_comment = (
            f"Population within 5 km EPZ: {pop_5km:,}. "
            f"Score based on GHSL GHS-POP R2023A 100 m grid."
        )

    ep.fetched_at = now
    ep.run_id = run_id

    # --- SiteObservation for notable findings ---
    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="RI-04", source_type="raster",
            observation=result.error,
            impact="negative" if result.pop_density_5km is None else "neutral",
            confidence="low", run_id=run_id,
        ))

    density_5km = result.pop_density_5km
    if density_5km is not None and density_5km > CAUTION_POP_DENSITY_5KM:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="RI-04", source_type="raster",
            observation=(
                f"Population density within 5 km is {density_5km:.0f} persons/km², "
                f"exceeding CAUTION threshold of {CAUTION_POP_DENSITY_5KM} persons/km². "
                f"A12 avoidance rule triggered. "
                f"Source: GHS-POP R2023A 100 m."
            ),
            impact="negative", confidence="medium", run_id=run_id,
        ))


def _build_ri04_comment(result: GhslPopResult) -> str:
    """Build a structured comment for the RI-04 quality column."""
    parts: list[str] = []
    for ring in result.rings:
        parts.append(
            f"{ring.radius_km} km: {ring.pop_total:,} pop, "
            f"{ring.pop_density:.0f} p/km²"
        )
    parts.append("Epoch: 2020")
    parts.append("Source: GHS-POP R2023A 100 m (Mollweide)")
    return "; ".join(parts)


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write a blocking observation when enrichment fails entirely."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id="RI-04", source_type="raster",
        observation=f"GHSL population enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
