# man_hours: 3.0
"""Batch enrichment and DB persistence for the EU Flood Risk connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.eu_flood_risk.models import (
    CRITERION_IDS,
    SOURCE_APSFR,
    SOURCE_COMBINED,
    SOURCE_GLOFAS,
    BatchResult,
    EuFloodRiskResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.eu_flood_risk.client import EuFloodRiskConnector

log = get_logger(__name__)


def enrich_site(
    connector: EuFloodRiskConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist flood risk data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_sources(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("flood_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            hazard_class=cached.flood_zone_class,
            source=cached.nh09_quality,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        _persist_result(session, site_id, result, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            hazard_class=result.hazard_class,
            depth_rp100_m=result.flood_depth.depth_rp100_m,
            source=SOURCE_COMBINED,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("flood_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EuFloodRiskConnector,
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

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("flood_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                hazard_class=cached.flood_zone_class,
                source=cached.nh09_quality,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            _persist_result(session, site.site_id, result, run_id)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "flood_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                hazard_class=result.hazard_class,
                depth_rp100=result.flood_depth.depth_rp100_m,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                hazard_class=result.hazard_class,
                depth_rp100_m=result.flood_depth.depth_rp100_m,
                source=SOURCE_COMBINED,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("flood_site_error", site_id=str(site.site_id), error=str(exc))
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
                "flood_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "flood_batch_done", run_id=run_id,
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
    """Check if NH-09 flood data is already cached for this site+run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.flood_zone_class is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
    return None


def _ensure_data_sources(session: Session) -> None:
    """Ensure DataSource provenance records exist for JRC and EEA."""
    for name, url, desc in [
        (
            SOURCE_GLOFAS,
            "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/",
            "JRC/GloFAS Global River Flood Hazard Maps v2.1.2 — "
            "flood water depth at 7 return periods (10–500 yr), ~90 m resolution",
        ),
        (
            SOURCE_APSFR,
            "https://sdi.eea.europa.eu/webdav/datastore/public/eea_v_4326_100_k_floods-ref-data-under-fd_p_2011-now_v03_r00/",
            "EEA Floods Directive Reference Spatial Dataset v3.0 — "
            "Areas of Potential Significant Flood Risk (APSFR) polygons",
        ),
    ]:
        existing = session.query(DataSource).filter_by(name=name).first()
        if existing is None:
            session.add(DataSource(
                name=name, url=url, description=desc,
                last_fetched=datetime.now(timezone.utc),
            ))
            session.flush()


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EuFloodRiskResult,
    run_id: str,
) -> None:
    """Write flood data to SiteNaturalHazards NH-08 and NH-09 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    # NH-08: Coastal flooding
    coastal_apsfr = [a for a in result.apsfr if a.source_type == "coastal"]
    if coastal_apsfr:
        row.storm_surge_risk = coastal_apsfr[0].probability_scenario
    row.nh08_quality = result.quality
    nh08_parts: list[str] = []
    if result.coastal_flood_assessed:
        nh08_parts.append(f"Coastal APSFR: {len(coastal_apsfr)} designation(s)")
    else:
        nh08_parts.append("No coastal APSFR data (JRC/GloFAS covers riverine only)")
    nh08_parts.append(f"Sources: {', '.join(result.sources)}")
    row.nh08_comment = "; ".join(nh08_parts)

    # NH-09: River flooding
    row.flood_zone_class = result.hazard_class
    if result.flood_depth.depth_rp100_m is not None and result.flood_depth.depth_rp100_m > 0:
        row.nearest_river_km = 0.0
    row.nh09_quality = result.quality
    nh09_parts: list[str] = []
    d100 = result.flood_depth.depth_rp100_m
    if d100 is not None:
        nh09_parts.append(f"Depth RP100: {d100:.2f} m")
    d500 = result.flood_depth.depth_rp500_m
    if d500 is not None:
        nh09_parts.append(f"Depth RP500: {d500:.2f} m")
    if result.flood_return_period_threshold:
        nh09_parts.append(f"First flood at RP{result.flood_return_period_threshold}")
    if result.screening_flags:
        nh09_parts.append(f"Flags: {', '.join(result.screening_flags)}")
    river_apsfr = [a for a in result.apsfr if a.source_type == "river"]
    if river_apsfr:
        nh09_parts.append(f"River APSFR: {len(river_apsfr)} designation(s)")
    nh09_parts.append(f"Sources: {', '.join(result.sources)}")
    row.nh09_comment = "; ".join(nh09_parts)

    row.fetched_at = now
    row.run_id = run_id

    # SiteObservation for quality issues
    if result.is_permanent_water:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="raster",
            observation=(
                "Site coincides with permanent water body — "
                "flood hazard assessment not applicable. "
                "Verify site coordinates."
            ),
            impact="blocking", confidence="low", run_id=run_id,
        ))

    if result.is_spurious_depth:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="raster",
            observation=(
                "Spurious flood depth detected — model artefact suspected. "
                "Screening deferred to APSFR regulatory data."
            ),
            impact="negative", confidence="low", run_id=run_id,
        ))

    if result.error:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="raster",
            observation=f"Validation issues: {result.error}",
            impact="negative", confidence="medium", run_id=run_id,
        ))

    if result.hazard_class == "exclusionary":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="raster",
            observation=(
                f"Site is within the modelled floodplain with depth "
                f"{d100:.2f} m at 100-year return period "
                f"(threshold: {0.5} m). "
                f"Exclusionary flag E8 triggered. "
                f"IAEA SSG-18 §4.51 requires design-basis flood assessment."
            ) if d100 and d100 > 0.5 else (
                "Site classified as exclusionary due to permanent water body "
                "or other flood hazard condition."
            ),
            impact="blocking", confidence="high", run_id=run_id,
        ))

    if not result.apsfr and result.quality != "insufficient":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-08", source_type="vector",
            observation=(
                "No EEA APSFR data available for this site. "
                "Coastal flood assessment relies on JRC/GloFAS riverine data only. "
                "National marine agency data (N-05) recommended for NH-08."
            ),
            impact="neutral", confidence="medium", run_id=run_id,
        ))

    # A11: Flood risk avoidance observation
    if "A11" in result.screening_flags:
        a11_parts: list[str] = []
        if d100 is not None and d100 > 0:
            a11_parts.append(
                f"GloFAS flood depth {d100:.2f} m at 100-year return period"
            )
        elif result.flood_return_period_threshold:
            rp_t = result.flood_return_period_threshold
            a11_parts.append(
                f"First flood exposure at RP{rp_t}"
            )
        river_apsfr = [a for a in result.apsfr if a.source_type == "river"]
        coastal_apsfr = [a for a in result.apsfr if a.source_type == "coastal"]
        if river_apsfr:
            a11_parts.append(
                f"{len(river_apsfr)} river APSFR designation(s) "
                f"(highest: {river_apsfr[0].probability_scenario})"
            )
        if coastal_apsfr:
            a11_parts.append(
                f"{len(coastal_apsfr)} coastal APSFR designation(s) "
                f"(highest: {coastal_apsfr[0].probability_scenario})"
            )
        a11_parts.append(
            f"Hazard class: {result.hazard_class}; "
            f"exposure class: {result.flood_exposure_class}"
        )
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-09", source_type="raster",
            observation=(
                "A11 flood risk avoidance triggered. "
                + "; ".join(a11_parts)
                + ". IAEA SSG-18 §5 requires flood risk assessment."
            ),
            impact="negative", confidence=result.quality, run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-09", source_type="raster",
        observation=f"Flood risk enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
