# man_hours: 5.0
"""Batch enrichment and DB persistence for the seismic hazard connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteAttribute`` / ``DataQualityFlag`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.seismic_hazard.models import (
    BatchResult,
    SeismicHazardResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataQualityFlag, DataSource, Site, SiteAttribute
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.seismic_hazard.client import SeismicHazardConnector

log = get_logger(__name__)


# ------------------------------------------------------------------
# Public entry points (called by connector delegation methods)
# ------------------------------------------------------------------


def enrich_site(
    connector: SeismicHazardConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist seismic hazard data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    source_id = _ensure_data_source(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached is not None:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("seismic_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            pga_475yr=float(cached.value_numeric) if cached.value_numeric else None,
            source=cached.value_json.get("source") if cached.value_json else None,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch_all(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id, source_id)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            pga_475yr=result.pga_475yr, source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_flag(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("seismic_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: SeismicHazardConnector,
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

    source_id = _ensure_data_source(session)
    first = sites[0]
    connector.discover_model(float(first.latitude), float(first.longitude))

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached is not None:
            log.info("seismic_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                pga_475yr=float(cached.value_numeric) if cached.value_numeric else None,
                source=cached.value_json.get("source") if cached.value_json else None,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch_all(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id, source_id)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "seismic_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                pga_475yr=result.pga_475yr, source=result.source,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                pga_475yr=result.pga_475yr, source=result.source,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("seismic_site_error", site_id=str(site.site_id), error=str(exc))
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
                "seismic_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

        time.sleep(connector._inter_request_delay)

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "seismic_batch_done", run_id=run_id,
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
    existing = (
        session.query(SiteAttribute)
        .filter_by(site_id=site_id, criterion_id="NH-01", run_id=run_id)
        .first()
    )
    if existing and existing.fetched_at:
        age = datetime.now(timezone.utc) - existing.fetched_at
        if age < timedelta(days=ttl_days):
            return existing
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    existing = session.query(DataSource).filter_by(name="efehr_eshm20").first()
    if existing:
        return existing.source_id

    ds = DataSource(
        name="efehr_eshm20",
        url="http://appsrvr.share-eu.org:8080/share/",
        description=(
            "EFEHR ESHM20 European Seismic Hazard Model — "
            "PGA, hazard curves, uniform hazard spectra"
        ),
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: SeismicHazardResult,
    run_id: str,
    source_id: uuid.UUID,
) -> None:
    """Write 3 SiteAttribute rows (NH-01, NH-03, NH-04) and quality flags."""
    now = datetime.now(timezone.utc)

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-01",
        value_numeric=result.pga_475yr, value_json=result.to_dict(),
        source_id=source_id, fetched_at=now, run_id=run_id,
    ))
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-03",
        value_numeric=result.pga_475yr,
        value_json={
            "pga_475yr": result.pga_475yr, "source": result.source,
            "note": "PGA interaction term for liquefaction assessment",
        },
        source_id=source_id, fetched_at=now, run_id=run_id,
    ))
    session.merge(SiteAttribute(
        site_id=site_id, criterion_id="NH-04",
        value_numeric=result.pga_475yr,
        value_json={
            "pga_rock_475yr": result.pga_475yr,
            "vs30_reference": result.vs30_reference, "source": result.source,
            "note": (
                "Rock-condition PGA for amplification assessment. "
                "Vs30-based amplification requires S-02 EGDI data."
            ),
        },
        source_id=source_id, fetched_at=now, run_id=run_id,
    ))

    if result.quality != "high":
        session.add(DataQualityFlag(
            site_id=site_id, dataset="seismic_hazard", dimension="completeness",
            level=result.quality, detail=result.error or f"Source: {result.source}",
            run_id=run_id,
        ))
    if result.source == "gem_global_v2023":
        session.add(DataQualityFlag(
            site_id=site_id, dataset="seismic_hazard", dimension="source",
            level="medium",
            detail="GEM global fallback used instead of EFEHR ESHM20. No hazard curve or UHS available.",
            run_id=run_id,
        ))
    if result.grid_distance_km > 15.0:
        session.add(DataQualityFlag(
            site_id=site_id, dataset="seismic_hazard", dimension="spatial",
            level="low",
            detail=f"Nearest EFEHR grid node is {result.grid_distance_km:.1f} km from site (threshold: 15 km)",
            run_id=run_id,
        ))


def _persist_error_flag(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(DataQualityFlag(
        site_id=site_id, dataset="seismic_hazard", dimension="availability",
        level="insufficient", detail=f"Enrichment failed: {error}", run_id=run_id,
    ))
