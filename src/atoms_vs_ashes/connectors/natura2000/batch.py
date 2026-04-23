# man_hours: 4.0
"""Batch enrichment and DB persistence for the Natura 2000 connector.

Handles per-site commit isolation, cache-based resumability, progress
logging, and writes to ``SiteInfrastructureV2`` / ``SiteObservation`` /
``ScreeningVerdict`` tables.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.connectors.natura2000.models import (
    SOURCE_NAME,
    BatchResult,
    Natura2000Result,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import (
    ScreeningVerdict,
    Site,
    SiteInfrastructureV2,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.natura2000.client import Natura2000Connector

log = get_logger(__name__)

CRITERION_ID = "NS-08"
# Abort batch after this many consecutive EU sites where the EEA API fails
# (avoids ~8+ minutes per site when the service is down).
CIRCUIT_FAILURE_THRESHOLD = 2
DEFAULT_WFS_URL = (
    "https://bio.discomap.eea.europa.eu/arcgis/services/"
    "ProtectedSites/Natura2000Sites/MapServer/WFSServer"
)


def _is_transport_failure(result: Natura2000Result) -> bool:
    """True when the connector could not reach EEA (vs valid empty response)."""
    err = (result.error or "").lower()
    if result.quality != "low":
        return False
    return (
        "failed after retries" in err
        or "wfs query failed" in err
        or "timeout" in err
    )


def enrich_site(
    connector: Natura2000Connector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist Natura 2000 data for a single DB site."""
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
        log.info("natura2000_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="cached",
            sensitivity_class=cached.ns08_comment,
            elapsed_ms=elapsed,
        )

    try:
        result = connector.fetch(
            float(site.latitude), float(site.longitude),
            country_code=site.country_code,
        )
        _persist_result(session, site_id, result, run_id)
        _persist_screening_verdict(session, site_id, result, run_id)
        _log_natura2000_raw(session, connector, site_id, run_id, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)

        status = "non_eu" if not result.is_eu_member else "ok"
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status=status,
            sensitivity_class=result.sensitivity_class,
            nearest_distance_km=result.n2k_nearest_distance_km,
            source=result.source, elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"Natura 2000 enrichment failed: {exc}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("natura2000_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id, site_name=site.name, status="error",
            error=str(exc), elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: Natura2000Connector,
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
        "natura2000_batch_start", run_id=run_id,
        total=batch.total_sites,
        expected_api_calls=sum(
            1 for s in sites
            if s.country_code in connector._eu_member_states
        ),
    )

    consecutive_transport_failures = 0

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("natura2000_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name, status="cached",
                elapsed_ms=elapsed_ms,
            ))
            continue

        is_eu = site.country_code in connector._eu_member_states

        try:
            result = connector.fetch(
                float(site.latitude), float(site.longitude),
                country_code=site.country_code,
            )
            _persist_result(session, site.site_id, result, run_id)
            _persist_screening_verdict(session, site.site_id, result, run_id)
            _log_natura2000_raw(
                session, connector, site.site_id, run_id, result,
            )
            session.commit()

            if is_eu:
                if result.quality == "high":
                    batch.succeeded += 1
                    consecutive_transport_failures = 0
                else:
                    batch.degraded += 1
                    if _is_transport_failure(result):
                        consecutive_transport_failures += 1
                    else:
                        consecutive_transport_failures = 0
            else:
                batch.skipped_non_eu += 1

            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            log.info(
                "natura2000_site_complete",
                site_id=str(site.site_id), site_name=site.name,
                index=i + 1, total=len(sites),
                sensitivity=result.sensitivity_class,
                nearest_km=result.n2k_nearest_distance_km,
                elapsed_ms=elapsed_ms,
            )
            eu_status = (
                "ok"
                if (is_eu and result.quality == "high")
                else ("degraded" if is_eu else "non_eu")
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id, site_name=site.name,
                status=eu_status,
                sensitivity_class=result.sensitivity_class,
                nearest_distance_km=result.n2k_nearest_distance_km,
                source=result.source, elapsed_ms=elapsed_ms,
            ))

            if (
                consecutive_transport_failures
                >= CIRCUIT_FAILURE_THRESHOLD
            ):
                remaining = len(sites) - (i + 1)
                batch.skipped_after_abort = remaining
                batch.aborted_reason = (
                    "EEA Natura 2000 API failed repeatedly (timeouts/503). "
                    "Remaining sites were not queried; retry when the service "
                    "recovers (see bio.discomap.eea.europa.eu status)."
                )
                log.error(
                    "natura2000_batch_circuit_abort",
                    run_id=run_id,
                    threshold=CIRCUIT_FAILURE_THRESHOLD,
                    skipped_remaining=remaining,
                )
                break
        except Exception as exc:
            session.rollback()
            log.error("natura2000_site_error", site_id=str(site.site_id), error=str(exc))
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_ID,
                observation=f"Natura 2000 enrichment failed: {exc}",
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
                "natura2000_batch_progress",
                completed=i + 1, total=len(sites),
                succeeded=batch.succeeded, degraded=batch.degraded,
                failed=batch.failed, non_eu=batch.skipped_non_eu,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

        if is_eu:
            time.sleep(connector._inter_request_delay)

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "natura2000_batch_done", run_id=run_id,
        total=batch.total_sites, succeeded=batch.succeeded,
        degraded=batch.degraded, failed=batch.failed,
        cached=batch.skipped_cached, non_eu=batch.skipped_non_eu,
        skipped_after_abort=batch.skipped_after_abort,
        aborted=bool(batch.aborted_reason),
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
    """Return cached row if NS-08 data is fresh for this run."""
    row = session.get(SiteInfrastructureV2, site_id)
    if row is None or row.ns08_quality is None:
        return None
    if row.fetched_at and row.run_id == run_id:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return row
    return None


def _ensure_data_source(session: Session) -> uuid.UUID:
    return ensure_data_source(
        session,
        name=SOURCE_NAME,
        url=DEFAULT_WFS_URL,
        description=(
            "EEA Natura 2000 WFS — protected site polygons for "
            "NS-08 ecological sensitivity assessment"
        ),
    )


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: Natura2000Result,
    run_id: str,
) -> None:
    """Write Natura 2000 data to SiteInfrastructureV2 NS-08 columns."""
    now = datetime.now(timezone.utc)

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)

    row.n2k_nearest_distance_km = result.n2k_nearest_distance_km
    row.n2k_overlap = result.n2k_overlap
    row.n2k_sensitivity_class = result.sensitivity_class
    row.n2k_result_json = result.to_dict()
    row.ns08_quality = result.quality
    row.ns08_source = SOURCE_NAME
    row.ns08_comment = result.sensitivity_class
    row.fetched_at = now
    row.run_id = run_id

    if result.quality not in ("high",):
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=result.error or f"Quality: {result.quality}",
            run_id=run_id,
            confidence=result.quality if result.quality != "insufficient" else "low",
            impact="negative" if result.quality == "low" else "blocking" if result.quality == "insufficient" else "neutral",
        )


def _persist_screening_verdict(
    session: Session,
    site_id: uuid.UUID,
    result: Natura2000Result,
    run_id: str,
) -> None:
    """Write ScreeningVerdict rows for NS-08 avoidance checks.

    Uses all SMR designs from the database to create per-SMR verdicts
    (NS-08 thresholds are reactor-independent, so all SMRs get the same verdict).
    """
    from atoms_vs_ashes.db.models import SmrDesign

    smr_designs = session.query(SmrDesign).all()
    if not smr_designs:
        log.warning("natura2000_no_smr_designs", site_id=str(site_id))
        return

    for smr in smr_designs:
        verdict, threshold, justification = _determine_verdict(result)

        measured = (
            f"{result.n2k_nearest_distance_km:.2f} km"
            if result.n2k_nearest_distance_km is not None else "N/A"
        )

        existing = (
            session.query(ScreeningVerdict)
            .filter_by(
                site_id=site_id,
                smr_key=smr.smr_key,
                criterion_id=CRITERION_ID,
                run_id=run_id,
            )
            .first()
        )
        if existing:
            existing.verdict = verdict
            existing.threshold = threshold
            existing.justification = justification
            existing.measured_value = measured
            existing.confidence = result.quality
            existing.data_sources = [SOURCE_NAME]
        else:
            session.add(ScreeningVerdict(
                site_id=site_id,
                smr_key=smr.smr_key,
                criterion_id=CRITERION_ID,
                phase="exclusionary",
                verdict=verdict,
                measured_value=measured,
                threshold=threshold,
                justification=justification,
                confidence=result.quality,
                data_sources=[SOURCE_NAME],
                run_id=run_id,
            ))


def _determine_verdict(
    result: Natura2000Result,
) -> tuple[str, str, str]:
    """Determine screening verdict from Natura 2000 result.

    Returns (verdict, threshold, justification).
    """
    if not result.is_eu_member:
        return (
            "inconclusive",
            "Natura 2000 coverage",
            f"Natura 2000 not applicable in {result.country_code}; "
            f"see S-15 WDPA for protected area data.",
        )

    if result.quality != "high":
        return (
            "inconclusive",
            "NS-08 data availability",
            result.error or f"Natura 2000 data quality is {result.quality}.",
        )

    if result.n2k_overlap:
        codes = ", ".join(result.n2k_overlap_sitecodes[:3])
        return (
            "fail",
            "Natura 2000 overlap",
            f"Site overlaps with Natura 2000 area(s): {codes}. "
            f"Habitats Directive Article 6(3) requires appropriate assessment; "
            f"likely prohibitive for nuclear siting.",
        )

    if (result.n2k_nearest_distance_km is not None
            and result.n2k_nearest_distance_km < 1.0):
        return (
            "fail",
            "<1 km from Natura 2000",
            f"Site is {result.n2k_nearest_distance_km:.2f} km from "
            f"Natura 2000 area {result.n2k_nearest_sitecode}: "
            f"{result.n2k_nearest_sitename}. "
            f"Proximate site may cause significant disturbance.",
        )

    if result.n2k_nearest_distance_km is not None:
        return (
            "pass",
            "≥1 km from Natura 2000",
            f"Nearest Natura 2000 site ({result.n2k_nearest_sitecode}) is "
            f"{result.n2k_nearest_distance_km:.1f} km away. "
            f"Sensitivity class: {result.sensitivity_class}.",
        )

    return (
        "pass",
        "No Natura 2000 sites within 25 km",
        "No Natura 2000 designated areas found within the 25 km search radius.",
    )


def _log_natura2000_raw(
    session: Session,
    connector: Natura2000Connector,
    site_id: uuid.UUID,
    run_id: str,
    result: Natura2000Result,
) -> None:
    """Dual-write the Natura 2000 raw response (or skip-decision) to disk + DB.

    For EU sites the connector hits the EEA WFS and exposes
    ``last_raw_response``.  For non-EU sites no live WFS query is made; the
    audit row records the skip reason instead so an auditor can see that the
    connector evaluated the site and chose not to call out.
    """
    raw_body = getattr(connector, "last_raw_response", None)
    request_url = getattr(connector, "last_request_url", None) or DEFAULT_WFS_URL
    request_params = getattr(connector, "last_request_params", None)
    http_status = getattr(connector, "last_http_status", None)

    if raw_body is None:
        raw_body = {
            "type": "natura2000_skip",
            "skip_reason": "non_eu" if not result.is_eu_member else "no_response",
            "country_code": result.country_code,
            "is_eu_member": result.is_eu_member,
            "result_quality": result.quality,
            "result_error": result.error,
            "sensitivity_class": result.sensitivity_class,
            "nearest_distance_km": result.n2k_nearest_distance_km,
        }

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="natura2000",
        run_id=run_id,
        request_url=request_url,
        request_params=request_params,
        response_body=raw_body,
        http_status=http_status,
    )
