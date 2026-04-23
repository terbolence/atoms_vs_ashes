# man_hours: 2.0
"""Batch enrichment and DB persistence for the S-07 GVP volcanism connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.smithsonian_gvp.models import (
    CRITERION_ID,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    SiteEnrichmentSummary,
    SmithsonianGvpResult,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.smithsonian_gvp.client import SmithsonianGvpConnector

log = get_logger(__name__)


def enrich_site(
    connector: SmithsonianGvpConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist volcanic hazard data for a single DB site."""
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
        log.info("gvp_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            hazard_class=cached.nh07_quality,
            nearest_volcano_km=(
                float(cached.nearest_holocene_volcano_km)
                if cached.nearest_holocene_volcano_km is not None else None
            ),
            nearest_volcano_name=cached.volcano_name,
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
            hazard_class=result.hazard_class,
            nearest_volcano_km=(
                result.nearest_volcano.distance_km
                if result.nearest_volcano else None
            ),
            nearest_volcano_name=(
                result.nearest_volcano.volcano_name
                if result.nearest_volcano else None
            ),
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("gvp_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: SmithsonianGvpConnector,
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
        "gvp_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("gvp_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                nearest_volcano_km=(
                    float(cached.nearest_holocene_volcano_km)
                    if cached.nearest_holocene_volcano_km is not None else None
                ),
                nearest_volcano_name=cached.volcano_name,
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
            nv = result.nearest_volcano
            log.info(
                "gvp_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                hazard_class=result.hazard_class,
                nearest_volcano=(nv.volcano_name if nv else None),
                nearest_km=(round(nv.distance_km, 1) if nv else None),
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                hazard_class=result.hazard_class,
                nearest_volcano_km=(nv.distance_km if nv else None),
                nearest_volcano_name=(nv.volcano_name if nv else None),
                source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("gvp_site_error", site_id=str(site.site_id), error=str(exc))
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
                "gvp_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "gvp_batch_done", run_id=run_id,
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
    """Return cached row if volcano data is fresh enough for this run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.nearest_holocene_volcano_km is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    # Also accept cached "negligible" results where distance is null
    if row and row.nh07_quality is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    """Get or create the DataSource record for GVP VOTW."""
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "Smithsonian Institution Global Volcanism Program — "
            "Volcanoes of the World (VOTW) database. "
            "1,215 Holocene volcanoes, 11,089 eruption records. "
            "WFS from GVP GeoServer."
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: SmithsonianGvpResult,
    run_id: str,
) -> None:
    """Write volcanic hazard data to SiteNaturalHazards NH-07 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    nv = result.nearest_volcano
    row.nearest_holocene_volcano_km = nv.distance_km if nv else None
    row.volcano_name = nv.volcano_name if nv else None
    row.nh07_hazard_class = result.hazard_class
    row.nh07_quality = result.quality
    row.fetched_at = now
    row.run_id = run_id

    # Build structured comment
    comment_parts: list[str] = []
    comment_parts.append(f"hazard_class={result.hazard_class}")
    if nv:
        comment_parts.append(
            f"nearest: {nv.volcano_name} ({nv.distance_km:.1f} km, "
            f"{nv.primary_type}, {nv.country})"
        )
        if nv.last_eruption_year is not None:
            comment_parts.append(f"last eruption: {nv.last_eruption_year}")
        if nv.eruption_stats.max_vei is not None:
            comment_parts.append(f"max VEI: {nv.eruption_stats.max_vei}")
    else:
        comment_parts.append(
            f"No Holocene volcano within {result.search_radius_km} km"
        )
    if result.screening_flags:
        comment_parts.append(f"screening flags: {', '.join(result.screening_flags)}")
    comment_parts.append(f"Source: {result.source} ({result.database_version})")
    row.nh07_comment = "; ".join(comment_parts)

    # Write SiteObservation for significant findings
    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="wfs",
            observation=result.error,
            impact="negative", confidence="low", run_id=run_id,
        ))

    if result.hazard_class == "exclusionary":
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="wfs",
            observation=(
                f"Site is within {EXCLUSION_KM_STR} of Holocene volcano "
                f"{nv.volcano_name} ({nv.distance_km:.1f} km). "
                f"E-rule E7 applies: site within volcanic edifice or "
                f"primary hazard zone (IAEA SSG-21 §3.17–3.24)."
            ) if nv else "Exclusionary volcanic hazard detected.",
            impact="negative", confidence="high", run_id=run_id,
        ))
    elif result.hazard_class == "avoidance" and nv:
        flags_str = ", ".join(result.screening_flags) if result.screening_flags else "avoidance"
        session.add(SiteObservation(
            site_id=site_id, criterion_id=CRITERION_ID, source_type="wfs",
            observation=(
                f"Volcanic avoidance criteria triggered ({flags_str}): "
                f"nearest volcano {nv.volcano_name} at {nv.distance_km:.1f} km"
                f"{f', max VEI {nv.eruption_stats.max_vei}' if nv.eruption_stats.max_vei else ''}. "
                f"Detailed volcanic hazard assessment required."
            ),
            impact="negative", confidence="high", run_id=run_id,
        ))


EXCLUSION_KM_STR = "5 km"


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    """Write an error observation for a failed GVP enrichment."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id=CRITERION_ID, source_type="wfs",
        observation=f"GVP volcanism enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
