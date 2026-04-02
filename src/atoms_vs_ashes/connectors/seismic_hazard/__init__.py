# man_hours: 0.25
"""S-01 GEM/SHARE Seismic Hazard connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.seismic_hazard.client import SeismicHazardConnector
from atoms_vs_ashes.connectors.seismic_hazard.fallback import GemRasterFallback
from atoms_vs_ashes.connectors.seismic_hazard.models import (
    BatchResult,
    HazardCurve,
    SeismicHazardResult,
    SiteEnrichmentSummary,
    UniformHazardSpectrum,
)
from atoms_vs_ashes.connectors.seismic_hazard.parsers import (
    nearest_value,
    parse_map_csv,
    parse_nrml_curve,
    parse_nrml_spectra,
    validate_coordinates_in_scope,
    validate_curve_monotonicity,
    validate_pga,
)

__all__ = [
    "BatchResult",
    "GemRasterFallback",
    "HazardCurve",
    "SeismicHazardConnector",
    "SeismicHazardResult",
    "SiteEnrichmentSummary",
    "UniformHazardSpectrum",
    "nearest_value",
    "parse_map_csv",
    "parse_nrml_curve",
    "parse_nrml_spectra",
    "validate_coordinates_in_scope",
    "validate_curve_monotonicity",
    "validate_pga",
]
