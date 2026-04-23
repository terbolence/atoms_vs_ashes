# man_hours: 3.0
"""Batch enrichment and DB persistence for ESA WorldCover (S-36).

Runs ``WorldCoverConnector.classify()`` for non-EU sites, computes
buildable area metrics, and persists to ``SiteInfrastructureV2`` NS-04 /
NS-05 columns.  Fills the gap left by P12 CORINE for the 11 non-EU
in-scope countries.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.corine.models import CORINE_COVERED_COUNTRIES
from atoms_vs_ashes.connectors.worldcover.models import (
    CRITERION_NS04,
    CRITERION_NS05,
    NON_EU_COUNTRIES,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.worldcover.parsers import (
    NUCLEAR_ISLAND_HA,
    assess_buildable_adequacy,
    build_ns04_comment,
    compute_buildable_metrics,
)
from atoms_vs_ashes.db.models import (
    Site,
    SiteInfrastructureV2,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.worldcover.client import WorldCoverConnector

log = get_logger(__name__)


def enrich_site(
    connector: WorldCoverConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
    *,
    ring_defs: list[tuple[float, float, str]] | None = None,
    buildable_radius_m: float = 1_000,
    skip_if_enriched: bool = True,
) -> SiteEnrichmentSummary:
    """Fetch and persist WorldCover land cover data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_source(session)

    country = (site.country_code or "").upper()

    if country in CORINE_COVERED_COUNTRIES:
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="skipped",
            quality="corine_covered", elapsed_ms=elapsed,
        )

    if skip_if_enriched and _already_enriched(session, site_id):
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elapsed_ms=elapsed,
        )

    try:
        classification = connector.classify(
            float(site.latitude), float(site.longitude),
            ring_defs=ring_defs,
        )
        metrics = compute_buildable_metrics(
            classification, buildable_radius_m=buildable_radius_m,
        )
        _persist_result(session, site_id, metrics, run_id)
        _write_quality_observations(session, site_id, metrics, run_id)
        session.commit()

        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            buildable_area_ha=metrics["buildable_area_ha"],
            dominant_land_class=metrics["dominant_land_class"],
            quality="medium", elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS04,
            observation=f"WorldCover enrichment failed: {exc}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("worldcover_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: WorldCoverConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    ring_defs: list[tuple[float, float, str]] | None = None,
    buildable_radius_m: float = 1_000,
    skip_if_enriched: bool = True,
) -> BatchResult:
    """Enrich non-EU sites with WorldCover land cover data."""
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

    non_eu_sites = [
        s for s in sites
        if (s.country_code or "").upper() not in CORINE_COVERED_COUNTRIES
    ]
    log.info(
        "worldcover_batch_start", run_id=run_id,
        total=batch.total_sites,
        non_eu_sites=len(non_eu_sites),
        eu_sites_skipped=batch.total_sites - len(non_eu_sites),
    )

    batch.skipped_eu = batch.total_sites - len(non_eu_sites)

    for i, site in enumerate(non_eu_sites):
        site_start = time.monotonic()

        if skip_if_enriched and _already_enriched(session, site.site_id):
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            classification = connector.classify(
                float(site.latitude), float(site.longitude),
                ring_defs=ring_defs,
            )
            metrics = compute_buildable_metrics(
                classification, buildable_radius_m=buildable_radius_m,
            )
            _persist_result(session, site.site_id, metrics, run_id)
            _write_quality_observations(session, site.site_id, metrics, run_id)
            session.commit()
            batch.succeeded += 1

            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "worldcover_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                country=site.country_code,
                index=i + 1, total=len(non_eu_sites),
                buildable_ha=metrics["buildable_area_ha"],
                dominant=metrics["dominant_land_class"],
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                buildable_area_ha=metrics["buildable_area_ha"],
                dominant_land_class=metrics["dominant_land_class"],
                quality="medium", elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("worldcover_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_NS04,
                observation=f"WorldCover enrichment failed: {exc}",
                run_id=run_id, confidence="low", impact="blocking",
            )
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "worldcover_batch_progress",
                completed=i + 1, total=len(non_eu_sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "worldcover_batch_done", run_id=run_id,
        total=batch.total_sites, non_eu=len(non_eu_sites),
        succeeded=batch.succeeded, failed=batch.failed,
        cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------

def _already_enriched(session: Session, site_id: uuid.UUID) -> bool:
    """Check if WorldCover land cover fields are already populated."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return False
    if row.ns04_quality == "no_coverage":
        return False
    return getattr(row, "dominant_land_class", None) is not None


def _ensure_data_source(session: Session) -> uuid.UUID:
    return ensure_data_source(
        session,
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "ESA WorldCover 2021 v200 — 10 m global land cover from "
            "Sentinel-1/2. Used for NS-04/NS-05 in non-EU countries "
            "where CORINE has no coverage."
        ),
    )


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    metrics: dict[str, Any],
    run_id: str,
) -> None:
    """Write WorldCover-derived land cover metrics to SiteInfrastructureV2."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.dominant_land_class = metrics["dominant_land_class"]
    row.dominant_class_pct = metrics["dominant_class_pct"]
    row.favourable_land_pct = metrics["favourable_land_pct"]
    row.moderate_land_pct = metrics["moderate_land_pct"]
    row.unfavourable_land_pct = metrics["unfavourable_land_pct"]
    # See docs/post_processing/data_curation_methodology.md task 2.
    buildable_ha = metrics.get("buildable_area_ha")
    fav_pct = metrics.get("favourable_land_pct")
    if buildable_ha is not None and fav_pct is not None:
        row.favourable_area_ha = round(float(buildable_ha) * float(fav_pct) / 100.0, 2)
        row.favourable_area_method = "comment_buildable_x_fav_pct"
    row.ns04_quality = "medium"
    row.ns04_comment = build_ns04_comment(metrics)

    if row.buildable_area_ha is None:
        row.buildable_area_ha = metrics["buildable_area_ha"]
        row.ns05_quality = "worldcover_10m"
        row.ns05_comment = (
            f"WorldCover-derived buildable area: {metrics['buildable_area_ha']:.1f} ha "
            f"(developable land within 0\u20131 km radius). "
            f"Adequacy: {assess_buildable_adequacy(metrics['buildable_area_ha'])}."
        )

    if row.patch_count is None and metrics.get("patch_count") is not None:
        row.patch_count = metrics["patch_count"]
    if row.largest_contiguous_ha is None and metrics.get("largest_contiguous_ha") is not None:
        row.largest_contiguous_ha = metrics["largest_contiguous_ha"]

    if metrics.get("natural_seminatural_ha") is not None:
        row.ecological_natural_pct = metrics.get("unfavourable_land_pct")

    row.fetched_at = now
    row.run_id = run_id


def _write_quality_observations(
    session: Session,
    site_id: uuid.UUID,
    metrics: dict[str, Any],
    run_id: str,
) -> None:
    """Write SiteObservation records for quality flags."""
    buildable = metrics.get("buildable_area_ha", 0.0)
    unfav_pct = metrics.get("unfavourable_land_pct", 0.0)

    if unfav_pct > 70:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS04,
            observation=(
                f"Site is predominantly forest/wetland/water: "
                f"{unfav_pct:.0f}% unfavourable land cover within 0\u20132 km "
                f"(ESA WorldCover). Development may face significant "
                f"environmental constraints."
            ),
            run_id=run_id, confidence="medium", impact="negative",
        )

    if buildable < NUCLEAR_ISLAND_HA:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS05,
            observation=(
                f"WorldCover-classified buildable area ({buildable:.1f} ha) is below "
                f"nuclear island minimum ({NUCLEAR_ISLAND_HA} ha). "
                f"Note: FIX-03 site_area_ha from OSM polygon is the primary A15 signal."
            ),
            run_id=run_id, confidence="medium", impact="negative",
        )
