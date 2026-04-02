"""Phase 3 — Run analysis modules using cached connector data.

All analysis functions are pure — they do not make API calls.  If the
required input data is missing from the cache (Phase 2 failure), the
analysis is skipped for that site with an error snapshot entry.
"""

from __future__ import annotations

import time
import traceback
from typing import Any

from ava_client import display
from ava_client.cache import SiteDataCache
from ava_client.resolver import ResolvedSite
from ava_client.snapshot import build_header, build_site_section, pretty_json


def run_analyses(
    sites: list[ResolvedSite],
    settings: Any,
    cache: SiteDataCache,
    run_id: str,
) -> dict[str, int]:
    """Execute all analysis modules on cached Phase-2 data.

    Returns aggregated ``{"ok": N, "fail": M, "skip": K}`` counts.
    """
    stats = {"ok": 0, "fail": 0, "skip": 0}

    _run_corine_analyses(sites, cache, run_id, stats)
    _run_osm_analyses(sites, cache, run_id, stats)
    _run_population_analysis(sites, cache, run_id, stats)
    _run_coal_site_analysis(sites, cache, run_id, stats)

    return stats


# -- CORINE-dependent analyses -----------------------------------------------

def _run_corine_analyses(
    sites: list[ResolvedSite], cache: SiteDataCache, run_id: str,
    stats: dict[str, int],
) -> None:
    from atoms_vs_ashes.analysis.wildfire_context import assess_wildfire_context
    from atoms_vs_ashes.analysis.ecological_sensitivity import assess_ecological_sensitivity
    from atoms_vs_ashes.analysis.site_topography import assess_site_topography
    from atoms_vs_ashes.analysis.laydown_area import assess_laydown_area

    modules = [
        ("analysis_wildfire_context.md", "Wildfire Context (NH-13)",
         "Combustibility classification from CORINE",
         lambda feats, s: assess_wildfire_context(s.lat, s.lon, features=feats)),
        ("analysis_ecological_sensitivity.md", "Ecological Sensitivity (NS-08)",
         "Landscape fragmentation metrics from CORINE",
         lambda feats, s: assess_ecological_sensitivity(s.lat, s.lon, features=feats)),
        ("analysis_site_topography.md", "Site Topography (NS-04)",
         "Land cover classification within site footprint",
         lambda feats, s: assess_site_topography(s.lat, s.lon, features=feats)),
        ("analysis_laydown_area.md", "Laydown Area (NS-13)",
         "Suitable laydown areas from CORINE",
         lambda feats, s: assess_laydown_area(s.lat, s.lon, features=feats)),
    ]

    for filename, title, desc, fn in modules:
        md = build_header(title, desc, run_id, len(sites))
        for site in sites:
            features = cache.get(site, "corine_features")
            if features is None:
                md += build_site_section(site, "skip", 0, "No CORINE data cached",
                                         "CORINE fetch failed or was skipped")
                stats["skip"] += 1
                continue
            t0 = time.monotonic()
            try:
                result = fn(features, site)
                ms = int((time.monotonic() - t0) * 1000)
                status = "ok" if not result.error else "error"
                summary = str(result.error) if result.error else "OK"
                md += build_site_section(site, status, ms, summary,
                                         pretty_json(result.to_dict()))
                stats["ok"] += 1
                display.print_status(
                    f"[dim]analysis[/dim] {site.country} {site.name} {filename.replace('.md','')} "
                    f"[green]OK[/green] ({ms}ms)"
                )
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += build_site_section(site, "error", ms, str(exc),
                                         traceback.format_exc())
                stats["fail"] += 1
                display.print_status(
                    f"[dim]analysis[/dim] {site.country} {site.name} {filename.replace('.md','')} "
                    f"[red]FAIL[/red] ({ms}ms: {exc})"
                )
        cache.put_snapshot(filename, md)


# -- OSM-dependent analyses --------------------------------------------------

def _run_osm_analyses(
    sites: list[ResolvedSite], cache: SiteDataCache, run_id: str,
    stats: dict[str, int],
) -> None:
    from atoms_vs_ashes.analysis.aviation_hazard import assess_aviation_hazard
    from atoms_vs_ashes.analysis.military_proximity import assess_military_proximity
    from atoms_vs_ashes.analysis.transmitter_proximity import assess_transmitter_proximity
    from atoms_vs_ashes.analysis.grid_proximity import assess_grid_proximity
    from atoms_vs_ashes.analysis.land_availability import assess_land_availability

    modules = [
        ("analysis_aviation_hazard.md", "Aviation Hazard (HI-01)",
         "Airport proximity from OSM", "osm_airports",
         lambda elems, s: assess_aviation_hazard(s.lat, s.lon, elements=elems)),
        ("analysis_military_proximity.md", "Military Proximity (HI-06)",
         "Military installation proximity from OSM", "osm_military_areas",
         lambda elems, s: assess_military_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_transmitter_proximity.md", "Transmitter Proximity (HI-07)",
         "High-power transmitter proximity from OSM", "osm_transmitters",
         lambda elems, s: assess_transmitter_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_grid_proximity.md", "Grid Proximity (NS-02)",
         "HV power infrastructure proximity from OSM", "osm_power_infrastructure",
         lambda elems, s: assess_grid_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_land_availability.md", "Land Availability (NS-05)",
         "Contiguous buildable land from OSM", "osm_land_use",
         lambda elems, s: assess_land_availability(s.lat, s.lon, elements=elems)),
    ]

    for filename, title, desc, cache_key, fn in modules:
        md = build_header(title, desc, run_id, len(sites))
        for site in sites:
            elements = cache.get(site, cache_key)
            if elements is None:
                md += build_site_section(site, "skip", 0,
                                         f"No OSM {cache_key} data cached",
                                         "OSM fetch failed or was skipped")
                stats["skip"] += 1
                continue
            t0 = time.monotonic()
            try:
                result = fn(elements, site)
                ms = int((time.monotonic() - t0) * 1000)
                status = "ok" if not result.error else "error"
                summary = str(result.error) if result.error else "OK"
                md += build_site_section(site, status, ms, summary,
                                         pretty_json(result.to_dict()))
                stats["ok"] += 1
                display.print_status(
                    f"[dim]analysis[/dim] {site.country} {site.name} {filename.replace('.md','')} "
                    f"[green]OK[/green] ({ms}ms)"
                )
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += build_site_section(site, "error", ms, str(exc),
                                         traceback.format_exc())
                stats["fail"] += 1
                display.print_status(
                    f"[dim]analysis[/dim] {site.country} {site.name} {filename.replace('.md','')} "
                    f"[red]FAIL[/red] ({ms}ms: {exc})"
                )
        cache.put_snapshot(filename, md)


# -- Population projection --------------------------------------------------

def _run_population_analysis(
    sites: list[ResolvedSite], cache: SiteDataCache, run_id: str,
    stats: dict[str, int],
) -> None:
    from atoms_vs_ashes.analysis.population_projection import project_population

    md = build_header("Population Projection (RI-06)",
                      "60-year population projection using UN WPP growth rates",
                      run_id, len(sites))
    for site in sites:
        pop_result = cache.get(site, "population")
        if pop_result is None:
            md += build_site_section(site, "skip", 0, "No population data cached",
                                     "Population fetch failed")
            stats["skip"] += 1
            continue
        t0 = time.monotonic()
        try:
            result = project_population(pop_result, site.country)
            ms = int((time.monotonic() - t0) * 1000)
            total_current = sum(r.get("current_population", 0) for r in result.ring_projections)
            total_projected = sum(r.get("projected_population", 0) for r in result.ring_projections)
            summary = (f"current={total_current:,}, projected={total_projected:,}, "
                       f"rate={result.growth_rate}, year={result.projection_year}")
            md += build_site_section(site, "ok", ms, summary, pretty_json(result.to_dict()))
            stats["ok"] += 1
            display.print_status(
                f"[dim]analysis[/dim] {site.country} {site.name} population_projection "
                f"[green]OK[/green] ({ms}ms)"
            )
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += build_site_section(site, "error", ms, str(exc), traceback.format_exc())
            stats["fail"] += 1
            display.print_status(
                f"[dim]analysis[/dim] {site.country} {site.name} population_projection "
                f"[red]FAIL[/red] ({ms}ms: {exc})"
            )
    cache.put_snapshot("analysis_population_projection.md", md)


# -- Coal site analysis (no live data needed) --------------------------------

def _run_coal_site_analysis(
    sites: list[ResolvedSite], cache: SiteDataCache, run_id: str,
    stats: dict[str, int],
) -> None:
    from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

    md = build_header("Coal Site Analysis (NS-05)",
                      "Coal site area sufficiency for SMR deployment",
                      run_id, len(sites))
    for site in sites:
        t0 = time.monotonic()
        try:
            result = evaluate_coal_site(site_area_ha=100.0, status="operating")
            ms = int((time.monotonic() - t0) * 1000)
            summary = f"sufficient={result.is_sufficient}, ratio={result.sufficiency_ratio:.2f}"
            md += build_site_section(site, "ok", ms, summary, pretty_json(result.to_dict()))
            stats["ok"] += 1
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += build_site_section(site, "error", ms, str(exc), traceback.format_exc())
            stats["fail"] += 1
    cache.put_snapshot("analysis_coal_site_analysis.md", md)
