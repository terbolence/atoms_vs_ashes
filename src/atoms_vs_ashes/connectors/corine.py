# man_hours: 14.0
"""CORINE Land Cover WFS connector.

Fetches CLC classification data from the Copernicus / EEA WFS endpoint
and computes area statistics in concentric rings around a site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from shapely.geometry import shape

from atoms_vs_ashes.geo import (
    bbox_around,
    buffer_ring_wgs84,
    geodesic_area_ha,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# CLC taxonomy
# ---------------------------------------------------------------------------

CLC_LABELS: dict[str, str] = {
    "111": "Continuous urban fabric",
    "112": "Discontinuous urban fabric",
    "121": "Industrial or commercial units",
    "122": "Road and rail networks",
    "123": "Port areas",
    "124": "Airports",
    "131": "Mineral extraction sites",
    "132": "Dump sites",
    "133": "Construction sites",
    "141": "Green urban areas",
    "142": "Sport and leisure facilities",
    "211": "Non-irrigated arable land",
    "212": "Permanently irrigated land",
    "213": "Rice fields",
    "221": "Vineyards",
    "222": "Fruit trees and berry plantations",
    "223": "Olive groves",
    "231": "Pastures",
    "241": "Annual crops with permanent crops",
    "242": "Complex cultivation patterns",
    "243": "Agriculture with natural vegetation",
    "244": "Agro-forestry areas",
    "311": "Broad-leaved forest",
    "312": "Coniferous forest",
    "313": "Mixed forest",
    "321": "Natural grasslands",
    "322": "Moors and heathland",
    "323": "Sclerophyllous vegetation",
    "324": "Transitional woodland-shrub",
    "331": "Beaches, dunes, sands",
    "332": "Bare rocks",
    "333": "Sparsely vegetated areas",
    "334": "Burnt areas",
    "335": "Glaciers and perpetual snow",
    "411": "Inland marshes",
    "412": "Peat bogs",
    "421": "Salt marshes",
    "422": "Salines",
    "423": "Intertidal flats",
    "511": "Water courses",
    "512": "Water bodies",
    "521": "Coastal lagoons",
    "522": "Estuaries",
    "523": "Sea and ocean",
}

DEVELOPABLE_CODES: frozenset[str] = frozenset({
    "121",  # Industrial / commercial
    "131",  # Mineral extraction
    "132",  # Dump sites
    "133",  # Construction sites
    "211",  # Non-irrigated arable
    "231",  # Pastures
    "242",  # Complex cultivation
    "243",  # Agriculture with natural vegetation
    "321",  # Natural grasslands
    "331",  # Beaches, dunes, sands
    "333",  # Sparsely vegetated
})

# Rings for proximity land assessment (inner_m, outer_m, label)
DEFAULT_RINGS: list[tuple[float, float, str]] = [
    (0, 500, "0-500m"),
    (500, 1_000, "500m-1km"),
    (1_000, 2_000, "1-2km"),
]

DEFAULT_WFS_URL = (
    "https://image.discomap.eea.europa.eu/arcgis/services/"
    "Corine/CLC2018_WM/MapServer/WFSServer"
)
DEFAULT_LAYER = "Corine:CLC2018_CLC2018_V2018_20"

# Known property keys that hold the CLC code across different WFS providers
_CLC_CODE_KEYS = ("code_18", "Code_18", "CODE_18", "clc_code", "CLC_CODE")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RingClassification:
    """Land cover area breakdown for a single ring."""

    label: str
    inner_m: float
    outer_m: float
    total_area_ha: float
    by_class: dict[str, float] = field(default_factory=dict)
    developable_ha: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "inner_m": self.inner_m,
            "outer_m": self.outer_m,
            "total_area_ha": round(self.total_area_ha, 2),
            "by_class": {k: round(v, 3) for k, v in self.by_class.items()},
            "developable_ha": round(self.developable_ha, 3),
        }


@dataclass
class SiteClassification:
    """Full CORINE classification result for a site."""

    lat: float
    lon: float
    rings: list[RingClassification] = field(default_factory=list)
    total_developable_ha: float = 0.0
    source: str = "corine_wfs"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "rings": [r.to_dict() for r in self.rings],
            "total_developable_ha": round(self.total_developable_ha, 3),
            "source": self.source,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class CorineConnector:
    """Fetches CORINE Land Cover data via WFS and classifies land in rings."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("corine", {})

        self._wfs_url: str = cfg.get("wfs_url", DEFAULT_WFS_URL)
        self._layer: str = cfg.get("layer_name", DEFAULT_LAYER)
        self._timeout: int = cfg.get("timeout_s", 30)
        self._client = httpx.Client(timeout=self._timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify WFS endpoint is reachable."""
        try:
            resp = self._client.get(
                self._wfs_url,
                params={"service": "WFS", "request": "GetCapabilities"},
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def fetch(
        self, lat: float, lon: float, radius_m: float = 2_500,
    ) -> list[dict[str, Any]]:
        """Fetch CLC features within a bounding box around *(lat, lon)*."""
        bbox = bbox_around(lat, lon, radius_m)
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"

        try:
            resp = self._client.get(
                self._wfs_url,
                params={
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeNames": self._layer,
                    "outputFormat": "GEOJSON",
                    "srsName": "EPSG:4326",
                    "bbox": bbox_str,
                    "count": "5000",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            log.info(
                "corine_fetch_ok",
                lat=lat, lon=lon,
                feature_count=len(features),
            )
            return features
        except httpx.HTTPError as exc:
            log.warning("corine_wfs_error", error=str(exc), lat=lat, lon=lon)
            return []
        except (ValueError, KeyError) as exc:
            log.warning("corine_parse_error", error=str(exc), lat=lat, lon=lon)
            return []

    def classify(
        self,
        lat: float,
        lon: float,
        ring_defs: list[tuple[float, float, str]] | None = None,
    ) -> SiteClassification:
        """Fetch CLC data and compute area breakdown per ring.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        ring_defs
            Concentric ring definitions as *(inner_m, outer_m, label)*.
            Defaults to 0-500 m, 500 m–1 km, 1–2 km.
        """
        if ring_defs is None:
            ring_defs = DEFAULT_RINGS

        max_radius = max(outer for _, outer, _ in ring_defs)
        features = self.fetch(lat, lon, radius_m=max_radius + 500)

        if not features:
            return SiteClassification(
                lat=lat, lon=lon,
                error="No CLC features returned from WFS",
            )

        return self._analyze_rings(lat, lon, features, ring_defs)

    # ------------------------------------------------------------------
    # Pure-logic helpers (testable without network)
    # ------------------------------------------------------------------

    @staticmethod
    def analyze_rings_from_features(
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]] | None = None,
    ) -> SiteClassification:
        """Classify pre-fetched features — useful for testing / cached data."""
        if ring_defs is None:
            ring_defs = DEFAULT_RINGS
        return CorineConnector._do_analyze(lat, lon, features, ring_defs)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _analyze_rings(
        self,
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]],
    ) -> SiteClassification:
        return self._do_analyze(lat, lon, features, ring_defs)

    @staticmethod
    def _do_analyze(
        lat: float,
        lon: float,
        features: list[dict[str, Any]],
        ring_defs: list[tuple[float, float, str]],
    ) -> SiteClassification:
        result = SiteClassification(lat=lat, lon=lon)

        ring_geoms = [
            (
                buffer_ring_wgs84(lat, lon, inner, outer),
                label, inner, outer,
            )
            for inner, outer, label in ring_defs
        ]

        parsed = _parse_clc_features(features)
        if not parsed:
            result.error = "No valid CLC polygons parsed from features"
            return result

        total_dev = 0.0
        for ring_geom, label, inner_m, outer_m in ring_geoms:
            ring_area = geodesic_area_ha(ring_geom)
            by_class: dict[str, float] = {}
            dev_ha = 0.0

            for feat_geom, clc_code in parsed:
                try:
                    intersection = ring_geom.intersection(feat_geom)
                    if intersection.is_empty:
                        continue
                    area_ha = geodesic_area_ha(intersection)
                    by_class[clc_code] = by_class.get(clc_code, 0.0) + area_ha
                    if clc_code in DEVELOPABLE_CODES:
                        dev_ha += area_ha
                except Exception:
                    continue

            rc = RingClassification(
                label=label,
                inner_m=inner_m,
                outer_m=outer_m,
                total_area_ha=ring_area,
                by_class=by_class,
                developable_ha=dev_ha,
            )
            result.rings.append(rc)
            total_dev += dev_ha

        result.total_developable_ha = total_dev
        return result

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _parse_clc_features(
    features: list[dict[str, Any]],
) -> list[tuple[Any, str]]:
    """Extract *(shapely_geometry, clc_code)* pairs from GeoJSON features."""
    parsed: list[tuple[Any, str]] = []
    for feat in features:
        try:
            geom = shape(feat["geometry"])
            props = feat.get("properties", {})
            clc_code = _extract_clc_code(props)
            if clc_code:
                parsed.append((geom, clc_code))
        except Exception:
            continue
    return parsed


def _extract_clc_code(props: dict[str, Any]) -> str:
    for key in _CLC_CODE_KEYS:
        val = props.get(key)
        if val:
            return str(val).strip()
    return ""
