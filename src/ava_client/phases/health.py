"""Phase 1 — Health checks for all upstream API connectors."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ava_client import display, snapshot


def run_health_checks(
    settings: Any,
    skip: set[str],
    output_dir: Path,
    run_id: str,
    write_snapshots: bool = True,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Run connectivity checks and return (results, auto_skip).

    *auto_skip* contains connector slugs that failed and should be
    skipped in subsequent phases.
    """
    from atoms_vs_ashes.connectors.corine import CorineConnector
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.population import PopulationConnector

    checks: list[tuple[str, str, str, Any]] = []

    if "corine" not in skip:
        checks.append(("CORINE", "EEA ArcGIS REST", "corine",
                        lambda: CorineConnector(settings).health_check()))
    if "osm" not in skip:
        checks.append(("OSM", "Overpass API", "osm",
                        lambda: OverpassClient(settings).health_check()))
    if "population" not in skip:
        checks.append(("Population", "Overpass (via OSM)", "population",
                        lambda: PopulationConnector(settings).health_check()))
    if "egdi" not in skip:
        from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
        checks.append(("EGDI Geology", "EGDI WFS", "egdi",
                        lambda: all(EgdiGeologyConnector(settings).health_check().values())))
    if "seismic" not in skip:
        from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector
        checks.append(("Seismic Hazard", "EFEHR REST", "seismic",
                        lambda: SeismicHazardConnector(settings).health_check()))

    results: list[dict[str, Any]] = []
    auto_skip: set[str] = set()

    for conn_name, endpoint, slug, fn in checks:
        t0 = time.monotonic()
        try:
            ok = fn()
            ms = int((time.monotonic() - t0) * 1000)
            status = "PASS" if ok else "FAIL"
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            status = f"FAIL ({exc})"
            ok = False

        if not ok:
            auto_skip.add(slug)
            display.print_warning(f"{conn_name} will be skipped (health check failed)")

        results.append({
            "connector": conn_name,
            "endpoint": endpoint,
            "slug": slug,
            "status": status if "FAIL" not in str(status) else "FAIL",
            "elapsed_ms": ms,
        })

    # Add entries for explicitly skipped connectors
    for slug in skip:
        results.append({
            "connector": slug.upper(),
            "endpoint": "—",
            "slug": slug,
            "status": "SKIP",
            "elapsed_ms": 0,
        })

    display.print_health_table(results)

    if write_snapshots:
        md = snapshot.build_header("Health Checks", "Connectivity test for all upstream APIs",
                                   run_id, site_count=0)
        md += "| Connector | Endpoint | Status | Elapsed |\n"
        md += "|-----------|----------|--------|---------|\n"
        for r in results:
            md += f"| {r['connector']} | {r['endpoint']} | {r['status']} | {r['elapsed_ms']} ms |\n"
        snapshot.write_snapshot(output_dir, "health_checks.md", md)

    return results, auto_skip
