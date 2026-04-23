# man_hours: 3.0
"""Batch enrichment and DB persistence for the Eurostat Projections connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to:
  - SiteRadiological (RI-06: population projections / growth trajectory)
  - SiteInfrastructureV2 (NS-09/NS-10/NS-12: socioeconomic, workforce, policy)
"""

from __future__ import annotations

import json
import math
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.eurostat_projections.models import (
    BatchResult,
    EurostatProjectionsResult,
    PopulationProjectionResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteInfrastructureV2,
    SiteObservation,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.eurostat_projections.client import (
        EurostatProjectionsConnector,
    )

log = get_logger(__name__)

_SOURCE_CONFIGS = [
    {
        "name": "eurostat_europop2023",
        "url": "https://ec.europa.eu/eurostat/web/population-demography/population-projections",
        "description": (
            "Eurostat EUROPOP2023 national population projections (proj_23np) — "
            "EU-27 + EFTA, 2022–2100 baseline. European Commission. Free reuse."
        ),
    },
    {
        "name": "eurostat_europop2019_regional",
        "url": "https://ec.europa.eu/eurostat/databrowser/product/page/proj_19rp3",
        "description": (
            "Eurostat EUROPOP2019 regional projections (proj_19rp3) — "
            "NUTS3 level, 2019–2060. European Commission. Free reuse."
        ),
    },
    {
        "name": "eurostat_regional_statistics",
        "url": "https://ec.europa.eu/eurostat/web/regions-and-cities",
        "description": (
            "Eurostat regional demographic and economic statistics — "
            "DEMO_R_PJANGRP3, NAMA_10R_3POPGDP, LFST_R_LFE2EN2N, EDAT_LFSE_04."
        ),
    },
    {
        "name": "nso_supplements",
        "url": "https://population.un.org/wpp/",
        "description": (
            "Curated national population projections for non-EU countries "
            "from national statistical offices and UN WPP 2024."
        ),
    },
]


def enrich_site(
    connector: EurostatProjectionsConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist projection data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_sources(session)

    cached = _check_cache(session, site_id, run_id)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("projections_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            country_code=site.country_code,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        _persist_result(session, site_id, result, run_id)
        _log_projections_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        pop_proj = result.population_projection
        log.info(
            "projections_site_complete",
            site_id=str(site_id), site_name=site.name,
            country=site.country_code,
            growth=pop_proj.growth_classification if pop_proj else None,
            quality=result.quality,
            elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            country_code=site.country_code,
            growth_classification=(
                pop_proj.growth_classification if pop_proj else None
            ),
            quality=result.quality,
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_projections_raw(
                session, connector, site_id, run_id,
                None, error=str(exc),
            )
        except Exception as log_exc:
            log.warning("projections_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("projections_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            country_code=site.country_code,
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: EurostatProjectionsConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
    """Enrich multiple sites with per-site commit isolation."""
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

    if not connector.data_loaded():
        log.info("projections_batch_loading_data")
        connector.ingest_projections()

    log.info("projections_batch_start", run_id=run_id, total=batch.total_sites)

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id)
        if cached:
            log.info("projections_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                country_code=site.country_code, elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            _persist_result(session, site.site_id, result, run_id)
            _log_projections_raw(session, connector, site.site_id, run_id, result)
            session.commit()
            batch.succeeded += 1

            pop_proj = result.population_projection
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "projections_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=batch.total_sites,
                country=site.country_code,
                growth=pop_proj.growth_classification if pop_proj else None,
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                country_code=site.country_code,
                growth_classification=(
                    pop_proj.growth_classification if pop_proj else None
                ),
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error(
                "projections_site_error",
                site_id=str(site.site_id), error=str(exc),
            )
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_projections_raw(
                    session, connector, site.site_id, run_id,
                    None, error=str(exc),
                )
            except Exception as log_exc:
                log.warning("projections_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="error",
                country_code=site.country_code,
                error=str(exc), elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "projections_batch_progress",
                completed=i + 1, total=batch.total_sites,
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "projections_batch_done", run_id=run_id,
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
) -> bool:
    """Return True if RI-06 data has already been written for this run."""
    ri = session.get(SiteRadiological, site_id)
    if ri and ri.ri06_quality and ri.run_id == run_id:
        return True
    return False


def _ensure_data_sources(session: Session) -> None:
    """Get-or-create DataSource records for all S-17 sources."""
    now = datetime.now(timezone.utc)
    for cfg in _SOURCE_CONFIGS:
        existing = session.query(DataSource).filter_by(name=cfg["name"]).first()
        if not existing:
            ds = DataSource(
                name=cfg["name"],
                url=cfg["url"],
                description=cfg["description"],
                last_fetched=now,
            )
            session.add(ds)
    session.flush()


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EurostatProjectionsResult,
    run_id: str,
) -> None:
    """Write projection + socioeconomic data to domain tables."""
    now = datetime.now(timezone.utc)

    _persist_ri06(session, site_id, result, run_id, now)
    _persist_ns09_ns10_ns12(session, site_id, result, run_id, now)


_GHSL_QUALITY_PREFIX = "ghsl_pop_"
_RING_AREA_KM2 = math.pi * 25 ** 2  # area of 25 km radius circle ≈ 1963.5 km²


def _compute_ring_level_pop_60yr(
    pop_density_25km: float | None,
    pop: PopulationProjectionResult,
) -> int | None:
    """Derive 60-year projected population for the 25 km ring around a site.

    Uses GHSL ``pop_density_25km`` (people/km²) to estimate current ring
    population, then applies the Eurostat growth trajectory.  Falls back to the
    national ``projected_pop_2080`` when density is unavailable.

    See LL-021: column semantics require ring-level, not national-level values.
    """
    if pop_density_25km is not None and float(pop_density_25km) > 0:
        ring_pop_now = float(pop_density_25km) * _RING_AREA_KM2

        growth = _infer_growth_factor_60yr(pop)
        return round(ring_pop_now * growth)

    return pop.projected_pop_2080


def _infer_growth_factor_60yr(pop: PopulationProjectionResult) -> float:
    """Return the best available 60-year growth multiplier.

    Priority order:
      1. ``receptor_growth_factor_60yr`` (direct ratio base→2080)
      2. Compound extrapolation from ``pop_change_pct_2050``
      3. Ratio of two available projection milestones (2030→2080)
      4. 1.0 (no growth applied)
    """
    if pop.receptor_growth_factor_60yr is not None:
        return pop.receptor_growth_factor_60yr

    if pop.pop_change_pct_2050 is not None:
        return (1 + pop.pop_change_pct_2050 / 100) ** (60 / 30)

    if pop.projected_pop_2030 and pop.projected_pop_2080 and pop.projected_pop_2030 > 0:
        ratio_50yr = pop.projected_pop_2080 / pop.projected_pop_2030
        return ratio_50yr ** (60 / 50)

    return 1.0


def _persist_ri06(
    session: Session,
    site_id: uuid.UUID,
    result: EurostatProjectionsResult,
    run_id: str,
    now: datetime,
) -> None:
    """Write RI-06 data to SiteRadiological.

    Guard: if the row already holds GHS-POP satellite data (quality starts with
    'ghsl_pop_'), that empirically-derived CAGR is higher quality than Eurostat
    model projections.  In that case we:
      - keep  pop_growth_rate_pct  (satellite CAGR 2020→2030)
      - keep  ri06_quality         ('ghsl_pop_100m_r2023a')
      - compute ring-level projected_pop_25km_60yr from GHSL density × growth
      - merge S-17 long-term projections into ri06_comment as supplementary JSON
    If no prior data exists we write everything from S-17.
    """
    ri = session.get(SiteRadiological, site_id)
    if ri is None:
        ri = SiteRadiological(site_id=site_id)
        session.add(ri)

    has_ghsl = ri.ri06_quality and str(ri.ri06_quality).startswith(_GHSL_QUALITY_PREFIX)
    pop = result.population_projection

    if pop:
        ring_pop = _compute_ring_level_pop_60yr(ri.pop_density_25km, pop)

        if has_ghsl:
            ri.projected_pop_25km_60yr = ring_pop
            try:
                existing = json.loads(ri.ri06_comment) if ri.ri06_comment else {}
            except (json.JSONDecodeError, TypeError):
                existing = {"ghsl_note": ri.ri06_comment}
            existing["s17_eurostat_supplement"] = pop.to_dict()
            ri.ri06_comment = _truncate(json.dumps(existing), 2000)
        else:
            ri.pop_growth_rate_pct = pop.pop_change_pct_2050
            ri.projected_pop_25km_60yr = ring_pop
            ri.ri06_quality = result.quality
            ri.ri06_comment = _truncate(json.dumps(pop.to_dict()), 2000)
    else:
        if not has_ghsl:
            ri.ri06_quality = result.quality or "insufficient"
            ri.ri06_comment = result.error or "No projection data available"

    ri.fetched_at = now
    ri.run_id = run_id


def _persist_ns09_ns10_ns12(
    session: Session,
    site_id: uuid.UUID,
    result: EurostatProjectionsResult,
    run_id: str,
    now: datetime,
) -> None:
    """Write NS-09, NS-10, NS-12 data to SiteInfrastructureV2."""
    infra = session.get(SiteInfrastructureV2, site_id)
    if infra is None:
        infra = SiteInfrastructureV2(site_id=site_id)
        session.add(infra)

    if result.socioeconomic:
        infra.ns09_quality = result.quality
        infra.ns09_comment = _truncate(json.dumps(result.socioeconomic.to_dict()), 2000)

    if result.workforce:
        infra.ns10_quality = result.quality
        infra.ns10_comment = _truncate(json.dumps(result.workforce.to_dict()), 2000)

    if result.policy_proxy:
        infra.ns12_quality = "low"
        infra.ns12_comment = _truncate(json.dumps(result.policy_proxy.to_dict()), 500)

    infra.fetched_at = now
    infra.run_id = run_id


def _persist_error_observation(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    error: str,
) -> None:
    """Write a blocking observation when enrichment fails entirely."""
    session.add(SiteObservation(
        site_id=site_id, criterion_id="RI-06", source_type="api",
        observation=f"Eurostat Projections enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))


def _log_projections_raw(
    session: Session,
    connector: EurostatProjectionsConnector,
    site_id: uuid.UUID,
    run_id: str,
    result: EurostatProjectionsResult | None,
    *,
    error: str | None = None,
) -> None:
    """Persist the per-site projections assessment to ``site_raw_responses``.

    Eurostat Projections runs a one-off Phase A ingestion of national +
    regional Eurostat datasets and computes per-site results locally.  The
    raw row therefore captures the assessment payload plus a digest of the
    ingested datasets (counts of countries / regions covered, Eurostat API
    URL, NSO supplement count) so an auditor can reproduce the figure.
    """
    body: dict[str, Any] = {
        "type": "eurostat_projections_assessment",
        "catalogue": {
            "statistics_api_url": getattr(connector, "_statistics_api_url", None),
            "n_national_bsl": _len_or_none(getattr(connector, "_national_bsl", None)),
            "n_national_lmig": _len_or_none(getattr(connector, "_national_lmig", None)),
            "n_national_hmig": _len_or_none(getattr(connector, "_national_hmig", None)),
            "n_indicators": _len_or_none(getattr(connector, "_indicators", None)),
            "n_regional_proj": _len_or_none(getattr(connector, "_regional_proj", None)),
            "n_nso_supplements": _len_or_none(getattr(connector, "_nso_supplements", None)),
        },
    }
    if result is not None:
        body["assessment"] = result.to_dict()
    if error is not None:
        body["error"] = error

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="eurostat_projections",
        run_id=run_id,
        request_url=(
            getattr(connector, "_statistics_api_url", "")
            or _SOURCE_CONFIGS[0]["url"]
        ),
        response_body=body,
        http_status=200 if (result is not None and error is None) else None,
    )


def _len_or_none(obj: Any) -> int | None:
    """Return ``len(obj)`` when defined, else ``None`` (for digest fields)."""
    if obj is None:
        return None
    try:
        return len(obj)
    except TypeError:
        return None


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
