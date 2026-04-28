# man_hours: 1.0
"""Backfill NH-05 nearest mine distance from stored EGDI raw responses."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from atoms_vs_ashes.connectors.egdi_geology.parsers import (
    nearest_feature_distance,
    parse_geojson_features,
)
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site, SiteNaturalHazards, SiteRawResponse

_CONNECTOR = "egdi_geology"
_MINE_LAYERS = {"ms:egdi_mines", "ms:coalheritage"}


@dataclass(frozen=True)
class MineDistance:
    site_id: uuid.UUID
    site_name: str
    distance_km: float | None
    feature_count: int
    raw_run_id: str | None


def distance_from_raw_response(
    response_body: dict[str, Any] | None,
    *,
    lat: float,
    lon: float,
) -> tuple[float | None, int]:
    """Return nearest mine distance and feature count from EGDI raw JSON."""
    features: list[dict[str, Any]] = []
    for layer in (response_body or {}).get("layers", []):
        if not isinstance(layer, dict) or layer.get("layer_name") not in _MINE_LAYERS:
            continue
        features.extend(parse_geojson_features(layer.get("response_body") or {}))
    distance, _nearest = nearest_feature_distance(features, lat, lon)
    return distance, len(features)


def collect_distances() -> list[MineDistance]:
    """Compute one latest raw-response distance per site."""
    out: list[MineDistance] = []
    seen: set[uuid.UUID] = set()
    with session_scope() as session:
        rows = session.execute(
            select(Site, SiteRawResponse)
            .join(SiteRawResponse, SiteRawResponse.site_id == Site.site_id)
            .where(SiteRawResponse.connector_slug == _CONNECTOR)
            .order_by(Site.site_id, SiteRawResponse.fetched_at.desc())
        ).all()

        for site, raw in rows:
            if site.site_id in seen:
                continue
            seen.add(site.site_id)
            distance, feature_count = distance_from_raw_response(
                raw.response_body,
                lat=float(site.latitude),
                lon=float(site.longitude),
            )
            out.append(
                MineDistance(
                    site_id=site.site_id,
                    site_name=str(site.name),
                    distance_km=distance,
                    feature_count=feature_count,
                    raw_run_id=raw.run_id,
                )
            )
    return out


def apply_distances(distances: list[MineDistance]) -> int:
    """Persist distances to ``site_natural_hazards``."""
    updated = 0
    with session_scope() as session:
        for item in distances:
            row = session.get(SiteNaturalHazards, item.site_id)
            if row is None:
                row = SiteNaturalHazards(site_id=item.site_id)
                session.add(row)
            row.mining_void_distance_km = item.distance_km
            row.mining_void_present = item.distance_km is not None
            row.nh05b_quality = "medium" if item.feature_count else "low"
            row.nh05b_comment = _comment(item)
            updated += 1
    return updated


def _comment(item: MineDistance) -> str:
    if item.distance_km is None:
        return (
            "No mapped EGDI mine/mining-heritage feature in stored raw "
            f"response; raw_run_id={item.raw_run_id}."
        )
    return (
        "Nearest mapped EGDI mine/mining-heritage feature: "
        f"{item.distance_km:.3f} km; features within buffer: "
        f"{item.feature_count}; raw_run_id={item.raw_run_id}."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write DB updates.")
    args = parser.parse_args()

    distances = collect_distances()
    with_distance = sum(d.distance_km is not None for d in distances)
    summary = {
        "sites_with_raw": len(distances),
        "sites_with_mine_distance": with_distance,
        "sites_without_mine_features": len(distances) - with_distance,
        "applied": 0,
    }
    if args.apply:
        summary["applied"] = apply_distances(distances)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
