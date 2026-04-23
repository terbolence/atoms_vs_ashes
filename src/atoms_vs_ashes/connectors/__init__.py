# man_hours: 0.5
"""Connector framework — API clients for external geospatial data sources.

Connectors are imported lazily inside each CLI command to avoid eager loading
of heavy dependencies (rasterio, GDAL, etc.) that can hang on network-mounted
filesystems (e.g. Google Drive). Do not add top-level imports here.
"""

__all__ = [
    "CopernicusDemConnector",
    "CopernicusEmsConnector",
    "CopernicusEra5Connector",
    "CorineConnector",
    "EeaIndustrialConnector",
    "Efsm20FaultsConnector",
    "EgdiGeologyConnector",
    "EntsoEConnector",
    "EuFloodRiskConnector",
    "EurostatGiscoConnector",
    "EurostatProjectionsConnector",
    "GeonamesDumpConnector",
    "GfmsConnector",
    "GhslPopConnector",
    "GlofasDischargeConnector",
    "HydroRiversConnector",
    "Natura2000Connector",
    "NoaaNceiConnector",
    "OneGeologyConnector",
    "OurAirportsConnector",
    "OverpassClient",
    "PopulationConnector",
    "SeismicHazardConnector",
    "SevesoConnector",
    "SmithsonianGvpConnector",
    "WdpaConnector",
    "WokamKarstConnector",
    "WorldCoverConnector",
    "WriAqueductConnector",
    "ZhuLiquefactionConnector",
    "MANDATORY_LOGGING_CONNECTORS",
]


# ---------------------------------------------------------------------------
# Raw-response logging registry
# ---------------------------------------------------------------------------
# Single source of truth for every connector that MUST dual-write raw
# responses to ``site_raw_responses`` (DB) and ``data/raw_responses/<slug>/``
# (disk).  Consumed by:
#   * tests/test_raw_response_logging.py   (CI gate)
#   * scripts/verify_raw_response_coverage.py  (per-run audit)
#
# The Cursor rule .cursor/rules/raw-response-logging.mdc requires every new
# per-site connector to be added here.
#
# Each entry:
#   slug -> {
#       "logger_fn": "log_raw_response" | "log_raster_extraction",
#       "batch_module": dotted path of the connector batch module that calls
#                       the logger (used by the test to monkey-patch the
#                       logger symbol in the right place),
#   }
#
MANDATORY_LOGGING_CONNECTORS: dict[str, dict[str, str]] = {
    # Live HTTP APIs ----------------------------------------------------
    "corine": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.corine.batch",
    },
    "natura2000": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.natura2000.batch",
    },
    "egdi_geology": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.egdi_geology.batch",
    },
    "onegeology": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.onegeology.batch",
    },
    "noaa_ncei": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.noaa_ncei.batch",
    },
    "osm": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.osm.batch",
    },
    "copernicus_ems": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.copernicus_ems.batch",
    },
    "seismic_hazard": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.seismic_hazard.batch",
    },
    "entso_e": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.entso_e.batch",
    },
    "population": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.population.batch",
    },
    "eurostat_gisco": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.eurostat_gisco.batch",
    },
    "eurostat_projections": {
        "logger_fn": "log_raw_response",
        "batch_module": "atoms_vs_ashes.connectors.eurostat_projections.batch",
    },
    # Per-site raster extractions --------------------------------------
    "bdticm_bedrock": {
        "logger_fn": "log_raster_extraction",
        "batch_module": "atoms_vs_ashes.connectors.bdticm_bedrock.batch",
    },
    "copernicus_dem": {
        "logger_fn": "log_raster_extraction",
        "batch_module": "atoms_vs_ashes.connectors.copernicus_dem.batch",
    },
    "soilgrids": {
        "logger_fn": "log_raster_extraction",
        "batch_module": "atoms_vs_ashes.connectors.soilgrids.batch",
    },
    "copernicus_era5": {
        "logger_fn": "log_raster_extraction",
        "batch_module": "atoms_vs_ashes.connectors.copernicus_era5.batch",
    },
}
