# man_hours: 4.0
"""Batch enrichment and DB persistence for CORINE Land Cover (P12).

Runs ``CorineConnector.classify()`` for all sites, computes buildable
area metrics, and persists to ``SiteInfrastructureV2`` NS-04 / NS-05
columns.  Handles non-EU coverage gaps, FIX-03 non-overwrite, cache-
based resumability, and per-site commit isolation.
"""

from __future__ import annotations

import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.corine.models import (
    CORINE_COVERED_COUNTRIES,
    DEFAULT_RINGS,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.corine.parsers import (
    NUCLEAR_ISLAND_HA,
    assess_buildable_adequacy,
    build_ns04_comment,
    compute_buildable_metrics,
    is_corine_covered,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    Site,
    SiteInfrastructureV2,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.corine.client import CorineConnector

log = get_logger(__name__)

CRITERION_NS04 = "NS-04"
CRITERION_NS05 = "NS-05"
_DEFAULT_INTER_REQUEST_DELAY_S = 2.0
_DEFAULT_CACHE_TTL_DAYS = 30


def enrich_site(
    connector: CorineConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
    *,
    ring_defs: list[tuple[float, float, str]] | None = None,
    buildable_radius_m: float = 1_000,
    skip_if_enriched: bool = True,
) -> SiteEnrichmentSummary:
    """Fetch and persist CORINE land cover data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_source(session)

    country = (site.country_code or "").upper()

    if not is_corine_covered(country):
        _persist_non_eu(session, site_id, country, run_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="non_eu",
            quality="no_coverage", elapsed_ms=elapsed,
        )

    if skip_if_enriched and _already_enriched(session, site_id):
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("corine_batch_skip", site_id=str(site_id), reason="already_enriched")
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elapsed_ms=elapsed,
        )

    try:
        classification = connector.classify(
            float(site.latitude), float(site.longitude),
            ring_defs=ring_defs or DEFAULT_RINGS,
        )
        metrics = compute_buildable_metrics(
            classification, buildable_radius_m=buildable_radius_m,
        )
        _persist_result(session, site_id, metrics, run_id)
        _write_quality_observations(session, site_id, metrics, run_id)
        if connector.last_raw_response is not None:
            log_raw_response(
                session,
                site_id=site_id,
                connector_slug="corine",
                run_id=run_id,
                request_url=connector.last_request_url or "",
                request_params=connector.last_request_params,
                response_body=connector.last_raw_response,
                http_status=connector.last_http_status,
            )
        session.commit()

        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            buildable_area_ha=metrics["buildable_area_ha"],
            dominant_land_class=metrics["dominant_land_class"],
            quality="high", elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS04,
            observation=f"CORINE enrichment failed: {exc}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("corine_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: CorineConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    ring_defs: list[tuple[float, float, str]] | None = None,
    buildable_radius_m: float = 1_000,
    inter_request_delay_s: float = _DEFAULT_INTER_REQUEST_DELAY_S,
    skip_if_enriched: bool = True,
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

    eu_count = sum(
        1 for s in sites
        if is_corine_covered((s.country_code or "").upper())
    )
    log.info(
        "corine_batch_start", run_id=run_id,
        total=batch.total_sites, eu_sites=eu_count,
        non_eu_sites=batch.total_sites - eu_count,
        expected_api_calls=eu_count,
    )

    for i, site in enumerate(sites):
        site_start = time.monotonic()
        country = (site.country_code or "").upper()

        if not is_corine_covered(country):
            _persist_non_eu(session, site.site_id, country, run_id)
            session.commit()
            batch.skipped_non_eu += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="non_eu",
                quality="no_coverage", elapsed_ms=elapsed_ms,
            ))
            continue

        if skip_if_enriched and _already_enriched(session, site.site_id):
            batch.skipped_already_enriched += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            classification = connector.classify(
                float(site.latitude), float(site.longitude),
                ring_defs=ring_defs or DEFAULT_RINGS,
            )
            metrics = compute_buildable_metrics(
                classification, buildable_radius_m=buildable_radius_m,
            )
            _persist_result(session, site.site_id, metrics, run_id)
            _write_quality_observations(session, site.site_id, metrics, run_id)
            if connector.last_raw_response is not None:
                log_raw_response(
                    session,
                    site_id=site.site_id,
                    connector_slug="corine",
                    run_id=run_id,
                    request_url=connector.last_request_url or "",
                    request_params=connector.last_request_params,
                    response_body=connector.last_raw_response,
                    http_status=connector.last_http_status,
                )
            session.commit()
            batch.succeeded += 1

            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "corine_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                buildable_ha=metrics["buildable_area_ha"],
                dominant=metrics["dominant_land_class"],
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                buildable_area_ha=metrics["buildable_area_ha"],
                dominant_land_class=metrics["dominant_land_class"],
                quality="high", elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("corine_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_NS04,
                observation=f"CORINE enrichment failed: {exc}",
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
                "corine_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                non_eu=batch.skipped_non_eu,
                already_enriched=batch.skipped_already_enriched,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

        jitter = random.uniform(-0.5, 0.5)
        time.sleep(max(0.1, inter_request_delay_s + jitter))

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "corine_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, non_eu=batch.skipped_non_eu,
        already_enriched=batch.skipped_already_enriched,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------

def _already_enriched(session: Session, site_id: uuid.UUID) -> bool:
    """Check if CORINE land cover fields are already populated."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        return False
    return getattr(row, "dominant_land_class", None) is not None


def _ensure_data_source(session: Session) -> uuid.UUID:
    return ensure_data_source(
        session,
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=(
            "EEA CORINE Land Cover 2018 — ArcGIS REST vector query for "
            "NS-04 land class, NS-05 buildable area, NS-08 ecological fraction"
        ),
    )


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    metrics: dict[str, Any],
    run_id: str,
) -> None:
    """Write CORINE-derived land cover metrics to SiteInfrastructureV2."""
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
    # See docs/post_processing/data_curation_methodology.md task 2 — buildable
    # already excludes water/built-up; multiplying by % favourable restricts
    # the remainder to land-use-favourable pixels.
    buildable_ha = metrics.get("buildable_area_ha")
    fav_pct = metrics.get("favourable_land_pct")
    if buildable_ha is not None and fav_pct is not None:
        row.favourable_area_ha = round(float(buildable_ha) * float(fav_pct) / 100.0, 2)
        row.favourable_area_method = "comment_buildable_x_fav_pct"
    row.ns04_quality = "high"
    row.ns04_comment = build_ns04_comment(metrics)

    # NS-05: buildable_area_ha — do not overwrite if FIX-03 already set it
    if row.buildable_area_ha is None:
        row.buildable_area_ha = metrics["buildable_area_ha"]
        row.ns05_quality = "corine_proxy"
        row.ns05_comment = (
            f"CORINE-derived buildable area: {metrics['buildable_area_ha']:.1f} ha "
            f"(developable land within 0\u20131 km radius). "
            f"Adequacy: {assess_buildable_adequacy(metrics['buildable_area_ha'])}."
        )
    else:
        # FIX-03 already populated — append CORINE value as reference
        existing_comment = row.ns05_comment or ""
        corine_ref = (
            f" [CORINE ref: {metrics['buildable_area_ha']:.1f} ha developable in 0\u20131 km]"
        )
        if "CORINE ref" not in existing_comment:
            row.ns05_comment = existing_comment + corine_ref

    if row.patch_count is None and metrics.get("patch_count") is not None:
        row.patch_count = metrics["patch_count"]
    if row.largest_contiguous_ha is None and metrics.get("largest_contiguous_ha") is not None:
        row.largest_contiguous_ha = metrics["largest_contiguous_ha"]

    # NS-08: ecological natural fraction
    if metrics.get("natural_seminatural_ha") is not None:
        row.ecological_natural_pct = metrics.get("unfavourable_land_pct")

    row.fetched_at = now
    row.run_id = run_id


def _persist_non_eu(
    session: Session,
    site_id: uuid.UUID,
    country_code: str,
    run_id: str,
) -> None:
    """Write coverage-gap metadata for a non-EU site."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.ns04_quality = "no_coverage"
    row.ns04_comment = (
        f"CORINE not available for {country_code}; "
        f"requires S-36 ESA WorldCover"
    )
    row.fetched_at = now
    row.run_id = run_id

    write_observation(
        session, site_id=site_id, criterion_id=CRITERION_NS04,
        observation=(
            f"CORINE Land Cover not available for country {country_code}. "
            f"Non-EU country outside CORINE spatial coverage. "
            f"Deferred to S-36 ESA WorldCover (Tier C)."
        ),
        run_id=run_id, confidence="low", impact="neutral",
    )


def _write_quality_observations(
    session: Session,
    site_id: uuid.UUID,
    metrics: dict[str, Any],
    run_id: str,
) -> None:
    """Write SiteObservation records for quality flags per the spec."""
    buildable = metrics.get("buildable_area_ha", 0.0)
    unfav_pct = metrics.get("unfavourable_land_pct", 0.0)

    if unfav_pct > 70:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS04,
            observation=(
                f"Site is predominantly forest/wetland/water: "
                f"{unfav_pct:.0f}% unfavourable land cover within 0\u20132 km. "
                f"Development may face significant environmental constraints."
            ),
            run_id=run_id, confidence="medium", impact="negative",
        )

    if buildable < NUCLEAR_ISLAND_HA:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_NS05,
            observation=(
                f"CORINE-classified buildable area ({buildable:.1f} ha) is below "
                f"nuclear island minimum ({NUCLEAR_ISLAND_HA} ha). "
                f"Note: FIX-03 site_area_ha from OSM polygon is the primary A15 signal."
            ),
            run_id=run_id, confidence="medium", impact="negative",
        )
