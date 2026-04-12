# man_hours: 4.0
"""RI-06 Population projection proxy.

Priority 3 fallback -- S-20 GHSL (P1) and S-17 Eurostat (P2) not yet implemented.
Uses country-level UN WPP 2024 medium-variant growth rates applied to current
population data from the Population connector.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.population import PopulationConnector, PopulationResult
from atoms_vs_ashes.db.models import SiteRadiological
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "RI-06"
PROJECTION_HORIZON_YEARS = 60

COUNTRY_GROWTH_RATES: dict[str, float] = {
    "PL": -0.0045, "CZ": -0.0020, "SK": -0.0030, "HU": -0.0040,
    "AT": 0.0010, "SI": -0.0015, "HR": -0.0060, "BA": -0.0070,
    "RS": -0.0060, "ME": -0.0030, "XK": 0.0010, "AL": -0.0050,
    "MK": -0.0030, "RO": -0.0060, "BG": -0.0080, "MD": -0.0080,
    "UA": -0.0060, "BY": -0.0040, "EE": -0.0020, "LV": -0.0050,
    "LT": -0.0050, "AM": -0.0030, "TR": 0.0040,
}

DEFAULT_GROWTH_RATE = -0.0030


@dataclass
class ProjectionResult:
    lat: float
    lon: float
    current_density_5km: float = 0.0
    projected_density_5km: float = 0.0
    growth_rate: float = 0.0
    country_code: str = ""
    projection_year: int = 0
    ring_projections: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat, "lon": self.lon,
            "current_density_5km": round(self.current_density_5km, 1),
            "projected_density_5km": round(self.projected_density_5km, 1),
            "growth_rate_annual": self.growth_rate,
            "country_code": self.country_code,
            "projection_year": self.projection_year,
            "projection_source": "UN WPP 2024 medium variant",
            "ring_projections": self.ring_projections,
            "error": self.error,
        }


def project_population(
    pop_result: PopulationResult,
    country_code: str,
    horizon_years: int = PROJECTION_HORIZON_YEARS,
) -> ProjectionResult:
    rate = COUNTRY_GROWTH_RATES.get(country_code, DEFAULT_GROWTH_RATE)
    multiplier = (1 + rate) ** horizon_years

    ring_projections = []
    current_5km = 0.0
    projected_pop_25km = 0
    for ring in pop_result.rings:
        projected_density = ring.density_per_km2 * multiplier
        projected_pop = int(ring.population * multiplier)
        ring_projections.append({
            "ring": f"{ring.inner_km}-{ring.outer_km}km",
            "current_density": round(ring.density_per_km2, 1),
            "projected_density": round(projected_density, 1),
            "current_population": ring.population,
            "projected_population": projected_pop,
        })
        if ring.outer_km <= 5.5:
            current_5km = ring.density_per_km2
        if ring.outer_km <= 25.5:
            projected_pop_25km += projected_pop

    return ProjectionResult(
        lat=pop_result.lat,
        lon=pop_result.lon,
        current_density_5km=current_5km,
        projected_density_5km=current_5km * multiplier,
        growth_rate=rate,
        country_code=country_code,
        projection_year=2025 + horizon_years,
        ring_projections=ring_projections,
    )


def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, country_code: str,
    session: Session, run_id: str,
    pop_connector: PopulationConnector,
) -> ProjectionResult:
    t0 = time.monotonic()

    try:
        pop_result = pop_connector.fetch(lat, lon)
    except Exception as exc:
        log.warning("population_projection_error", error=str(exc), site_id=str(site_id))
        pop_result = PopulationResult(lat=lat, lon=lon, error=str(exc))

    result = project_population(pop_result, country_code)

    ensure_data_source(
        session, name="un_wpp_2024_proxy",
        url="https://population.un.org/wpp/",
        description="UN WPP 2024 medium-variant country-level growth rates (proxy)",
    )

    row = session.get(SiteRadiological, site_id)
    if row is None:
        row = SiteRadiological(site_id=site_id)
        session.add(row)
    row.pop_growth_rate_pct = result.growth_rate * 100
    row.ri06_quality = "low"
    row.ri06_comment = (
        f"Proxy: {country_code} country-level growth rate "
        f"({result.growth_rate:+.3%}/yr) applied to current OSM data"
    )
    row.fetched_at = datetime.now(timezone.utc)
    row.run_id = run_id

    write_observation(
        session, site_id=site_id, criterion_id=CRITERION_ID,
        observation="Proxy projection from country-level growth rate, not spatial model",
        run_id=run_id, confidence="low", impact="neutral",
    )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("population_projection_assess_ok", site_id=str(site_id),
             criterion_id=CRITERION_ID, run_id=run_id, elapsed_ms=elapsed_ms)
    return result
