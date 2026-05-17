# man_hours: 2.0
"""Backfill NH-08 distance-to-coast from S-38 Natural Earth coastline."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from sqlalchemy import select, text

from atoms_vs_ashes.connectors.natural_earth import (
    CoastlineDataset,
    compute_distance_to_coast_km,
    load_coastline_dataset,
)
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site

_SOURCE_NAME = "natural_earth_coastline_50m"
_SOURCE_URL = "https://www.naturalearthdata.com/downloads/50m-physical-vectors/"
_COMMENT_PREFIX = "Natural Earth coastline distance:"


@dataclass(frozen=True)
class SiteCoastDistance:
    site_id: uuid.UUID
    site_name: str
    country_code: str
    distance_km: float
    feature_count: int
    source_path: Path


def collect_distances(
    dataset: CoastlineDataset,
    *,
    limit: int | None = None,
    site_name: str | None = None,
) -> list[SiteCoastDistance]:
    """Compute S-38 coast distances for sites with coordinates."""
    out: list[SiteCoastDistance] = []
    with session_scope() as session:
        stmt = select(
            Site.site_id,
            Site.name,
            Site.country_code,
            Site.latitude,
            Site.longitude,
        ).order_by(Site.country_code, Site.name)
        if site_name:
            stmt = stmt.where(Site.name.ilike(f"%{site_name}%"))
        if limit:
            stmt = stmt.limit(limit)
        for site_id, name, country_code, latitude, longitude in session.execute(stmt).all():
            distance = compute_distance_to_coast_km(
                lat=float(latitude),
                lon=float(longitude),
                dataset=dataset,
            )
            out.append(
                SiteCoastDistance(
                    site_id=site_id,
                    site_name=str(name),
                    country_code=str(country_code),
                    distance_km=distance.distance_km,
                    feature_count=distance.feature_count,
                    source_path=distance.source_path,
                )
            )
    return out


def apply_distances(distances: Sequence[SiteCoastDistance]) -> int:
    """Persist S-38 distances to ``site_natural_hazards``."""
    updated = 0
    with session_scope() as session:
        _ensure_data_source(session)
        for item in distances:
            existing_comment = session.execute(
                text(
                    "select nh08_comment from site_natural_hazards "
                    "where site_id = :site_id"
                ),
                {"site_id": item.site_id},
            ).scalar_one_or_none()
            merged_comment = _merge_comment(existing_comment, item)
            session.execute(
                text(
                    """
                    insert into site_natural_hazards (
                        site_id, distance_to_coast_km, nh08_quality, nh08_comment
                    )
                    values (:site_id, :distance_to_coast_km, :nh08_quality, :nh08_comment)
                    on conflict (site_id) do update set
                        distance_to_coast_km = excluded.distance_to_coast_km,
                        nh08_quality = excluded.nh08_quality,
                        nh08_comment = excluded.nh08_comment
                    """
                ),
                {
                    "site_id": item.site_id,
                    "distance_to_coast_km": item.distance_km,
                    "nh08_quality": "medium",
                    "nh08_comment": merged_comment,
                },
            )
            updated += 1
    return updated


def summarize(distances: Sequence[SiteCoastDistance]) -> dict[str, object]:
    """Return coverage and NH-08 threshold-bucket summary."""
    buckets = {
        "<2": 0,
        "2-5": 0,
        "5-10": 0,
        "10-50": 0,
        ">50": 0,
    }
    for item in distances:
        d = item.distance_km
        if d < 2:
            buckets["<2"] += 1
        elif d < 5:
            buckets["2-5"] += 1
        elif d < 10:
            buckets["5-10"] += 1
        elif d <= 50:
            buckets["10-50"] += 1
        else:
            buckets[">50"] += 1
    anchors = [
        {
            "site_id": str(item.site_id),
            "site_name": item.site_name,
            "country_code": item.country_code,
            "distance_to_coast_km": item.distance_km,
        }
        for item in distances
        if _is_anchor(item.site_name)
    ]
    return {
        "count": len(distances),
        "buckets": buckets,
        "min_km": min((d.distance_km for d in distances), default=None),
        "max_km": max((d.distance_km for d in distances), default=None),
        "anchors": anchors,
    }


def _ensure_data_source(session) -> None:
    session.execute(
        text(
            """
            insert into data_sources (source_id, name, url, description, last_fetched)
            values (
                :source_id, :name, :url, :description, :last_fetched
            )
            on conflict (name) do update set
                url = excluded.url,
                description = excluded.description,
                last_fetched = excluded.last_fetched
            """
        ),
        {
            "source_id": uuid.uuid4(),
            "name": _SOURCE_NAME,
            "url": _SOURCE_URL,
            "description": (
                "Natural Earth 1:50m physical coastline, public-domain static "
                "vector used for S-38 NH-08 coast-distance screening."
            ),
            "last_fetched": datetime.now(timezone.utc),
        },
    )


def _merge_comment(existing: str | None, item: SiteCoastDistance) -> str:
    parts = [
        p.strip()
        for p in (existing or "").split(";")
        if p.strip() and not p.strip().startswith(_COMMENT_PREFIX)
    ]
    parts.append(
        f"{_COMMENT_PREFIX} {item.distance_km:.3f} km; "
        f"source=S-38 Natural Earth 1:50m coastline; "
        f"features_considered={item.feature_count}"
    )
    return "; ".join(parts)


def _is_anchor(site_name: str) -> bool:
    lowered = site_name.lower()
    return any(
        token in lowered
        for token in ("braila", "brăila", "porto romano", "varna", "constanta")
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write DB updates.")
    parser.add_argument("--asset-path", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--site-name", default=None)
    args = parser.parse_args(argv)

    dataset = load_coastline_dataset(args.asset_path)
    distances = collect_distances(
        dataset,
        limit=args.limit,
        site_name=args.site_name,
    )
    summary = summarize(distances)
    summary["applied"] = False
    if args.apply:
        summary["updated"] = apply_distances(distances)
        summary["applied"] = True
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
