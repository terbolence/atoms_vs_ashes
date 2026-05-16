#!/usr/bin/env python3
# man_hours: 0.6
"""Fix 09: Recalculate EP-01 composite, feasibility flag, and comment.

Background
----------
``run_fix07_ep01_road_score_recalc.py`` repaired the
``ep01_road_score`` column after the LL-017 silent-null bug, but it
did not back-propagate the change into the dependent composite
fields. That left ``site_emergency_planning`` with three stale
columns relative to the five canonical EP-01 sub-scores:

- ``ep01_composite_score``  -- the weighted 0-100 feasibility score.
- ``ep01_evacuation_feasible`` -- boolean derived from the threshold.
- ``ep01_comment`` -- the human-readable explanation shown in the GUI.

In the current merged DB, 308/361 rows show a stored composite that
disagrees with the weighted sum of the five sub-score columns, and
56 sites still carry a stale ``ep01_composite_score < 30`` failure
even though only 5 would fail when recomputed from the present
sub-scores. This script restores consistency without changing the
underlying scoring rubric.

Safety
------
- No live API calls. Reads / writes the local Postgres canonical DB
  only.
- Dry-run by default: prints before/after fail counts and largest
  deltas without modifying any row.
- Writes are only performed with the explicit ``--apply`` flag, and
  run inside a single transaction.
- Re-running with ``--apply`` is idempotent: rows already in sync
  are left untouched.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import create_engine, text

from atoms_vs_ashes.analysis.emergency_plan import (
    DEFAULT_FAIL_THRESHOLD,
    composite_from_sub_scores,
)
from atoms_vs_ashes.config import Settings

# Match the persisted comment grammar emitted by ``_persist_ep_data``:
#   "DRV-02 composite: <x>/100 (FEASIBLE|NOT FEASIBLE). Sub-scores: ...
#    Sources: osm_overpass, ghsl_pop_100m_r2023a, copernicus_dem_30m."
_SOURCES_RE = re.compile(r"Sources:\s*(.+?)\s*\.?\s*$")

# Recompute tolerance: stored column is Numeric(5, 1), so anything
# beyond ~0.1 is a real drift rather than a rounding artefact.
_MATCH_TOLERANCE = 0.1


def _extract_sources(comment: str | None) -> str | None:
    """Return the comma-separated source list from an EP-01 comment.

    Returns ``None`` when the comment is missing or does not carry a
    ``Sources:`` clause we recognise.
    """
    if not comment:
        return None
    match = _SOURCES_RE.search(comment)
    if not match:
        return None
    sources = match.group(1).strip().rstrip(".").strip()
    return sources or None


def _build_comment(
    *,
    composite: float,
    feasible: bool,
    sub_scores: dict[str, float],
    sources: str | None,
) -> str:
    """Render the canonical EP-01 comment string.

    Mirrors the format used by
    :meth:`EmergencyPlanCheck._persist_ep_data` so the GUI and audit
    bundles see a consistent shape regardless of whether the row was
    written by the screening engine or this repair script.
    """
    sub_details = "; ".join(
        f"{name}={value:.0f}" for name, value in sub_scores.items()
    )
    body = (
        f"DRV-02 composite: {composite:.1f}/100 "
        f"({'FEASIBLE' if feasible else 'NOT FEASIBLE'}). "
        f"Sub-scores: {sub_details}."
    )
    if sources:
        body += f" Sources: {sources}."
    return body


def _row_recompute(row) -> tuple[float, bool, str]:
    """Return ``(new_composite, new_feasible, new_comment)`` for ``row``."""
    sub_scores = {
        "ep01_roads": float(row.ep01_road_score or 0.0),
        "ep01_special_pop": float(row.ep01_special_pop_score or 0.0),
        "ep01_geography": float(row.ep01_geography_score or 0.0),
        "ep01_terrain": float(row.ep01_terrain_score or 0.0),
        "ep01_population": float(row.ep01_population_score or 0.0),
    }
    new_composite = composite_from_sub_scores(
        ep01_road_score=sub_scores["ep01_roads"],
        ep01_special_pop_score=sub_scores["ep01_special_pop"],
        ep01_geography_score=sub_scores["ep01_geography"],
        ep01_terrain_score=sub_scores["ep01_terrain"],
        ep01_population_score=sub_scores["ep01_population"],
    )
    new_feasible = new_composite >= DEFAULT_FAIL_THRESHOLD
    new_comment = _build_comment(
        composite=new_composite,
        feasible=new_feasible,
        sub_scores=sub_scores,
        sources=_extract_sources(row.ep01_comment),
    )
    return new_composite, new_feasible, new_comment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recalculate EP-01 composite, evacuation_feasible, and "
            "comment from the five stored sub-score columns. Dry-run by "
            "default; pass --apply to write."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Persist the recomputed values to site_emergency_planning. "
            "Without this flag the script only prints a diagnostic."
        ),
    )
    parser.add_argument(
        "--limit-report",
        type=int,
        default=12,
        help="Number of largest-delta rows to show in the report.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    engine = create_engine(Settings().database.url, pool_pre_ping=True)

    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT current_database()")).scalar()
        rows = conn.execute(
            text(
                """
                SELECT  ep.site_id,
                        s.name,
                        s.country_code,
                        ep.ep01_composite_score,
                        ep.ep01_evacuation_feasible,
                        ep.ep01_road_score,
                        ep.ep01_special_pop_score,
                        ep.ep01_geography_score,
                        ep.ep01_terrain_score,
                        ep.ep01_population_score,
                        ep.ep01_comment
                FROM    site_emergency_planning ep
                JOIN    sites s ON s.site_id = ep.site_id
                WHERE   ep.ep01_composite_score IS NOT NULL
                ORDER BY s.country_code, s.name
                """
            )
        ).fetchall()

    print(f"[fix09] DB           : {db_name}")
    print(f"[fix09] Mode         : {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"[fix09] Rows scanned : {len(rows)}")

    deltas: list[tuple] = []
    stored_fail = recomputed_fail = 0
    flipped_fail_to_pass = flipped_pass_to_fail = 0
    needs_update: list[tuple] = []

    for row in rows:
        stored_composite = float(row.ep01_composite_score)
        stored_feasible = bool(row.ep01_evacuation_feasible) if (
            row.ep01_evacuation_feasible is not None
        ) else None
        new_composite, new_feasible, new_comment = _row_recompute(row)

        if stored_composite < DEFAULT_FAIL_THRESHOLD:
            stored_fail += 1
        if new_composite < DEFAULT_FAIL_THRESHOLD:
            recomputed_fail += 1
        if (
            stored_composite < DEFAULT_FAIL_THRESHOLD
            and new_composite >= DEFAULT_FAIL_THRESHOLD
        ):
            flipped_fail_to_pass += 1
        if (
            stored_composite >= DEFAULT_FAIL_THRESHOLD
            and new_composite < DEFAULT_FAIL_THRESHOLD
        ):
            flipped_pass_to_fail += 1

        composite_drift = abs(stored_composite - new_composite)
        feasibility_drift = stored_feasible != new_feasible and (
            stored_feasible is not None
        )
        comment_drift = (row.ep01_comment or "") != new_comment

        if (
            composite_drift > _MATCH_TOLERANCE
            or feasibility_drift
            or comment_drift
        ):
            needs_update.append(
                (
                    row.site_id,
                    new_composite,
                    new_feasible,
                    new_comment,
                )
            )
            deltas.append(
                (
                    composite_drift,
                    row.name,
                    row.country_code,
                    stored_composite,
                    new_composite,
                )
            )

    deltas.sort(reverse=True)

    print(f"[fix09] Stored < 30      : {stored_fail}")
    print(f"[fix09] Recomputed < 30  : {recomputed_fail}")
    print(
        f"[fix09] Drift threshold  : composite |delta| > "
        f"{_MATCH_TOLERANCE} or feasibility / comment text changes"
    )
    print(f"[fix09] Rows needing update: {len(needs_update)}")
    print(f"[fix09] Flipped fail->pass: {flipped_fail_to_pass}")
    print(f"[fix09] Flipped pass->fail: {flipped_pass_to_fail}")

    if deltas:
        n = min(args.limit_report, len(deltas))
        print(f"\n[fix09] Top {n} composite-score deltas:")
        print(
            f"  {'site':<40} {'cc':<3} {'stored':>7} {'new':>7} {'|delta|':>8}"
        )
        for delta, name, country_code, stored, new in deltas[:n]:
            print(
                f"  {name[:40]:<40} {country_code:<3} "
                f"{stored:>7.1f} {new:>7.1f} {delta:>8.1f}"
            )

    if not args.apply:
        print("\n[fix09] Dry-run complete. Re-run with --apply to write.")
        return 0

    if not needs_update:
        print("\n[fix09] No rows require updates -- nothing to write.")
        return 0

    print(f"\n[fix09] Applying {len(needs_update)} updates...")
    with engine.begin() as conn:
        for site_id, composite, feasible, comment in needs_update:
            conn.execute(
                text(
                    """
                    UPDATE site_emergency_planning
                    SET    ep01_composite_score    = :composite,
                           ep01_evacuation_feasible = :feasible,
                           ep01_comment             = :comment
                    WHERE  site_id = :site_id
                    """
                ),
                {
                    "composite": composite,
                    "feasible": feasible,
                    "comment": comment,
                    "site_id": site_id,
                },
            )

    print("[fix09] Apply complete.")
    print(
        "[fix09] Reminder: rerun `atoms-vs-ashes score run` so "
        "screening_verdicts and ranking_scores reflect the repaired "
        "EP-01 values."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
