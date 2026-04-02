# man_hours: 14.0
"""Emergency Planning Zone population analysis (RI-04, RI-05).

RI-04 — Population density screening at EPZ radii (5 / 16 / 25 / 80 km).
         "Extremely high population density within the EPZ" is flagged as
         avoidance per EPRI guidance.  Configurable threshold (default:
         > 1 000 persons / km² within 5 km).

RI-05 — Distance to nearest city > 50 000.  Rank-only metric (no pass/fail).
"""

from __future__ import annotations

import json
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.population import (
    PopulatedPlace,
    PopulationConnector,
    PopulationResult,
    RingPopulation,
)
from atoms_vs_ashes.db.models import (
    ScreeningResult,
    Site,
    SiteAttribute,
)
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.screening.base import ScreeningCheck, register_check

log = get_logger(__name__)

RI04_CRITERION_ID = "RI-04"
RI05_CRITERION_ID = "RI-05"
PHASE = "screening"

DEFAULT_EPZ_RADII_KM = [5, 16, 25, 80]
DEFAULT_DENSITY_THRESHOLD = 1_000  # persons/km² within 5 km
DEFAULT_CITY_POP_THRESHOLD = 50_000


# ---------------------------------------------------------------------------
# Pure-logic evaluation (testable without DB)
# ---------------------------------------------------------------------------

def evaluate_ri04(
    rings: list[RingPopulation],
    density_threshold: float,
    inner_radius_km: float = 5.0,
) -> tuple[str, dict[str, Any], str]:
    """Evaluate RI-04: population density screening.

    Returns *(verdict, value_dict, justification)*.
    """
    if not rings:
        return (
            "inconclusive",
            {"rings": [], "density_threshold": density_threshold},
            "No population data available for EPZ analysis",
        )

    inner_ring = None
    for r in rings:
        if r.outer_km <= inner_radius_km + 0.5:
            inner_ring = r
            break

    ring_data = [r.to_dict() for r in rings]

    if inner_ring is None:
        return (
            "inconclusive",
            {"rings": ring_data, "density_threshold": density_threshold},
            f"No ring data for {inner_radius_km} km radius",
        )

    # Compute ring densities for all rings
    ring_densities = {}
    max_ring_density = 0.0
    max_ring_label = ""
    for r in rings:
        label = f"{r.inner_km}-{r.outer_km}km"
        ring_densities[label] = round(r.density_per_km2, 1)
        if r.density_per_km2 > max_ring_density:
            max_ring_density = r.density_per_km2
            max_ring_label = label

    value_dict: dict[str, Any] = {
        "rings": ring_data,
        "inner_density_per_km2": round(inner_ring.density_per_km2, 1),
        "density_threshold": density_threshold,
        "exceeds_threshold": inner_ring.density_per_km2 > density_threshold,
        "ring_densities": ring_densities,
        "max_density_ring": max_ring_label,
        "max_density_value": round(max_ring_density, 1),
    }

    if inner_ring.density_per_km2 > density_threshold:
        verdict = "fail"
        justification = (
            f"Population density within {inner_radius_km} km is "
            f"{inner_ring.density_per_km2:,.0f} persons/km², exceeding "
            f"avoidance threshold of {density_threshold:,.0f} persons/km²"
        )
    else:
        verdict = "pass"
        justification = (
            f"Population density within {inner_radius_km} km is "
            f"{inner_ring.density_per_km2:,.0f} persons/km² "
            f"(threshold: {density_threshold:,.0f} persons/km²)"
        )
        max_ring = max(rings, key=lambda r: r.density_per_km2)
        if max_ring.density_per_km2 > density_threshold * 0.5:
            justification += (
                f". Note: density in {max_ring.inner_km}-{max_ring.outer_km} km "
                f"ring is {max_ring.density_per_km2:,.0f} persons/km²"
            )

    return verdict, value_dict, justification


def evaluate_ri05(
    nearest_cities: list[PopulatedPlace],
    city_threshold: int,
) -> dict[str, Any]:
    """Evaluate RI-05: distance to nearest city > *city_threshold*.

    Returns a value dict for ranking (no pass/fail verdict).
    """
    if not nearest_cities:
        return {
            "nearest_city_name": None,
            "nearest_city_population": None,
            "nearest_city_distance_km": None,
            "city_population_threshold": city_threshold,
            "cities_within_80km": 0,
        }

    nearest = nearest_cities[0]
    return {
        "nearest_city_name": nearest.name,
        "nearest_city_population": nearest.population,
        "nearest_city_distance_km": round(nearest.distance_km, 1),
        "city_population_threshold": city_threshold,
        "cities_within_80km": len(nearest_cities),
        "all_cities": [
            {
                "name": c.name,
                "population": c.population,
                "distance_km": round(c.distance_km, 1),
            }
            for c in nearest_cities[:10]
        ],
    }


# ---------------------------------------------------------------------------
# Screening check — RI-04
# ---------------------------------------------------------------------------

@register_check
class PopulationDensityCheck(ScreeningCheck):
    """RI-04: Population Density Screening at EPZ radii."""

    criterion_id = RI04_CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningResult]:
        epz_cfg = _epz_config(settings)
        radii_km = epz_cfg.get("radii_km", DEFAULT_EPZ_RADII_KM)
        density_threshold = epz_cfg.get(
            "population_density_avoidance_threshold", DEFAULT_DENSITY_THRESHOLD,
        )
        city_threshold = epz_cfg.get(
            "city_population_threshold", DEFAULT_CITY_POP_THRESHOLD,
        )

        connector = PopulationConnector(settings)

        source_id = ensure_data_source(
            session,
            name="osm_overpass_population",
            url=connector._overpass._url,
            description="OSM Overpass API for population density screening",
        )

        sites = session.execute(select(Site)).scalars().all()
        results: list[ScreeningResult] = []

        for site in sites:
            lat, lon = float(site.latitude), float(site.longitude)
            t0 = time.monotonic()

            try:
                pop_result = connector.fetch(
                    lat, lon,
                    radii_km=radii_km,
                    city_threshold=city_threshold,
                )
            except Exception as exc:
                log.warning(
                    "epz_population_screen_error",
                    site_id=str(site.site_id), error=str(exc),
                    criterion_id=RI04_CRITERION_ID, run_id=run_id,
                )
                pop_result = PopulationResult(lat=lat, lon=lon, error=str(exc))

            # RI-04: population density verdict
            verdict, value_dict, justification = evaluate_ri04(
                pop_result.rings, density_threshold,
            )

            elapsed_ms = int((time.monotonic() - t0) * 1000)

            if verdict == "inconclusive":
                write_quality_flag(
                    session,
                    site_id=site.site_id,
                    dataset="population",
                    dimension="epz_density",
                    level="low",
                    detail="Population data unavailable for RI-04 screening",
                    run_id=run_id,
                )

            if pop_result.rings and all(r.place_count == 0 for r in pop_result.rings):
                write_quality_flag(
                    session,
                    site_id=site.site_id,
                    dataset="population",
                    dimension="epz_density",
                    level="medium",
                    detail="Zero populated places found; density may be underestimated",
                    run_id=run_id,
                )

            threshold_text = (
                f">{density_threshold:,.0f} persons/km² within "
                f"{radii_km[0]} km (EPRI avoidance)"
            )
            results.append(
                ScreeningResult(
                    site_id=site.site_id,
                    criterion_id=self.criterion_id,
                    phase=self.phase,
                    verdict=verdict,
                    value=json.dumps(value_dict),
                    threshold=threshold_text,
                    justification=justification,
                    source_refs="osm_overpass / geonames (population)",
                    run_id=run_id,
                )
            )

            # FIX-01-E: RI-04 dual persistence — also as SiteAttribute
            max_ring_density = 0.0
            max_ring_label = ""
            density_by_ring = {}
            for r in pop_result.rings:
                label = f"{r.inner_km}-{r.outer_km}km"
                density_by_ring[label] = round(r.density_per_km2, 1)
                if r.density_per_km2 > max_ring_density:
                    max_ring_density = r.density_per_km2
                    max_ring_label = label

            session.merge(
                SiteAttribute(
                    site_id=site.site_id,
                    criterion_id=RI04_CRITERION_ID,
                    value_numeric=max_ring_density,
                    value_json={
                        "ring_densities": density_by_ring,
                        "max_density_ring": max_ring_label,
                        "max_density_value": round(max_ring_density, 1),
                        "verdict": verdict,
                        "threshold_persons_per_km2": density_threshold,
                    },
                    source_id=source_id,
                    run_id=run_id,
                    cache_status="fresh",
                )
            )

            # RI-05: city distance (ranking — stored as SiteAttribute)
            ri05_data = evaluate_ri05(
                pop_result.nearest_large_cities, city_threshold,
            )
            ri05_distance = ri05_data.get("nearest_city_distance_km")
            session.merge(
                SiteAttribute(
                    site_id=site.site_id,
                    criterion_id=RI05_CRITERION_ID,
                    value_numeric=ri05_distance,
                    value_json=ri05_data,
                    source_id=source_id,
                    run_id=run_id,
                    cache_status="fresh",
                )
            )

            log.info(
                "epz_population_screen_ok",
                site_id=str(site.site_id),
                criterion_id=RI04_CRITERION_ID,
                run_id=run_id,
                verdict=verdict,
                elapsed_ms=elapsed_ms,
            )

        connector.close()
        log.info("epz_population_persist_ok", run_id=run_id, site_count=len(results))
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _epz_config(settings: Settings) -> dict[str, Any]:
    """Read EPZ config from the screening section."""
    return settings._yaml.get("screening", {}).get("epz", {})
