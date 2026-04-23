# man_hours: 1.5
"""Batch wrapper for ``PopulationConnector`` with mandatory raw response logging.

Population is consumed by several screening checks (RI-04, RI-06, EP-01).
Historically each caller invoked :meth:`PopulationConnector.fetch` directly
and no raw responses were persisted.

This module provides the canonical ``enrich_site``/``enrich_batch`` entry
points required by the raw-response logging contract
(see ``.cursor/rules/raw-response-logging.mdc``).  Each call dual-writes the
combined Overpass + GeoNames raw payload to the ``site_raw_responses`` table
and to ``data/raw_responses/population/<run_id>/<site_id>.json``.

The Overpass calls themselves are also captured by the OSM client's internal
accumulator; we drain that buffer here so the population row contains the
full chain of per-site HTTP traffic in one place.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.population.models import (
    DEFAULT_CITY_THRESHOLD,
    DEFAULT_RADII_KM,
    PopulationResult,
)
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.population.client import PopulationConnector

log = get_logger(__name__)


def enrich_site(
    connector: PopulationConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
    *,
    radii_km: list[float] | None = None,
    city_threshold: int = DEFAULT_CITY_THRESHOLD,
) -> PopulationResult:
    """Fetch population for one site and dual-write the raw response."""
    site = session.get(Site, site_id)
    if site is None:
        raise ValueError(f"Site {site_id} not found")

    lat, lon = float(site.latitude), float(site.longitude)
    t0 = time.monotonic()

    _reset_overpass_log(connector)

    try:
        result = connector.fetch(
            lat,
            lon,
            radii_km=radii_km or list(DEFAULT_RADII_KM),
            city_threshold=city_threshold,
        )
        _log_population_raw(session, connector, site_id, run_id, lat, lon, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info(
            "population_site_complete",
            site_id=str(site_id),
            site_name=site.name,
            total_population=result.total_population_80km,
            elapsed_ms=elapsed,
        )
        return result
    except Exception as exc:
        session.rollback()
        try:
            _log_population_raw(
                session, connector, site_id, run_id, lat, lon,
                None, error=str(exc),
            )
            session.commit()
        except Exception as log_exc:
            session.rollback()
            log.warning("population_raw_log_after_error_failed", error=str(log_exc))
        log.error("population_site_error", site_id=str(site_id), error=str(exc))
        raise


def enrich_batch(
    connector: PopulationConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    radii_km: list[float] | None = None,
    city_threshold: int = DEFAULT_CITY_THRESHOLD,
) -> list[PopulationResult]:
    """Enrich multiple sites with per-site commit isolation."""
    query = session.query(Site)
    if site_ids is not None:
        if not site_ids:
            return []
        query = query.filter(Site.site_id.in_(site_ids))
    elif country_codes is not None:
        query = query.filter(Site.country_code.in_(country_codes))

    sites = query.order_by(Site.country_code, Site.name).all()
    if not sites:
        return []

    out: list[PopulationResult] = []
    radii = radii_km or list(DEFAULT_RADII_KM)

    for i, site in enumerate(sites):
        try:
            result = enrich_site(
                connector,
                site.site_id,
                session,
                run_id,
                radii_km=radii,
                city_threshold=city_threshold,
            )
            out.append(result)
        except Exception as exc:
            log.error(
                "population_batch_site_failed",
                site_id=str(site.site_id),
                error=str(exc),
            )

        if (i + 1) % 25 == 0:
            log.info(
                "population_batch_progress",
                completed=i + 1,
                total=len(sites),
            )

    return out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _reset_overpass_log(connector: PopulationConnector) -> None:
    """Clear OverpassClient's per-call accumulator before a fetch."""
    overpass = getattr(connector, "_overpass", None)
    reset = getattr(overpass, "reset_raw_call_log", None)
    if callable(reset):
        reset()


def _drain_overpass_log(connector: PopulationConnector) -> list[dict[str, Any]]:
    overpass = getattr(connector, "_overpass", None)
    consume = getattr(overpass, "consume_raw_call_log", None)
    if callable(consume):
        return consume()
    return []


def _log_population_raw(
    session: Session,
    connector: PopulationConnector,
    site_id: uuid.UUID,
    run_id: str,
    lat: float,
    lon: float,
    result: PopulationResult | None,
    *,
    error: str | None = None,
) -> None:
    """Dual-write the per-site population payload to disk and DB."""
    overpass_calls = _drain_overpass_log(connector)

    body: dict[str, Any] = {
        "type": "population_assessment",
        "lat": lat,
        "lon": lon,
        "overpass_calls": overpass_calls,
        "geonames": {
            "url": getattr(connector, "last_geonames_url", None),
            "params": getattr(connector, "last_geonames_params", None),
            "status": getattr(connector, "last_geonames_status", None),
            "response": getattr(connector, "last_geonames_response", None),
        },
    }
    if result is not None:
        body["assessment"] = result.to_dict()
    if error is not None:
        body["error"] = error

    log_raw_response(
        session,
        site_id=site_id,
        connector_slug="population",
        run_id=run_id,
        request_url=getattr(connector, "last_geonames_url", "") or "overpass+geonames",
        request_params=getattr(connector, "last_geonames_params", None),
        response_body=body,
        http_status=getattr(connector, "last_geonames_status", None),
    )
