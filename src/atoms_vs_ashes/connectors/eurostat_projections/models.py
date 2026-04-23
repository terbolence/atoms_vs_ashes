# man_hours: 2.0
"""Result dataclasses and domain constants for S-17 Eurostat Demographic Projections.

Pure data definitions — no I/O, no HTTP, no database imports.
Serves criteria RI-06 (population projections), NS-09 (socioeconomic),
NS-10 (workforce), NS-12 (public opinion proxy / nuclear policy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("RI-06", "NS-09", "NS-10", "NS-12")

SOURCE_NAMES = {
    "europop2023": "eurostat_europop2023",
    "europop2019_regional": "eurostat_europop2019_regional",
    "regional_statistics": "eurostat_regional_statistics",
    "nso_supplements": "nso_supplements",
}

STATISTICS_API_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
)

GISCO_BASE_URL = "https://gisco-services.ec.europa.eu/distribution/v2"

IN_SCOPE_EU = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "RO", "BG", "EE", "LV", "LT",
})

IN_SCOPE_CANDIDATE = frozenset({"TR", "RS", "ME", "MK", "AL"})

IN_SCOPE_NON_EU = frozenset({"BA", "XK", "MD", "UA", "BY", "AM"})

IN_SCOPE_ALL = IN_SCOPE_EU | IN_SCOPE_CANDIDATE | IN_SCOPE_NON_EU

VALID_GROWTH_CLASSES = frozenset({
    "rapid_growth", "moderate_growth", "stable",
    "moderate_decline", "rapid_decline",
})

VALID_POLICY_STANCES = frozenset({
    "favourable", "neutral", "unfavourable",
    "moratorium", "phaseout", "unknown",
})


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PopulationProjectionResult:
    """Population projections and growth trajectory for a site."""

    base_population: int | None = None
    base_year: int = 2022
    projected_pop_2030: int | None = None
    projected_pop_2040: int | None = None
    projected_pop_2050: int | None = None
    projected_pop_2060: int | None = None
    projected_pop_2080: int | None = None
    pop_change_pct_2050: float | None = None
    pop_change_pct_2080: float | None = None
    receptor_growth_factor_60yr: float | None = None
    projection_lo_2050: int | None = None
    projection_hi_2050: int | None = None
    projection_lo_2080: int | None = None
    projection_hi_2080: int | None = None
    growth_classification: str = "stable"
    urban_expansion_pressure: float | None = None
    median_age_2050: float | None = None
    old_age_dependency_2050: float | None = None
    net_migration_rate_projected: float | None = None
    projection_source: str = "europop2023"
    projection_variant: str = "baseline"
    spatial_level: str = "national"

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_population": self.base_population,
            "base_year": self.base_year,
            "projected_pop_2030": self.projected_pop_2030,
            "projected_pop_2040": self.projected_pop_2040,
            "projected_pop_2050": self.projected_pop_2050,
            "projected_pop_2060": self.projected_pop_2060,
            "projected_pop_2080": self.projected_pop_2080,
            "pop_change_pct_2050": self.pop_change_pct_2050,
            "pop_change_pct_2080": self.pop_change_pct_2080,
            "receptor_growth_factor_60yr": self.receptor_growth_factor_60yr,
            "projection_lo_2050": self.projection_lo_2050,
            "projection_hi_2050": self.projection_hi_2050,
            "projection_lo_2080": self.projection_lo_2080,
            "projection_hi_2080": self.projection_hi_2080,
            "growth_classification": self.growth_classification,
            "urban_expansion_pressure": self.urban_expansion_pressure,
            "median_age_2050": self.median_age_2050,
            "old_age_dependency_2050": self.old_age_dependency_2050,
            "net_migration_rate_projected": self.net_migration_rate_projected,
            "projection_source": self.projection_source,
            "projection_variant": self.projection_variant,
            "spatial_level": self.spatial_level,
        }


@dataclass
class SocioeconomicResult:
    """Socioeconomic indicators for NS-09."""

    nuts3_gdp_million_eur: float | None = None
    nuts3_gdp_per_capita_eur: float | None = None
    national_gdp_per_capita_eur: float | None = None
    gdp_gap_to_national_pct: float | None = None
    gdp_growth_5yr_pct: float | None = None
    fiscal_capacity_index: float | None = None
    deprivation_index: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nuts3_gdp_million_eur": self.nuts3_gdp_million_eur,
            "nuts3_gdp_per_capita_eur": self.nuts3_gdp_per_capita_eur,
            "national_gdp_per_capita_eur": self.national_gdp_per_capita_eur,
            "gdp_gap_to_national_pct": self.gdp_gap_to_national_pct,
            "gdp_growth_5yr_pct": self.gdp_growth_5yr_pct,
            "fiscal_capacity_index": self.fiscal_capacity_index,
            "deprivation_index": self.deprivation_index,
        }


@dataclass
class WorkforceResult:
    """Workforce indicators for NS-10."""

    working_age_pop: int | None = None
    working_age_pct: float | None = None
    projected_working_age_2050: int | None = None
    employment_rate_pct: float | None = None
    unemployment_rate_pct: float | None = None
    employment_industry_pct: float | None = None
    employment_construction_pct: float | None = None
    employment_energy_pct: float | None = None
    tertiary_education_pct: float | None = None
    retraining_pool_index: float | None = None
    coal_energy_employment: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "working_age_pop": self.working_age_pop,
            "working_age_pct": self.working_age_pct,
            "projected_working_age_2050": self.projected_working_age_2050,
            "employment_rate_pct": self.employment_rate_pct,
            "unemployment_rate_pct": self.unemployment_rate_pct,
            "employment_industry_pct": self.employment_industry_pct,
            "employment_construction_pct": self.employment_construction_pct,
            "employment_energy_pct": self.employment_energy_pct,
            "tertiary_education_pct": self.tertiary_education_pct,
            "retraining_pool_index": self.retraining_pool_index,
            "coal_energy_employment": self.coal_energy_employment,
        }


@dataclass
class PolicyProxyResult:
    """Nuclear policy proxy indicators for NS-12."""

    nuclear_policy_stance: str | None = None
    energy_sector_dependence: float | None = None
    education_index: float | None = None
    policy_source: str = "curated_2026"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nuclear_policy_stance": self.nuclear_policy_stance,
            "energy_sector_dependence": self.energy_sector_dependence,
            "education_index": self.education_index,
            "policy_source": self.policy_source,
        }


@dataclass
class NsoProjection:
    """Curated national projection from a non-EU statistical office."""

    country_code: str
    country_name: str
    source: str
    source_url: str
    retrieved_date: str
    projection_variant: str
    base_year: int
    projections: dict[str, dict[str, float]] = field(default_factory=dict)
    median_age_2050: float | None = None
    old_age_dependency_2050: float | None = None
    quality_note: str | None = None

    def population_at(self, year: int | str) -> int | None:
        entry = self.projections.get(str(year))
        if entry is None:
            return None
        pop = entry.get("population")
        return int(pop) if pop is not None else None

    def growth_rate_at(self, year: int | str) -> float | None:
        entry = self.projections.get(str(year))
        if entry is None:
            return None
        return entry.get("growth_rate")


@dataclass
class EurostatProjectionsResult:
    """Complete result for a single site from Eurostat Demographic Projections."""

    lat: float
    lon: float
    country_code: str
    nuts3_code: str | None = None
    nuts2_code: str | None = None
    population_projection: PopulationProjectionResult | None = None
    socioeconomic: SocioeconomicResult | None = None
    workforce: WorkforceResult | None = None
    policy_proxy: PolicyProxyResult | None = None
    source: str = "eurostat_europop2023"
    reference_year: int = 2022
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "country_code": self.country_code,
            "nuts3_code": self.nuts3_code,
            "nuts2_code": self.nuts2_code,
            "population_projection": (
                self.population_projection.to_dict()
                if self.population_projection else None
            ),
            "socioeconomic": (
                self.socioeconomic.to_dict() if self.socioeconomic else None
            ),
            "workforce": (
                self.workforce.to_dict() if self.workforce else None
            ),
            "policy_proxy": (
                self.policy_proxy.to_dict() if self.policy_proxy else None
            ),
            "source": self.source,
            "reference_year": self.reference_year,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class IngestionResult:
    """Summary of a data ingestion run."""

    n_countries_with_projections: int = 0
    n_regions_with_data: int = 0
    n_nso_supplements_loaded: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_countries_with_projections": self.n_countries_with_projections,
            "n_regions_with_data": self.n_regions_with_data,
            "n_nso_supplements_loaded": self.n_nso_supplements_loaded,
            "errors": self.errors,
            "elapsed_s": round(self.elapsed_s, 1),
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    country_code: str | None = None
    growth_classification: str | None = None
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
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "country_code": s.country_code,
                    "growth_classification": s.growth_classification,
                    "quality": s.quality,
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
