# man_hours: 16.0
"""Adjacent land assessment for NS-05 scoring.

Computes available developable land within concentric rings around a site,
subtracting protected areas (Natura 2000, WDPA), and produces the
``available_adjacent_ha`` metric used in the ranking phase.

The assessment uses CORINE land cover data and overlays it with protected
area boundaries to determine how much land near the coal plant could
realistically be acquired or converted for SMR construction.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from shapely.geometry import shape
from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.corine import (
    DEVELOPABLE_CODES,
    CorineConnector,
    SiteClassification,
)
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-05"

PROTECTED_AREA_WFS_URL = (
    "https://bio.discomap.eea.europa.eu/arcgis/services/"
    "ProtectedSites/Natura2000Sites/MapServer/WFSServer"
)
PROTECTED_AREA_LAYER = "Natura2000Sites:Natura2000polygon"

WDPA_API_URL = "https://api.protectedplanet.net/v3/protected_areas/search"


@dataclass
class ProtectedArea:
    """A protected area polygon near the site."""

    name: str
    designation: str
    area_ha: float
    source: str = "natura2000"


@dataclass
class ProximityResult:
    """Complete proximity land assessment for a site."""

    site_area_ha: float | None
    corine_classification: SiteClassification | None = None
    total_developable_ha: float = 0.0
    protected_area_ha: float = 0.0
    available_adjacent_ha: float = 0.0
    protected_areas: list[ProtectedArea] = field(default_factory=list)
    smr_compatibility: dict[str, bool] = field(default_factory=dict)
    quality: str = "estimated"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        corine = (
            self.corine_classification.to_dict()
            if self.corine_classification else None
        )
        return {
            "site_area_ha": self.site_area_ha,
            "corine": corine,
            "total_developable_ha": round(self.total_developable_ha, 2),
            "protected_area_ha": round(self.protected_area_ha, 2),
            "available_adjacent_ha": round(self.available_adjacent_ha, 2),
            "protected_areas": [
                {
                    "name": pa.name,
                    "designation": pa.designation,
                    "area_ha": round(pa.area_ha, 2),
                    "source": pa.source,
                }
                for pa in self.protected_areas
            ],
            "smr_compatibility": self.smr_compatibility,
            "quality": self.quality,
        }


class ProximityLandAnalysis:
    """Assess adjacent developable land around a coal plant site.

    Workflow:
    1. Fetch CORINE land cover in concentric rings (0-500 m, 500 m-1 km, 1-2 km).
    2. Fetch protected area boundaries (Natura 2000 / WDPA) within 2 km.
    3. Subtract protected area from developable land.
    4. Compare effective area against each SMR type's land requirement.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._corine = CorineConnector(settings)
        pa_cfg: dict[str, Any] = {}
        if hasattr(settings, "_yaml"):
            pa_cfg = settings._yaml.get("connectors", {}).get(
                "protected_areas", {}
            )
        self._pa_wfs_url = pa_cfg.get("wfs_url", PROTECTED_AREA_WFS_URL)
        self._pa_layer = pa_cfg.get("layer_name", PROTECTED_AREA_LAYER)
        self._wdpa_token: str | None = pa_cfg.get("wdpa_token")

    def assess(
        self,
        lat: float,
        lon: float,
        site_area_ha: float | None,
    ) -> ProximityResult:
        """Run the full proximity land assessment."""
        result = ProximityResult(site_area_ha=site_area_ha)

        classification = self._corine.classify(lat, lon)
        result.corine_classification = classification

        if classification.error:
            result.error = classification.error
            result.quality = "insufficient"
        else:
            result.total_developable_ha = classification.total_developable_ha

        protected = self._fetch_protected_areas(lat, lon, radius_m=2_000)
        result.protected_areas = protected
        result.protected_area_ha = sum(pa.area_ha for pa in protected)

        result.available_adjacent_ha = max(
            0.0,
            result.total_developable_ha - result.protected_area_ha,
        )

        effective_area = (site_area_ha or 0.0) + result.available_adjacent_ha
        result.smr_compatibility = _check_smr_land_compatibility(
            effective_area, self._settings,
        )

        return result

    def assess_and_persist(
        self,
        lat: float,
        lon: float,
        site_area_ha: float | None,
        site_id: Any,
        session: Session,
        run_id: str,
    ) -> ProximityResult:
        """Assess and store the result as a ``SiteAttribute`` for NS-05."""
        t0 = time.monotonic()
        result = self.assess(lat, lon, site_area_ha)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        source_id = ensure_data_source(
            session,
            name="corine_clc2018_wfs",
            url=self._corine._wfs_url,
            description="CORINE Land Cover 2018 WFS for proximity land analysis",
        )

        attr = SiteAttribute(
            site_id=site_id,
            criterion_id=CRITERION_ID,
            value_numeric=result.available_adjacent_ha,
            value_json=result.to_dict(),
            source_id=source_id,
            run_id=run_id,
            cache_status="fresh",
        )
        session.merge(attr)

        if result.error:
            write_quality_flag(
                session,
                site_id=site_id,
                dataset="corine",
                dimension="land_cover",
                level="insufficient",
                detail=result.error,
                run_id=run_id,
            )
        elif result.quality == "insufficient":
            write_quality_flag(
                session,
                site_id=site_id,
                dataset="corine",
                dimension="land_cover",
                level="low",
                detail="Proximity data quality is estimated with limited coverage",
                run_id=run_id,
            )

        if not result.protected_areas:
            write_quality_flag(
                session,
                site_id=site_id,
                dataset="natura2000",
                dimension="protected_areas",
                level="medium",
                detail="No Natura 2000 / WDPA data available; protected area check incomplete",
                run_id=run_id,
            )

        log.info(
            "proximity_land_assess_ok",
            site_id=str(site_id),
            criterion_id=CRITERION_ID,
            run_id=run_id,
            available_ha=round(result.available_adjacent_ha, 2),
            elapsed_ms=elapsed_ms,
        )

        return result

    def _fetch_protected_areas(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[ProtectedArea]:
        """Fetch Natura 2000 + WDPA protected areas within *radius_m*."""
        areas: list[ProtectedArea] = []
        areas.extend(self._fetch_natura2000(lat, lon, radius_m))
        if self._wdpa_token:
            areas.extend(self._fetch_wdpa(lat, lon, radius_m))
        return areas

    def _fetch_natura2000(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[ProtectedArea]:
        """Query Natura 2000 WFS for protected sites near the location."""
        from atoms_vs_ashes.geo import bbox_around

        bbox = bbox_around(lat, lon, radius_m)
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"

        try:
            resp = httpx.get(
                self._pa_wfs_url,
                params={
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeNames": self._pa_layer,
                    "outputFormat": "GEOJSON",
                    "srsName": "EPSG:4326",
                    "bbox": bbox_str,
                    "count": "200",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("proximity_land_assess_error", error=str(exc), sub="natura2000")
            return []

        site_buffer = buffer_circle_wgs84(lat, lon, radius_m)
        areas: list[ProtectedArea] = []

        for feat in data.get("features", []):
            try:
                geom = shape(feat["geometry"])
                if not geom.is_valid:
                    geom = geom.buffer(0)
                intersection = site_buffer.intersection(geom)
                if intersection.is_empty:
                    continue

                props = feat.get("properties", {})
                area_ha = geodesic_area_ha(intersection)
                areas.append(
                    ProtectedArea(
                        name=props.get("SITENAME", props.get("sitename", "")),
                        designation=props.get(
                            "SITETYPE", props.get("sitetype", "Natura 2000")
                        ),
                        area_ha=area_ha,
                        source="natura2000",
                    )
                )
            except Exception:
                continue

        log.info(
            "proximity_land_assess_ok",
            sub="natura2000",
            lat=lat, lon=lon,
            count=len(areas),
        )
        return areas

    def _fetch_wdpa(
        self, lat: float, lon: float, radius_m: float,
    ) -> list[ProtectedArea]:
        """Query WDPA API for additional protected areas."""
        if not self._wdpa_token:
            return []

        try:
            resp = httpx.get(
                WDPA_API_URL,
                params={
                    "token": self._wdpa_token,
                    "lat": lat,
                    "lon": lon,
                    "radius": radius_m / 1_000,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("proximity_land_assess_error", error=str(exc), sub="wdpa")
            return []

        areas: list[ProtectedArea] = []
        for pa in data.get("protected_areas", []):
            reported_area = float(pa.get("reported_area", 0) or 0)
            if reported_area > 0:
                areas.append(
                    ProtectedArea(
                        name=pa.get("name", ""),
                        designation=pa.get("designation", {}).get("name", ""),
                        area_ha=reported_area,
                        source="wdpa",
                    )
                )

        return areas

    def close(self) -> None:
        self._corine.close()


def _check_smr_land_compatibility(
    effective_area_ha: float,
    settings: Settings,
) -> dict[str, bool]:
    """Check which SMR types fit within the effective available area."""
    result: dict[str, bool] = {}
    for key, spec in settings.smr_types.items():
        land_ha = float(spec.get("land_ha", 0))
        result[key] = effective_area_ha >= land_ha
    return result
