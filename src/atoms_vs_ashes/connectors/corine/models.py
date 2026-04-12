# man_hours: 2.0
"""CORINE Land Cover data models and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



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

DEFAULT_RINGS: list[tuple[float, float, str]] = [
    (0, 500, "0-500m"),
    (500, 1_000, "500m-1km"),
    (1_000, 2_000, "1-2km"),
]

HIGH_COMBUSTIBILITY_CLC: frozenset[str] = frozenset({
    "311", "312", "313", "322", "324",
})

MEDIUM_COMBUSTIBILITY_CLC: frozenset[str] = frozenset({
    "321", "323", "243",
})

NATURAL_SEMINATURAL_CLC: frozenset[str] = frozenset({
    "311", "312", "313", "321", "322", "323", "324",
    "331", "332", "333", "334", "335",
    "411", "412", "421", "422", "423",
    "511", "512", "521", "522", "523",
})

LAYDOWN_SUITABLE_CLC: frozenset[str] = frozenset({
    "121", "131", "133", "142", "211", "231",
})

FAVOURABLE_FOOTPRINT_CLC: frozenset[str] = frozenset({
    "111", "112", "121", "122", "123", "124",
    "131", "132", "133", "141", "142",
    "211", "231",
})

MODERATE_FOOTPRINT_CLC: frozenset[str] = frozenset({
    "241", "242", "243", "244", "321",
})

UNFAVOURABLE_FOOTPRINT_CLC: frozenset[str] = frozenset({
    "311", "312", "313",
    "411", "412", "421", "422", "423",
    "511", "512", "521", "522", "523",
})

_CLC_CODE_KEYS = ("code_18", "Code_18", "CODE_18", "clc_code", "CLC_CODE")

# Legacy WFS endpoint (broken as of April 2026, EEA returns 400)
DEFAULT_WFS_URL = (
    "https://image.discomap.eea.europa.eu/arcgis/services/"
    "Corine/CLC2018_WM/MapServer/WFSServer"
)
DEFAULT_LAYER = "Corine:CLC2018_CLC2018_V2018_20"

DEFAULT_REST_URL = (
    "https://image.discomap.eea.europa.eu/arcgis/rest/services/"
    "Corine/CLC2018_WM/MapServer"
)
DEFAULT_REST_LAYER_ID = 0

# EU/EEA countries covered by CORINE
CORINE_COVERED_COUNTRIES: frozenset[str] = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "RO", "BG",
    "EE", "LV", "LT",
})

NON_EU_COUNTRIES: frozenset[str] = frozenset({
    "BA", "RS", "ME", "XK", "AL", "MK", "MD", "UA", "BY", "AM", "TR",
})


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
