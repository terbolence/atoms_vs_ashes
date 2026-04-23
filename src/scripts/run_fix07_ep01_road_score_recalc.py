#!/usr/bin/env python3
# man_hours: 0.5
"""Fix 07: Recalculate ep01_road_score from already-populated road_density_km_per_km2.

No Overpass calls needed. Sites that previously had road_density_km_per_km2 > 0
but ep01_road_score = 0 were the victims of the LL-017 silent-null bug (score
was never back-propagated after road-density was filled by a later run).

This script reads road_density_km_per_km2, total_road_km, and has_motorway_access
from site_emergency_planning and rewrites ep01_road_score using the same formula
as score_ep01_roads() in emergency_plan.py.

Safe to re-run: skips sites where ep01_road_score is already correct (nonzero OR
density is genuinely 0).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from atoms_vs_ashes.config import Settings
from sqlalchemy import create_engine, text

# ---- scoring constants (mirror emergency_plan.py) -------------------------
ROAD_DENSITY_EXCELLENT = 2.0
ROAD_DENSITY_ADEQUATE = 0.8
ROAD_DENSITY_POOR = 0.3


def _score(density: float, total_km: float, has_motorway: bool) -> float:
    """Pure scoring function, identical to score_ep01_roads()."""
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
        base_score = max(0.0, 30 * (density / ROAD_DENSITY_POOR))

    return round(min(100.0, base_score + motorway_bonus), 1)


def main() -> None:
    engine = create_engine(Settings().database.url)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT site_id,
                       road_density_km_per_km2,
                       total_road_km,
                       has_motorway_access,
                       ep01_road_score
                FROM   site_emergency_planning
                WHERE  road_density_km_per_km2 IS NOT NULL
                  AND  road_density_km_per_km2 > 0
                  AND  ep01_road_score = 0
                ORDER BY site_id
                """
            )
        ).fetchall()

    if not rows:
        print("[fix07] No sites to recalculate — ep01_road_score is already correct.")
        return

    print(f"[fix07] Recalculating ep01_road_score for {len(rows)} sites...")

    updated = 0
    with engine.begin() as conn:
        for row in rows:
            density = float(row.road_density_km_per_km2 or 0.0)
            total_km = float(row.total_road_km or 0.0)
            has_motorway = bool(row.has_motorway_access)

            new_score = _score(density, total_km, has_motorway)

            conn.execute(
                text(
                    "UPDATE site_emergency_planning "
                    "SET ep01_road_score = :score "
                    "WHERE site_id = :sid"
                ),
                {"score": new_score, "sid": row.site_id},
            )
            updated += 1

    print(f"[fix07] Done — updated {updated} rows.")

    with engine.connect() as conn:
        still_zero = conn.execute(
            text(
                "SELECT COUNT(*) FROM site_emergency_planning "
                "WHERE road_density_km_per_km2 > 0 AND ep01_road_score = 0"
            )
        ).scalar()
        all_zero = conn.execute(
            text(
                "SELECT COUNT(*) FROM site_emergency_planning "
                "WHERE ep01_road_score = 0"
            )
        ).scalar()

    print(f"[fix07] Sites with density>0 but score=0 remaining: {still_zero}")
    print(f"[fix07] Sites with score=0 total (genuine zero-density or not enriched): {all_zero}")


if __name__ == "__main__":
    main()
