# man_hours: 3.0
"""NS-04 Site topography / land cover within footprint.

Uses CORINE to classify land cover at site footprint scale.
Priority 1 for NS-04c; S-36 ESA WorldCover supplements for non-EU.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.connectors.corine import (
    CorineConnector,
    FAVOURABLE_FOOTPRINT_CLC,
    MODERATE_FOOTPRINT_CLC,
    NON_EU_COUNTRIES,
    UNFAVOURABLE_FOOTPRINT_CLC,
    parse_clc_features,
)
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-04"


@dataclass
class FootprintResult:
    """Land cover classification within site footprint."""
    lat: float
    lon: float
    dominant_class: str = "unknown"
    dominant_class_pct: float = 0.0
    favourable_pct: float = 0.0
    moderate_pct: float = 0.0
    unfavourable_pct: float = 0.0
    by_class: dict[str, float] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "dominant_class": self.dominant_class,
            "dominant_class_pct": round(self.dominant_class_pct, 1),
            "favourable_pct": round(self.favourable_pct, 1),
            "moderate_pct": round(self.moderate_pct, 1),
            "unfavourable_pct": round(self.unfavourable_pct, 1),
            "by_class": {k: round(v, 2) for k, v in self.by_class.items()},
            "error": self.error,
        }


def assess_site_topography(
    lat: float,
    lon: float,
    corine: CorineConnector,
    site_area_ha: float | None = None,
) -> FootprintResult:
    """Classify land cover within the site footprint."""
    radius_m = max(
        math.sqrt((site_area_ha or 0) * 10_000 / math.pi),
        500,
    )

    features = corine.fetch(lat, lon, radius_m=radius_m + 200)
    if not features:
        return FootprintResult(lat=lat, lon=lon, error="No CLC features returned")

    parsed = parse_clc_features(features)
    if not parsed:
        return FootprintResult(lat=lat, lon=lon, error="No valid CLC polygons parsed")

    buffer_geom = buffer_circle_wgs84(lat, lon, radius_m)
    buffer_area = geodesic_area_ha(buffer_geom)

    by_class: dict[str, float] = {}
    for geom, clc_code in parsed:
        try:
            intersection = buffer_geom.intersection(geom)
            if intersection.is_empty:
                continue
            area_ha = geodesic_area_ha(intersection)
            by_class[clc_code] = by_class.get(clc_code, 0.0) + area_ha
        except Exception:
            continue

    result = FootprintResult(lat=lat, lon=lon, by_class=by_class)

    if not by_class:
        return result

    fav_ha = sum(v for k, v in by_class.items() if k in FAVOURABLE_FOOTPRINT_CLC)
    mod_ha = sum(v for k, v in by_class.items() if k in MODERATE_FOOTPRINT_CLC)
    unfav_ha = sum(v for k, v in by_class.items() if k in UNFAVOURABLE_FOOTPRINT_CLC)
    total = fav_ha + mod_ha + unfav_ha
    if total > 0:
        result.favourable_pct = fav_ha / total * 100
        result.moderate_pct = mod_ha / total * 100
        result.unfavourable_pct = unfav_ha / total * 100

    dominant = max(by_class, key=by_class.get)
    result.dominant_class = dominant
    result.dominant_class_pct = (by_class[dominant] / buffer_area * 100) if buffer_area > 0 else 0

    return result


def assess_and_persist(
    lat: float,
    lon: float,
    site_id: Any,
    country_code: str,
    session: Session,
    run_id: str,
    corine: CorineConnector,
    site_area_ha: float | None = None,
) -> FootprintResult:
    """Assess and persist NS-04."""
    t0 = time.monotonic()

    if country_code in NON_EU_COUNTRIES:
        write_quality_flag(
            session, site_id=site_id, dataset="corine", dimension="site_topography",
            level="insufficient", detail=f"CORINE does not cover {country_code}", run_id=run_id,
        )
        result = FootprintResult(lat=lat, lon=lon, error=f"No CORINE coverage for {country_code}")
    else:
        result = assess_site_topography(lat, lon, corine, site_area_ha)

    source_id = ensure_data_source(
        session, name="corine_clc2018_wfs", url=corine._wfs_url,
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=result.unfavourable_pct,
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.error:
        write_quality_flag(
            session, site_id=site_id, dataset="corine", dimension="site_topography",
            level="low", detail=result.error, run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("site_topography_assess_ok", site_id=str(site_id), criterion_id=CRITERION_ID,
             run_id=run_id, elapsed_ms=elapsed_ms)
    return result
