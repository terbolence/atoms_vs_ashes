# man_hours: 3.0
"""Batch: write GeoNames nearest city to Site.extended_data; optionally RI-05 columns."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session
from sqlalchemy.orm import attributes as orm_attributes

from atoms_vs_ashes.connectors.geonames_dump.models import (
    EXTENDED_DATA_KEY,
    RI05_QUALITY_TAG,
    SOURCE_DESCRIPTION,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    NearestGeonamesResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.db.models import DataSource, Site, SiteRadiological
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.geonames_dump.client import GeonamesDumpConnector

log = get_logger(__name__)


def enrich_batch(
    connector: GeonamesDumpConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    overwrite_ri05: bool = False,
) -> BatchResult:
    """For each site: merge extended_data; fill SiteRadiological RI-05 if gap or overwrite."""
    batch = BatchResult(run_id=run_id)
    t0 = time.monotonic()

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

    if not connector.data_loaded():
        connector.load_cities()

    _ensure_data_source(session)
    dump_date = connector.dump_date_iso()

    for i, site in enumerate(sites):
        site_start = time.monotonic()
        try:
            lat = float(site.latitude)
            lon = float(site.longitude)
            nearest = connector.nearest_for(lat, lon)

            _merge_extended_data(
                session, site, nearest, dump_date=dump_date,
            )
            batch.extended_data_written += 1

            ri_updated = _maybe_update_ri05_main(
                session,
                site.site_id,
                nearest,
                run_id,
                overwrite=overwrite_ri05,
            )
            if ri_updated:
                batch.ri05_main_filled += 1

            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="ok",
                nearest_name=nearest.name if nearest else None,
                distance_km=nearest.distance_km if nearest else None,
                ri05_main_updated=ri_updated,
                elapsed_ms=elapsed_ms,
            ))
        except Exception as exc:
            session.rollback()
            log.error(
                "geonames_dump_site_error",
                site_id=str(site.site_id),
                error=str(exc),
            )
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="error",
                error=str(exc),
                elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 50 == 0:
            log.info(
                "geonames_dump_progress",
                done=i + 1,
                total=len(sites),
                succeeded=batch.succeeded,
                failed=batch.failed,
            )

    batch.elapsed_s = time.monotonic() - t0
    log.info(
        "geonames_dump_batch_done",
        run_id=run_id,
        total=batch.total_sites,
        succeeded=batch.succeeded,
        failed=batch.failed,
        extended_data=batch.extended_data_written,
        ri05_main_filled=batch.ri05_main_filled,
    )
    return batch


def _ensure_data_source(session: Session) -> uuid.UUID:
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        return existing.source_id
    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _merge_extended_data(
    session: Session,
    site: Site,
    nearest: NearestGeonamesResult | None,
    *,
    dump_date: str,
) -> None:
    payload = (
        nearest.to_extended_data_dict(dump_date=dump_date)
        if nearest
        else {
            "source": SOURCE_NAME,
            "dump_date": dump_date,
            "attribution": "GeoNames (CC BY 4.0)",
            "nearest": None,
            "reason": "no_matching_city_after_filter",
        }
    )
    base = dict(site.extended_data) if site.extended_data else {}
    base[EXTENDED_DATA_KEY] = payload
    site.extended_data = base
    orm_attributes.flag_modified(site, "extended_data")


def _maybe_update_ri05_main(
    session: Session,
    site_id: uuid.UUID,
    nearest: NearestGeonamesResult | None,
    run_id: str,
    *,
    overwrite: bool,
) -> bool:
    """Return True if SiteRadiological RI-05 columns were written."""
    if nearest is None:
        return False

    ri = session.get(SiteRadiological, site_id)
    if ri is None:
        ri = SiteRadiological(site_id=site_id)
        session.add(ri)

    if not overwrite and ri.nearest_city_name is not None:
        return False

    ri.nearest_city_50k_km = nearest.distance_km
    ri.nearest_city_name = nearest.name
    ri.nearest_city_pop = nearest.population
    ri.ri05_quality = RI05_QUALITY_TAG
    ri.ri05_comment = (
        f"Nearest place ≥50k (GeoNames {nearest.dump_label}): {nearest.name} "
        f"({nearest.country_code}), pop {nearest.population:,}, "
        f"{nearest.distance_km:.1f} km, geonameid={nearest.geoname_id}. "
        f"{nearest.attribution}."
    )
    ri.fetched_at = datetime.now(timezone.utc)
    ri.run_id = run_id
    return True
