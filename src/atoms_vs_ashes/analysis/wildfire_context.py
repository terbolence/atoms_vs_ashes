# man_hours: 4.0
"""NH-13 Wildfire context assessment using CORINE land cover.

Priority 2 fallback for NH-13b (combustible vegetation / WUI proxy).
S-35 EFFIS+FIRMS (P1) and S-36 ESA WorldCover (P1) not yet implemented.
Evidence grade: Ranking-grade (CORINE 100 m MMU too coarse for screening).
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
    HIGH_COMBUSTIBILITY_CLC,
    MEDIUM_COMBUSTIBILITY_CLC,
    NON_EU_COUNTRIES,
    parse_clc_features,
)
from atoms_vs_ashes.db.models import SiteNaturalHazards
from atoms_vs_ashes.geo import buffer_ring_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NH-13"
DEFAULT_BUFFER_RADII_KM = [5, 16, 25]

RESIDENTIAL_CLC = frozenset({"111", "112"})


@dataclass
class WildfireResult:
    """Wildfire context assessment result."""
    lat: float
    lon: float
    ring_combustibility: list[dict[str, Any]] = field(default_factory=list)
    max_combustible_pct: float = 0.0
    wui_proxy_ha: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "ring_combustibility": self.ring_combustibility,
            "max_combustible_pct": round(self.max_combustible_pct, 1),
            "wui_proxy_ha": round(self.wui_proxy_ha, 2),
            "error": self.error,
        }


def assess_wildfire_context(
    lat: float,
    lon: float,
    corine: CorineConnector | None = None,
    buffer_radii_km: list[float] | None = None,
    *,
    features: list[dict[str, Any]] | None = None,
) -> WildfireResult:
    """Compute combustible vegetation percentages at EPZ radii.

    Pass *corine* to fetch data on demand, or *features* to use
    pre-fetched GeoJSON features (avoids redundant API calls).
    """
    if buffer_radii_km is None:
        buffer_radii_km = DEFAULT_BUFFER_RADII_KM

    max_radius_m = max(buffer_radii_km) * 1000
    if features is None:
        if corine is None:
            return WildfireResult(lat=lat, lon=lon, error="No CORINE connector or pre-fetched features provided")
        features = corine.fetch(lat, lon, radius_m=max_radius_m + 500)

    if not features:
        return WildfireResult(lat=lat, lon=lon, error="No CLC features returned")

    parsed = parse_clc_features(features)
    if not parsed:
        return WildfireResult(lat=lat, lon=lon, error="No valid CLC polygons parsed")

    result = WildfireResult(lat=lat, lon=lon)
    max_pct = 0.0

    prev_outer = 0.0
    for radius_km in sorted(buffer_radii_km):
        inner_m = prev_outer * 1000
        outer_m = radius_km * 1000
        ring = buffer_ring_wgs84(lat, lon, inner_m, outer_m)
        ring_area = geodesic_area_ha(ring)

        high_ha = 0.0
        medium_ha = 0.0

        for geom, clc_code in parsed:
            try:
                intersection = ring.intersection(geom)
                if intersection.is_empty:
                    continue
                area_ha = geodesic_area_ha(intersection)
                if clc_code in HIGH_COMBUSTIBILITY_CLC:
                    high_ha += area_ha
                elif clc_code in MEDIUM_COMBUSTIBILITY_CLC:
                    medium_ha += area_ha
            except Exception:
                continue

        total_combustible = high_ha + medium_ha
        pct = (total_combustible / ring_area * 100) if ring_area > 0 else 0.0
        max_pct = max(max_pct, pct)

        result.ring_combustibility.append({
            "ring": f"{prev_outer}-{radius_km}km",
            "high_combustibility_ha": round(high_ha, 2),
            "medium_combustibility_ha": round(medium_ha, 2),
            "total_combustible_ha": round(total_combustible, 2),
            "ring_area_ha": round(ring_area, 2),
            "combustible_pct": round(pct, 1),
        })
        prev_outer = radius_km

    result.max_combustible_pct = max_pct

    wui_ring = buffer_ring_wgs84(lat, lon, 0, 1000)
    wui_ha = 0.0
    for geom, clc_code in parsed:
        if clc_code not in RESIDENTIAL_CLC and clc_code not in HIGH_COMBUSTIBILITY_CLC:
            continue
        try:
            intersection = wui_ring.intersection(geom)
            if not intersection.is_empty:
                wui_ha += geodesic_area_ha(intersection)
        except Exception:
            continue
    result.wui_proxy_ha = wui_ha

    return result


def assess_and_persist(
    lat: float,
    lon: float,
    site_id: Any,
    country_code: str,
    session: Session,
    run_id: str,
    corine: CorineConnector,
) -> WildfireResult:
    """Assess wildfire context and persist to SiteNaturalHazards NH-13."""
    t0 = time.monotonic()

    if country_code in NON_EU_COUNTRIES:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"CORINE does not cover {country_code}; NH-13 requires S-36 ESA WorldCover",
            run_id=run_id, confidence="low", impact="blocking",
        )
        result = WildfireResult(lat=lat, lon=lon, error=f"No CORINE coverage for {country_code}")
    else:
        result = assess_wildfire_context(lat, lon, corine)

    ensure_data_source(
        session,
        name="corine_clc2018_wfs",
        url=corine._wfs_url,
        description="CORINE Land Cover 2018 WFS for wildfire context",
    )

    row = session.get(SiteNaturalHazards, site_id)
    if row is None:
        row = SiteNaturalHazards(site_id=site_id)
        session.add(row)
    row.wildfire_combustible_pct = result.max_combustible_pct
    row.wildfire_wui_ha = result.wui_proxy_ha
    row.nh13_quality = "low" if result.error else "medium"
    row.fetched_at = datetime.now(timezone.utc)
    row.run_id = run_id

    if result.error:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=result.error, run_id=run_id, confidence="low", impact="negative",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info(
        "wildfire_context_assess_ok",
        site_id=str(site_id),
        criterion_id=CRITERION_ID,
        run_id=run_id,
        max_combustible_pct=round(result.max_combustible_pct, 1),
        elapsed_ms=elapsed_ms,
    )
    return result
