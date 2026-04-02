# man_hours: 0.25
"""CORINE Land Cover connector package."""

from atoms_vs_ashes.connectors.corine.client import (
    CorineConnector,
    parse_clc_features,
    extract_clc_code,
)
from atoms_vs_ashes.connectors.corine.models import (
    CLC_LABELS,
    CORINE_COVERED_COUNTRIES,
    CRITERION_IDS,
    DEFAULT_LAYER,
    DEFAULT_RINGS,
    DEFAULT_WFS_URL,
    DEVELOPABLE_CODES,
    FAVOURABLE_FOOTPRINT_CLC,
    HIGH_COMBUSTIBILITY_CLC,
    LAYDOWN_SUITABLE_CLC,
    MEDIUM_COMBUSTIBILITY_CLC,
    MODERATE_FOOTPRINT_CLC,
    NATURAL_SEMINATURAL_CLC,
    NON_EU_COUNTRIES,
    UNFAVOURABLE_FOOTPRINT_CLC,
    RingClassification,
    SiteClassification,
)

__all__ = [
    "CLC_LABELS",
    "CORINE_COVERED_COUNTRIES",
    "CRITERION_IDS",
    "CorineConnector",
    "DEFAULT_LAYER",
    "DEFAULT_RINGS",
    "DEFAULT_WFS_URL",
    "DEVELOPABLE_CODES",
    "FAVOURABLE_FOOTPRINT_CLC",
    "HIGH_COMBUSTIBILITY_CLC",
    "LAYDOWN_SUITABLE_CLC",
    "MEDIUM_COMBUSTIBILITY_CLC",
    "MODERATE_FOOTPRINT_CLC",
    "NATURAL_SEMINATURAL_CLC",
    "NON_EU_COUNTRIES",
    "RingClassification",
    "SiteClassification",
    "UNFAVOURABLE_FOOTPRINT_CLC",
    "extract_clc_code",
    "parse_clc_features",
]
