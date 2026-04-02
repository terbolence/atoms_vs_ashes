# man_hours: 12.0
"""Live integration snapshot generator.

Picks the first power plant per in-scope country from the GEM Coal Plant
Tracker XLSX, runs every implemented connector endpoint and analysis module
against it, and writes one Markdown snapshot per endpoint into
``tests/integrationSnapshots/``.

Usage::

    # All countries (can take 15-30 min due to API rate limits)
    python scripts/live_integration_snapshots.py

    # Limit to N sample sites for a quick check
    python scripts/live_integration_snapshots.py --max-sites 3

    # Skip slow connectors
    python scripts/live_integration_snapshots.py --skip egdi seismic
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SNAPSHOT_DIR = PROJECT_ROOT / "tests" / "integrationSnapshots"

FALLBACK_SITES: list[dict[str, Any]] = [
    {"name": "Rovinari",            "country": "RO", "lat": 44.1456, "lon": 23.1234},
    {"name": "Bełchatów",           "country": "PL", "lat": 51.2644, "lon": 19.3278},
    {"name": "Tušimice",            "country": "CZ", "lat": 50.3928, "lon": 13.3278},
    {"name": "Nováky",              "country": "SK", "lat": 48.7178, "lon": 18.5250},
    {"name": "Mátra",               "country": "HU", "lat": 47.8333, "lon": 20.0167},
    {"name": "Mellach",             "country": "AT", "lat": 46.9433, "lon": 15.4889},
    {"name": "Šoštanj",             "country": "SI", "lat": 46.3856, "lon": 15.0489},
    {"name": "Plomin",              "country": "HR", "lat": 45.1364, "lon": 14.1647},
    {"name": "Tuzla",               "country": "BA", "lat": 44.5333, "lon": 18.6833},
    {"name": "Nikola Tesla A",      "country": "RS", "lat": 44.6167, "lon": 20.2500},
    {"name": "Pljevlja",            "country": "ME", "lat": 43.3572, "lon": 19.3539},
    {"name": "Kosovo A",            "country": "XK", "lat": 42.6317, "lon": 21.0694},
    {"name": "Vlorë TEC",           "country": "AL", "lat": 40.4525, "lon": 19.4833},
    {"name": "Bitola REK",          "country": "MK", "lat": 41.0253, "lon": 21.3367},
    {"name": "Maritsa East 2",      "country": "BG", "lat": 42.1500, "lon": 25.9667},
    {"name": "Moldavskaya GRES",    "country": "MD", "lat": 46.6806, "lon": 29.9444},
    {"name": "Burshtyn TES",        "country": "UA", "lat": 49.2525, "lon": 24.6453},
    {"name": "Lukoml GRES",         "country": "BY", "lat": 54.4500, "lon": 29.1833},
    {"name": "Narva (Eesti)",       "country": "EE", "lat": 59.2750, "lon": 27.7833},
    {"name": "Riga TEC-2",         "country": "LV", "lat": 56.8478, "lon": 24.2039},
    {"name": "Elektrėnai",          "country": "LT", "lat": 54.7856, "lon": 24.6619},
    {"name": "Hrazdan TPP",         "country": "AM", "lat": 40.2683, "lon": 44.5575},
    {"name": "Afşin-Elbistan B",    "country": "TR", "lat": 38.2569, "lon": 36.6858},
]


@dataclass
class SampleSite:
    name: str
    country: str
    lat: float
    lon: float


def _load_from_xlsx(settings: Any) -> list[SampleSite]:
    """Try to load first plant per country from GEM XLSX."""
    try:
        import pandas as pd
    except ImportError:
        return []

    from atoms_vs_ashes.ingest.sites import COUNTRY_NAME_TO_CODE

    tracker_path = PROJECT_ROOT / settings.source_files.get(
        "coal_tracker",
        "sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx",
    )
    if not tracker_path.exists():
        return []

    sheet = settings.source_files.get("coal_tracker_sheet", "Units")
    df = pd.read_excel(tracker_path, sheet_name=sheet, dtype=str)
    df = df[df["Country/Area"].isin(COUNTRY_NAME_TO_CODE)]
    df = df.dropna(subset=["Latitude", "Longitude"])

    seen: set[str] = set()
    sites: list[SampleSite] = []
    for _, row in df.iterrows():
        cc = COUNTRY_NAME_TO_CODE.get(row["Country/Area"], "")
        if cc in seen:
            continue
        seen.add(cc)
        try:
            lat = float(row["Latitude"])
            lon = float(row["Longitude"])
        except (ValueError, TypeError):
            continue
        sites.append(SampleSite(
            name=row.get("Plant name", "unknown"),
            country=cc,
            lat=lat,
            lon=lon,
        ))
    return sorted(sites, key=lambda s: s.country)


def load_sample_sites(settings: Any) -> list[SampleSite]:
    sites = _load_from_xlsx(settings)
    if sites:
        print(f"Loaded {len(sites)} sites from GEM XLSX")
        return sites

    print("GEM XLSX not found, using fallback representative sites")
    return [SampleSite(**s) for s in FALLBACK_SITES]


# ── Helpers ───────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _json(obj: Any, max_items: int = 50) -> str:
    """Pretty-print a JSON-serializable object, truncating large lists."""
    def _trim(o: Any) -> Any:
        if isinstance(o, list) and len(o) > max_items:
            return o[:max_items] + [f"... ({len(o) - max_items} more items)"]
        if isinstance(o, dict):
            return {k: _trim(v) for k, v in o.items()}
        return o
    return json.dumps(_trim(obj), indent=2, default=str, ensure_ascii=False)


def _osm_elements_to_list(elements: list[Any]) -> list[dict[str, Any]]:
    """Convert OsmElement list to dicts for serialization."""
    out = []
    for el in elements[:50]:
        d: dict[str, Any] = {
            "osm_type": el.osm_type,
            "osm_id": el.osm_id,
            "lat": el.lat,
            "lon": el.lon,
        }
        if el.tags:
            d["name"] = el.tags.get("name", "")
            interesting = {
                k: v for k, v in el.tags.items()
                if k in (
                    "name", "aeroway", "iata", "icao", "type",
                    "landuse", "military", "man_made", "tower:type",
                    "power", "voltage", "substation", "operator",
                    "highway", "waterway", "place", "population",
                    "amenity",
                )
            }
            d["tags"] = interesting
        out.append(d)
    if len(elements) > 50:
        out.append({"note": f"... {len(elements) - 50} more elements truncated"})
    return out


def _header(title: str, description: str) -> str:
    return (
        f"<!-- man_hours: 0.1 -->\n"
        f"# {title}\n\n"
        f"**Generated:** {_ts()}\n"
        f"**Description:** {description}\n\n"
        f"---\n\n"
    )


def _site_section(site: SampleSite, status: str, elapsed_ms: int,
                  summary: str, detail: str) -> str:
    icon = "PASS" if status == "ok" else "FAIL" if status == "error" else "SKIP"
    return (
        f"## {site.country} - {site.name}\n\n"
        f"- **Coordinates:** {site.lat}, {site.lon}\n"
        f"- **Status:** {icon} ({elapsed_ms} ms)\n"
        f"- **Summary:** {summary}\n\n"
        f"<details>\n<summary>Full response</summary>\n\n"
        f"```json\n{detail}\n```\n\n"
        f"</details>\n\n"
        f"---\n\n"
    )


def _write(filename: str, content: str) -> None:
    path = SNAPSHOT_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"  -> {path.relative_to(PROJECT_ROOT)}")


# ── Endpoint runners ──────────────────────────────────────────────────

def run_health_checks(settings: Any, skip: set[str]) -> str:
    from atoms_vs_ashes.connectors.corine import CorineConnector
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.population import PopulationConnector

    lines = _header("Health Checks", "Connectivity test for all upstream APIs")
    lines += "| Connector | Endpoint | Status | Elapsed |\n"
    lines += "|-----------|----------|--------|---------|\n"

    checks: list[tuple[str, str, Any]] = [
        ("CORINE", "EEA ArcGIS REST", lambda: CorineConnector(settings).health_check()),
        ("OSM", "Overpass API", lambda: OverpassClient(settings).health_check()),
        ("Population", "Overpass (via OSM)", lambda: PopulationConnector(settings).health_check()),
    ]

    if "egdi" not in skip:
        from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
        checks.append((
            "EGDI Geology", "EGDI WFS",
            lambda: all(EgdiGeologyConnector(settings).health_check().values()),
        ))

    if "seismic" not in skip:
        from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector
        checks.append(("Seismic Hazard", "EFEHR REST", lambda: SeismicHazardConnector(settings).health_check()))

    for name, endpoint, fn in checks:
        t0 = time.monotonic()
        try:
            ok = fn()
            ms = int((time.monotonic() - t0) * 1000)
            status = "PASS" if ok else "FAIL"
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            status = f"ERROR: {exc}"
        lines += f"| {name} | {endpoint} | {status} | {ms} ms |\n"

    return lines


def run_corine(settings: Any, sites: list[SampleSite]) -> str:
    from atoms_vs_ashes.connectors.corine import CorineConnector
    conn = CorineConnector(settings)
    md = _header("CORINE Land Cover - classify()", "Fetch CLC features + ring classification for each site")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = conn.classify(site.lat, site.lon)
            ms = int((time.monotonic() - t0) * 1000)
            summary = f"{len(result.rings)} rings, developable={result.total_developable_ha:.1f} ha"
            if result.error:
                summary += f", error={result.error}"
            md += _site_section(site, "ok" if not result.error else "error", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
        time.sleep(1)
    conn.close()
    return md


def run_osm_endpoint(
    settings: Any, sites: list[SampleSite],
    method_name: str, title: str, description: str,
    call_fn: Any,
) -> str:
    from atoms_vs_ashes.connectors.osm import OverpassClient
    osm = OverpassClient(settings)
    md = _header(title, description)
    for site in sites:
        t0 = time.monotonic()
        try:
            raw = call_fn(osm, site)
            ms = int((time.monotonic() - t0) * 1000)
            if isinstance(raw, list):
                serialized = _osm_elements_to_list(raw)
                summary = f"{len(raw)} elements returned"
            elif isinstance(raw, dict):
                serialized = raw
                summary = ", ".join(f"{k}={v}" for k, v in raw.items() if not isinstance(v, dict))
            else:
                serialized = str(raw)
                summary = str(raw)[:200]
            md += _site_section(site, "ok", ms, summary, _json(serialized))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
        time.sleep(2)
    osm.close()
    return md


def run_population(settings: Any, sites: list[SampleSite]) -> str:
    from atoms_vs_ashes.connectors.population import PopulationConnector
    conn = PopulationConnector(settings)
    md = _header("Population - fetch()", "Ring population analysis for each site")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = conn.fetch(site.lat, site.lon)
            ms = int((time.monotonic() - t0) * 1000)
            summary = (
                f"total_pop_80km={result.total_population_80km:,}, "
                f"rings={len(result.rings)}, "
                f"large_cities={len(result.nearest_large_cities)}"
            )
            md += _site_section(site, "ok", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
        time.sleep(2)
    conn.close()
    return md


def run_egdi(settings: Any, sites: list[SampleSite]) -> str:
    from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
    conn = EgdiGeologyConnector(settings)
    md = _header("EGDI Geology - fetch_all()", "Full geological assessment (faults, lithology, mines, karst, hydrogeology, boreholes)")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = conn.fetch_all(site.lat, site.lon, country_code=site.country)
            ms = int((time.monotonic() - t0) * 1000)
            summary = (
                f"quality={result.quality}, "
                f"layers_with_data={len(result.layers_with_data)}/{len(result.layers_queried)}"
            )
            md += _site_section(site, "ok", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
    conn.close()
    return md


def run_seismic(settings: Any, sites: list[SampleSite]) -> str:
    from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector
    conn = SeismicHazardConnector(settings)
    md = _header("Seismic Hazard - fetch_all()", "PGA, hazard curve, and UHS via EFEHR/GEM fallback")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = conn.fetch_all(site.lat, site.lon)
            ms = int((time.monotonic() - t0) * 1000)
            summary = (
                f"PGA_475yr={result.pga_475yr}, "
                f"PGA_2475yr={result.pga_2475yr}, "
                f"source={result.source}, "
                f"quality={result.quality}"
            )
            md += _site_section(site, "ok" if result.quality != "insufficient" else "error", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
    conn.close()
    return md


# ── Analysis module runners (use pre-fetched data) ───────────────────

def run_analysis_with_corine(
    settings: Any, sites: list[SampleSite],
    corine_cache: dict[str, tuple[list[Any], Any]],
) -> dict[str, str]:
    """Run CORINE-dependent analysis modules, return filename->content map."""
    from atoms_vs_ashes.analysis.wildfire_context import assess_wildfire_context
    from atoms_vs_ashes.analysis.ecological_sensitivity import assess_ecological_sensitivity
    from atoms_vs_ashes.analysis.site_topography import assess_site_topography
    from atoms_vs_ashes.analysis.laydown_area import assess_laydown_area

    modules = [
        ("analysis_wildfire_context.md",
         "Wildfire Context (NH-13)",
         "Combustibility classification from CORINE land cover",
         lambda feats, site: assess_wildfire_context(site.lat, site.lon, features=feats)),
        ("analysis_ecological_sensitivity.md",
         "Ecological Sensitivity (NS-08)",
         "Landscape fragmentation metrics from CORINE",
         lambda feats, site: assess_ecological_sensitivity(site.lat, site.lon, features=feats)),
        ("analysis_site_topography.md",
         "Site Topography (NS-04)",
         "Land cover classification within site footprint",
         lambda feats, site: assess_site_topography(site.lat, site.lon, features=feats)),
        ("analysis_laydown_area.md",
         "Laydown Area (NS-13)",
         "Suitable laydown areas from CORINE",
         lambda feats, site: assess_laydown_area(site.lat, site.lon, features=feats)),
    ]

    results: dict[str, str] = {}
    for filename, title, desc, fn in modules:
        md = _header(title, desc)
        for site in sites:
            entry = corine_cache.get(site.country)
            if entry is None:
                md += _site_section(site, "error", 0, "No CORINE data cached", "CORINE fetch failed or was skipped")
                continue
            features, _ = entry
            t0 = time.monotonic()
            try:
                result = fn(features, site)
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "ok" if not result.error else "error", ms,
                                    str(result.error) if result.error else "OK",
                                    _json(result.to_dict()))
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
        results[filename] = md
    return results


def run_analysis_with_osm(
    settings: Any, sites: list[SampleSite],
    osm_cache: dict[str, dict[str, Any]],
) -> dict[str, str]:
    """Run OSM-dependent analysis modules."""
    from atoms_vs_ashes.analysis.aviation_hazard import assess_aviation_hazard
    from atoms_vs_ashes.analysis.military_proximity import assess_military_proximity
    from atoms_vs_ashes.analysis.transmitter_proximity import assess_transmitter_proximity
    from atoms_vs_ashes.analysis.grid_proximity import assess_grid_proximity
    from atoms_vs_ashes.analysis.land_availability import assess_land_availability

    modules = [
        ("analysis_aviation_hazard.md",
         "Aviation Hazard (HI-01)", "Airport proximity from OSM",
         "airports",
         lambda elems, site: assess_aviation_hazard(site.lat, site.lon, elements=elems)),
        ("analysis_military_proximity.md",
         "Military Proximity (HI-06)", "Military installation proximity from OSM",
         "military_areas",
         lambda elems, site: assess_military_proximity(site.lat, site.lon, elements=elems)),
        ("analysis_transmitter_proximity.md",
         "Transmitter Proximity (HI-07)", "High-power transmitter proximity from OSM",
         "transmitters",
         lambda elems, site: assess_transmitter_proximity(site.lat, site.lon, elements=elems)),
        ("analysis_grid_proximity.md",
         "Grid Proximity (NS-02)", "HV power infrastructure proximity from OSM",
         "power_infrastructure",
         lambda elems, site: assess_grid_proximity(site.lat, site.lon, elements=elems)),
        ("analysis_land_availability.md",
         "Land Availability (NS-05)", "Contiguous buildable land from OSM",
         "land_use",
         lambda elems, site: assess_land_availability(site.lat, site.lon, elements=elems)),
    ]

    results: dict[str, str] = {}
    for filename, title, desc, cache_key, fn in modules:
        md = _header(title, desc)
        for site in sites:
            site_cache = osm_cache.get(site.country, {})
            elements = site_cache.get(cache_key)
            if elements is None:
                md += _site_section(site, "error", 0, f"No OSM {cache_key} data cached", "OSM fetch failed or was skipped")
                continue
            t0 = time.monotonic()
            try:
                result = fn(elements, site)
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "ok" if not result.error else "error", ms,
                                    str(result.error) if result.error else "OK",
                                    _json(result.to_dict()))
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
        results[filename] = md
    return results


def run_analysis_population(
    settings: Any, sites: list[SampleSite],
    pop_cache: dict[str, Any],
) -> str:
    from atoms_vs_ashes.analysis.population_projection import project_population

    md = _header("Population Projection (RI-06)", "60-year population projection using UN WPP growth rates")
    for site in sites:
        pop_result = pop_cache.get(site.country)
        if pop_result is None:
            md += _site_section(site, "error", 0, "No population data cached", "Population fetch failed")
            continue
        t0 = time.monotonic()
        try:
            result = project_population(pop_result, site.country)
            ms = int((time.monotonic() - t0) * 1000)
            total_current = sum(r.get("current_population", 0) for r in result.ring_projections)
            total_projected = sum(r.get("projected_population", 0) for r in result.ring_projections)
            summary = (
                f"current_total={total_current:,}, "
                f"projected_total={total_projected:,}, "
                f"growth_rate={result.growth_rate}, "
                f"year={result.projection_year}"
            )
            md += _site_section(site, "ok", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
    return md


def run_coal_site_analysis(settings: Any, sites: list[SampleSite]) -> str:
    from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

    md = _header("Coal Site Analysis (NS-05)", "Coal site area sufficiency for SMR deployment")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = evaluate_coal_site(site_area_ha=100.0, status="operating")
            ms = int((time.monotonic() - t0) * 1000)
            summary = f"sufficient={result.is_sufficient}, ratio={result.sufficiency_ratio:.2f}"
            md += _site_section(site, "ok", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
    return md


# ── Main orchestrator ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate live integration snapshots")
    parser.add_argument("--max-sites", type=int, default=0,
                        help="Limit number of sample sites (0 = all)")
    parser.add_argument("--skip", nargs="*", default=[],
                        choices=["corine", "osm", "population", "egdi", "seismic", "analysis"],
                        help="Skip specific connector groups")
    args = parser.parse_args()

    skip = set(args.skip)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    from atoms_vs_ashes.config import Settings
    settings = Settings(PROJECT_ROOT / "config" / "default.yml")
    sites = load_sample_sites(settings)
    if args.max_sites > 0:
        sites = sites[:args.max_sites]

    total_start = time.monotonic()
    print(f"\n{'='*60}")
    print(f"Live Integration Snapshots")
    print(f"Sites: {len(sites)} | Skip: {skip or 'none'}")
    print(f"{'='*60}\n")

    # Phase 1: Health checks
    print("[1/7] Running health checks...")
    health_md = run_health_checks(settings, skip)
    _write("health_checks.md", health_md)

    # Phase 2: CORINE
    corine_cache: dict[str, tuple[list[Any], Any]] = {}
    if "corine" not in skip:
        print(f"\n[2/7] CORINE classify — {len(sites)} sites...")
        from atoms_vs_ashes.connectors.corine import CorineConnector
        conn = CorineConnector(settings)
        corine_md = _header("CORINE Land Cover - classify()", "Fetch CLC features + ring classification")
        for i, site in enumerate(sites, 1):
            print(f"  [{i}/{len(sites)}] {site.country} {site.name}...", end=" ", flush=True)
            t0 = time.monotonic()
            try:
                features = conn.fetch(site.lat, site.lon, radius_m=5000)
                result = conn.classify(site.lat, site.lon) if features else None
                ms = int((time.monotonic() - t0) * 1000)
                corine_cache[site.country] = (features, result)
                summary = f"{len(features)} features"
                if result:
                    summary += f", {len(result.rings)} rings, dev={result.total_developable_ha:.1f}ha"
                    if result.error:
                        summary += f", error={result.error}"
                corine_md += _site_section(
                    site, "ok" if features else "error", ms, summary,
                    _json(result.to_dict() if result else {"features_count": 0}),
                )
                print(f"OK ({ms}ms, {len(features)} features)")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                corine_md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
                print(f"FAIL ({ms}ms: {exc})")
            time.sleep(2)
        conn.close()
        _write("corine_classify.md", corine_md)
    else:
        print("\n[2/7] CORINE — skipped")

    # Phase 3: OSM endpoints
    osm_cache: dict[str, dict[str, Any]] = {}
    osm_endpoints = [
        ("fetch_populated_places", "OSM Populated Places", "Populated places with population tags",
         lambda osm, s: osm.fetch_populated_places(s.lat, s.lon, 80_000)),
        ("fetch_amenities", "OSM Amenities", "Hospitals, prisons, care homes within 30 km",
         lambda osm, s: osm.fetch_amenities(s.lat, s.lon, 30_000, ["hospital", "prison", "nursing_home"])),
        ("fetch_road_density", "OSM Road Density", "Road network density within 25 km",
         lambda osm, s: osm.fetch_road_density(s.lat, s.lon, 25_000)),
        ("fetch_waterways", "OSM Waterways", "Major rivers and canals within 25 km",
         lambda osm, s: osm.fetch_waterways(s.lat, s.lon, 25_000)),
        ("fetch_airports", "OSM Airports (HI-01)", "Airports and heliports within 80 km",
         lambda osm, s: osm.fetch_airports(s.lat, s.lon, 80)),
        ("fetch_military_areas", "OSM Military (HI-06)", "Military installations within 25 km",
         lambda osm, s: osm.fetch_military_areas(s.lat, s.lon, 25)),
        ("fetch_transmitters", "OSM Transmitters (HI-07)", "Communication towers and transmitters within 25 km",
         lambda osm, s: osm.fetch_transmitters(s.lat, s.lon, 25)),
        ("fetch_power_infrastructure", "OSM Power Infra (NS-02)", "HV lines and substations within 50 km",
         lambda osm, s: osm.fetch_power_infrastructure(s.lat, s.lon, 50)),
        ("fetch_land_use", "OSM Land Use (NS-05)", "Land use polygons within 5 km",
         lambda osm, s: osm.fetch_land_use(s.lat, s.lon, 5)),
    ]

    if "osm" not in skip:
        from atoms_vs_ashes.connectors.osm import OverpassClient
        osm_client = OverpassClient(settings)

        for ep_idx, (method, title, desc, call_fn) in enumerate(osm_endpoints, 1):
            print(f"\n[3/7] OSM {method} ({ep_idx}/{len(osm_endpoints)}) — {len(sites)} sites...")
            ep_md = _header(f"{title} - {method}()", desc)
            cache_key = method.replace("fetch_", "")

            for i, site in enumerate(sites, 1):
                print(f"  [{i}/{len(sites)}] {site.country} {site.name}...", end=" ", flush=True)
                t0 = time.monotonic()
                try:
                    raw = call_fn(osm_client, site)
                    ms = int((time.monotonic() - t0) * 1000)

                    if site.country not in osm_cache:
                        osm_cache[site.country] = {}
                    osm_cache[site.country][cache_key] = raw

                    if isinstance(raw, list):
                        serialized = _osm_elements_to_list(raw)
                        summary = f"{len(raw)} elements"
                    elif isinstance(raw, dict):
                        serialized = raw
                        summary = ", ".join(f"{k}={v}" for k, v in raw.items() if not isinstance(v, (dict, list)))
                    else:
                        serialized = str(raw)
                        summary = str(raw)[:200]

                    ep_md += _site_section(site, "ok", ms, summary, _json(serialized))
                    print(f"OK ({ms}ms, {summary})")
                except Exception as exc:
                    ms = int((time.monotonic() - t0) * 1000)
                    ep_md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
                    print(f"FAIL ({ms}ms: {exc})")
                time.sleep(5)

            _write(f"osm_{cache_key}.md", ep_md)
            time.sleep(3)
        osm_client.close()
    else:
        print("\n[3/7] OSM — skipped")

    # Phase 4: Population
    pop_cache: dict[str, Any] = {}
    if "population" not in skip:
        print(f"\n[4/7] Population fetch — {len(sites)} sites...")
        from atoms_vs_ashes.connectors.population import PopulationConnector
        pop_conn = PopulationConnector(settings)
        pop_md = _header("Population - fetch()", "Ring population analysis")
        for i, site in enumerate(sites, 1):
            print(f"  [{i}/{len(sites)}] {site.country} {site.name}...", end=" ", flush=True)
            t0 = time.monotonic()
            try:
                result = pop_conn.fetch(site.lat, site.lon)
                ms = int((time.monotonic() - t0) * 1000)
                pop_cache[site.country] = result
                summary = f"total_80km={result.total_population_80km:,}, cities={len(result.nearest_large_cities)}"
                pop_md += _site_section(site, "ok", ms, summary, _json(result.to_dict()))
                print(f"OK ({ms}ms, pop={result.total_population_80km:,})")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                pop_md += _site_section(site, "error", ms, str(exc), traceback.format_exc())
                print(f"FAIL ({ms}ms: {exc})")
            time.sleep(5)
        pop_conn.close()
        _write("population_fetch.md", pop_md)
    else:
        print("\n[4/7] Population — skipped")

    # Phase 5: EGDI Geology
    if "egdi" not in skip:
        print(f"\n[5/7] EGDI Geology fetch_all — {len(sites)} sites...")
        egdi_md = run_egdi(settings, sites)
        _write("egdi_geology.md", egdi_md)
    else:
        print("\n[5/7] EGDI — skipped")

    # Phase 6: Seismic Hazard
    if "seismic" not in skip:
        print(f"\n[6/7] Seismic Hazard fetch_all — {len(sites)} sites...")
        seismic_md = run_seismic(settings, sites)
        _write("seismic_hazard.md", seismic_md)
    else:
        print("\n[6/7] Seismic — skipped")

    # Phase 7: Analysis modules (use cached data)
    if "analysis" not in skip:
        print(f"\n[7/7] Analysis modules (pure functions on cached data)...")

        if corine_cache:
            corine_analyses = run_analysis_with_corine(settings, sites, corine_cache)
            for fname, content in corine_analyses.items():
                _write(fname, content)

        if osm_cache:
            osm_analyses = run_analysis_with_osm(settings, sites, osm_cache)
            for fname, content in osm_analyses.items():
                _write(fname, content)

        if pop_cache:
            pop_proj_md = run_analysis_population(settings, sites, pop_cache)
            _write("analysis_population_projection.md", pop_proj_md)

        coal_md = run_coal_site_analysis(settings, sites)
        _write("analysis_coal_site_analysis.md", coal_md)
    else:
        print("\n[7/7] Analysis — skipped")

    elapsed = time.monotonic() - total_start
    mins = elapsed / 60
    print(f"\n{'='*60}")
    print(f"Done. {mins:.1f} min total.")
    print(f"Snapshots: {SNAPSHOT_DIR.relative_to(PROJECT_ROOT)}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
