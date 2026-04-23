#!/usr/bin/env python
# man_hours: 3.5
"""Overpass Batch Orchestrator — autonomous interleaved EP-02 / EP-04 / transport.

Strategy per round:
  PRE-ROUND (once if needed):
    0. Run EP-01 road_score recalc (pure DB, no Overpass — fast)
  EACH ROUND:
    1. Run ONE pass of EP-02 (all remaining zero-density sites)
    2. Run ONE pass of EP-04 (all remaining NULL-amenity sites)
    3. Run ONE pass of transport gaps (nearest_highway/rail/waterway NULL sites)
    4. Check remaining counts for all three
    5. If any remain → cooldown → go to 1
    6. Repeat until all are at 0

Interleaving lets the Overpass server breathe between heavy road-geom
queries (EP-02) and lighter amenity/transport queries, and ensures
progress on all workstreams even when one is temporarily blocked.

Launch detached:
    nohup python scripts/run_overpass_orchestrator.py > /tmp/overpass_orchestrator.log 2>&1 &

Monitor:
    tail -f /tmp/overpass_orchestrator.log
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from atoms_vs_ashes.config import Settings
from sqlalchemy import create_engine, text

PYTHON = sys.executable
SCRIPTS = PROJECT_ROOT / "scripts"
EP01_SCRIPT  = SCRIPTS / "run_fix07_ep01_road_score_recalc.py"
EP02_SCRIPT  = SCRIPTS / "run_ep02_road_density_requery.py"
EP04_SCRIPT  = SCRIPTS / "run_fix05_osm_amenities_batch.py"
TRAN_SCRIPT  = SCRIPTS / "run_fix08_transport_gaps.py"

PASS_COOLDOWN_S = 300


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_engine():
    return create_engine(Settings().database.url, echo=False, pool_pre_ping=True)


def get_remaining(engine) -> dict:
    with engine.connect() as c:
        ep02 = c.execute(text("""
            SELECT COUNT(*) FROM site_emergency_planning
            WHERE road_density_km_per_km2 = 0
              AND (total_road_km IS NULL OR total_road_km = 0)
        """)).scalar()
        ep04 = c.execute(text("""
            SELECT COUNT(*) FROM site_emergency_planning
            WHERE hospital_count_epz IS NULL
        """)).scalar()
        transport = c.execute(text("""
            SELECT COUNT(DISTINCT s.site_id)
            FROM   sites s
            LEFT JOIN site_infrastructure_v2 iv ON iv.site_id = s.site_id
            WHERE  iv.nearest_highway_km IS NULL
               OR  iv.nearest_rail_km    IS NULL
               OR  iv.nearest_waterway_km IS NULL
        """)).scalar()
    return {"ep02": ep02, "ep04": ep04, "transport": transport}


def print_stats(engine) -> None:
    with engine.connect() as c:
        ep01 = c.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE ep01_road_score > 0) AS ok,
                COUNT(*) FILTER (WHERE ep01_road_score = 0 OR ep01_road_score IS NULL) AS zero_or_null
            FROM site_emergency_planning
        """)).mappings().first()
        ep02 = c.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE road_density_km_per_km2 > 0) AS ok,
                COUNT(*) FILTER (WHERE road_density_km_per_km2 = 0
                                    OR road_density_km_per_km2 IS NULL) AS rem,
                AVG(road_density_km_per_km2)
                    FILTER (WHERE road_density_km_per_km2 > 0) AS avg_d,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY road_density_km_per_km2)
                    FILTER (WHERE road_density_km_per_km2 > 0) AS med_d
            FROM site_emergency_planning
        """)).mappings().first()
        ep04 = c.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE hospital_count_epz IS NOT NULL) AS ok,
                COUNT(*) FILTER (WHERE hospital_count_epz IS NULL) AS rem,
                AVG(hospital_count_epz)
                    FILTER (WHERE hospital_count_epz IS NOT NULL) AS avg_h,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hospital_count_epz)
                    FILTER (WHERE hospital_count_epz IS NOT NULL) AS med_h
            FROM site_emergency_planning
        """)).mappings().first()
        tran = c.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE iv.nearest_highway_km IS NOT NULL) AS hw_ok,
                COUNT(*) FILTER (WHERE iv.nearest_highway_km IS NULL)     AS hw_null,
                COUNT(*) FILTER (WHERE iv.nearest_rail_km IS NOT NULL)    AS rail_ok,
                COUNT(*) FILTER (WHERE iv.nearest_rail_km IS NULL)        AS rail_null,
                COUNT(*) FILTER (WHERE iv.nearest_waterway_km IS NOT NULL) AS ww_ok,
                COUNT(*) FILTER (WHERE iv.nearest_waterway_km IS NULL)    AS ww_null
            FROM sites s
            LEFT JOIN site_infrastructure_v2 iv ON iv.site_id = s.site_id
        """)).mappings().first()

    log(f"  EP-01: {ep01['ok']} OK (road_score>0), {ep01['zero_or_null']} zero/null")
    log(f"  EP-02: {ep02['ok']} OK, {ep02['rem']} remaining | "
        f"density avg={float(ep02['avg_d'] or 0):.3f} med={float(ep02['med_d'] or 0):.3f}")
    log(f"  EP-04: {ep04['ok']} OK, {ep04['rem']} remaining | "
        f"hospital avg={float(ep04['avg_h'] or 0):.1f} med={float(ep04['med_h'] or 0):.0f}")
    log(f"  Transport: hw {tran['hw_ok']} OK / {tran['hw_null']} NULL | "
        f"rail {tran['rail_ok']} OK / {tran['rail_null']} NULL | "
        f"ww {tran['ww_ok']} OK / {tran['ww_null']} NULL")


# ---------------------------------------------------------------------------
# Script runner
# ---------------------------------------------------------------------------

def run_script(script_path: Path, args: list[str], label: str) -> int:
    cmd = [PYTHON, str(script_path)] + args
    log(f"[{label}] Running: {' '.join(str(c) for c in cmd)}")
    t0 = time.monotonic()

    try:
        proc = subprocess.Popen(
            cmd, cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in proc.stdout:
            print(f"  | {line}", end="", flush=True)

        proc.wait()
        elapsed = time.monotonic() - t0
        log(f"[{label}] Exit code {proc.returncode} ({elapsed/60:.1f} min)")
        return proc.returncode
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log(f"[{label}] SUBPROCESS EXCEPTION after {elapsed/60:.1f} min: {exc}")
        log(f"[{label}] Orchestrator will continue to next pass after 60s cooldown.")
        time.sleep(60)
        return -1


# ---------------------------------------------------------------------------
# EP-01 recalc (pure DB, runs until no zero-scores remain)
# ---------------------------------------------------------------------------

def run_ep01_recalc_if_needed(engine) -> None:
    """Check for ep01_road_score=0 on sites with density>0 and fix them."""
    with engine.connect() as c:
        zero_with_density = c.execute(text("""
            SELECT COUNT(*) FROM site_emergency_planning
            WHERE road_density_km_per_km2 > 0 AND ep01_road_score = 0
        """)).scalar()

    if zero_with_density == 0:
        log("EP-01 recalc: already correct — no zero-score sites with density>0.")
        return

    log(f"EP-01 recalc: {zero_with_density} sites have density>0 but score=0 — running recalc...")
    run_script(EP01_SCRIPT, [], "EP-01 recalc")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Overpass orchestrator — interleaved EP-02/EP-04/transport until done."
    )
    parser.add_argument("--overpass-url", default=None)
    args = parser.parse_args()

    url_args = ["--overpass-url", args.overpass_url] if args.overpass_url else []

    engine = _get_engine()

    log("=" * 70)
    log("OVERPASS BATCH ORCHESTRATOR — interleaved autonomous mode")
    log("Workstreams: EP-01 recalc (DB) + EP-02 (Overpass) + EP-04 (Overpass) + transport (Overpass)")
    log("=" * 70)

    # EP-01 recalc: pure DB, always safe to run first
    run_ep01_recalc_if_needed(engine)

    counts = get_remaining(engine)
    log(
        f"Starting state: EP-02={counts['ep02']} rem, "
        f"EP-04={counts['ep04']} rem, "
        f"transport={counts['transport']} rem"
    )
    print_stats(engine)

    round_num = 0

    while True:
        counts = get_remaining(engine)
        if counts["ep02"] == 0 and counts["ep04"] == 0 and counts["transport"] == 0:
            break

        round_num += 1
        log(f"{'='*70}")
        log(
            f"ROUND {round_num} — "
            f"EP-02={counts['ep02']} rem, "
            f"EP-04={counts['ep04']} rem, "
            f"transport={counts['transport']} rem"
        )
        log(f"{'='*70}")

        ep02_before     = counts["ep02"]
        ep04_before     = counts["ep04"]
        transport_before = counts["transport"]

        # --- EP-02 pass ---
        if ep02_before > 0:
            log(f"EP-02 pass — {ep02_before} sites to attempt")
            run_script(EP02_SCRIPT, url_args, f"EP-02 R{round_num}")
        else:
            log("EP-02: already complete, skipping")

        # --- EP-04 pass ---
        counts = get_remaining(engine)
        if counts["ep04"] > 0:
            log(f"EP-04 pass — {counts['ep04']} sites to attempt")
            run_script(
                EP04_SCRIPT,
                ["--max-passes", "1"] + url_args,
                f"EP-04 R{round_num}",
            )
        else:
            log("EP-04: already complete, skipping")

        # --- Transport pass ---
        counts = get_remaining(engine)
        if counts["transport"] > 0:
            log(f"Transport pass — {counts['transport']} sites with NULL columns")
            run_script(TRAN_SCRIPT, url_args, f"Transport R{round_num}")
        else:
            log("Transport: already complete, skipping")

        # --- EP-01 recalc after round (density may have been filled by EP-02) ---
        run_ep01_recalc_if_needed(engine)

        # --- Check progress ---
        counts = get_remaining(engine)
        ep02_progressed      = ep02_before     - counts["ep02"]
        ep04_progressed      = ep04_before     - counts["ep04"]
        transport_progressed = transport_before - counts["transport"]
        total_progressed     = ep02_progressed + ep04_progressed + transport_progressed

        log(f"Round {round_num} results:")
        log(f"  EP-02:     {ep02_progressed} enriched this round, {counts['ep02']} remaining")
        log(f"  EP-04:     {ep04_progressed} enriched this round, {counts['ep04']} remaining")
        log(f"  Transport: {transport_progressed} enriched this round, {counts['transport']} remaining")
        print_stats(engine)

        if counts["ep02"] == 0 and counts["ep04"] == 0 and counts["transport"] == 0:
            break

        if total_progressed == 0:
            cooldown = PASS_COOLDOWN_S * 2
            log(
                f"Zero progress this round — server heavily loaded. "
                f"Extended cooldown {cooldown}s..."
            )
        else:
            cooldown = PASS_COOLDOWN_S
            log(f"Cooldown {cooldown}s before next round...")

        time.sleep(cooldown)

    # --- Final report ---
    final = get_remaining(engine)
    engine.dispose()

    log("=" * 70)
    log("ORCHESTRATOR FINISHED")
    log(
        f"Final: EP-02={final['ep02']} remaining, "
        f"EP-04={final['ep04']} remaining, "
        f"transport={final['transport']} remaining"
    )
    if final["ep02"] == 0 and final["ep04"] == 0 and final["transport"] == 0:
        log("ALL SITES ENRICHED SUCCESSFULLY")
    else:
        remaining_items = []
        if final["ep02"]:
            remaining_items.append(f"EP-02: {final['ep02']}")
        if final["ep04"]:
            remaining_items.append(f"EP-04: {final['ep04']}")
        if final["transport"]:
            remaining_items.append(f"transport: {final['transport']}")
        log(f"GAPS REMAIN: {', '.join(remaining_items)}")
        log("Re-run this script to continue.")
    log("=" * 70)


if __name__ == "__main__":
    _CRASH_COOLDOWN_S = 300  # 5 min before restarting after an unexpected crash
    while True:
        try:
            main()
            break  # clean exit — all done
        except KeyboardInterrupt:
            print("\n[orchestrator] Interrupted by user — exiting.", flush=True)
            break
        except Exception as exc:
            import traceback
            print(
                f"\n[orchestrator] UNHANDLED EXCEPTION: {exc}\n"
                f"{traceback.format_exc()}"
                f"Sleeping {_CRASH_COOLDOWN_S}s then restarting the main loop...\n",
                flush=True,
            )
            time.sleep(_CRASH_COOLDOWN_S)
