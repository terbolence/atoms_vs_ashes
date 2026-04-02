"""Overpass API worker — fetches all OSM endpoints + population per site.

Shares the Overpass rate limiter since both OSM and Population hit the
same ``overpass-api.de`` backend (max 2 concurrent slots).
"""

from __future__ import annotations

import time
import traceback
from typing import Any

from ava_client import display
from ava_client.cache import SiteDataCache
from ava_client.config import OSM_INTER_ENDPOINT_DELAY_S
from ava_client.rate_limiter import ApiRateLimiter
from ava_client.resolver import ResolvedSite
from ava_client.snapshot import build_header, build_site_section, pretty_json


def _osm_elements_to_list(elements: list[Any], limit: int = 50) -> list[dict[str, Any]]:
    """Serialise OsmElement instances to plain dicts for JSON snapshots."""
    out: list[dict[str, Any]] = []
    for el in elements[:limit]:
        d: dict[str, Any] = {
            "osm_type": el.osm_type, "osm_id": el.osm_id,
            "lat": el.lat, "lon": el.lon,
        }
        if el.tags:
            d["name"] = el.tags.get("name", "")
            d["tags"] = {
                k: v for k, v in el.tags.items()
                if k in (
                    "name", "aeroway", "iata", "icao", "type", "landuse",
                    "military", "man_made", "tower:type", "power", "voltage",
                    "substation", "operator", "highway", "waterway", "place",
                    "population", "amenity",
                )
            }
        out.append(d)
    if len(elements) > limit:
        out.append({"note": f"... {len(elements) - limit} more elements truncated"})
    return out


def _build_osm_endpoint_list() -> list[tuple[str, str, str, Any]]:
    """Return ``(cache_key, title, description, call_fn)`` per OSM endpoint."""
    return [
        ("populated_places", "OSM Populated Places", "Populated places with population tags",
         lambda osm, s: osm.fetch_populated_places(s.lat, s.lon, 80_000)),
        ("amenities", "OSM Amenities", "Hospitals, prisons, care homes within 30 km",
         lambda osm, s: osm.fetch_amenities(s.lat, s.lon, 30_000, ["hospital", "prison", "nursing_home"])),
        ("road_density", "OSM Road Density", "Road network density within 25 km",
         lambda osm, s: osm.fetch_road_density(s.lat, s.lon, 25_000)),
        ("waterways", "OSM Waterways", "Major rivers and canals within 25 km",
         lambda osm, s: osm.fetch_waterways(s.lat, s.lon, 25_000)),
        ("airports", "OSM Airports (HI-01)", "Airports and heliports within 80 km",
         lambda osm, s: osm.fetch_airports(s.lat, s.lon, 80)),
        ("military_areas", "OSM Military (HI-06)", "Military installations within 25 km",
         lambda osm, s: osm.fetch_military_areas(s.lat, s.lon, 25)),
        ("transmitters", "OSM Transmitters (HI-07)", "Communication towers within 25 km",
         lambda osm, s: osm.fetch_transmitters(s.lat, s.lon, 25)),
        ("power_infrastructure", "OSM Power Infra (NS-02)", "HV lines and substations within 50 km",
         lambda osm, s: osm.fetch_power_infrastructure(s.lat, s.lon, 50)),
        ("land_use", "OSM Land Use (NS-05)", "Land use polygons within 5 km",
         lambda osm, s: osm.fetch_land_use(s.lat, s.lon, 5)),
    ]


# ---------------------------------------------------------------------------
# Main worker
# ---------------------------------------------------------------------------

def run_overpass_worker(
    sites: list[ResolvedSite],
    settings: Any,
    cache: SiteDataCache,
    limiter: ApiRateLimiter,
    run_id: str,
) -> dict[str, int]:
    """Fetch all OSM endpoints + population for every site."""
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.population import PopulationConnector

    stats = {"ok": 0, "fail": 0}
    osm_endpoints = _build_osm_endpoint_list()
    osm_client = OverpassClient(settings)
    pop_client = PopulationConnector(settings)

    try:
        for site in sites:
            for ep_idx, (cache_key, title, desc, call_fn) in enumerate(osm_endpoints):
                limiter.wait()
                t0 = time.monotonic()
                try:
                    raw = call_fn(osm_client, site)
                    ms = int((time.monotonic() - t0) * 1000)
                    cache.put(site, f"osm_{cache_key}", raw)
                    _append_osm_snapshot(cache, cache_key, title, desc, site, raw, ms, run_id)
                    stats["ok"] += 1
                    display.print_status(
                        f"[dim]overpass[/dim] {site.country} {site.name} osm_{cache_key} "
                        f"[green]OK[/green] ({ms}ms)")
                except Exception as exc:
                    ms = int((time.monotonic() - t0) * 1000)
                    _append_osm_snapshot_error(cache, cache_key, title, desc, site, exc, ms, run_id)
                    stats["fail"] += 1
                    display.print_status(
                        f"[dim]overpass[/dim] {site.country} {site.name} osm_{cache_key} "
                        f"[red]FAIL[/red] ({ms}ms: {exc})")
                if ep_idx < len(osm_endpoints) - 1:
                    time.sleep(OSM_INTER_ENDPOINT_DELAY_S)

            # Population (also via Overpass)
            limiter.wait()
            t0 = time.monotonic()
            try:
                pop_result = pop_client.fetch(site.lat, site.lon)
                ms = int((time.monotonic() - t0) * 1000)
                cache.put(site, "population", pop_result)
                _append_pop_snapshot(cache, site, pop_result, ms, run_id)
                stats["ok"] += 1
                display.print_status(
                    f"[dim]overpass[/dim] {site.country} {site.name} population "
                    f"[green]OK[/green] ({ms}ms, pop={pop_result.total_population_80km:,})")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                _append_pop_snapshot_error(cache, site, exc, ms, run_id)
                stats["fail"] += 1
                display.print_status(
                    f"[dim]overpass[/dim] {site.country} {site.name} population "
                    f"[red]FAIL[/red] ({ms}ms: {exc})")
    finally:
        osm_client.close()
        pop_client.close()

    return stats


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def _append_osm_snapshot(
    cache: SiteDataCache, cache_key: str, title: str, desc: str,
    site: ResolvedSite, raw: Any, ms: int, run_id: str,
) -> None:
    filename = f"osm_{cache_key}.md"
    existing = cache.get_snapshot(filename) or build_header(
        f"{title} - fetch_{cache_key}()", desc, run_id, site_count=0)
    if isinstance(raw, list):
        serialized = _osm_elements_to_list(raw)
        summary = f"{len(raw)} elements"
    elif isinstance(raw, dict):
        serialized = raw
        summary = ", ".join(f"{k}={v}" for k, v in raw.items() if not isinstance(v, (dict, list)))
    else:
        serialized = str(raw)
        summary = str(raw)[:200]
    existing += build_site_section(site, "ok", ms, summary, pretty_json(serialized))
    cache.put_snapshot(filename, existing)


def _append_osm_snapshot_error(
    cache: SiteDataCache, cache_key: str, title: str, desc: str,
    site: ResolvedSite, exc: Exception, ms: int, run_id: str,
) -> None:
    filename = f"osm_{cache_key}.md"
    existing = cache.get_snapshot(filename) or build_header(
        f"{title} - fetch_{cache_key}()", desc, run_id, site_count=0)
    existing += build_site_section(site, "error", ms, str(exc), traceback.format_exc())
    cache.put_snapshot(filename, existing)


def _append_pop_snapshot(
    cache: SiteDataCache, site: ResolvedSite, result: Any, ms: int, run_id: str,
) -> None:
    filename = "population_fetch.md"
    existing = cache.get_snapshot(filename) or build_header(
        "Population - fetch()", "Ring population analysis", run_id, site_count=0)
    summary = (f"total_80km={result.total_population_80km:,}, "
               f"cities={len(result.nearest_large_cities)}")
    existing += build_site_section(site, "ok", ms, summary, pretty_json(result.to_dict()))
    cache.put_snapshot(filename, existing)


def _append_pop_snapshot_error(
    cache: SiteDataCache, site: ResolvedSite, exc: Exception, ms: int, run_id: str,
) -> None:
    filename = "population_fetch.md"
    existing = cache.get_snapshot(filename) or build_header(
        "Population - fetch()", "Ring population analysis", run_id, site_count=0)
    existing += build_site_section(site, "error", ms, str(exc), traceback.format_exc())
    cache.put_snapshot(filename, existing)
