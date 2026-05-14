# man_hours: 14.0
"""Emergency Planning Zone population analysis (RI-04, RI-05).

RI-04 — Population density screening at EPZ radii (5 / 16 / 25 / 80 km).
         Population density is recorded for ranking/review only. High EPZ
         ring density must not emit a failing screening verdict.

RI-05 — Distance to nearest city > 50 000.  Rank-only metric (no pass/fail).
"""

from __future__ import annotations

import json
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.population import (
    PopulatedPlace,
    PopulationConnector,
    PopulationResult,
    RingPopulation,
)
from atoms_vs_ashes.db.models import (
    ScreeningVerdict as ScreeningVerdictModel,
    Site,
    SiteRadiological,
    SmrDesign,
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
    """Evaluate RI-04: population density evidence capture.

    Returns *(verdict, value_dict, justification)*. Dense EPZ rings are
    retained in the payload for ranking/review, but the verdict is non-failing.
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
        verdict = "pass"
        justification = (
            f"Population density within {inner_radius_km} km is "
            f"{inner_ring.density_per_km2:,.0f} persons/km², exceeding "
            f"the legacy review threshold of {density_threshold:,.0f} "
            "persons/km²; recorded for RI-04 ranking/review only"
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
    """RI-04: Populate EPZ-ring density evidence without failing sites."""

    criterion_id = RI04_CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningVerdictModel]:
        from datetime import datetime, timezone

        epz_cfg = _epz_config(settings)
        radii_km = epz_cfg.get("radii_km", DEFAULT_EPZ_RADII_KM)
        density_threshold = epz_cfg.get(
            "population_density_avoidance_threshold", DEFAULT_DENSITY_THRESHOLD,
        )
        city_threshold = epz_cfg.get(
            "city_population_threshold", DEFAULT_CITY_POP_THRESHOLD,
        )

        connector = PopulationConnector(settings)

        ensure_data_source(
            session,
            name="osm_overpass_population",
            url=connector._overpass._url,
            description="OSM Overpass API for population density screening",
        )

        smr_designs = session.execute(select(SmrDesign)).scalars().all()
        sites = session.execute(select(Site)).scalars().all()
        verdicts: list[ScreeningVerdictModel] = []

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

            verdict, value_dict, justification = evaluate_ri04(
                pop_result.rings, density_threshold,
            )

            elapsed_ms = int((time.monotonic() - t0) * 1000)

            if verdict == "inconclusive":
                write_observation(
                    session, site_id=site.site_id, criterion_id=RI04_CRITERION_ID,
                    observation="Population data unavailable for RI-04 screening",
                    run_id=run_id, confidence="low", impact="blocking",
                )

            if pop_result.rings and all(r.place_count == 0 for r in pop_result.rings):
                write_observation(
                    session, site_id=site.site_id, criterion_id=RI04_CRITERION_ID,
                    observation="Zero populated places found; density may be underestimated",
                    run_id=run_id, confidence="medium", impact="negative",
                )

            threshold_text = (
                f">{density_threshold:,.0f} persons/km² within "
                f"{radii_km[0]} km (legacy review marker only; not a gate)"
            )

            ri_row = session.get(SiteRadiological, site.site_id)
            if ri_row is None:
                ri_row = SiteRadiological(site_id=site.site_id)
                session.add(ri_row)

            for r in pop_result.rings:
                if r.outer_km <= 5.5:
                    ri_row.pop_density_5km = r.density_per_km2
                    ri_row.pop_total_5km = r.population
                elif r.outer_km <= 16.5:
                    ri_row.pop_density_16km = r.density_per_km2
                    ri_row.pop_total_16km = r.population
                elif r.outer_km <= 25.5:
                    ri_row.pop_density_25km = r.density_per_km2
                    ri_row.pop_total_25km = r.population
                elif r.outer_km <= 80.5:
                    ri_row.pop_density_80km = r.density_per_km2
                    ri_row.pop_total_80km = r.population
            ri_row.ri04_quality = "low" if verdict == "inconclusive" else "medium"
            ri_row.fetched_at = datetime.now(timezone.utc)
            ri_row.run_id = run_id

            ri05_data = evaluate_ri05(
                pop_result.nearest_large_cities, city_threshold,
            )
            ri_row.nearest_city_50k_km = ri05_data.get("nearest_city_distance_km")
            ri_row.nearest_city_name = ri05_data.get("nearest_city_name")
            ri_row.nearest_city_pop = ri05_data.get("nearest_city_population")
            ri_row.ri05_quality = "medium" if ri05_data.get("nearest_city_name") else "low"

            for smr in smr_designs:
                verdicts.append(
                    ScreeningVerdictModel(
                        site_id=site.site_id,
                        smr_key=smr.smr_key,
                        criterion_id=self.criterion_id,
                        phase=self.phase,
                        verdict=verdict,
                        measured_value=json.dumps(value_dict),
                        threshold=threshold_text,
                        justification=justification,
                        confidence="medium" if verdict != "inconclusive" else "low",
                        data_sources=["osm_overpass", "geonames (population)"],
                        run_id=run_id,
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
        log.info("epz_population_persist_ok", run_id=run_id, site_count=len(verdicts))
        return verdicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _epz_config(settings: Settings) -> dict[str, Any]:
    """Read EPZ config from the screening section."""
    return settings._yaml.get("screening", {}).get("epz", {})
