# man_hours: 0.25
"""S-04 Copernicus CDS / ERA5 connector package.

Two-tier design (LL-011):
  Tier 1: Bulk NetCDF download from Copernicus CDS (monthly means, ERA5-Land,
           CMIP6 projections). One-time setup; requires CDS account + token.
           IMPORTANT: Tier 1 requires explicit user consent (live-api-safety rule).
  Tier 2: Per-site xarray extraction + pure computation (wind rose, GEV extremes,
           SPI drought index, Pasquill stability classes). Local only, consent-free.

Criteria: NH-10 (wind), NH-11 (precipitation/snow/drought), NH-12 (temperature),
          RI-01 (atmospheric dispersion), NS-01 (seasonality proxy),
          EP-02 (seasonal constraints proxy).
"""

from atoms_vs_ashes.connectors.copernicus_era5.client import CopernicusEra5Connector
from atoms_vs_ashes.connectors.copernicus_era5.models import (
    CRITERION_IDS,
    SOURCE_ERA5,
    BatchResult,
    ClimateProjectionAssessment,
    Era5ClimateResult,
    PrecipitationAssessment,
    SiteEnrichmentSummary,
    StabilityAssessment,
    TemperatureAssessment,
    WindAssessment,
)

__all__ = [
    "CopernicusEra5Connector",
    "Era5ClimateResult",
    "WindAssessment",
    "TemperatureAssessment",
    "PrecipitationAssessment",
    "StabilityAssessment",
    "ClimateProjectionAssessment",
    "BatchResult",
    "SiteEnrichmentSummary",
    "CRITERION_IDS",
    "SOURCE_ERA5",
]
