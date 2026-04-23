# man_hours: 3.0
"""Batch enrichment and DB persistence for the S-03 OneGeology connector.

S-03 is a *supplementary* connector: it only writes to SiteNaturalHazards
for NH-02 and NH-05 where S-02 EGDI data is insufficient or low quality.

Persistence contract:
  NH-02 row is written only if s02 nh02_quality ∈ {None, "insufficient", "low"}.
  NH-05 row is written only if s02 nh05_quality ∈ {None, "insufficient", "low"}.
  Written value_json includes supplementation provenance metadata.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.onegeology.models import (
    BatchResult,
    OneGeologyResult,
    S02_SUPPLEMENT_THRESHOLD,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteNaturalHazards,
    SiteObservation,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.onegeology.client import OneGeologyConnector

log = get_logger(__name__)

_SOURCE_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "onegeology_national_faults": (
        "https://onegeology.org/",
        "OneGeology national geological survey — fault proximity (NH-02 supplement)",
    ),
    "onegeology_national_karst": (
        "https://onegeology.org/",
        "OneGeology national geological survey — karst zones (NH-05 supplement)",
    ),
}


def enrich_site(
    connector: OneGeologyConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist OneGeology data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id, site_name="<unknown>", status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()

    nh_row = session.get(SiteNaturalHazards, site_id)
    s02_nh02_quality = nh_row.nh02_quality if nh_row else None
    s02_nh05_quality = nh_row.nh05_quality if nh_row else None

    # Skip if S-02 already provided adequate data for both criteria
    if (
        s02_nh02_quality not in S02_SUPPLEMENT_THRESHOLD
        and s02_nh05_quality not in S02_SUPPLEMENT_THRESHOLD
    ):
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "onegeology_skip_s02_adequate",
            site_id=str(site_id), site_name=site.name,
            nh02=s02_nh02_quality, nh05=s02_nh05_quality,
        )
        _log_skip(
            session, site_id, run_id, "s02_adequate",
            nh02=s02_nh02_quality, nh05=s02_nh05_quality,
            country_code=site.country_code,
        )
        session.commit()
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="s02_adequate",
            quality="s02_adequate", elapsed_ms=elapsed,
        )

    # Cache check on S-03 data itself (nh02_source == "onegeology_national_faults")
    if _check_cache(session, site_id, connector._cache_ttl_days):
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("onegeology_cache_hit", site_id=str(site_id))
        _log_skip(
            session, site_id, run_id, "cached",
            nh02=s02_nh02_quality, nh05=s02_nh05_quality,
            country_code=site.country_code,
        )
        session.commit()
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            elapsed_ms=elapsed,
        )

    _ensure_data_sources(session)

    try:
        result = connector.fetch_all(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code or "",
            s02_nh02_quality=s02_nh02_quality,
            s02_nh05_quality=s02_nh05_quality,
        )

        if not result.supplements_s02 and not result.endpoints_queried:
            # No endpoint registered for this country
            elapsed = int((time.monotonic() - t0) * 1000)
            log.info(
                "onegeology_no_endpoint",
                site_id=str(site_id), country=site.country_code,
            )
            _log_skip(
                session, site_id, run_id, "no_endpoint",
                nh02=s02_nh02_quality, nh05=s02_nh05_quality,
                country_code=site.country_code,
            )
            session.commit()
            return SiteEnrichmentSummary(
                site_id=site_id, site_name=site.name,
                status="no_endpoint", elapsed_ms=elapsed,
            )

        criteria = _persist_result(session, site_id, result, run_id)
        combined = {
            "layers": connector.last_raw_responses or [],
            "endpoints_queried": result.endpoints_queried,
            "endpoints_failed": result.endpoints_failed,
            "supplements_s02": result.supplements_s02,
        }
        log_raw_response(
            session,
            site_id=site_id,
            connector_slug="onegeology",
            run_id=run_id,
            request_url=(
                result.endpoints_queried[0] if result.endpoints_queried else ""
            ),
            response_body=combined,
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "onegeology_site_complete",
            site_id=str(site_id), site_name=site.name,
            quality=result.quality, criteria_count=len(criteria), elapsed_ms=elapsed,
        )
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="ok",
            criteria_written=criteria, quality=result.quality, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("onegeology_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: OneGeologyConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
    """Enrich multiple sites with per-site commit isolation and progress logging.

    S-03 is expected to be fast: most EU sites will be skipped because S-02
    EGDI already provided adequate NH-02 data. S-03 adds value primarily for
    karst (21 countries without EGDI karst coverage) and non-EU fault mapping.
    """
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

        nh_row = session.get(SiteNaturalHazards, site.site_id)
        s02_nh02_quality = nh_row.nh02_quality if nh_row else None
        s02_nh05_quality = nh_row.nh05_quality if nh_row else None

        if (
            s02_nh02_quality not in S02_SUPPLEMENT_THRESHOLD
            and s02_nh05_quality not in S02_SUPPLEMENT_THRESHOLD
        ):
            log.info(
                "onegeology_skip_s02_adequate",
                site_id=str(site.site_id), country=site.country_code,
            )
            _log_skip(
                session, site.site_id, run_id, "s02_adequate",
                nh02=s02_nh02_quality, nh05=s02_nh05_quality,
                country_code=site.country_code,
            )
            session.commit()
            batch.skipped_s02_adequate += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name,
                status="s02_adequate", elapsed_ms=elapsed_ms,
            ))
            continue

        if _check_cache(session, site.site_id, connector._cache_ttl_days):
            log.info("onegeology_cache_hit", site_id=str(site.site_id))
            _log_skip(
                session, site.site_id, run_id, "cached",
                nh02=s02_nh02_quality, nh05=s02_nh05_quality,
                country_code=site.country_code,
            )
            session.commit()
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name,
                status="cached", elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.fetch_all(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code or "",
                s02_nh02_quality=s02_nh02_quality,
                s02_nh05_quality=s02_nh05_quality,
            )

            if not result.supplements_s02 and not result.endpoints_queried:
                log.info(
                    "onegeology_no_endpoint",
                    site_id=str(site.site_id), country=site.country_code,
                )
                _log_skip(
                    session, site.site_id, run_id, "no_endpoint",
                    nh02=s02_nh02_quality, nh05=s02_nh05_quality,
                    country_code=site.country_code,
                )
                session.commit()
                batch.skipped_no_endpoint += 1
                elapsed_ms = int((time.monotonic() - site_start) * 1000)
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name,
                    status="no_endpoint", elapsed_ms=elapsed_ms,
                ))
                continue

            criteria = _persist_result(session, site.site_id, result, run_id)
            combined = {
                "layers": connector.last_raw_responses or [],
                "endpoints_queried": result.endpoints_queried,
                "endpoints_failed": result.endpoints_failed,
                "supplements_s02": result.supplements_s02,
            }
            log_raw_response(
                session,
                site_id=site.site_id,
                connector_slug="onegeology",
                run_id=run_id,
                request_url=(
                    result.endpoints_queried[0] if result.endpoints_queried else ""
                ),
                response_body=combined,
            )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "onegeology_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                quality=result.quality, criteria_count=len(criteria),
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="ok",
                criteria_written=criteria, quality=result.quality,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error("onegeology_site_error", site_id=str(site.site_id), error=str(exc))
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
                "onegeology_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, failed=batch.failed,
                skipped_s02=batch.skipped_s02_adequate,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "onegeology_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        failed=batch.failed, cached=batch.skipped_cached,
        s02_adequate=batch.skipped_s02_adequate,
        no_endpoint=batch.skipped_no_endpoint,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------


def _check_cache(
    session: Session,
    site_id: uuid.UUID,
    ttl_days: int,
) -> bool:
    """Return True if S-03 already wrote NH-02 or NH-05 within the TTL window."""
    row = session.get(SiteNaturalHazards, site_id)
    if not row:
        return False
    # Detect an S-03 write: source is our connector name
    s03_wrote = row.nh02_source == "onegeology_national_faults" or (
        row.nh05_comment is not None and "onegeology" in (row.nh05_comment or "")
    )
    if not s03_wrote:
        return False
    if row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return True
    return False


def _ensure_data_sources(session: Session) -> None:
    for name, (url, description) in _SOURCE_DESCRIPTIONS.items():
        existing = session.query(DataSource).filter_by(name=name).first()
        if not existing:
            ds = DataSource(
                name=name, url=url, description=description,
                last_fetched=datetime.now(timezone.utc),
            )
            session.add(ds)
            session.flush()


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: OneGeologyResult,
    run_id: str,
) -> list[str]:
    """Write S-03 supplementary data to SiteNaturalHazards.

    Only writes criteria where S-02 had insufficient/low quality.
    The value_json includes supplementation provenance.
    """
    now = datetime.now(timezone.utc)
    written: list[str] = []

    nh_row = session.get(SiteNaturalHazards, site_id)
    if nh_row is None:
        nh_row = SiteNaturalHazards(site_id=site_id)
        session.add(nh_row)

    # NH-02 — Fault proximity supplement
    if result.faults is not None:
        if result.faults.nearest_fault_distance_km is not None:
            nh_row.nearest_fault_km = result.faults.nearest_fault_distance_km
        nh_row.nh02_quality = "medium" if result.faults.fault_count_within_buffer > 0 else "low"
        nh_row.nh02_source = "onegeology_national_faults"
        nh_row.nh02_comment = (
            f"Supplemented by S-03 OneGeology from {result.faults.source_endpoint}; "
            f"{result.faults.fault_count_within_buffer} fault(s) within buffer"
        )
        written.append("NH-02")
    elif result.faults is None and _s02_needs_supplement("NH-02", nh_row):
        # No endpoint or query failed — record the gap
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-02", source_type="api",
            observation=(
                "S-03 OneGeology: no national survey endpoint registered for "
                f"country '{result.country_code}'; NH-02 remains at S-02 quality"
            ),
            impact="negative", confidence="low", run_id=run_id,
        ))

    # NH-05 — Karst supplement
    if result.karst is not None:
        nh_row.karst_present = result.karst.in_karst_zone
        if result.karst.karst_class:
            nh_row.karst_formation_type = result.karst.karst_class
        quality = "medium" if result.karst.in_karst_zone else "low"
        nh_row.nh05_quality = quality
        nh_row.nh05_comment = (
            f"onegeology: supplemented from {result.karst.source_endpoint}; "
            f"layer={result.karst.source_layer}; "
            f"in_karst_zone={result.karst.in_karst_zone}"
        )
        written.append("NH-05")
    elif result.karst is None and _s02_needs_supplement("NH-05", nh_row):
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-05", source_type="api",
            observation=(
                "S-03 OneGeology: no karst layer registered for "
                f"country '{result.country_code}'; NH-05 remains insufficient"
            ),
            impact="negative", confidence="low", run_id=run_id,
        ))

    nh_row.fetched_at = now
    nh_row.run_id = run_id
    return written


def _s02_needs_supplement(criterion_id: str, nh_row: SiteNaturalHazards | None) -> bool:
    """Return True if the criterion still needs supplementation."""
    if nh_row is None:
        return True
    if criterion_id == "NH-02":
        return nh_row.nh02_quality in S02_SUPPLEMENT_THRESHOLD
    if criterion_id == "NH-05":
        return nh_row.nh05_quality in S02_SUPPLEMENT_THRESHOLD
    return False


def _persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-02", source_type="api",
        observation=f"S-03 OneGeology enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))


def _log_skip(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    skip_reason: str,
    *,
    nh02: str | None,
    nh05: str | None,
    country_code: str | None,
) -> None:
    """Log an audit row when S-03 short-circuits without hitting OneGeology.

    The S-03 connector intentionally skips most EU sites because S-02 EGDI
    already provided adequate NH-02 / NH-05 data.  Per the mandatory raw-
    response logging contract, we still emit a row so an auditor can see
    that S-03 evaluated the site and chose not to call out.
    """
    body: dict[str, Any] = {
        "type": "onegeology_skip",
        "skip_reason": skip_reason,
        "country_code": country_code,
        "s02_quality": {"nh02": nh02, "nh05": nh05},
    }
    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="onegeology",
        run_id=run_id,
        request_url="onegeology://skip",
        response_body=body,
        http_status=None,
    )
