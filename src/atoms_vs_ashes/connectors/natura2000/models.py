# man_hours: 3.0
"""Result dataclasses and domain constants for S-14 Natura 2000.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NS-08",)

SOURCE_NAME = "natura2000_eea_wfs"

DEFAULT_WFS_URL = (
    "https://bio.discomap.eea.europa.eu/arcgis/services/"
    "ProtectedSites/Natura2000Sites/MapServer/WFSServer"
)
DEFAULT_LAYER = "Natura2000Sites:Natura2000polygon"

EU_MEMBER_STATES_INSCOPE = frozenset([
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "RO", "BG", "EE", "LV", "LT",
])

NON_EU_INSCOPE = frozenset([
    "BA", "RS", "ME", "XK", "AL", "MK", "UA", "MD", "BY", "AM", "TR",
])

VALID_SITETYPES = frozenset({"A", "B", "C"})

SITECODE_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3,7}$")

EPZ_RADII_M_DEFAULT = [5_000, 16_000, 25_000]
SEARCH_RADIUS_M_DEFAULT = 25_000

EUROPEAN_LAT_MIN, EUROPEAN_LAT_MAX = 34.0, 72.0
EUROPEAN_LON_MIN, EUROPEAN_LON_MAX = -25.0, 45.0


# ---------------------------------------------------------------------------
# Parsed feature
# ---------------------------------------------------------------------------

@dataclass
class Natura2000Site:
    """A single Natura 2000 site parsed from WFS GeoJSON."""

    sitecode: str
    sitename: str
    sitetype: str  # A = SPA, B = pSCI/SCI/SAC, C = both
    member_state: str
    area_ha: float
    area_km2: float
    release_date: str | None = None
    conservation_a: int = 0
    conservation_b: int = 0
    conservation_c: int = 0
    conservation_d: int = 0
    conservation_missing: int = 0
    geometry: Any = None  # Shapely Polygon | MultiPolygon (WGS84)
    centroid_lat: float = 0.0
    centroid_lon: float = 0.0

    @property
    def conservation_score(self) -> float | None:
        """Ratio of excellent conservation (A) to total assessed."""
        denom = self.conservation_a + self.conservation_b + self.conservation_c + self.conservation_d
        if denom == 0:
            return None
        return self.conservation_a / denom

    def to_dict(self) -> dict[str, Any]:
        return {
            "sitecode": self.sitecode,
            "sitename": self.sitename,
            "sitetype": self.sitetype,
            "member_state": self.member_state,
            "area_ha": self.area_ha,
            "area_km2": self.area_km2,
            "release_date": self.release_date,
            "conservation_a": self.conservation_a,
            "conservation_b": self.conservation_b,
            "conservation_c": self.conservation_c,
            "conservation_d": self.conservation_d,
            "conservation_missing": self.conservation_missing,
            "conservation_score": self.conservation_score,
            "centroid_lat": self.centroid_lat,
            "centroid_lon": self.centroid_lon,
        }


# ---------------------------------------------------------------------------
# Per-site proximity result
# ---------------------------------------------------------------------------

@dataclass
class SiteProximity:
    """Distance result for a single nearby Natura 2000 site."""

    sitecode: str
    sitename: str
    sitetype: str
    distance_km: float
    overlap: bool
    area_ha: float
    conservation_score: float | None = None
    direction_deg: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sitecode": self.sitecode,
            "sitename": self.sitename,
            "sitetype": self.sitetype,
            "distance_km": round(self.distance_km, 3),
            "overlap": self.overlap,
            "area_ha": self.area_ha,
            "conservation_score": self.conservation_score,
            "direction_deg": round(self.direction_deg, 1) if self.direction_deg is not None else None,
        }


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------

@dataclass
class Natura2000Result:
    """Complete Natura 2000 proximity assessment for a single candidate site."""

    lat: float
    lon: float
    country_code: str = ""
    is_eu_member: bool = False

    n2k_overlap: bool | None = None
    n2k_overlap_sitecodes: list[str] = field(default_factory=list)
    n2k_nearest_distance_km: float | None = None
    n2k_nearest_sitecode: str | None = None
    n2k_nearest_sitename: str | None = None
    n2k_nearest_sitetype: str | None = None
    n2k_nearest_area_ha: float | None = None

    n2k_sites_within_5km: int = 0
    n2k_sites_within_16km: int = 0
    n2k_sites_within_25km: int = 0

    n2k_area_fraction_5km: float | None = None
    n2k_area_fraction_16km: float | None = None
    n2k_area_fraction_25km: float | None = None

    n2k_spa_count: int = 0   # Birds Directive (type A or C)
    n2k_sac_count: int = 0   # Habitats Directive (type B or C)
    n2k_combined_count: int = 0  # Both designations (type C)
    n2k_total_protected_area_ha: float = 0.0

    n2k_max_conservation_score: float | None = None
    sensitivity_class: str = "unknown"

    nearby_sites: list[SiteProximity] = field(default_factory=list)
    reference_date: str | None = None

    source: str = SOURCE_NAME
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "is_eu_member": self.is_eu_member,
            "n2k_overlap": self.n2k_overlap,
            "n2k_overlap_sitecodes": self.n2k_overlap_sitecodes,
            "n2k_nearest_distance_km": (
                round(self.n2k_nearest_distance_km, 3)
                if self.n2k_nearest_distance_km is not None else None
            ),
            "n2k_nearest_sitecode": self.n2k_nearest_sitecode,
            "n2k_nearest_sitename": self.n2k_nearest_sitename,
            "n2k_nearest_sitetype": self.n2k_nearest_sitetype,
            "n2k_nearest_area_ha": self.n2k_nearest_area_ha,
            "n2k_sites_within_5km": self.n2k_sites_within_5km,
            "n2k_sites_within_16km": self.n2k_sites_within_16km,
            "n2k_sites_within_25km": self.n2k_sites_within_25km,
            "n2k_area_fraction_5km": (
                round(self.n2k_area_fraction_5km, 4)
                if self.n2k_area_fraction_5km is not None else None
            ),
            "n2k_area_fraction_16km": (
                round(self.n2k_area_fraction_16km, 4)
                if self.n2k_area_fraction_16km is not None else None
            ),
            "n2k_area_fraction_25km": (
                round(self.n2k_area_fraction_25km, 4)
                if self.n2k_area_fraction_25km is not None else None
            ),
            "n2k_spa_count": self.n2k_spa_count,
            "n2k_sac_count": self.n2k_sac_count,
            "n2k_combined_count": self.n2k_combined_count,
            "n2k_total_protected_area_ha": round(self.n2k_total_protected_area_ha, 2),
            "n2k_max_conservation_score": (
                round(self.n2k_max_conservation_score, 4)
                if self.n2k_max_conservation_score is not None else None
            ),
            "sensitivity_class": self.sensitivity_class,
            "nearby_sites": [s.to_dict() for s in self.nearby_sites],
            "reference_date": self.reference_date,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Batch result (reusable pattern)
# ---------------------------------------------------------------------------

@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "degraded" | "error" | "cached" | "non_eu"
    sensitivity_class: str | None = None
    nearest_distance_km: float | None = None
    source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    degraded: int = 0  # EU site persisted but EEA returned low/empty data quality
    failed: int = 0
    skipped_cached: int = 0
    skipped_non_eu: int = 0
    skipped_after_abort: int = 0
    aborted_reason: str | None = None
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "degraded": self.degraded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "skipped_non_eu": self.skipped_non_eu,
            "skipped_after_abort": self.skipped_after_abort,
            "aborted_reason": self.aborted_reason,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "sensitivity_class": s.sensitivity_class,
                    "nearest_distance_km": s.nearest_distance_km,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        base = (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.degraded} degraded, {self.failed} failed, "
            f"{self.skipped_cached} cached, {self.skipped_non_eu} non-EU ({elapsed})"
        )
        if self.aborted_reason:
            base += (
                f"; aborted: {self.skipped_after_abort} not processed — "
                f"{self.aborted_reason}"
            )
        return base
