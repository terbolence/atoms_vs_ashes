"""Orchestration engine — drives the four execution phases.

Phase 2 (connector fetch) submits one worker per API group to a
``ThreadPoolExecutor`` so different APIs are queried in parallel while
each respects its own rate limit.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ava_client import display
from ava_client.cache import SiteDataCache
from ava_client.config import RATE_LIMITS
from ava_client.phases import analysis, health, summary
from ava_client.phases.connectors import (
    run_corine_worker,
    run_egdi_worker,
    run_overpass_worker,
    run_seismic_worker,
)
from ava_client.rate_limiter import ApiRateLimiter
from ava_client.resolver import ResolvedSite


def run(
    sites: list[ResolvedSite],
    settings: Any,
    *,
    run_id: str,
    skip: set[str],
    output_dir: Path,
    write_snapshots: bool = True,
    dry_run: bool = False,
) -> int:
    """Execute all four phases and return an exit code (0 = clean, 1 = partial)."""

    total_start = time.monotonic()
    cache = SiteDataCache()

    display.print_header(run_id, len(sites), str(settings._yaml.get("_path", "default.yml")), skip)

    # -- Phase 1: Health Checks -----------------------------------------------
    display.print_phase_title(1, 4, "Health Checks")
    health_results, auto_skip = health.run_health_checks(
        settings, skip, output_dir, run_id, write_snapshots,
    )
    effective_skip = skip | auto_skip

    if dry_run:
        display.print_warning("Dry-run mode — stopping after health checks.")
        return 0

    all_connectors_skipped = all(
        slug in effective_skip
        for slug in ("corine", "osm", "population", "egdi", "seismic")
    )
    if all_connectors_skipped:
        display.print_warning("All connectors skipped or failed. Nothing to fetch.")
        return 5

    # -- Phase 2: Connector Fetch (parallel) ----------------------------------
    display.print_phase_title(2, 4, "Connector Fetch (parallel)")

    limiters = {
        name: ApiRateLimiter(name, delay, concurrency)
        for name, (delay, concurrency) in RATE_LIMITS.items()
    }

    workers: dict[str, Any] = {}
    if "osm" not in effective_skip or "population" not in effective_skip:
        workers["overpass"] = (
            run_overpass_worker,
            (sites, settings, cache, limiters["overpass"], run_id),
        )
    if "corine" not in effective_skip:
        workers["corine"] = (
            run_corine_worker,
            (sites, settings, cache, limiters["corine"], run_id),
        )
    if "egdi" not in effective_skip:
        workers["egdi"] = (
            run_egdi_worker,
            (sites, settings, cache, limiters["egdi"], run_id),
        )
    if "seismic" not in effective_skip:
        workers["seismic"] = (
            run_seismic_worker,
            (sites, settings, cache, limiters["seismic"], run_id),
        )

    fetch_stats: dict[str, dict[str, int]] = {}
    with ThreadPoolExecutor(max_workers=len(workers), thread_name_prefix="ava") as pool:
        futures = {
            pool.submit(fn, *args): name
            for name, (fn, args) in workers.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                fetch_stats[name] = future.result()
            except Exception as exc:
                display.print_fail(f"{name} worker crashed: {exc}")
                fetch_stats[name] = {"ok": 0, "fail": 1}

    # -- Phase 3: Analysis ----------------------------------------------------
    if "analysis" not in effective_skip:
        display.print_phase_title(3, 4, "Analysis Modules")
        analysis_stats = analysis.run_analyses(sites, settings, cache, run_id)
    else:
        display.print_phase_title(3, 4, "Analysis Modules (skipped)")
        analysis_stats = {"ok": 0, "fail": 0, "skip": 0}

    # -- Phase 4: Summary -----------------------------------------------------
    elapsed = time.monotonic() - total_start
    display.print_phase_title(4, 4, "Summary")
    summary.generate_summary(
        run_id=run_id,
        site_count=len(sites),
        health_results=health_results,
        fetch_stats=fetch_stats,
        analysis_stats=analysis_stats,
        elapsed_s=elapsed,
        cache=cache,
        output_dir=output_dir,
        write_snapshots=write_snapshots,
    )

    total_fail = sum(s.get("fail", 0) for s in fetch_stats.values()) + analysis_stats.get("fail", 0)
    return 1 if total_fail > 0 else 0
