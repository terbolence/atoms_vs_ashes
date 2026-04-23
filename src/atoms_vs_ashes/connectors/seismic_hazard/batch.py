# man_hours: 5.0
"""Batch enrichment and DB persistence for the seismic hazard connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteNaturalHazards`` / ``SiteObservation`` tables.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.connectors.seismic_hazard.models import (
    BatchResult,
    SeismicHazardResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteNaturalHazards, SiteObservation
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.seismic_hazard.client import SeismicHazardConnector

log = get_logger(__name__)


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
    _ensure_data_source(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("seismic_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            pga_475yr=float(cached.pga_475yr_g) if cached.pga_475yr_g else None,
            source=cached.nh01_source,
            elapsed_ms=elapsed,
        )

    try:
        connector.reset_raw_call_log()
        result = connector.fetch_all(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        _log_seismic_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            pga_475yr=result.pga_475yr, source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_seismic_raw(session, connector, site_id, run_id, None, error=str(exc))
        except Exception as log_exc:
            log.warning("seismic_raw_log_after_error_failed", error=str(log_exc))
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

    _ensure_data_source(session)
    first = sites[0]
    connector.discover_model(float(first.latitude), float(first.longitude))

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("seismic_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                pga_475yr=float(cached.pga_475yr_g) if cached.pga_475yr_g else None,
                source=cached.nh01_source,
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            connector.reset_raw_call_log()
            result = connector.fetch_all(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            _log_seismic_raw(session, connector, site.site_id, run_id, result)
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
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_seismic_raw(session, connector, site.site_id, run_id, None, error=str(exc))
            except Exception as log_exc:
                log.warning("seismic_raw_log_after_error_failed", error=str(log_exc))
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

    _write_batch_metadata(batch)

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
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.pga_475yr_g is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days) and row.run_id == run_id:
            return row
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
) -> None:
    """Write seismic data to SiteNaturalHazards NH-01 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)

    row.pga_475yr_g = result.pga_475yr
    row.pga_2475yr_g = result.pga_2475yr
    row.spectral_accel_json = result.to_dict()
    row.nh01_source = result.source
    row.nh01_quality = result.quality
    row.fetched_at = now
    row.run_id = run_id

    comment_parts: list[str] = []
    if result.model_name:
        comment_parts.append(f"Model: {result.model_name}")
    if result.hazard_curve:
        comment_parts.append(f"Hazard curve: {len(result.hazard_curve.imls)} IML points")
    if result.uhs:
        comment_parts.append(f"UHS: {len(result.uhs.periods)} periods")
    elif result.sa_values:
        comment_parts.append(f"SA(T) from curves: {len(result.sa_values)} periods")
    else:
        comment_parts.append("UHS: unavailable (spectra endpoint non-functional)")
    if result.grid_distance_km > 0:
        comment_parts.append(f"Grid distance: {result.grid_distance_km:.1f} km")
    row.nh01_comment = "; ".join(comment_parts) if comment_parts else None

    if result.quality != "high":
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-01", source_type="api",
            observation=result.error or f"Source: {result.source}",
            impact="negative" if result.quality == "low" else "neutral",
            confidence=result.quality, run_id=run_id,
        ))
    if "gem_global" in result.source:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-01", source_type="api",
            observation="GEM global fallback used instead of EFEHR. No hazard curve or UHS available.",
            impact="negative", confidence="medium", run_id=run_id,
        ))
    if result.grid_distance_km > 15.0:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-01", source_type="api",
            observation=f"Nearest EFEHR grid node is {result.grid_distance_km:.1f} km from site (threshold: 15 km)",
            impact="negative", confidence="low", run_id=run_id,
        ))


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-01", source_type="api",
        observation=f"Enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))


def _log_seismic_raw(
    session: Session,
    connector: SeismicHazardConnector,
    site_id: uuid.UUID,
    run_id: str,
    result: SeismicHazardResult | None,
    *,
    error: str | None = None,
) -> None:
    """Persist this site's accumulated EFEHR calls + assembled result.

    Combines every per-call entry from ``connector.consume_raw_call_log()``
    into a single ``response_body`` dict so the disk file and DB row contain
    the full EFEHR/GEM dialogue for the site plus the parsed assessment.
    """
    calls = connector.consume_raw_call_log()
    body: dict[str, Any] = {
        "type": "seismic_hazard_assessment",
        "calls": calls,
    }
    if result is not None:
        body["result"] = {
            "lat": result.lat,
            "lon": result.lon,
            "pga_475yr": result.pga_475yr,
            "pga_2475yr": result.pga_2475yr,
            "source": result.source,
            "model_name": result.model_name,
            "model_id": result.model_id,
            "grid_distance_km": result.grid_distance_km,
            "quality": result.quality,
            "error": result.error,
            "sa_values": result.sa_values,
        }
    if error is not None:
        body["error"] = error

    last_status = next(
        (c["http_status"] for c in reversed(calls) if c.get("http_status") is not None),
        None,
    )
    base_url = getattr(connector, "_base_url", "") or ""
    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="seismic_hazard",
        run_id=run_id,
        request_url=base_url,
        response_body=body,
        http_status=last_status,
    )


def _write_batch_metadata(batch: BatchResult) -> None:
    """LL-024: Write batch-level audit metadata to disk for reproducibility."""
    meta_dir = Path("sources") / "seismic_hazard"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / f"batch_{batch.run_id}.meta.json"

    source_counts: dict[str, int] = {}
    quality_counts: dict[str, int] = {}
    errors: list[dict[str, str]] = []
    for s in batch.per_site:
        src = s.source or "unknown"
        source_counts[src] = source_counts.get(src, 0) + 1
        if s.status == "error" and s.error:
            errors.append({"site_id": str(s.site_id), "error": s.error})

    meta = {
        "run_id": batch.run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sites": batch.total_sites,
        "succeeded": batch.succeeded,
        "failed": batch.failed,
        "cached": batch.skipped_cached,
        "elapsed_s": round(batch.elapsed_s, 1),
        "source_distribution": source_counts,
        "errors": errors[:20],
    }

    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log.info("seismic_batch_metadata_written", path=str(meta_path))
