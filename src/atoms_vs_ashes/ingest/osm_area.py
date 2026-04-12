# man_hours: 8.0
"""Ingest site boundary areas from OpenStreetMap power-plant polygons.

Iterates over all sites, queries the OSM Overpass API for ``power=plant``
polygons near each site's coordinates, computes geodesic area, and persists
the result as ``site_area_ha`` on the ``sites`` table.  A :class:`DataSource`
provenance record is maintained in ``data_sources``, and quality issues are
logged via :class:`SiteObservation`.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm import (
    fetch_plant_boundaries,
    find_best_plant_boundary,
    health_check,
)
from atoms_vs_ashes.db.models import AuditLog, DataSource, Site, SiteObservation
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

OSM_SOURCE_NAME = "OpenStreetMap Overpass API"
OSM_SOURCE_URL = "https://overpass-api.de/api/interpreter"
REQUEST_DELAY_S = 1.1


def _ensure_data_source(session: Session) -> DataSource:
    """Get or create the OSM data-source provenance record."""
    stmt = select(DataSource).where(DataSource.name == OSM_SOURCE_NAME)
    source = session.execute(stmt).scalar_one_or_none()
    if source is None:
        source = DataSource(
            name=OSM_SOURCE_NAME,
            url=OSM_SOURCE_URL,
            description=(
                "OpenStreetMap power=plant polygons queried via Overpass API. "
                "Used to determine coal plant site boundary areas in hectares."
            ),
        )
        session.add(source)
        session.flush()
    return source


def ingest_site_areas(
    session: Session,
    settings: Settings,
    *,
    run_id: str,
    search_radius_m: int = 2000,
    skip_if_populated: bool = True,
    request_delay_s: float = REQUEST_DELAY_S,
) -> dict[str, int]:
    """Fetch OSM plant boundaries and update ``site_area_ha`` for all sites.

    Parameters
    ----------
    skip_if_populated:
        When *True*, sites that already have a non-NULL ``site_area_ha``
        are left untouched.
    request_delay_s:
        Minimum pause between Overpass requests (rate-limit courtesy).

    Returns
    -------
    dict with keys ``updated``, ``skipped``, ``no_match``, ``error``.
    """
    if not health_check():
        log.error("osm_overpass_unreachable")
        raise ConnectionError("Overpass API is not reachable")

    source = _ensure_data_source(session)
    source.last_fetched = datetime.now(timezone.utc)

    sites = session.execute(select(Site)).scalars().all()
    counts = {"updated": 0, "skipped": 0, "no_match": 0, "error": 0}

    for site in sites:
        if skip_if_populated and site.site_area_ha is not None:
            counts["skipped"] += 1
            continue

        lat = float(site.latitude)
        lon = float(site.longitude)

        try:
            boundaries = fetch_plant_boundaries(
                lat, lon, radius_m=search_radius_m,
            )
            best = find_best_plant_boundary(lat, lon, boundaries)
        except Exception as exc:
            log.warning(
                "osm_fetch_error",
                site_id=str(site.site_id),
                name=site.name,
                error=str(exc),
            )
            session.add(
                SiteObservation(
                    site_id=site.site_id,
                    criterion_id="NS-05",
                    source_type="api",
                    observation=f"OSM Overpass query failed: {exc}",
                    impact="negative",
                    confidence="low",
                    run_id=run_id,
                )
            )
            counts["error"] += 1
            time.sleep(request_delay_s)
            continue

        if best is None:
            log.info(
                "no_osm_boundary",
                site_id=str(site.site_id),
                name=site.name,
            )
            session.add(
                SiteObservation(
                    site_id=site.site_id,
                    criterion_id="NS-05",
                    source_type="api",
                    observation=(
                        f"No power=plant polygon found within {search_radius_m} m "
                        f"of site coordinates ({lat}, {lon})"
                    ),
                    impact="negative",
                    confidence="low",
                    run_id=run_id,
                )
            )
            counts["no_match"] += 1
        else:
            old_area = float(site.site_area_ha) if site.site_area_ha else None
            site.site_area_ha = round(best.area_ha, 2)
            site.updated_at = datetime.now(timezone.utc)

            session.add(
                AuditLog(
                    operation="update",
                    table_name="sites",
                    site_id=site.site_id,
                    before_value={"site_area_ha": old_area},
                    after_value={
                        "site_area_ha": best.area_ha,
                        "osm_id": best.osm_id,
                        "osm_type": best.osm_type,
                        "osm_name": best.name,
                        "centroid_lat": best.centroid_lat,
                        "centroid_lon": best.centroid_lon,
                    },
                    run_id=run_id,
                    message=(
                        f"Site area from OSM {best.osm_type}/{best.osm_id} "
                        f"({best.name or 'unnamed'}): {best.area_ha:.2f} ha"
                    ),
                )
            )
            log.info(
                "site_area_updated",
                site_id=str(site.site_id),
                name=site.name,
                area_ha=best.area_ha,
                osm_id=best.osm_id,
            )
            counts["updated"] += 1

        time.sleep(request_delay_s)

    session.add(
        AuditLog(
            operation="ingest",
            table_name="sites",
            run_id=run_id,
            message=(
                f"OSM site area ingestion: "
                f"{counts['updated']} updated, {counts['skipped']} skipped, "
                f"{counts['no_match']} no match, {counts['error']} errors"
            ),
        )
    )

    log.info("osm_area_ingestion_complete", **counts)
    return counts
