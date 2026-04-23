# man_hours: 3.0
"""Batch enrichment and DB persistence for the ENTSO-E connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` for NS-02 grid capacity.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.entso_e.models import (
    DEFAULT_API_URL,
    SOURCE_NAME,
    BatchResult,
    EntsoEResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.entso_e.client import EntsoEConnector

log = get_logger(__name__)

CRITERION_ID = "NS-02"


def enrich_site(
    connector: EntsoEConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist ENTSO-E grid data for a single DB site."""
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
        log.info("entsoe_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elapsed_ms=elapsed,
        )

    installed_mw = _safe_float(getattr(site, "installed_capacity_mw", None))

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
            site_name=site.name,
            alternative_names=getattr(site, "alternative_names", None),
            installed_capacity_mw=installed_mw,
        )
        _persist_result(session, site_id, result, run_id, installed_mw)
        _log_entsoe_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)

        log.info(
            "entsoe_site_complete",
            site_id=str(site_id), site_name=site.name,
            country=site.country_code,
            readiness=result.nuclear_readiness,
            quality=result.quality,
            elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            country_code=site.country_code,
            nuclear_readiness=result.nuclear_readiness,
            total_installed_mw=(
                result.capacity.total_installed_mw if result.capacity else None
            ),
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"ENTSO-E enrichment failed: {exc}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        try:
            _log_entsoe_raw(session, connector, site_id, run_id, None, error=str(exc))
        except Exception as log_exc:
            log.warning("entsoe_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("entsoe_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EntsoEConnector,
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

    log.info("entsoe_batch_start", run_id=run_id, total=batch.total_sites)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("entsoe_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elapsed_ms=elapsed_ms,
            ))
            continue

        installed_mw = _safe_float(getattr(site, "installed_capacity_mw", None))

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
                site_name=site.name,
                alternative_names=getattr(site, "alternative_names", None),
                installed_capacity_mw=installed_mw,
            )
            _persist_result(session, site.site_id, result, run_id, installed_mw)
            _log_entsoe_raw(session, connector, site.site_id, run_id, result)
            session.commit()

            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "entsoe_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                country=site.country_code,
                readiness=result.nuclear_readiness,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                country_code=site.country_code,
                nuclear_readiness=result.nuclear_readiness,
                total_installed_mw=(
                    result.capacity.total_installed_mw if result.capacity else None
                ),
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("entsoe_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_ID,
                observation=f"ENTSO-E enrichment failed: {exc}",
                run_id=run_id, confidence="low", impact="blocking",
            )
            try:
                _log_entsoe_raw(session, connector, site.site_id, run_id, None, error=str(exc))
            except Exception as log_exc:
                log.warning("entsoe_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "entsoe_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "entsoe_batch_done", run_id=run_id,
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
) -> SiteInfrastructureV2 | None:
    """Return cached row if ENTSO-E grid data is fresh for this run."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None or row.grid_export_capacity_mw is None:
        return None
    if row.ns02_comment and SOURCE_NAME in (row.ns02_comment or ""):
        if row.fetched_at and row.run_id == run_id:
            age = datetime.now(timezone.utc) - row.fetched_at
            if age < timedelta(days=ttl_days):
                return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    return ensure_data_source(
        session,
        name=SOURCE_NAME,
        url=DEFAULT_API_URL,
        description=(
            "ENTSO-E Transparency Platform REST API — zone-level "
            "grid capacity data for NS-02 assessment"
        ),
    )


def _safe_float(value: object) -> float | None:
    """Coerce a Decimal/float/int to float, returning None on failure."""
    if value is None:
        return None
    try:
        f = float(value)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EntsoEResult,
    run_id: str,
    installed_capacity_mw: float | None = None,
) -> None:
    """Write ENTSO-E grid data to SiteInfrastructureV2 NS-02 columns.

    Uses a priority cascade for ``grid_export_capacity_mw``:
      P2 — ENTSO-E per-unit fuzzy match (high quality)
      P3 — GEM installed capacity fallback (low / medium quality)
    Zone-level totals are recorded in ``ns02_comment`` only.
    """
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    capacity_mw: float | None = None
    capacity_source: str | None = None

    # P2: ENTSO-E per-unit match
    match = result.per_unit_match
    if match is not None and match.matched:
        capacity_mw = match.capacity_mw
        capacity_source = "entsoe_per_unit_match"

    # P3: GEM installed capacity fallback
    if capacity_mw is None and installed_capacity_mw is not None:
        capacity_mw = installed_capacity_mw
        capacity_source = "gem_coal_tracker"

    row.grid_export_capacity_mw = capacity_mw
    row.ns02_quality = result.quality
    row.ns02_comment = _build_comment(result, capacity_source, installed_capacity_mw)
    row.fetched_at = now
    row.run_id = run_id

    if result.quality in ("insufficient", "low"):
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=result.error or f"ENTSO-E quality: {result.quality}",
            run_id=run_id,
            confidence=result.quality if result.quality != "insufficient" else "low",
            impact=(
                "blocking" if result.quality == "insufficient"
                else "negative"
            ),
        )


def _build_comment(
    result: EntsoEResult,
    capacity_source: str | None = None,
    installed_capacity_mw: float | None = None,
) -> str:
    """Build provenance comment for ns02_comment column."""
    parts = [f"source: {SOURCE_NAME}"]
    parts.append(f"zone: {result.bidding_zone_name} ({result.bidding_zone_eic})")
    parts.append(f"readiness: {result.nuclear_readiness}")

    if result.capacity:
        c = result.capacity
        parts.append(f"zone_total_installed: {c.total_installed_mw:.0f} MW")
        if c.has_nuclear_precedent:
            parts.append(f"nuclear: {c.nuclear_installed_mw:.0f} MW ({c.nuclear_units} units)")
        if c.largest_unit_mw:
            parts.append(f"largest_unit: {c.largest_unit_name} ({c.largest_unit_mw:.0f} MW)")

    match = result.per_unit_match
    if match is not None and match.matched:
        unit_names = ", ".join(u.unit_name for u in match.matched_units)
        parts.append(
            f"grid_export_capacity: {match.capacity_mw:.0f} MW from "
            f"per-unit match [{match.strategy}] "
            f"({match.unit_count} units: {unit_names}; "
            f"score={match.best_score:.0f})"
        )
    elif capacity_source == "gem_coal_tracker" and installed_capacity_mw:
        fallback_detail = "no A71 unit name matched"
        if match is not None:
            if match.best_score > 0:
                fallback_detail = (
                    f"best A71 fuzzy score {match.best_score:.0f} < threshold"
                )
            if match.zone_unknown_count > 0:
                fallback_detail += (
                    f"; zone has {match.zone_unknown_count} unnamed units "
                    f"totalling {match.zone_unknown_total_mw:.0f} MW"
                )
        parts.append(
            f"grid_export_capacity: {installed_capacity_mw:.0f} MW from "
            f"GEM installed capacity (fallback — {fallback_detail})"
        )
    else:
        no_match_detail = "no per-unit match, no GEM fallback"
        if match is not None and match.zone_unknown_count > 0:
            no_match_detail += (
                f"; zone has {match.zone_unknown_count} unnamed units "
                f"totalling {match.zone_unknown_total_mw:.0f} MW"
            )
        parts.append(f"grid_export_capacity: not determined ({no_match_detail})")

    if result.interconnection:
        ic = result.interconnection
        parts.append(f"interconnectors: {ic.n_interconnectors}")
        parts.append(f"ntc_export: {ic.total_ntc_export_mw:.0f} MW")

    if result.error:
        parts.append(f"error: {result.error}")

    return "; ".join(parts)


def _log_entsoe_raw(
    session: Session,
    connector: EntsoEConnector,
    site_id: uuid.UUID,
    run_id: str,
    result: EntsoEResult | None,
    *,
    error: str | None = None,
) -> None:
    """Persist the per-site ENTSO-E assessment to ``site_raw_responses``.

    ENTSO-E queries are zone-level (one set of REST calls per bidding zone
    in ``ingest_zones``) and the per-site ``fetch()`` is a local lookup +
    fuzzy unit match.  The raw row therefore captures the assessment plus a
    digest of the zone source data so an auditor can reproduce the
    decision.
    """
    body: dict[str, Any] = {
        "type": "entso_e_assessment",
        "api_url": getattr(connector, "_api_url", None),
        "reference_year": getattr(connector, "_reference_year", None),
    }
    if result is not None:
        capacity = result.capacity
        match = result.per_unit_match
        body["assessment"] = {
            "lat": result.lat,
            "lon": result.lon,
            "country_code": result.country_code,
            "bidding_zone_eic": result.bidding_zone_eic,
            "bidding_zone_name": result.bidding_zone_name,
            "nuclear_readiness": result.nuclear_readiness,
            "quality": result.quality,
            "reference_year": result.reference_year,
            "error": result.error,
            "capacity": (
                {
                    "total_installed_mw": capacity.total_installed_mw,
                    "thermal_installed_mw": capacity.thermal_installed_mw,
                    "nuclear_installed_mw": capacity.nuclear_installed_mw,
                    "hydro_installed_mw": capacity.hydro_installed_mw,
                    "wind_solar_installed_mw": capacity.wind_solar_installed_mw,
                    "other_installed_mw": capacity.other_installed_mw,
                    "largest_unit_mw": capacity.largest_unit_mw,
                    "largest_unit_name": capacity.largest_unit_name,
                    "nuclear_units": capacity.nuclear_units,
                    "has_nuclear_precedent": capacity.has_nuclear_precedent,
                }
                if capacity is not None else None
            ),
            "per_unit_match": (
                {
                    "matched": match.matched,
                    "strategy": match.strategy,
                    "unit_count": match.unit_count,
                    "capacity_mw": match.capacity_mw,
                    "best_score": match.best_score,
                    "matched_units": [
                        {"unit_name": u.unit_name, "installed_mw": u.installed_mw}
                        for u in (match.matched_units or [])
                    ],
                }
                if match is not None else None
            ),
        }
        # Zone source digest (counts only — full zone XML lives in cache)
        zone_assessments = getattr(connector, "_zone_assessments", {}) or {}
        zone = zone_assessments.get(result.bidding_zone_eic)
        if zone is not None:
            body["zone_source"] = {
                "zone_eic": zone.zone_eic,
                "country_code": zone.country_code,
                "reference_year": zone.reference_year,
                "n_units": len(zone.units or []),
                "queried_at": (
                    zone.queried_at.isoformat()
                    if getattr(zone, "queried_at", None) is not None else None
                ),
            }
    if error is not None:
        body["error"] = error

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="entso_e",
        run_id=run_id,
        request_url=getattr(connector, "_api_url", "") or "",
        response_body=body,
        http_status=200 if (result is not None and error is None) else None,
    )
