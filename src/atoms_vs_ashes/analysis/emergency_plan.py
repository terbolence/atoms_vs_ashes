# man_hours: 16.0
"""EP-01 Emergency Planning Feasibility composite.

Combines four sub-criteria into an overall feasibility assessment:

EP-02 — Evacuation route capacity (road network density within EPZ).
EP-03 — Special populations within EPZ (hospitals, prisons, care homes).
EP-04 — Physical geography barriers (rivers, major waterways that
         complicate evacuation).
EP-05 — EPZ population magnitude (from population connector).

The composite verdict is ``pass`` when no sub-criterion flags severe
concern, ``fail`` when multiple sub-criteria are critically adverse, and
``inconclusive`` when data is insufficient.

Scoring uses a weighted 0–100 scale:
  EP-02 weight 0.30  (road adequacy)
  EP-03 weight 0.20  (special populations)
  EP-04 weight 0.15  (geography barriers)
  EP-05 weight 0.35  (EPZ population load)

A composite score below the configurable ``fail_threshold`` (default 30)
produces a ``fail`` verdict.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.connectors.population import PopulationConnector, PopulationResult
from atoms_vs_ashes.db.models import (
    DataQualityFlag,
    ScreeningResult,
    Site,
    SiteAttribute,
)
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.screening.base import ScreeningCheck, register_check

log = get_logger(__name__)

EP01_CRITERION_ID = "EP-01"
PHASE = "screening"

# Sub-criteria weights (must sum to 1.0)
WEIGHTS = {
    "ep02_roads": 0.30,
    "ep03_special_pop": 0.20,
    "ep04_geography": 0.15,
    "ep05_population": 0.35,
}

DEFAULT_FAIL_THRESHOLD = 30
DEFAULT_EPZ_RADIUS_KM = 25

# Special population amenity types queried from OSM
SPECIAL_POP_AMENITIES = ["hospital", "prison", "nursing_home", "clinic"]

# Road density benchmarks (km of road per km²)
# Based on European average for rural/suburban areas
ROAD_DENSITY_EXCELLENT = 2.0
ROAD_DENSITY_ADEQUATE = 0.8
ROAD_DENSITY_POOR = 0.3


# ---------------------------------------------------------------------------
# Sub-criterion scorers (0–100, higher = more favourable)
# ---------------------------------------------------------------------------

def score_ep02_roads(road_data: dict[str, Any]) -> tuple[float, str]:
    """Score evacuation route capacity based on road density.

    Higher road density = better evacuation capacity = higher score.
    """
    density = road_data.get("density_km_per_km2", 0.0)
    total_km = road_data.get("total_road_km", 0.0)
    by_class = road_data.get("by_class_km", {})

    has_motorway = by_class.get("motorway", 0) + by_class.get("trunk", 0) > 0
    motorway_bonus = 10 if has_motorway else 0

    if density >= ROAD_DENSITY_EXCELLENT:
        base_score = 90
    elif density >= ROAD_DENSITY_ADEQUATE:
        base_score = 60 + 30 * (
            (density - ROAD_DENSITY_ADEQUATE)
            / (ROAD_DENSITY_EXCELLENT - ROAD_DENSITY_ADEQUATE)
        )
    elif density >= ROAD_DENSITY_POOR:
        base_score = 30 + 30 * (
            (density - ROAD_DENSITY_POOR)
            / (ROAD_DENSITY_ADEQUATE - ROAD_DENSITY_POOR)
        )
    else:
        base_score = max(0, 30 * (density / ROAD_DENSITY_POOR))

    score = min(100, base_score + motorway_bonus)

    justification = (
        f"Road density {density:.2f} km/km² "
        f"({total_km:.0f} km total), "
        f"{'includes' if has_motorway else 'no'} motorway/trunk"
    )
    return round(score, 1), justification


def score_ep03_special_populations(
    amenities: list[dict[str, Any]],
    epz_population: int,
) -> tuple[float, str]:
    """Score based on number and type of special-population facilities.

    Fewer special-population facilities relative to total population
    = easier emergency planning = higher score.
    """
    counts: dict[str, int] = {}
    for a in amenities:
        atype = a.get("amenity", "other")
        counts[atype] = counts.get(atype, 0) + 1

    total_facilities = len(amenities)
    hospitals = counts.get("hospital", 0) + counts.get("clinic", 0)
    prisons = counts.get("prison", 0)
    care_homes = counts.get("nursing_home", 0)

    if total_facilities == 0:
        score = 90.0
        justification = "No special-population facilities found within EPZ"
    else:
        per_100k = total_facilities / max(epz_population / 100_000, 0.1)
        if per_100k <= 2:
            score = 80.0
        elif per_100k <= 5:
            score = 60.0
        elif per_100k <= 10:
            score = 40.0
        else:
            score = 20.0

        if prisons > 0:
            score -= 10 * prisons

        score = max(0, min(100, score))
        justification = (
            f"{total_facilities} facilities "
            f"({hospitals} hospital/clinic, {prisons} prison, "
            f"{care_homes} care home), "
            f"{per_100k:.1f} per 100k population"
        )

    return round(score, 1), justification


def score_ep04_geography(
    waterway_count: int,
    has_major_river: bool,
) -> tuple[float, str]:
    """Score physical geography barriers to evacuation.

    Fewer barriers = easier evacuation = higher score.
    Rivers and large waterways can segment evacuation routes, reducing
    the number of available escape paths.
    """
    if waterway_count == 0:
        score = 95.0
        justification = "No significant waterway barriers within EPZ"
    elif not has_major_river and waterway_count <= 2:
        score = 75.0
        justification = (
            f"{waterway_count} minor waterway(s), "
            "no major river crossing EPZ"
        )
    elif not has_major_river:
        score = 55.0
        justification = (
            f"{waterway_count} waterways, no major river — "
            "moderate barrier complexity"
        )
    elif waterway_count <= 3:
        score = 40.0
        justification = (
            f"Major river plus {waterway_count - 1} other waterway(s) — "
            "significant barrier"
        )
    else:
        score = max(10, 40 - 5 * (waterway_count - 3))
        justification = (
            f"Major river and {waterway_count - 1} waterways — "
            "complex evacuation geography"
        )

    return round(score, 1), justification


def score_ep05_population(
    epz_population: int,
    density_inner_km2: float,
    density_threshold: float,
) -> tuple[float, str]:
    """Score EPZ population load.

    Lower population within the EPZ = easier emergency planning = higher score.
    """
    ratio = density_inner_km2 / density_threshold if density_threshold else 0

    if ratio <= 0.1:
        score = 95.0
    elif ratio <= 0.3:
        score = 80.0
    elif ratio <= 0.6:
        score = 60.0
    elif ratio <= 1.0:
        score = 35.0
    else:
        score = max(0, 20 - 10 * (ratio - 1.0))

    score = max(0, min(100, score))
    justification = (
        f"EPZ population {epz_population:,}, "
        f"inner density {density_inner_km2:,.0f}/km² "
        f"({ratio:.0%} of threshold)"
    )
    return round(score, 1), justification


# ---------------------------------------------------------------------------
# Composite evaluation (pure logic)
# ---------------------------------------------------------------------------

@dataclass
class EP01SubScore:
    sub_criterion: str
    score: float
    weight: float
    justification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub_criterion": self.sub_criterion,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": round(self.score * self.weight, 2),
            "justification": self.justification,
        }


@dataclass
class EP01Result:
    composite_score: float = 0.0
    sub_scores: list[EP01SubScore] = field(default_factory=list)
    verdict: str = "inconclusive"
    justification: str = ""
    data_quality: str = "estimated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite_score": round(self.composite_score, 1),
            "sub_scores": [s.to_dict() for s in self.sub_scores],
            "verdict": self.verdict,
            "justification": self.justification,
            "data_quality": self.data_quality,
        }


def evaluate_ep01(
    road_data: dict[str, Any],
    amenities: list[dict[str, Any]],
    waterway_count: int,
    has_major_river: bool,
    epz_population: int,
    density_inner_km2: float,
    density_threshold: float,
    fail_threshold: float = DEFAULT_FAIL_THRESHOLD,
) -> EP01Result:
    """Compute the EP-01 composite feasibility score."""
    subs: list[EP01SubScore] = []

    s02, j02 = score_ep02_roads(road_data)
    subs.append(EP01SubScore("EP-02", s02, WEIGHTS["ep02_roads"], j02))

    s03, j03 = score_ep03_special_populations(amenities, epz_population)
    subs.append(EP01SubScore("EP-03", s03, WEIGHTS["ep03_special_pop"], j03))

    s04, j04 = score_ep04_geography(waterway_count, has_major_river)
    subs.append(EP01SubScore("EP-04", s04, WEIGHTS["ep04_geography"], j04))

    s05, j05 = score_ep05_population(
        epz_population, density_inner_km2, density_threshold,
    )
    subs.append(EP01SubScore("EP-05", s05, WEIGHTS["ep05_population"], j05))

    composite = sum(s.score * s.weight for s in subs)

    if composite < fail_threshold:
        verdict = "fail"
        justification = (
            f"EP-01 composite score {composite:.0f}/100 "
            f"below threshold {fail_threshold}"
        )
    else:
        verdict = "pass"
        justification = (
            f"EP-01 composite score {composite:.0f}/100 "
            f"(threshold {fail_threshold})"
        )

    low_subs = [s for s in subs if s.score < 30]
    if low_subs:
        names = ", ".join(s.sub_criterion for s in low_subs)
        justification += f". Critical sub-scores: {names}"

    return EP01Result(
        composite_score=composite,
        sub_scores=subs,
        verdict=verdict,
        justification=justification,
    )


# ---------------------------------------------------------------------------
# Screening check — EP-01
# ---------------------------------------------------------------------------

@register_check
class EmergencyPlanCheck(ScreeningCheck):
    """EP-01: Emergency Planning Feasibility composite."""

    criterion_id = EP01_CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningResult]:
        epz_cfg = settings._yaml.get("screening", {}).get("epz", {})
        radii_km = epz_cfg.get("radii_km", DEFAULT_EPZ_RADIUS_KM)
        density_threshold = epz_cfg.get(
            "population_density_avoidance_threshold", 1_000,
        )
        fail_threshold = epz_cfg.get(
            "ep01_fail_threshold", DEFAULT_FAIL_THRESHOLD,
        )
        epz_radius_m = DEFAULT_EPZ_RADIUS_KM * 1_000

        overpass = OverpassClient()
        pop_connector = PopulationConnector(settings)
        sites = session.execute(select(Site)).scalars().all()
        results: list[ScreeningResult] = []

        for site in sites:
            lat, lon = float(site.latitude), float(site.longitude)

            ep01_result = self._assess_site(
                lat, lon,
                epz_radius_m=epz_radius_m,
                density_threshold=density_threshold,
                fail_threshold=fail_threshold,
                radii_km=(
                    radii_km
                    if isinstance(radii_km, list)
                    else DEFAULT_EPZ_RADIUS_KM
                ),
                overpass=overpass,
                pop_connector=pop_connector,
            )

            if ep01_result.verdict == "inconclusive":
                session.add(
                    DataQualityFlag(
                        site_id=site.site_id,
                        dataset="emergency_planning",
                        dimension="ep01_composite",
                        level="low",
                        detail="Insufficient data for EP-01 assessment",
                        run_id=run_id,
                    )
                )

            session.merge(
                SiteAttribute(
                    site_id=site.site_id,
                    criterion_id=self.criterion_id,
                    value_numeric=ep01_result.composite_score,
                    value_json=ep01_result.to_dict(),
                    run_id=run_id,
                    cache_status="fresh",
                )
            )

            results.append(
                ScreeningResult(
                    site_id=site.site_id,
                    criterion_id=self.criterion_id,
                    phase=self.phase,
                    verdict=ep01_result.verdict,
                    value=json.dumps(ep01_result.to_dict()),
                    threshold=f"Composite >= {fail_threshold}/100",
                    justification=ep01_result.justification,
                    source_refs="osm_overpass (roads, amenities, waterways)",
                    run_id=run_id,
                )
            )

        overpass.close()
        pop_connector.close()
        return results

    @staticmethod
    def _assess_site(
        lat: float,
        lon: float,
        *,
        epz_radius_m: float,
        density_threshold: float,
        fail_threshold: float,
        radii_km: list[float] | int,
        overpass: OverpassClient,
        pop_connector: PopulationConnector,
    ) -> EP01Result:
        """Gather all sub-criterion data and compute EP-01."""
        radii = radii_km if isinstance(radii_km, list) else [5, 16, 25, 80]

        try:
            road_data = overpass.fetch_road_density(lat, lon, epz_radius_m)
        except Exception as exc:
            log.warning("ep01_road_error", error=str(exc), lat=lat, lon=lon)
            road_data = {"density_km_per_km2": 0, "total_road_km": 0}

        try:
            raw_amenities = overpass.fetch_amenities(
                lat, lon, epz_radius_m, SPECIAL_POP_AMENITIES,
            )
            amenities = [
                {"amenity": el.tags.get("amenity", ""), "name": el.tags.get("name", "")}
                for el in raw_amenities
            ]
        except Exception as exc:
            log.warning("ep01_amenity_error", error=str(exc), lat=lat, lon=lon)
            amenities = []

        try:
            waterways = overpass.fetch_waterways(lat, lon, epz_radius_m)
            waterway_count = len(waterways)
            has_major_river = any(
                el.tags.get("waterway") == "river" for el in waterways
            )
        except Exception as exc:
            log.warning("ep01_waterway_error", error=str(exc), lat=lat, lon=lon)
            waterway_count = 0
            has_major_river = False

        try:
            pop_result = pop_connector.fetch(lat, lon, radii_km=radii)
            epz_population = pop_result.total_population_80km
            inner_ring = pop_result.rings[0] if pop_result.rings else None
            density_inner = inner_ring.density_per_km2 if inner_ring else 0.0
        except Exception as exc:
            log.warning("ep01_pop_error", error=str(exc), lat=lat, lon=lon)
            epz_population = 0
            density_inner = 0.0

        return evaluate_ep01(
            road_data=road_data,
            amenities=amenities,
            waterway_count=waterway_count,
            has_major_river=has_major_river,
            epz_population=epz_population,
            density_inner_km2=density_inner,
            density_threshold=density_threshold,
            fail_threshold=fail_threshold,
        )
