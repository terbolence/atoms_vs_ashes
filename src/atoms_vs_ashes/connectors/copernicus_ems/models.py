# man_hours: 1.5
"""Result dataclasses and domain constants for S-10 Copernicus EMS.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

CRITERION_IDS = ("NH-08", "NH-09", "EP-05")

SOURCE_RRM = "cems_rrm"
SOURCE_RAPID = "cems_rapid"
SOURCE_COMBINED = "cems_combined"

RRM_API_URL = (
    "https://riskandrecovery.emergency.copernicus.eu/api/public-activations/"
)
RAPID_API_URL = (
    "https://mapping.emergency.copernicus.eu/activations/api/activations/"
)

DEFAULT_CACHE_DIR = "sources/copernicus_ems/geodata"
DEFAULT_SITE_BUFFER_KM = 100.0

# Site countries — used for DB queries and result attribution
INSCOPE_COUNTRIES = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BA", "RS", "ME", "XK",
    "AL", "MK", "RO", "BG", "MD", "UA", "BY", "EE", "LV", "LT", "AM", "TR",
})

# Broader European set for activation ingestion — a flood in Germany near
# the Polish border is relevant to Polish sites, so we ingest activations
# from all neighbouring European countries.
ACTIVATION_COUNTRIES = frozenset(INSCOPE_COUNTRIES | {
    "DE", "IT", "FR", "GR", "CH", "FI", "SE", "NO", "DK", "IE", "GB",
    "BE", "NL", "LU", "PT", "ES", "CY", "MT", "IS", "LI", "GE", "AZ",
})

# Rapid API categories to ingest (storms cause flash floods)
RAPID_CATEGORIES = ("flood", "storm")

# Project bounding box for centroid filtering (generous buffer around
# the 23 inscope countries at 12–45°E, 35–60°N)
PROJECT_BBOX = (5.0, 30.0, 50.0, 65.0)  # (min_lon, min_lat, max_lon, max_lat)

# Country name → ISO mapping for API responses
COUNTRY_NAME_MAP: dict[str, str] = {
    "Poland": "PL", "Czech Republic": "CZ", "Czechia": "CZ",
    "Slovakia": "SK", "Hungary": "HU", "Austria": "AT",
    "Slovenia": "SI", "Croatia": "HR",
    "Bosnia and Herzegovina": "BA", "Bosnia & Herzegovina": "BA",
    "Serbia": "RS", "Montenegro": "ME", "Kosovo": "XK",
    "Albania": "AL", "North Macedonia": "MK", "Macedonia": "MK",
    "Romania": "RO", "Bulgaria": "BG", "Moldova": "MD",
    "Ukraine": "UA", "Belarus": "BY",
    "Estonia": "EE", "Latvia": "LV", "Lithuania": "LT",
    "Armenia": "AM", "Turkey": "TR", "Türkiye": "TR",
    "Germany": "DE", "Italy": "IT", "France": "FR", "Greece": "GR",
    "Switzerland": "CH", "Finland": "FI", "Sweden": "SE", "Norway": "NO",
    "Denmark": "DK", "Ireland": "IE", "United Kingdom": "GB",
    "Belgium": "BE", "Netherlands": "NL", "Luxembourg": "LU",
    "Portugal": "PT", "Spain": "ES", "Cyprus": "CY", "Malta": "MT",
    "Georgia": "GE", "Azerbaijan": "AZ",
}


@dataclass
class RrmActivation:
    """Metadata for a single RRM (Risk and Recovery Mapping) activation."""

    code: str
    name: str
    category: str
    sub_category: str | None = None
    drm_phase: str | None = None
    countries: list[str] = field(default_factory=list)
    centroid_lon: float | None = None
    centroid_lat: float | None = None
    activation_time: str | None = None
    closed: bool = False
    download_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "sub_category": self.sub_category,
            "drm_phase": self.drm_phase,
            "countries": self.countries,
            "centroid_lon": self.centroid_lon,
            "centroid_lat": self.centroid_lat,
            "activation_time": self.activation_time,
            "closed": self.closed,
            "download_urls": self.download_urls,
        }


@dataclass
class RapidActivation:
    """Metadata for a single Rapid Mapping activation."""

    code: str
    name: str
    category: str
    countries: list[str] = field(default_factory=list)
    centroid_lon: float | None = None
    centroid_lat: float | None = None
    activation_time: str | None = None
    closed: bool = False
    n_aois: int = 0
    n_products: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "countries": self.countries,
            "centroid_lon": self.centroid_lon,
            "centroid_lat": self.centroid_lat,
            "activation_time": self.activation_time,
            "closed": self.closed,
            "n_aois": self.n_aois,
            "n_products": self.n_products,
        }


@dataclass
class FloodFootprint:
    """A single flood delineation polygon from a CEMS activation."""

    activation_code: str
    activation_type: str  # "rrm" | "rapid"
    activation_date: str | None = None
    category: str = "flood"
    countries: list[str] = field(default_factory=list)
    area_km2: float = 0.0
    product_name: str | None = None
    source_url: str | None = None
    # geometry stored separately in spatial index

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_code": self.activation_code,
            "activation_type": self.activation_type,
            "activation_date": self.activation_date,
            "category": self.category,
            "countries": self.countries,
            "area_km2": self.area_km2,
            "product_name": self.product_name,
            "source_url": self.source_url,
        }


@dataclass
class FootprintSummary:
    """Summary of a flood footprint relative to a site."""

    activation_code: str
    activation_date: str | None = None
    distance_km: float = 0.0
    intersection_area_km2: float = 0.0
    category: str = "flood"

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_code": self.activation_code,
            "activation_date": self.activation_date,
            "distance_km": self.distance_km,
            "intersection_area_km2": self.intersection_area_km2,
            "category": self.category,
        }


@dataclass
class FlashFloodAssessment:
    """Flash flood susceptibility assessment for a single site."""

    lat: float
    lon: float
    susceptibility: str | None = None  # "high" | "medium" | "low" | None
    distance_to_nearest_km: float | None = None
    intersection_area_km2: float = 0.0
    n_events_within_buffer: int = 0
    nearest_activation_code: str | None = None
    nearest_activation_date: str | None = None
    footprints_intersecting: list[FootprintSummary] = field(default_factory=list)
    nh08_seiche_proxy: str | None = None
    nh08_tidal_proxy: str | None = None
    nh08_wave_proxy: str | None = None
    source: str = SOURCE_COMBINED
    quality: str = "insufficient"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "susceptibility": self.susceptibility,
            "distance_to_nearest_km": self.distance_to_nearest_km,
            "intersection_area_km2": self.intersection_area_km2,
            "n_events_within_buffer": self.n_events_within_buffer,
            "nearest_activation_code": self.nearest_activation_code,
            "nearest_activation_date": self.nearest_activation_date,
            "footprints_intersecting": [f.to_dict() for f in self.footprints_intersecting],
            "nh08_seiche_proxy": self.nh08_seiche_proxy,
            "nh08_tidal_proxy": self.nh08_tidal_proxy,
            "nh08_wave_proxy": self.nh08_wave_proxy,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class CatalogueIngestionResult:
    """Summary of catalogue ingestion run."""

    run_id: str
    n_rrm_fetched: int = 0
    n_rapid_fetched: int = 0
    n_new_ingested: int = 0
    n_skipped_cached: int = 0
    n_footprints_total: int = 0
    elapsed_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "n_rrm_fetched": self.n_rrm_fetched,
            "n_rapid_fetched": self.n_rapid_fetched,
            "n_new_ingested": self.n_new_ingested,
            "n_skipped_cached": self.n_skipped_cached,
            "n_footprints_total": self.n_footprints_total,
            "elapsed_s": round(self.elapsed_s, 1),
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached" | "no_data"
    susceptibility: str | None = None
    n_events: int = 0
    source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    no_data: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "no_data": self.no_data,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "susceptibility": s.susceptibility,
                    "n_events": s.n_events,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        if mins >= 1:
            elapsed = f"{mins:.1f} min"
        else:
            elapsed = f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached, "
            f"{self.no_data} no-data ({elapsed})"
        )
