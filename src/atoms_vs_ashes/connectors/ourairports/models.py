# man_hours: 2.0
"""Result dataclasses and domain constants for S-39 OurAirports.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_NAME = "ourairports"
SOURCE_URL = "https://ourairports.com/data/"
AIRPORTS_CSV_URL = "https://ourairports.com/data/airports.csv"
RUNWAYS_CSV_URL = "https://ourairports.com/data/runways.csv"

CRITERION_ID = "HI-01"

# Airport type → avoidance tier mapping (IAEA NS-G-3.1 §3.18)
AIRPORT_TYPE_TIER: dict[str, str] = {
    "large_airport": "A4",
    "medium_airport": "A2",
    "small_airport": "A3",
    "heliport": "A1",
    "seaplane_base": "A3",
}

# Avoidance distance thresholds in km (from IAEA NS-G-3.1 / EPRI)
AVOIDANCE_THRESHOLDS_KM: dict[str, float] = {
    "A1": 2.0,   # Flight path proximity
    "A2": 8.0,   # Type 2 (medium) airport proximity
    "A3": 4.0,   # Small airport proximity
    "A4": 16.0,  # Large airport proximity
}

# Types to skip entirely
SKIP_TYPES: frozenset[str] = frozenset({"closed", "balloonport"})

# 23 in-scope countries (ISO 3166-1 alpha-2)
IN_SCOPE_COUNTRIES: frozenset[str] = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BA", "RS", "ME",
    "XK", "AL", "MK", "RO", "BG", "MD", "UA", "BY", "EE", "LV",
    "LT", "AM", "TR",
})

# Bordering countries whose airports may be within 100 km of in-scope sites
BORDER_BUFFER_COUNTRIES: frozenset[str] = frozenset({
    "DE", "IT", "GE", "IR", "IQ", "SY", "GR", "FI", "SE", "RU",
})

ALL_RELEVANT_COUNTRIES: frozenset[str] = IN_SCOPE_COUNTRIES | BORDER_BUFFER_COUNTRIES

# Bounding box for candidate sites (with margin for border airports)
SITE_LAT_MIN = 33.0
SITE_LAT_MAX = 62.0
SITE_LON_MIN = 10.0
SITE_LON_MAX = 47.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AirportRecord:
    """A single airport parsed from OurAirports CSV.

    ``runway_length_m`` is the longest hard-surface (asphalt/concrete) runway
    associated with this airport in ``runways.csv``; falls back to the
    longest runway of any surface when no hard-surface runway exists.
    Stored as ``None`` when no runway record could be associated.
    """

    ident: str
    name: str
    airport_type: str
    latitude: float
    longitude: float
    elevation_ft: int | None = None
    country_code: str = ""
    municipality: str | None = None
    scheduled_service: bool = False
    iata_code: str | None = None
    icao_code: str | None = None
    avoidance_tier: str | None = None
    runway_length_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ident": self.ident,
            "name": self.name,
            "airport_type": self.airport_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_ft": self.elevation_ft,
            "country_code": self.country_code,
            "municipality": self.municipality,
            "scheduled_service": self.scheduled_service,
            "iata_code": self.iata_code,
            "icao_code": self.icao_code,
            "avoidance_tier": self.avoidance_tier,
            "runway_length_m": (
                round(self.runway_length_m, 0)
                if self.runway_length_m is not None else None
            ),
        }


@dataclass
class NearbyAirport:
    """An airport within the search radius of a site."""

    ident: str
    name: str
    airport_type: str
    avoidance_tier: str | None
    distance_km: float
    latitude: float
    longitude: float
    country_code: str = ""
    scheduled_service: bool = False
    runway_length_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ident": self.ident,
            "name": self.name,
            "airport_type": self.airport_type,
            "airport_class": self.airport_type,
            "avoidance_tier": self.avoidance_tier,
            "distance_km": round(self.distance_km, 2),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country_code": self.country_code,
            "scheduled_service": self.scheduled_service,
            "runway_length_m": (
                round(self.runway_length_m, 0)
                if self.runway_length_m is not None else None
            ),
        }


@dataclass
class AirportProximityResult:
    """Full airport proximity assessment for a single site."""

    lat: float
    lon: float
    nearest_airport_km: float | None = None
    nearest_airport_name: str | None = None
    nearest_airport_type: str | None = None
    nearest_airport_class: str | None = None
    nearest_airport_runway_length_m: float | None = None
    nearest_airport_scheduled_service: bool | None = None
    nearest_large_airport_km: float | None = None
    nearest_type2_airport_km: float | None = None
    nearest_small_airport_km: float | None = None
    nearest_flight_path_km: float | None = None
    airport_count: int = 0
    airports_within_30km: list[NearbyAirport] = field(default_factory=list)
    avoidance_violations: list[str] = field(default_factory=list)
    quality: str = "high"
    error: str | None = None
    source: str = SOURCE_NAME

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "nearest_airport_km": (
                round(self.nearest_airport_km, 2)
                if self.nearest_airport_km is not None else None
            ),
            "nearest_airport_name": self.nearest_airport_name,
            "nearest_airport_type": self.nearest_airport_type,
            "nearest_airport_class": self.nearest_airport_class
                or self.nearest_airport_type,
            "nearest_airport_runway_length_m": (
                round(self.nearest_airport_runway_length_m, 0)
                if self.nearest_airport_runway_length_m is not None else None
            ),
            "nearest_airport_scheduled_service": self.nearest_airport_scheduled_service,
            "nearest_large_airport_km": (
                round(self.nearest_large_airport_km, 2)
                if self.nearest_large_airport_km is not None else None
            ),
            "nearest_type2_airport_km": (
                round(self.nearest_type2_airport_km, 2)
                if self.nearest_type2_airport_km is not None else None
            ),
            "nearest_small_airport_km": (
                round(self.nearest_small_airport_km, 2)
                if self.nearest_small_airport_km is not None else None
            ),
            "nearest_flight_path_km": (
                round(self.nearest_flight_path_km, 2)
                if self.nearest_flight_path_km is not None else None
            ),
            "airport_count": self.airport_count,
            "airports_within_30km": [a.to_dict() for a in self.airports_within_30km],
            "avoidance_violations": self.avoidance_violations,
            "quality": self.quality,
            "error": self.error,
            "source": self.source,
        }


@dataclass
class AirportIndex:
    """In-memory spatial index of airports."""

    airports: list[AirportRecord] = field(default_factory=list)
    tree: Any = None  # shapely.STRtree
    airport_count: int = 0
    countries_loaded: list[str] = field(default_factory=list)


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    nearest_airport_km: float | None = None
    nearest_airport_name: str | None = None
    quality: str | None = None
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
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
