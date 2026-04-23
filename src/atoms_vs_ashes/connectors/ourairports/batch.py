# man_hours: 2.5
"""Batch enrichment and DB persistence for the OurAirports connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteHumanHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.ourairports.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    AirportProximityResult,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import Site, SiteHumanHazards
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.ourairports.client import OurAirportsConnector

log = get_logger(__name__)


def enrich_site(
    connector: OurAirportsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist airport proximity data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    ensure_data_source(
        session, SOURCE_NAME, SOURCE_URL,
        description=(
            "OurAirports open airport database. Public domain nightly CSV "
            "dumps with global airport coordinates, types, and metadata."
        ),
    )

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("ourairports_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            nearest_airport_km=(
                float(cached.nearest_airport_km)
                if cached.nearest_airport_km is not None else None
            ),
            nearest_airport_name=cached.nearest_airport_name,
            quality=cached.hi01_quality,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(float(site.latitude), float(site.longitude))
        _persist_result(session, site.site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            nearest_airport_km=result.nearest_airport_km,
            nearest_airport_name=result.nearest_airport_name,
            quality=result.quality,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"OurAirports enrichment failed: {exc}",
            run_id=run_id, source_type="bulk_csv",
            impact="negative", confidence="low",
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("ourairports_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: OurAirportsConnector,
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

    # Pre-load the airport index once for the entire batch
    connector.load_index()

    ensure_data_source(
        session, SOURCE_NAME, SOURCE_URL,
        description=(
            "OurAirports open airport database. Public domain nightly CSV "
            "dumps with global airport coordinates, types, and metadata."
        ),
    )

    log.info(
        "ourairports_batch_start",
        run_id=run_id,
        total_sites=len(sites),
        index_airports=connector._index.airport_count if connector._index else 0,
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("ourairports_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
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
                "ourairports_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                nearest_km=(
                    round(result.nearest_airport_km, 1)
                    if result.nearest_airport_km is not None else None
                ),
                violations=result.avoidance_violations,
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                nearest_airport_km=result.nearest_airport_km,
                nearest_airport_name=result.nearest_airport_name,
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("ourairports_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_ID,
                observation=f"OurAirports enrichment failed: {exc}",
                run_id=run_id, source_type="bulk_csv",
                impact="negative", confidence="low",
            )
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 50 == 0:
            log.info(
                "ourairports_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "ourairports_batch_done", run_id=run_id,
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
) -> SiteHumanHazards | None:
    """Return cached row if airport data is fresh enough for this run."""
    row = session.get(SiteHumanHazards, site_id)
    if row and row.hi01_quality is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: AirportProximityResult,
    run_id: str,
) -> None:
    """Write airport proximity data to SiteHumanHazards columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        row = SiteHumanHazards(site_id=site_id)
        session.add(row)

    row.nearest_airport_km = result.nearest_airport_km
    row.nearest_airport_name = result.nearest_airport_name
    row.nearest_airport_type = result.nearest_airport_type
    row.flight_path_distance_km = result.nearest_flight_path_km
    row.airport_count = result.airport_count
    row.hi01_quality = result.quality
    row.hi01_comment = _build_comment(result)
    row.fetched_at = now
    row.run_id = run_id

    if result.avoidance_violations:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=(
                f"Airport avoidance violations: {', '.join(result.avoidance_violations)}. "
                f"Nearest airport: {result.nearest_airport_name} "
                f"({result.nearest_airport_type}) at "
                f"{result.nearest_airport_km:.1f} km."
            ),
            run_id=run_id, source_type="bulk_csv",
            impact="negative", confidence="high",
        )

    if result.quality == "low":
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=(
                "No airports found within 100 km search radius. "
                "This is unusual and may indicate a data gap."
            ),
            run_id=run_id, source_type="bulk_csv",
            impact="neutral", confidence="low",
        )

    if result.error:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"OurAirports enrichment error: {result.error}",
            run_id=run_id, source_type="bulk_csv",
            impact="negative", confidence="low",
        )


def _build_comment(result: AirportProximityResult) -> str:
    """Build human-readable HI-01 comment."""
    parts: list[str] = []

    if result.nearest_airport_km is not None:
        parts.append(
            f"Nearest: {result.nearest_airport_name} "
            f"({result.nearest_airport_type}) at "
            f"{result.nearest_airport_km:.1f} km"
        )
    else:
        parts.append("No airports within search radius")

    if result.nearest_large_airport_km is not None:
        parts.append(f"Nearest large: {result.nearest_large_airport_km:.1f} km")
    if result.nearest_type2_airport_km is not None:
        parts.append(f"Nearest medium: {result.nearest_type2_airport_km:.1f} km")

    parts.append(f"Within 30 km: {result.airport_count}")

    if result.avoidance_violations:
        parts.append(f"Violations: {', '.join(result.avoidance_violations)}")

    parts.append(f"Source: OurAirports; quality: {result.quality}")
    return "; ".join(parts)
