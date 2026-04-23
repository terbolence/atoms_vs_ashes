# man_hours: 12.0
"""Queue-based live integration snapshot generator.

Architecture
------------
- One worker thread per API backend (CORINE, Overpass, EGDI, Seismic).
- All workers run **in parallel**; each drains its own FIFO queue serially.
- Rate limits are per-API: CORINE 1.5 s, Overpass 12 s, EGDI/Seismic 2 s.
- On 429 / 504 / timeout the task is re-queued with exponential back-off
  (30 s × 2^attempt for Overpass) up to 3 retries.
- Fetch state is persisted to ``.fetch_state.json`` so the next run can
  skip already-retrieved data (use ``--clean`` to start fresh).
- Analysis modules run after all raw data is fetched.

Usage::

    python scripts/live_integration_snapshots.py
    python scripts/live_integration_snapshots.py --max-sites 3
    python scripts/live_integration_snapshots.py --skip egdi seismic
    python scripts/live_integration_snapshots.py --clean   # ignore prior state
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SNAPSHOT_DIR = PROJECT_ROOT / "tests" / "integrationSnapshots"
STATE_FILE = SNAPSHOT_DIR / ".fetch_state.json"

# ── Status constants ─────────────────────────────────────────────────
STATUS_DATA_OK = "data_ok"
STATUS_EMPTY = "empty"
STATUS_RATE_LIMITED = "rate_limited"
STATUS_FAILED = "failed"
STATUS_PENDING = "pending"

# ── Rate-limit configs per API ───────────────────────────────────────
API_CONFIGS: dict[str, dict[str, float]] = {
    "corine":  {"interval_s": 1.5,  "backoff_base_s": 5,  "max_retries": 3},
    "overpass": {"interval_s": 12.0, "backoff_base_s": 30, "max_retries": 3},
    "egdi":    {"interval_s": 2.0,  "backoff_base_s": 10, "max_retries": 3},
    "seismic": {"interval_s": 2.0,  "backoff_base_s": 10, "max_retries": 3},
}

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
    {"name": "Riga TEC-2",          "country": "LV", "lat": 56.8478, "lon": 24.2039},
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


@dataclass
class FetchTask:
    key: str
    api: str
    endpoint: str
    site: SampleSite
    execute: Callable[[], Any]
    attempt: int = 0
    retry_after: float = 0.0


@dataclass
class FetchResult:
    status: str = STATUS_PENDING
    data: Any = None
    error: str = ""
    elapsed_ms: int = 0
    attempts: int = 0
    element_count: int = 0


# ── Site loading ─────────────────────────────────────────────────────

def _load_from_xlsx(settings: Any) -> list[SampleSite]:
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
            lat, lon = float(row["Latitude"]), float(row["Longitude"])
        except (ValueError, TypeError):
            continue
        sites.append(SampleSite(name=row.get("Plant name", "unknown"), country=cc, lat=lat, lon=lon))
    return sorted(sites, key=lambda s: s.country)


def load_sample_sites(settings: Any) -> list[SampleSite]:
    sites = _load_from_xlsx(settings)
    if sites:
        return sites
    return [SampleSite(**s) for s in FALLBACK_SITES]


# ── State persistence ────────────────────────────────────────────────

def _load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"results": {}}


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


# ── Markdown helpers ─────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _json(obj: Any, max_items: int = 50) -> str:
    def _trim(o: Any) -> Any:
        if isinstance(o, list) and len(o) > max_items:
            return o[:max_items] + [f"… ({len(o) - max_items} more items)"]
        if isinstance(o, dict):
            return {k: _trim(v) for k, v in o.items()}
        return o
    return json.dumps(_trim(obj), indent=2, default=str, ensure_ascii=False)


def _osm_elements_to_list(elements: list[Any]) -> list[dict[str, Any]]:
    out = []
    for el in elements[:50]:
        d: dict[str, Any] = {"osm_type": el.osm_type, "osm_id": el.osm_id, "lat": el.lat, "lon": el.lon}
        if el.tags:
            d["name"] = el.tags.get("name", "")
            d["tags"] = {
                k: v for k, v in el.tags.items()
                if k in ("name", "aeroway", "iata", "icao", "type", "landuse", "military",
                         "man_made", "tower:type", "power", "voltage", "substation",
                         "operator", "highway", "waterway", "place", "population", "amenity")
            }
        out.append(d)
    if len(elements) > 50:
        out.append({"note": f"… {len(elements) - 50} more elements truncated"})
    return out


def _header(title: str, description: str) -> str:
    return (
        f"<!-- man_hours: 0.1 -->\n# {title}\n\n"
        f"**Generated:** {_ts()}\n**Description:** {description}\n\n---\n\n"
    )


def _site_section(site: SampleSite, status: str, elapsed_ms: int,
                  summary: str, detail: str) -> str:
    icon = {"data_ok": "PASS", "empty": "WARN_EMPTY", "rate_limited": "RATE_LIMITED",
            "failed": "FAIL", "ok": "PASS", "error": "FAIL"}.get(status, status.upper())
    return (
        f"## {site.country} – {site.name}\n\n"
        f"- **Coordinates:** {site.lat}, {site.lon}\n"
        f"- **Status:** {icon} ({elapsed_ms} ms)\n"
        f"- **Summary:** {summary}\n\n"
        f"<details>\n<summary>Full response</summary>\n\n"
        f"```json\n{detail}\n```\n\n</details>\n\n---\n\n"
    )


def _write(filename: str, content: str) -> None:
    path = SNAPSHOT_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"    → {path.relative_to(PROJECT_ROOT)}")


# ── API Worker ───────────────────────────────────────────────────────

class APIWorker(threading.Thread):
    """Drains a task queue serially, respecting rate limits and retrying."""

    def __init__(self, name: str, results: dict[str, FetchResult],
                 state: dict[str, Any], lock: threading.Lock):
        super().__init__(daemon=True, name=f"worker-{name}")
        self.api_name = name
        self.cfg = API_CONFIGS[name]
        self.tasks: list[FetchTask] = []
        self.results = results
        self.state = state
        self.lock = lock
        self.stats = {"ok": 0, "empty": 0, "retried": 0, "failed": 0, "skipped": 0}

    def enqueue(self, task: FetchTask) -> None:
        self.tasks.append(task)

    def run(self) -> None:
        interval = self.cfg["interval_s"]
        backoff_base = self.cfg["backoff_base_s"]
        max_retries = int(self.cfg["max_retries"])

        pending = list(self.tasks)
        retry_bucket: list[FetchTask] = []

        while pending or retry_bucket:
            now = time.monotonic()
            ready = [t for t in retry_bucket if t.retry_after <= now]
            for t in ready:
                retry_bucket.remove(t)
                pending.insert(0, t)

            if not pending:
                if retry_bucket:
                    wait = min(t.retry_after for t in retry_bucket) - now
                    time.sleep(max(0.5, wait))
                continue

            task = pending.pop(0)
            self._run_task(task, max_retries, backoff_base, retry_bucket)
            if pending or retry_bucket:
                time.sleep(interval)

        self._log(f"done: {self.stats}")

    def _run_task(self, task: FetchTask, max_retries: int,
                  backoff_base: float, retry_bucket: list[FetchTask]) -> None:
        attempt_label = f"[attempt {task.attempt + 1}] " if task.attempt > 0 else ""
        self._log(f"{attempt_label}{task.endpoint} / {task.site.country} {task.site.name}")

        t0 = time.monotonic()
        try:
            data = task.execute()
            elapsed = int((time.monotonic() - t0) * 1000)
        except Exception as exc:
            elapsed = int((time.monotonic() - t0) * 1000)
            self._handle_failure(task, str(exc), elapsed, max_retries, backoff_base, retry_bucket)
            return

        rate_limited = self._check_rate_limited(task)
        count = self._count_data(data, task)

        if rate_limited:
            self._handle_failure(task, f"rate_limited (HTTP {self._get_status(task)})",
                                 elapsed, max_retries, backoff_base, retry_bucket)
            return

        result = FetchResult(
            status=STATUS_DATA_OK if count > 0 else STATUS_EMPTY,
            data=data,
            elapsed_ms=elapsed,
            attempts=task.attempt + 1,
            element_count=count,
        )
        self._store(task, result)
        label = f"✓ {count} items" if count > 0 else "⚠ empty (0 items)"
        self._log(f"  {label} ({elapsed}ms)")

    def _handle_failure(self, task: FetchTask, error: str, elapsed: int,
                        max_retries: int, backoff_base: float,
                        retry_bucket: list[FetchTask]) -> None:
        task.attempt += 1
        if task.attempt < max_retries:
            backoff = backoff_base * (2 ** (task.attempt - 1))
            task.retry_after = time.monotonic() + backoff
            retry_bucket.append(task)
            self.stats["retried"] += 1
            self._log(f"  ✗ {error} → retry {task.attempt}/{max_retries} in {backoff:.0f}s")
        else:
            result = FetchResult(
                status=STATUS_FAILED,
                error=error,
                elapsed_ms=elapsed,
                attempts=task.attempt,
            )
            self._store(task, result)
            self.stats["failed"] += 1
            self._log(f"  ✗ {error} → FAILED after {task.attempt} attempts")

    def _store(self, task: FetchTask, result: FetchResult) -> None:
        with self.lock:
            self.results[task.key] = result
            self.state["results"][task.key] = {
                "status": result.status,
                "element_count": result.element_count,
                "elapsed_ms": result.elapsed_ms,
                "attempts": result.attempts,
                "error": result.error or None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _save_state(self.state)
        if result.status in (STATUS_DATA_OK, STATUS_EMPTY):
            self.stats["ok" if result.status == STATUS_DATA_OK else "empty"] += 1

    def _check_rate_limited(self, task: FetchTask) -> bool:
        if task.api == "overpass":
            try:
                osm_client = task.execute.__self__  # type: ignore[attr-defined]
                if hasattr(osm_client, "_last_http_status"):
                    return osm_client._last_http_status in (429, 504, 408)
                if hasattr(osm_client, "_overpass") and hasattr(osm_client._overpass, "_last_http_status"):
                    return osm_client._overpass._last_http_status in (429, 504, 408)
            except AttributeError:
                pass
        return False

    def _get_status(self, task: FetchTask) -> int:
        try:
            osm_client = task.execute.__self__  # type: ignore[attr-defined]
            if hasattr(osm_client, "_last_http_status"):
                return osm_client._last_http_status
            if hasattr(osm_client, "_overpass"):
                return osm_client._overpass._last_http_status
        except AttributeError:
            pass
        return 0

    @staticmethod
    def _count_data(data: Any, task: FetchTask) -> int:
        if data is None:
            return 0
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            if "features" in data:
                return len(data["features"])
            return 1 if data else 0
        if hasattr(data, "total_population_80km"):
            return data.total_population_80km or 0
        if hasattr(data, "rings"):
            return len(data.rings) if data.rings else 0
        if hasattr(data, "to_dict"):
            return 1
        return 1 if data else 0

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] [{self.api_name:>8}] {msg}", flush=True)


# ── Task builders ────────────────────────────────────────────────────

def _build_corine_tasks(
    sites: list[SampleSite], settings: Any, state: dict[str, Any],
) -> tuple[list[FetchTask], Any]:
    from atoms_vs_ashes.connectors.corine import CorineConnector
    conn = CorineConnector(settings)
    tasks = []
    for site in sites:
        key = f"corine:classify:{site.country}"
        if state.get("results", {}).get(key, {}).get("status") == STATUS_DATA_OK:
            continue
        tasks.append(FetchTask(
            key=key, api="corine", endpoint="classify", site=site,
            execute=lambda s=site: conn.fetch(s.lat, s.lon, radius_m=5000),
        ))
    return tasks, conn


def _build_overpass_tasks(
    sites: list[SampleSite], settings: Any, state: dict[str, Any],
) -> tuple[list[FetchTask], Any, Any]:
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.population import PopulationConnector

    osm = OverpassClient(settings)
    pop = PopulationConnector(settings)

    osm_endpoints: list[tuple[str, Callable]] = [
        ("populated_places", lambda s: osm.fetch_populated_places(s.lat, s.lon, 80_000)),
        ("amenities", lambda s: osm.fetch_amenities(s.lat, s.lon, 30_000, ["hospital", "prison", "nursing_home"])),
        ("road_density", lambda s: osm.fetch_road_density(s.lat, s.lon, 25_000)),
        ("waterways", lambda s: osm.fetch_waterways(s.lat, s.lon, 25_000)),
        ("airports", lambda s: osm.fetch_airports(s.lat, s.lon, 80)),
        ("military_areas", lambda s: osm.fetch_military_areas(s.lat, s.lon, 25)),
        ("transmitters", lambda s: osm.fetch_transmitters(s.lat, s.lon, 25)),
        ("power_infrastructure", lambda s: osm.fetch_power_infrastructure(s.lat, s.lon, 50)),
        ("land_use", lambda s: osm.fetch_land_use(s.lat, s.lon, 5)),
    ]

    tasks: list[FetchTask] = []
    for ep_name, call_fn in osm_endpoints:
        for site in sites:
            key = f"overpass:{ep_name}:{site.country}"
            prev = state.get("results", {}).get(key, {})
            if prev.get("status") == STATUS_DATA_OK:
                continue
            def _make_exec(fn: Callable, s: SampleSite) -> Callable:
                def _exec() -> Any:
                    result = fn(s)
                    _exec.__self__ = osm  # type: ignore[attr-defined]
                    return result
                _exec.__self__ = osm  # type: ignore[attr-defined]
                return _exec
            tasks.append(FetchTask(
                key=key, api="overpass", endpoint=ep_name, site=site,
                execute=_make_exec(call_fn, site),
            ))

    for site in sites:
        key = f"overpass:population:{site.country}"
        prev = state.get("results", {}).get(key, {})
        if prev.get("status") == STATUS_DATA_OK:
            continue
        def _make_pop_exec(s: SampleSite) -> Callable:
            def _exec() -> Any:
                result = pop.fetch(s.lat, s.lon)
                _exec.__self__ = pop  # type: ignore[attr-defined]
                return result
            _exec.__self__ = pop  # type: ignore[attr-defined]
            return _exec
        tasks.append(FetchTask(
            key=key, api="overpass", endpoint="population", site=site,
            execute=_make_pop_exec(site),
        ))

    return tasks, osm, pop


# ── Snapshot generation from results ─────────────────────────────────

def _generate_snapshots(
    sites: list[SampleSite], results: dict[str, FetchResult], settings: Any,
) -> None:
    print("\n  Generating Markdown snapshots...")

    # Health checks
    _write_health_checks(settings)

    # CORINE
    _write_corine_snapshots(sites, results)

    # OSM endpoints
    osm_endpoints = [
        ("populated_places", "OSM Populated Places", "Populated places with population tags"),
        ("amenities", "OSM Amenities", "Hospitals, prisons, care homes within 30 km"),
        ("road_density", "OSM Road Density", "Road network density within 25 km"),
        ("waterways", "OSM Waterways", "Major rivers and canals within 25 km"),
        ("airports", "OSM Airports (HI-01)", "Airports and heliports within 80 km"),
        ("military_areas", "OSM Military (HI-06)", "Military installations within 25 km"),
        ("transmitters", "OSM Transmitters (HI-07)", "Communication towers/transmitters within 25 km"),
        ("power_infrastructure", "OSM Power Infra (NS-02)", "HV lines and substations within 50 km"),
        ("land_use", "OSM Land Use (NS-05)", "Land use polygons within 5 km"),
    ]
    for ep_name, title, desc in osm_endpoints:
        _write_osm_snapshot(sites, results, ep_name, title, desc)

    # Population
    _write_population_snapshot(sites, results)

    # Analysis modules
    _write_analysis_snapshots(sites, results, settings)


def _write_health_checks(settings: Any) -> None:
    from atoms_vs_ashes.connectors.corine import CorineConnector
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.population import PopulationConnector

    lines = _header("Health Checks", "Connectivity test for all upstream APIs")
    lines += "| Connector | Endpoint | Status | Elapsed |\n|-----------|----------|--------|---------|\n"
    for name, endpoint, fn in [
        ("CORINE", "EEA ArcGIS REST", lambda: CorineConnector(settings).health_check()),
        ("OSM", "Overpass API", lambda: OverpassClient(settings).health_check()),
        ("Population", "Overpass (via OSM)", lambda: PopulationConnector(settings).health_check()),
    ]:
        t0 = time.monotonic()
        try:
            ok = fn()
            ms = int((time.monotonic() - t0) * 1000)
            status = "PASS" if ok else "FAIL"
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            status = f"ERROR: {exc}"
        lines += f"| {name} | {endpoint} | {status} | {ms} ms |\n"
    _write("health_checks.md", lines)


def _write_corine_snapshots(sites: list[SampleSite], results: dict[str, FetchResult]) -> None:
    md = _header("CORINE Land Cover – fetch()", "CLC features for each site")
    for site in sites:
        r = results.get(f"corine:classify:{site.country}")
        if r is None:
            md += _site_section(site, "failed", 0, "Not attempted", "{}")
            continue
        if r.status == STATUS_DATA_OK:
            count = len(r.data) if isinstance(r.data, list) else 0
            md += _site_section(site, "data_ok", r.elapsed_ms,
                                f"{count} features", _json(r.data[:10] if isinstance(r.data, list) else r.data))
        elif r.status == STATUS_EMPTY:
            md += _site_section(site, "empty", r.elapsed_ms, "0 features (outside CORINE coverage?)",
                                _json({"features_count": 0}))
        else:
            md += _site_section(site, r.status, r.elapsed_ms, r.error,
                                _json({"error": r.error, "attempts": r.attempts}))
    _write("corine_classify.md", md)


def _write_osm_snapshot(
    sites: list[SampleSite], results: dict[str, FetchResult],
    ep_name: str, title: str, desc: str,
) -> None:
    md = _header(f"{title} – fetch_{ep_name}()", desc)
    for site in sites:
        r = results.get(f"overpass:{ep_name}:{site.country}")
        if r is None:
            md += _site_section(site, "failed", 0, "Not attempted", "{}")
            continue
        if r.status in (STATUS_DATA_OK, STATUS_EMPTY):
            if isinstance(r.data, list):
                serialized = _osm_elements_to_list(r.data)
                summary = f"{len(r.data)} elements"
            elif isinstance(r.data, dict):
                serialized = r.data
                summary = ", ".join(f"{k}={v}" for k, v in r.data.items()
                                   if not isinstance(v, (dict, list)))
            else:
                serialized = str(r.data)
                summary = str(r.data)[:200]
            status_label = "data_ok" if r.element_count > 0 else "empty"
            md += _site_section(site, status_label, r.elapsed_ms, summary, _json(serialized))
        else:
            md += _site_section(site, r.status, r.elapsed_ms, r.error,
                                _json({"error": r.error, "attempts": r.attempts}))
    _write(f"osm_{ep_name}.md", md)


def _write_population_snapshot(sites: list[SampleSite], results: dict[str, FetchResult]) -> None:
    md = _header("Population – fetch()", "Ring population analysis for each site")
    for site in sites:
        r = results.get(f"overpass:population:{site.country}")
        if r is None:
            md += _site_section(site, "failed", 0, "Not attempted", "{}")
            continue
        if r.status in (STATUS_DATA_OK, STATUS_EMPTY):
            data = r.data
            if hasattr(data, "to_dict"):
                summary = f"total_80km={data.total_population_80km:,}, cities={len(data.nearest_large_cities)}"
                md += _site_section(site, "data_ok" if data.total_population_80km > 0 else "empty",
                                    r.elapsed_ms, summary, _json(data.to_dict()))
            else:
                md += _site_section(site, "empty", r.elapsed_ms, "Unknown format", _json(str(data)))
        else:
            md += _site_section(site, r.status, r.elapsed_ms, r.error,
                                _json({"error": r.error, "attempts": r.attempts}))
    _write("population_fetch.md", md)


def _write_analysis_snapshots(
    sites: list[SampleSite], results: dict[str, FetchResult], settings: Any,
) -> None:
    from atoms_vs_ashes.analysis.wildfire_context import assess_wildfire_context
    from atoms_vs_ashes.analysis.ecological_sensitivity import assess_ecological_sensitivity
    from atoms_vs_ashes.analysis.site_topography import assess_site_topography
    from atoms_vs_ashes.analysis.laydown_area import assess_laydown_area
    from atoms_vs_ashes.analysis.aviation_hazard import assess_aviation_hazard
    from atoms_vs_ashes.analysis.military_proximity import assess_military_proximity
    from atoms_vs_ashes.analysis.transmitter_proximity import assess_transmitter_proximity
    from atoms_vs_ashes.analysis.grid_proximity import assess_grid_proximity
    from atoms_vs_ashes.analysis.land_availability import assess_land_availability
    from atoms_vs_ashes.analysis.population_projection import project_population
    from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

    corine_analyses = [
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

    for filename, title, desc, fn in corine_analyses:
        md = _header(title, desc)
        for site in sites:
            r = results.get(f"corine:classify:{site.country}")
            if r is None or r.status != STATUS_DATA_OK:
                md += _site_section(site, "failed", 0, "No CORINE data",
                                    _json({"error": "CORINE fetch failed or was skipped"}))
                continue
            t0 = time.monotonic()
            try:
                result = fn(r.data, site)
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "data_ok" if not result.error else "empty", ms,
                                    result.error if result.error else "OK", _json(result.to_dict()))
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "failed", ms, str(exc), traceback.format_exc())
        _write(filename, md)

    osm_analyses = [
        ("analysis_aviation_hazard.md", "Aviation Hazard (HI-01)", "Airport proximity from OSM",
         "airports", lambda elems, s: assess_aviation_hazard(s.lat, s.lon, elements=elems)),
        ("analysis_military_proximity.md", "Military Proximity (HI-06)",
         "Military installation proximity from OSM",
         "military_areas", lambda elems, s: assess_military_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_transmitter_proximity.md", "Transmitter Proximity (HI-07)",
         "High-power transmitter proximity from OSM",
         "transmitters", lambda elems, s: assess_transmitter_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_grid_proximity.md", "Grid Proximity (NS-02)", "HV power grid proximity from OSM",
         "power_infrastructure", lambda elems, s: assess_grid_proximity(s.lat, s.lon, elements=elems)),
        ("analysis_land_availability.md", "Land Availability (NS-05)",
         "Contiguous buildable land from OSM",
         "land_use", lambda elems, s: assess_land_availability(s.lat, s.lon, elements=elems)),
    ]

    for filename, title, desc, cache_key, fn in osm_analyses:
        md = _header(title, desc)
        for site in sites:
            r = results.get(f"overpass:{cache_key}:{site.country}")
            if r is None or r.status not in (STATUS_DATA_OK, STATUS_EMPTY):
                md += _site_section(site, "failed", 0, f"No OSM {cache_key} data",
                                    _json({"error": "OSM fetch failed or was skipped"}))
                continue
            t0 = time.monotonic()
            try:
                result = fn(r.data, site)
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "data_ok" if not result.error else "empty", ms,
                                    result.error if result.error else "OK", _json(result.to_dict()))
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += _site_section(site, "failed", ms, str(exc), traceback.format_exc())
        _write(filename, md)

    # Population projection
    md = _header("Population Projection (RI-06)", "60-year population projection using UN WPP growth rates")
    for site in sites:
        r = results.get(f"overpass:population:{site.country}")
        if r is None or r.status != STATUS_DATA_OK or not hasattr(r.data, "to_dict"):
            md += _site_section(site, "failed", 0, "No population data",
                                _json({"error": "Population fetch failed"}))
            continue
        t0 = time.monotonic()
        try:
            result = project_population(r.data, site.country)
            ms = int((time.monotonic() - t0) * 1000)
            total_current = sum(rp.get("current_population", 0) for rp in result.ring_projections)
            total_projected = sum(rp.get("projected_population", 0) for rp in result.ring_projections)
            summary = (f"current_total={total_current:,}, projected_total={total_projected:,}, "
                       f"growth_rate={result.growth_rate}, year={result.projection_year}")
            md += _site_section(site, "data_ok", ms, summary, _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "failed", ms, str(exc), traceback.format_exc())
    _write("analysis_population_projection.md", md)

    # Coal site analysis
    md = _header("Coal Site Analysis (NS-05)", "Coal site area sufficiency for SMR deployment")
    for site in sites:
        t0 = time.monotonic()
        try:
            result = evaluate_coal_site(site_area_ha=100.0, status="operating")
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "data_ok", ms,
                                f"sufficient={result.is_sufficient}, ratio={result.sufficiency_ratio:.2f}",
                                _json(result.to_dict()))
        except Exception as exc:
            ms = int((time.monotonic() - t0) * 1000)
            md += _site_section(site, "failed", ms, str(exc), traceback.format_exc())
    _write("analysis_coal_site_analysis.md", md)


# ── Summary report ───────────────────────────────────────────────────

def _print_summary(results: dict[str, FetchResult], elapsed_s: float) -> None:
    total = len(results)
    ok = sum(1 for r in results.values() if r.status == STATUS_DATA_OK)
    empty = sum(1 for r in results.values() if r.status == STATUS_EMPTY)
    failed = sum(1 for r in results.values() if r.status in (STATUS_FAILED, STATUS_RATE_LIMITED))

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total tasks:     {total}")
    print(f"  ✓ Data OK:       {ok}")
    print(f"  ⚠ Empty:         {empty}")
    print(f"  ✗ Failed:        {failed}")
    print(f"  Elapsed:         {elapsed_s / 60:.1f} min")
    print(f"  Completeness:    {ok}/{total} ({ok / total * 100:.0f}%)" if total else "")

    if failed:
        print(f"\n  Failed tasks:")
        for key, r in sorted(results.items()):
            if r.status in (STATUS_FAILED, STATUS_RATE_LIMITED):
                print(f"    {key}: {r.error} ({r.attempts} attempts)")

    print(f"\n  Snapshots: tests/integrationSnapshots/")
    print(f"  State:     tests/integrationSnapshots/.fetch_state.json")
    print(f"{'=' * 60}\n")


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Queue-based live integration snapshots")
    parser.add_argument("--max-sites", type=int, default=0, help="Limit sites (0 = all)")
    parser.add_argument("--skip", nargs="*", default=[],
                        choices=["corine", "osm", "population", "egdi", "seismic", "analysis"],
                        help="Skip specific connector groups")
    parser.add_argument("--clean", action="store_true", help="Ignore prior state, start fresh")
    args = parser.parse_args()

    skip = set(args.skip)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    from atoms_vs_ashes.config import Settings
    settings = Settings(PROJECT_ROOT / "config" / "default.yml")
    sites = load_sample_sites(settings)
    if args.max_sites > 0:
        sites = sites[:args.max_sites]

    state = {} if args.clean else _load_state()
    if "results" not in state:
        state["results"] = {}
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    results: dict[str, FetchResult] = {}
    lock = threading.Lock()
    workers: list[APIWorker] = []
    connectors: list[Any] = []

    total_start = time.monotonic()
    print(f"\n{'=' * 60}")
    print(f"  Queue-Based Live Integration Snapshots")
    print(f"  Sites: {len(sites)} | Skip: {skip or 'none'} | Clean: {args.clean}")
    resumed = sum(1 for v in state["results"].values() if v.get("status") == STATUS_DATA_OK)
    if resumed:
        print(f"  Resuming: {resumed} tasks already completed from prior run")
    print(f"{'=' * 60}\n")

    # Build CORINE queue
    if "corine" not in skip:
        corine_tasks, corine_conn = _build_corine_tasks(sites, settings, state)
        connectors.append(corine_conn)
        if corine_tasks:
            w = APIWorker("corine", results, state, lock)
            for t in corine_tasks:
                w.enqueue(t)
            workers.append(w)
            print(f"  [corine]   {len(corine_tasks)} tasks queued (1.5s interval)")

    # Build Overpass queue (OSM + Population share the same API)
    overpass_skip = {"osm", "population"}.issubset(skip)
    if not overpass_skip:
        overpass_tasks, osm_conn, pop_conn = _build_overpass_tasks(sites, settings, state)
        connectors.extend([osm_conn, pop_conn])

        filtered = []
        for t in overpass_tasks:
            if t.endpoint == "population" and "population" in skip:
                continue
            if t.endpoint != "population" and "osm" in skip:
                continue
            filtered.append(t)

        if filtered:
            w = APIWorker("overpass", results, state, lock)
            for t in filtered:
                w.enqueue(t)
            workers.append(w)
            print(f"  [overpass] {len(filtered)} tasks queued (12s interval, 30s backoff)")

    if not workers:
        print("  No tasks to execute (all completed or skipped).")
    else:
        total_tasks = sum(len(w.tasks) for w in workers)
        print(f"\n  Starting {len(workers)} parallel workers ({total_tasks} total tasks)...\n")

        for w in workers:
            w.start()
        for w in workers:
            w.join()

    # Close connectors
    for c in connectors:
        if hasattr(c, "close"):
            c.close()

    # Load results from state for previously-completed tasks (for snapshot generation)
    for key, meta in state.get("results", {}).items():
        if key not in results and meta.get("status") == STATUS_DATA_OK:
            results[key] = FetchResult(
                status=STATUS_DATA_OK,
                element_count=meta.get("element_count", 0),
                elapsed_ms=meta.get("elapsed_ms", 0),
                attempts=meta.get("attempts", 1),
            )

    # Generate snapshots
    if "analysis" not in skip:
        _generate_snapshots(sites, results, settings)

    elapsed = time.monotonic() - total_start
    _print_summary(results, elapsed)


if __name__ == "__main__":
    main()
