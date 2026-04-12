# man_hours: 3.0
"""NS-13 Laydown area proxy using CORINE land cover.

Identifies contiguous areas of low-value land cover suitable for temporary
construction facilities within 5 km of site.
Priority 2 — I-2 OSM is P1 for NS-13 via EXT-01.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.corine import (
    CorineConnector,
    LAYDOWN_SUITABLE_CLC,
    NON_EU_COUNTRIES,
    parse_clc_features,
)
from atoms_vs_ashes.db.models import SiteInfrastructureV2
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-13"


@dataclass
class LaydownResult:
    """Laydown area availability assessment."""
    lat: float
    lon: float
    total_suitable_ha: float = 0.0
    largest_patch_ha: float = 0.0
    patch_count: int = 0
    by_class: dict[str, float] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "total_suitable_ha": round(self.total_suitable_ha, 2),
            "largest_patch_ha": round(self.largest_patch_ha, 2),
            "patch_count": self.patch_count,
            "by_class": {k: round(v, 2) for k, v in self.by_class.items()},
            "error": self.error,
        }


def assess_laydown_area(
    lat: float,
    lon: float,
    corine: CorineConnector | None = None,
    radius_m: float = 5_000,
    *,
    features: list[dict[str, Any]] | None = None,
) -> LaydownResult:
    """Identify suitable laydown areas within radius_m.

    Pass *corine* to fetch data on demand, or *features* to use
    pre-fetched GeoJSON features.
    """
    if features is None:
        if corine is None:
            return LaydownResult(lat=lat, lon=lon, error="No CORINE connector or pre-fetched features provided")
        features = corine.fetch(lat, lon, radius_m=radius_m + 500)
    if not features:
        return LaydownResult(lat=lat, lon=lon, error="No CLC features returned")

    parsed = parse_clc_features(features)
    if not parsed:
        return LaydownResult(lat=lat, lon=lon, error="No valid CLC polygons parsed")

    buffer_geom = buffer_circle_wgs84(lat, lon, radius_m)
    by_class: dict[str, float] = {}
    patch_areas: list[float] = []

    for geom, clc_code in parsed:
        if clc_code not in LAYDOWN_SUITABLE_CLC:
            continue
        try:
            intersection = buffer_geom.intersection(geom)
            if intersection.is_empty:
                continue
            area_ha = geodesic_area_ha(intersection)
            by_class[clc_code] = by_class.get(clc_code, 0.0) + area_ha
            patch_areas.append(area_ha)
        except Exception:
            continue

    total = sum(patch_areas)
    largest = max(patch_areas) if patch_areas else 0.0

    return LaydownResult(
        lat=lat, lon=lon,
        total_suitable_ha=total,
        largest_patch_ha=largest,
        patch_count=len(patch_areas),
        by_class=by_class,
    )


def assess_and_persist(
    lat: float,
    lon: float,
    site_id: Any,
    country_code: str,
    session: Session,
    run_id: str,
    corine: CorineConnector,
) -> LaydownResult:
    """Assess and persist NS-13."""
    t0 = time.monotonic()

    if country_code in NON_EU_COUNTRIES:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"CORINE does not cover {country_code}",
            run_id=run_id, confidence="low", impact="blocking",
        )
        result = LaydownResult(lat=lat, lon=lon, error=f"No CORINE coverage for {country_code}")
    else:
        result = assess_laydown_area(lat, lon, corine)

    ensure_data_source(
        session, name="corine_clc2018_wfs", url=corine._wfs_url,
    )

    row = session.get(SiteInfrastructureV2, site_id)
    if row is None:
        row = SiteInfrastructureV2(site_id=site_id)
        session.add(row)
    row.laydown_suitable_ha = result.total_suitable_ha
    row.laydown_largest_patch_ha = result.largest_patch_ha
    row.ns13_quality = "low" if result.error else "medium"
    row.fetched_at = datetime.now(timezone.utc)
    row.run_id = run_id

    if result.error:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=result.error, run_id=run_id, confidence="low", impact="negative",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("laydown_area_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
