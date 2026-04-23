# man_hours: 2.5
"""Result dataclasses and domain constants for S-16 Eurostat GISCO.

Pure data definitions — no I/O, no HTTP, no database imports.
Serves criteria RI-05 (nearest city / settlement hierarchy) as the
Priority 1 source, and provides supplementary RI-04 data for EU countries.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("RI-04", "RI-05")
SOURCE_NAME = "eurostat_gisco_urban_audit_2021"
SOURCE_URL = "https://ec.europa.eu/eurostat/web/gisco"
SOURCE_DESCRIPTION = (
    "Eurostat GISCO Urban Audit 2021 — City and Functional Urban Area "
    "boundaries with population from urb_cpop1. "
    "European Commission. Free reuse with attribution."
)

GISCO_BASE_URL = "https://gisco-services.ec.europa.eu/distribution/v2"
EUROSTAT_API_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
)

CITY_POP_THRESHOLD = 50_000

EU_MEMBER_STATES = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
})

IN_SCOPE_EU = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "RO", "BG", "EE", "LV", "LT",
})

IN_SCOPE_CANDIDATE = frozenset({"TR", "RS", "ME", "MK", "AL"})

IN_SCOPE_NON_EU = frozenset({"BA", "XK", "MD", "UA", "BY", "AM"})

IN_SCOPE_ALL = IN_SCOPE_EU | IN_SCOPE_CANDIDATE | IN_SCOPE_NON_EU


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NearbyCityRecord:
    """A city from the Urban Audit dataset near a site."""

    city_code: str
    city_name: str
    country_code: str
    distance_km: float
    population: int | None = None
    centroid_lat: float | None = None
    centroid_lon: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "city_code": self.city_code,
            "city_name": self.city_name,
            "country_code": self.country_code,
            "distance_km": round(self.distance_km, 2),
            "population": self.population,
        }


@dataclass
class CityProximityResult:
    """RI-05 city proximity assessment for a site."""

    nearest_city_name: str | None = None
    nearest_city_code: str | None = None
    nearest_city_distance_km: float | None = None
    nearest_city_population: int | None = None
    nearest_city_country: str | None = None
    cities_within_25km: int = 0
    cities_within_80km: int = 0
    largest_city_within_80km_name: str | None = None
    largest_city_within_80km_population: int | None = None
    nearby_cities: list[NearbyCityRecord] = field(default_factory=list)
    settlement_hierarchy: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nearest_city_name": self.nearest_city_name,
            "nearest_city_code": self.nearest_city_code,
            "nearest_city_distance_km": (
                round(self.nearest_city_distance_km, 2)
                if self.nearest_city_distance_km is not None else None
            ),
            "nearest_city_population": self.nearest_city_population,
            "nearest_city_country": self.nearest_city_country,
            "cities_within_25km": self.cities_within_25km,
            "cities_within_80km": self.cities_within_80km,
            "largest_city_within_80km_name": self.largest_city_within_80km_name,
            "largest_city_within_80km_population": self.largest_city_within_80km_population,
            "settlement_hierarchy": self.settlement_hierarchy,
            "nearby_cities": [c.to_dict() for c in self.nearby_cities],
        }


@dataclass
class EurostatGiscoResult:
    """Complete result for a single site from Eurostat GISCO."""

    lat: float
    lon: float
    country_code: str | None = None
    city_proximity: CityProximityResult | None = None
    source: str = SOURCE_NAME
    quality: str = "high"
    error: str | None = None

    @property
    def nearest_city_name(self) -> str | None:
        if self.city_proximity:
            return self.city_proximity.nearest_city_name
        return None

    @property
    def nearest_city_distance_km(self) -> float | None:
        if self.city_proximity:
            return self.city_proximity.nearest_city_distance_km
        return None

    @property
    def nearest_city_population(self) -> int | None:
        if self.city_proximity:
            return self.city_proximity.nearest_city_population
        return None

    @property
    def settlement_hierarchy(self) -> str:
        if self.city_proximity:
            return self.city_proximity.settlement_hierarchy
        return "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "city_proximity": (
                self.city_proximity.to_dict() if self.city_proximity else None
            ),
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class CityRecord:
    """Internal representation of an Urban Audit city."""

    city_code: str
    city_name: str
    country_code: str
    centroid_lat: float
    centroid_lon: float
    population: int | None = None
    nuts3_code: str | None = None
    area_sqm: float | None = None


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_city_name: str | None = None
    nearest_city_distance_km: float | None = None
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
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "nearest_city_name": s.nearest_city_name,
                    "nearest_city_distance_km": s.nearest_city_distance_km,
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
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
