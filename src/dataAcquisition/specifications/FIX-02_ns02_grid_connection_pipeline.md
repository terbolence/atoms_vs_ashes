# FIX-02: NS-02 Grid Connection Pipeline — Integration Specification

> **STATUS:** Specification complete — Implementation pending
> **Scope:** Full NS-02 grid connection data pipeline across four data sources

**Source ID:** FIX-02
**Phase:** 2 (Core Ranking)
**Estimated effort:** 30 h (see §11 breakdown)
**Criteria served:** NS-02 (grid connection — all sub-fields)
**Controllers affected:** I-2 OSM Overpass, I-4 GEM Coal Plant Tracker, S-13 ENTSO-E (new), S-45 PyPSA-Eur (new)

---

## 1. Purpose

This specification consolidates the four implementation items needed to fully populate the NS-02 (Grid Connection) columns in `site_infrastructure_v2`. The NS-02 schema requires eight data fields:

| Column | Type | Current status |
|--------|------|---------------|
| `nearest_substation_km` | NUMERIC(8,2) | Populated by I-2 OSM (with known deficiencies) |
| `substation_name` | VARCHAR(200) | Populated by I-2 OSM (often "unnamed") |
| `nearest_hv_line_km` | NUMERIC(8,2) | Populated by I-2 OSM (centroid distance, not nearest-point) |
| `hv_line_voltage_kv` | INTEGER | Populated by I-2 OSM (multi-voltage parsing broken) |
| `hv_line_count` | INTEGER | Populated by I-2 OSM |
| `substation_count` | INTEGER | Populated by I-2 OSM |
| `grid_export_capacity_mw` | NUMERIC(10,2) | **Not populated** |
| `ns02_quality` | VARCHAR(20) | Partial (only flags zero-infrastructure case) |

**Requirement:** This specification prioritises filling `grid_export_capacity_mw` — the only entirely missing field — via a four-tier data source cascade, while simultaneously fixing known deficiencies in the existing OSM power infrastructure queries.

---

## 2. Current State Assessment

### 2.1 What works

**Fact:** `analysis/grid_proximity.py` queries the Overpass API via `OverpassClient.fetch_power_infrastructure()` and returns a `GridResult` with substation distance/name, HV line distance/voltage/count, and lists of nearby infrastructure elements.

**Fact:** The integration snapshot for Tušimice (CZ) demonstrates that the pipeline works end-to-end: 768 HV lines, 1105 substations found in a 50 km radius, nearest line at 0.49 km (110 kV), nearest substation at 0.41 km.

### 2.2 What is broken

**Defect D-01:** Rovinari (RO) and Bełchatów (PL) returned zero infrastructure elements in integration testing, despite being major coal plants with obvious grid connections. Root cause is likely the Overpass query missing relations and/or rate-limiting issues during batch runs.

**Defect D-02:** `_parse_voltage_kv()` in `analysis/grid_proximity.py` cannot handle semicolon-separated multi-voltage tags (e.g., `"400000;220000"`), which are common on multi-circuit transmission lines in OSM. The parser returns `None` for these lines, silently dropping high-voltage infrastructure.

**Defect D-03:** The Overpass query uses `out center` for power lines, which returns the centroid of the way. For long transmission lines (50+ km), the centroid can be 10+ km from the nearest point on the line to the site. This systematically overestimates `nearest_hv_line_km`.

**Defect D-04:** The Overpass query does not fetch `relation["power"="substation"]`. Large 400 kV+ transmission substations in CEE are frequently mapped as OSM relations (composed of multiple ways). These are invisible to the current query.

### 2.3 What is missing

**Gap G-01:** `grid_export_capacity_mw` is never populated. No data source is wired to this column. The field exists in the schema (`SiteInfrastructureV2.grid_export_capacity_mw`, migration 006) but is always `NULL`.

**Gap G-02:** `ns02_quality` is only written when zero infrastructure is found. No quality assessment is performed when data is present (e.g., distinguishing between a site with 1 nearby substation vs. 50).

**Gap G-03:** `ns02_comment` is never populated. No provenance trail records which sources contributed to each field value.

---

## 3. Implementation Items

The four items are ordered to prioritise `grid_export_capacity_mw` (the missing field), as required.

### 3.1 FIX-02-A: GEM Capacity Fallback Wiring (2 h)

**Requirement:** Wire `sites.installed_capacity_mw` into `SiteInfrastructureV2.grid_export_capacity_mw` as the P4 (lowest-priority) floor value for grid export capacity.

**Rationale:** If a coal plant operated at capacity X MW, the grid connection was engineered to export at least X MW. This is a conservative floor estimate requiring zero new API calls.

**Fact:** `sites.installed_capacity_mw` is already populated during ingestion from the GEM Coal Plant Tracker's "Capacity (MW)" column (cell M1 in the "Units" sheet). The mapping is defined in `ingest/sites.py`:

```python
_COLUMN_MAP = {
    ...
    "Capacity (MW)": "installed_capacity_mw",
    ...
}
```

**Fact:** For supplementary sites added via `load_supplementary_sites()`, `installed_capacity_mw` may be `None` if not specified in the YAML config.

**Implementation:**

Modify `analysis/grid_proximity.py` `assess_and_persist()` to accept a `site` parameter (or `installed_capacity_mw` directly) and populate the field:

```python
def assess_and_persist(
    lat: float, lon: float,
    site_id: Any, session: Session, run_id: str,
    overpass: OverpassClient,
    installed_capacity_mw: float | None = None,
) -> GridResult:
    ...
    result = assess_grid_proximity(lat, lon, overpass)

    # FIX-02-A: GEM fallback for grid_export_capacity_mw
    export_capacity_mw = installed_capacity_mw
    export_capacity_source = "gem_coal_tracker" if export_capacity_mw else None
    export_capacity_quality = "low" if export_capacity_mw else None
    ...
```

**Quality flag:** `"low"` — proxy derived from coal plant nameplate capacity, not measured grid connection capacity.

**Validation:**
- `installed_capacity_mw` must be > 0 if present
- Plausibility: 1 MW ≤ value ≤ 10,000 MW (largest single coal units are ~1,300 MW)
- If `installed_capacity_mw` is `None`, leave `grid_export_capacity_mw` as `NULL` and note in `ns02_comment`

**Testing:**
- Unit test: `installed_capacity_mw=660.0` → `grid_export_capacity_mw=660.0`, quality `"low"`
- Unit test: `installed_capacity_mw=None` → `grid_export_capacity_mw=None`, quality unchanged
- Integration test: enrich a site with known GEM capacity → column populated in DB

### 3.2 FIX-02-B: S-13 ENTSO-E Connector Implementation (16 h)

**Requirement:** Implement the ENTSO-E Transparency Platform connector per the existing S-13 specification (`specifications/S-13_entso_e.md`, 1198 lines).

**Cross-reference:** This section does not duplicate the S-13 specification. All architectural decisions, data flows, dataclasses, XML parsing, API query patterns, EIC codes, testing strategy, and configuration are defined in S-13. This section specifies only the **additional fuzzy matching logic** needed to bridge ENTSO-E per-unit data to site-level `grid_export_capacity_mw`.

#### 3.2.1 Fuzzy matching: ENTSO-E per-unit → site name

**Fact:** The ENTSO-E A71 (Installed Generation Capacity per Unit) query returns individual generation units with `unit_name`, `psr_type`, and `installed_mw`. These unit names correspond to power plant names (e.g., "Rovinari Group 3", "Bełchatów Unit 1") but use different naming conventions from the GEM tracker.

**Requirement:** For each site, attempt to match ENTSO-E generation units from the site's bidding zone against the site's name and alternative names.

**Algorithm:**

```
match_entsoe_units(site, zone_units: list[GenerationUnit]) → MatchResult:

  candidates = [site.name] + (site.alternative_names or [])

  matched_units = []
  FOR unit IN zone_units:
    FOR candidate IN candidates:
      score = rapidfuzz.fuzz.token_set_ratio(
          normalise(candidate),
          normalise(unit.unit_name),
      )
      IF score >= MATCH_THRESHOLD (default 70):
          matched_units.append(unit)
          BREAK

  IF matched_units:
      total_mw = sum(u.installed_mw for u in matched_units)
      RETURN MatchResult(
          matched=True,
          capacity_mw=total_mw,
          unit_count=len(matched_units),
          best_score=max(scores),
          source="entsoe_per_unit_match",
          quality="high",
      )
  ELSE:
      RETURN MatchResult(matched=False, ...)
```

**Normalisation function:**

```python
def normalise(name: str) -> str:
    """Lowercase, strip diacritics, remove common suffixes."""
    import unicodedata
    s = unicodedata.normalize("NFKD", name.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    for suffix in ("power plant", "power station", "thermal",
                    "kraftwerk", "electrocentrala", "elektrownia"):
        s = s.replace(suffix, "")
    return s.strip()
```

**Fact:** `rapidfuzz` is a C-extension fuzzy matching library (~100× faster than `fuzzywuzzy`). It has no dependency on `python-Levenshtein`.

**Requirement:** Add `rapidfuzz` to `pyproject.toml` as a new dependency.

#### 3.2.2 Merge strategy with FIX-02-A

When ENTSO-E per-unit matching succeeds (score >= 70), the matched capacity **overwrites** the GEM fallback:

```python
if entsoe_match.matched:
    export_capacity_mw = entsoe_match.capacity_mw
    export_capacity_source = "entsoe_per_unit_match"
    export_capacity_quality = "high"
```

When matching fails but zone-level data is available, use the zone's total installed capacity as context (stored in `ns02_comment`), but retain the GEM fallback for `grid_export_capacity_mw`:

```python
else:
    # Keep FIX-02-A GEM value; annotate with zone context
    ns02_comment += (
        f"ENTSO-E zone {zone.zone_name}: {zone.total_installed_mw} MW total, "
        f"no per-unit match found (best score: {entsoe_match.best_score})"
    )
    export_capacity_quality = "medium"  # upgrade from "low" due to zone context
```

#### 3.2.3 New connector package

```
connectors/entso_e/
├── __init__.py              # exports EntsoEConnector, CRITERION_IDS
├── client.py                # EntsoEConnector class (per S-13 §5.1)
├── models.py                # CRITERION_IDS, result dataclasses (per S-13 §6)
├── parsers.py               # XML parsing (per S-13 §5.1)
├── batch.py                 # enrich_site, enrich_batch, enrich_all (per S-13 §5.3b)
└── matcher.py               # fuzzy matching logic (§3.2.1 above)
```

**Requirement:** Follow the connector interface pattern established by `seismic_hazard`:
- `__init__(settings)` reads `connectors.entso_e` from YAML config
- `health_check()` validates API token with a small test query
- `fetch(lat, lon)` returns `EntsoEResult` (zone lookup, no DB)
- `enrich_site(site_id, session, run_id)` fetches + persists
- `enrich_batch(session, run_id)` / `enrich_all(session, run_id)`
- `close()` / context manager

**Configuration:** Per S-13 §11.1 — `connectors.entso_e` section in `config/default.yml` including `security_token`, `api_url`, `bidding_zones`, `interconnectors`, `nuclear_readiness_thresholds`.

**Dependencies:**
- `httpx` (already in project)
- `lxml` (for XML parsing — verify in `pyproject.toml`, add if not present)
- `rapidfuzz` (new — for fuzzy matching)

### 3.3 FIX-02-C: I-2 OSM Overpass Power Query Fixes (4 h)

**Requirement:** Fix three deficiencies in the existing OSM power infrastructure query.

#### 3.3.1 Fix C-01: Add relation substations

**Fact:** The current `fetch_power_infrastructure()` query in `connectors/osm/client.py` (lines 322–350) fetches:
- `way["power"="line"]["voltage"]` — HV lines
- `node["power"="substation"]` — substations (nodes)
- `way["power"="substation"]` — substations (ways)
- `node["power"="plant"]` — power plants

**Defect:** Missing `relation["power"="substation"]`. Large transmission substations (400 kV+) in CEE are frequently mapped as OSM relations with multiple member ways representing different voltage sections.

**Implementation:** Add to the Overpass QL query:

```python
ql = (
    f"[out:json][timeout:120];\n"
    f"(\n"
    f'  way["power"="line"]["voltage"](around:{radius_m},{lat},{lon});\n'
    f'  node["power"="substation"](around:{radius_m},{lat},{lon});\n'
    f'  way["power"="substation"](around:{radius_m},{lat},{lon});\n'
    f'  relation["power"="substation"](around:{radius_m},{lat},{lon});\n'
    f'  node["power"="plant"](around:{radius_m},{lat},{lon});\n'
    f'  way["power"="plant"](around:{radius_m},{lat},{lon});\n'
    f");\n"
    f"out center geom;\n"
)
```

**Fact:** `out center geom` returns both the centroid (for ways/relations) and the full geometry (for lines). This enables Fix C-02 while retaining backwards compatibility for substations.

#### 3.3.2 Fix C-02: Nearest-point distance for power lines

**Defect:** The current `assess_grid_proximity()` in `analysis/grid_proximity.py` computes distance to each element using `haversine_km(lat, lon, el.lat, el.lon)` where `el.lat/lon` is the centroid returned by `out center`. For long transmission lines spanning 50+ km, the centroid can be 10+ km from the nearest point on the line to the site.

**Implementation:** When geometry nodes are available (from `out geom`), compute distance to the nearest point on the polyline:

```python
def _nearest_point_distance_km(
    site_lat: float, site_lon: float,
    geometry: list[dict[str, float]],
) -> float:
    """Minimum haversine distance from site to any node on a polyline."""
    if not geometry:
        return float("inf")
    return min(
        haversine_km(site_lat, site_lon, node["lat"], node["lon"])
        for node in geometry
    )
```

Update `assess_grid_proximity()` to prefer polyline distance for elements that have geometry data, falling back to centroid distance when geometry is absent:

```python
for el in elements:
    geom = getattr(el, "geometry", None) or []
    if geom and el.tags.get("power") == "line":
        dist = _nearest_point_distance_km(lat, lon, geom)
    elif el.lat is not None and el.lon is not None:
        dist = haversine_km(lat, lon, el.lat, el.lon)
    else:
        continue
    ...
```

**Requirement:** Update `OsmElement` to carry an optional `geometry` field:

```python
@dataclass
class OsmElement:
    osm_type: str
    osm_id: int
    lat: float | None = None
    lon: float | None = None
    tags: dict[str, str] = field(default_factory=dict)
    geometry: list[dict[str, float]] = field(default_factory=list)
```

Update `fetch_power_infrastructure()` to populate `geometry` from the Overpass response:

```python
OsmElement(
    osm_type=el.get("type", "node"),
    osm_id=el.get("id", 0),
    lat=el.get("lat") or el.get("center", {}).get("lat"),
    lon=el.get("lon") or el.get("center", {}).get("lon"),
    tags=el.get("tags", {}),
    geometry=el.get("geometry", []),
)
```

#### 3.3.3 Fix C-03: Multi-voltage parsing

**Defect:** `_parse_voltage_kv()` in `analysis/grid_proximity.py` fails on semicolon-separated values like `"400000;220000"`. The `float()` call raises `ValueError`, and the function returns `None`, silently dropping the line.

**Current code:**

```python
def _parse_voltage_kv(tags: dict[str, str]) -> float | None:
    raw = tags.get("voltage", "")
    if not raw:
        return None
    try:
        return float(raw.replace(",", "").strip()) / 1000
    except ValueError:
        return None
```

**Implementation:** Parse all semicolon-separated values and return the maximum:

```python
def _parse_voltage_kv(tags: dict[str, str]) -> float | None:
    raw = tags.get("voltage", "")
    if not raw:
        return None
    voltages: list[float] = []
    for part in raw.split(";"):
        cleaned = part.replace(",", "").strip()
        if not cleaned:
            continue
        try:
            voltages.append(float(cleaned) / 1000)
        except ValueError:
            continue
    return max(voltages) if voltages else None
```

**Rationale:** For multi-circuit lines, the maximum voltage determines the line's transmission capacity class. A line tagged `"400000;220000"` has a 400 kV circuit and a 220 kV circuit — the 400 kV value is the relevant one for assessing grid connection capability.

**Testing:**
- `_parse_voltage_kv({"voltage": "400000"})` → `400.0`
- `_parse_voltage_kv({"voltage": "400000;220000"})` → `400.0`
- `_parse_voltage_kv({"voltage": "110000;110000"})` → `110.0`
- `_parse_voltage_kv({"voltage": ""})` → `None`
- `_parse_voltage_kv({"voltage": "invalid"})` → `None`
- `_parse_voltage_kv({"voltage": "400000;"})` → `400.0`
- `_parse_voltage_kv({"voltage": ";220000"})` → `220.0`

### 3.4 FIX-02-D: S-45 PyPSA-Eur Static Enrichment (8 h)

**Requirement:** Implement a static data connector that loads the PyPSA-Eur network model and provides site-level grid export capacity via thermal line ratings.

#### 3.4.1 Source profile

| Field | Value |
|-------|-------|
| Name | PyPSA-Eur Grid Topology |
| Provider | PyPSA/TU Berlin (open-source energy modelling community) |
| URL | Data: `https://zenodo.org/records/15143557` (v0.6.0, April 2025); Code: `https://github.com/PyPSA/pypsa-eur` |
| Protocol | Static download (Zenodo ZIP, ~200 MB); periodic manual refresh |
| Auth | None (open data, ODbL license derived from OpenStreetMap) |
| Formats | CSV (`buses.csv`, `lines.csv`, `links.csv`, `transformers.csv`) |
| Spatial coverage | 35 European countries (all ENTSO-E area), voltages ≥ 220 kV (optionally ≥ 60 kV) |
| Temporal coverage | Snapshot based on OSM data vintage (typically 1–3 months old) |
| Update cadence | PyPSA-Eur releases approximately quarterly; data bundle updated accordingly |
| License | ODbL 1.0 (derived from OpenStreetMap). Attribution: "Contains data from OpenStreetMap (ODbL) processed by PyPSA-Eur" |

#### 3.4.2 Data structure

**Fact:** The PyPSA-Eur data bundle contains the following relevant files:

**`buses.csv`** — Substations/buses (network nodes):

| Column | Type | Description |
|--------|------|-------------|
| `Bus` | str | Bus identifier (station ID + voltage level) |
| `v_nom` | float | Nominal voltage (kV) |
| `x` | float | Longitude (EPSG:4326) |
| `y` | float | Latitude (EPSG:4326) |
| `carrier` | str | "AC" or "DC" |
| `station_id` | int | Groups multiple buses at the same physical substation |
| `under_construction` | bool | Construction status |

**`lines.csv`** — AC transmission lines (network edges):

| Column | Type | Description |
|--------|------|-------------|
| `Line` | str | Line identifier |
| `bus0` | str | From-bus identifier |
| `bus1` | str | To-bus identifier |
| `s_nom` | float | Nominal apparent power rating (MVA) |
| `v_nom` | float | Nominal voltage (kV) |
| `length` | float | Line length (km) |
| `num_parallel` | int | Number of parallel circuits |
| `carrier` | str | "AC" |

**Fact:** `s_nom` (in MVA) is the thermal rating of the line. For AC lines at power factors typical of transmission grids (~0.95), the MW export capacity is approximately `s_nom × 0.95`. For screening purposes, `s_nom` in MVA is a sufficient proxy for MW capacity.

#### 3.4.3 Spatial join algorithm

```
find_nearest_bus(site_lat, site_lon, buses_df, max_distance_km=50) → BusMatch | None:

  # Pre-filter: bounding box within ±0.5° (roughly 50 km at European latitudes)
  candidates = buses_df[
      (buses_df.y.between(site_lat - 0.5, site_lat + 0.5)) &
      (buses_df.x.between(site_lon - 0.5, site_lon + 0.5))
  ]

  # Compute haversine distance to each candidate
  candidates["dist_km"] = candidates.apply(
      lambda row: haversine_km(site_lat, site_lon, row.y, row.x),
      axis=1,
  )

  # Filter by max distance and select nearest
  nearby = candidates[candidates.dist_km <= max_distance_km]
  IF nearby.empty:
      RETURN None

  nearest = nearby.loc[nearby.dist_km.idxmin()]

  # Find all buses at the same physical substation (same station_id)
  station_buses = buses_df[buses_df.station_id == nearest.station_id]

  RETURN BusMatch(
      bus_id=nearest.Bus,
      station_id=nearest.station_id,
      distance_km=nearest.dist_km,
      voltage_kv=nearest.v_nom,
      bus_count=len(station_buses),
      bus_ids=station_buses.Bus.tolist(),
  )
```

#### 3.4.4 Export capacity computation

```
compute_export_capacity(bus_match, lines_df) → ExportCapacity:

  # Find all lines connected to any bus at this station
  connected_lines = lines_df[
      lines_df.bus0.isin(bus_match.bus_ids) |
      lines_df.bus1.isin(bus_match.bus_ids)
  ]

  IF connected_lines.empty:
      RETURN ExportCapacity(capacity_mw=None, quality="low")

  total_thermal_mva = connected_lines.s_nom.sum()
  max_line_mva = connected_lines.s_nom.max()
  max_voltage_kv = connected_lines.v_nom.max()
  line_count = len(connected_lines)

  # Approximate MW = MVA × power factor (0.95 for transmission)
  capacity_mw = round(total_thermal_mva * 0.95, 2)

  RETURN ExportCapacity(
      capacity_mw=capacity_mw,
      thermal_mva=total_thermal_mva,
      max_line_mva=max_line_mva,
      max_voltage_kv=max_voltage_kv,
      line_count=line_count,
      quality="high",
  )
```

#### 3.4.5 New connector package

```
connectors/pypsa_eur/
├── __init__.py              # exports PypsaEurConnector, CRITERION_IDS
├── loader.py                # load_buses(), load_lines() from CSV
├── models.py                # CRITERION_IDS, BusMatch, ExportCapacity, PypsaEurResult
└── spatial.py               # find_nearest_bus(), compute_export_capacity()
```

**Connector interface:**

```python
class PypsaEurConnector:
    def __init__(self, settings: Settings | None = None) -> None:
        cfg = {}
        if settings:
            cfg = settings.connector_config("pypsa_eur")
        self._data_dir = Path(cfg.get("data_dir", "sources/pypsa_eur"))
        self._max_distance_km = cfg.get("max_distance_km", 50)
        self._buses_df: pd.DataFrame | None = None
        self._lines_df: pd.DataFrame | None = None

    def health_check(self) -> bool:
        """Check that data files exist."""
        buses_path = self._data_dir / "buses.csv"
        lines_path = self._data_dir / "lines.csv"
        return buses_path.exists() and lines_path.exists()

    def _ensure_loaded(self) -> None:
        """Lazy-load CSVs on first use."""
        if self._buses_df is None:
            self._buses_df = load_buses(self._data_dir)
            self._lines_df = load_lines(self._data_dir)

    def fetch(self, lat: float, lon: float) -> PypsaEurResult:
        """Find nearest bus and compute export capacity."""
        self._ensure_loaded()
        bus_match = find_nearest_bus(
            lat, lon, self._buses_df,
            max_distance_km=self._max_distance_km,
        )
        if bus_match is None:
            return PypsaEurResult(lat=lat, lon=lon, quality="insufficient")
        export = compute_export_capacity(bus_match, self._lines_df)
        return PypsaEurResult(
            lat=lat, lon=lon,
            bus_match=bus_match,
            export_capacity=export,
            quality=export.quality,
        )

    def close(self) -> None:
        self._buses_df = None
        self._lines_df = None

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
```

**Static dataset storage:**

```
sources/pypsa_eur/
├── README.md                # download instructions, version, date
├── buses.csv                # from PyPSA-Eur data bundle
├── lines.csv                # from PyPSA-Eur data bundle
└── links.csv                # HVDC links (optional, for cross-border capacity)
```

**Configuration addition to `config/default.yml`:**

```yaml
connectors:
  pypsa_eur:
    data_dir: "sources/pypsa_eur"
    max_distance_km: 50
    min_voltage_kv: 110
    power_factor: 0.95
```

---

## 4. Data Flow / Merge Strategy

### 4.1 `grid_export_capacity_mw` priority cascade

The four sources for `grid_export_capacity_mw` are evaluated in priority order. The highest-confidence available value wins:

```
assess_grid_export_capacity(site, grid_result, entsoe_result, pypsa_result):

  capacity_mw = None
  source = None
  quality = None

  # P4: GEM fallback (lowest priority)
  IF site.installed_capacity_mw is not None AND site.installed_capacity_mw > 0:
      capacity_mw = site.installed_capacity_mw
      source = "gem_coal_tracker"
      quality = "low"

  # P3: ENTSO-E zone-level context (upgrades quality, keeps GEM value)
  IF entsoe_result is not None AND entsoe_result.capacity is not None:
      IF capacity_mw is not None:
          quality = "medium"  # GEM value corroborated by zone context

  # P2: ENTSO-E per-unit fuzzy match (overwrites if matched)
  IF entsoe_result is not None AND entsoe_result.per_unit_match is not None:
      IF entsoe_result.per_unit_match.matched:
          capacity_mw = entsoe_result.per_unit_match.capacity_mw
          source = "entsoe_per_unit_match"
          quality = "high"

  # P1: PyPSA-Eur thermal rating (highest priority, overwrites)
  IF pypsa_result is not None AND pypsa_result.export_capacity is not None:
      IF pypsa_result.export_capacity.capacity_mw is not None:
          capacity_mw = pypsa_result.export_capacity.capacity_mw
          source = "pypsa_eur_thermal_rating"
          quality = "high"

  RETURN (capacity_mw, source, quality)
```

### 4.2 Infrastructure fields (OSM-sourced)

| Field | Primary source | Cross-check source |
|-------|---------------|-------------------|
| `nearest_substation_km` | I-2 OSM (fixed, §3.3) | S-45 PyPSA-Eur `bus_match.distance_km` |
| `substation_name` | I-2 OSM (fixed, §3.3) | — |
| `nearest_hv_line_km` | I-2 OSM (fixed, §3.3) | — |
| `hv_line_voltage_kv` | I-2 OSM (fixed, §3.3) | S-45 PyPSA-Eur `export_capacity.max_voltage_kv` |
| `hv_line_count` | I-2 OSM (fixed, §3.3) | S-45 PyPSA-Eur `export_capacity.line_count` |
| `substation_count` | I-2 OSM (existing) | S-45 PyPSA-Eur `bus_match.bus_count` |

**Cross-check rule:** When PyPSA-Eur data is available, compare OSM `hv_line_voltage_kv` against PyPSA-Eur `max_voltage_kv`. If they differ by more than one voltage class (e.g., OSM says 110 kV, PyPSA-Eur says 400 kV), write an observation noting the discrepancy.

### 4.3 Quality determination

| Condition | `ns02_quality` |
|-----------|---------------|
| PyPSA-Eur bus found + ENTSO-E zone data available + OSM infrastructure found | `"high"` |
| ENTSO-E per-unit match + OSM infrastructure found (no PyPSA-Eur) | `"high"` |
| ENTSO-E zone data + OSM infrastructure found + GEM fallback | `"medium"` |
| Only OSM infrastructure found + GEM fallback (no ENTSO-E) | `"low"` |
| Only GEM fallback (no OSM, no ENTSO-E, no PyPSA-Eur) | `"low"` |
| No data from any source | `"insufficient"` |

### 4.4 Provenance trail (`ns02_comment`)

**Requirement:** `ns02_comment` must record which source provided each field value. Format:

```
grid_export_capacity_mw: {value} MW from {source} ({quality}).
nearest_substation_km: {value} km from OSM (way/{osm_id}).
hv_line_voltage_kv: {value} kV from OSM. PyPSA-Eur cross-check: {pypsa_kv} kV.
```

---

## 5. Persistence Mapping

All fields map to existing columns in `site_infrastructure_v2` (migration 006). No schema changes are required.

| Field | Target column | Source cascade | Notes |
|-------|--------------|---------------|-------|
| `nearest_substation_km` | `SiteInfrastructureV2.nearest_substation_km` | I-2 OSM (fixed) | |
| `substation_name` | `SiteInfrastructureV2.substation_name` | I-2 OSM (fixed) | |
| `nearest_hv_line_km` | `SiteInfrastructureV2.nearest_hv_line_km` | I-2 OSM (fixed, nearest-point) | |
| `hv_line_voltage_kv` | `SiteInfrastructureV2.hv_line_voltage_kv` | I-2 OSM (fixed, max from multi-voltage) | Cast to INTEGER |
| `hv_line_count` | `SiteInfrastructureV2.hv_line_count` | I-2 OSM (existing) | |
| `substation_count` | `SiteInfrastructureV2.substation_count` | I-2 OSM (existing) | |
| `grid_export_capacity_mw` | `SiteInfrastructureV2.grid_export_capacity_mw` | S-45 > S-13 per-unit > S-13 zone > I-4 GEM | |
| `ns02_quality` | `SiteInfrastructureV2.ns02_quality` | Derived from §4.3 | |
| `ns02_comment` | `SiteInfrastructureV2.ns02_comment` | Provenance trail (§4.4) | |

**DataSource provenance records:**

| Source | `data_sources.name` | `data_sources.url` |
|--------|---------------------|-------------------|
| I-2 OSM | `"osm_overpass_grid"` | `connectors.osm.overpass_url` |
| I-4 GEM | `"gem_coal_plant_tracker"` | Local file path |
| S-13 ENTSO-E | `"entsoe_transparency_platform"` | `"https://web-api.tp.entsoe.eu/api"` |
| S-45 PyPSA-Eur | `"pypsa_eur_grid_topology"` | `"https://zenodo.org/records/15143557"` |

---

## 6. Result Dataclasses

### 6.1 GridExportCapacityResult (new, for the cascade)

```
GridExportCapacityResult
├── capacity_mw: float | None
├── source: str | None             # "gem_coal_tracker" | "entsoe_per_unit_match" | "entsoe_zone" | "pypsa_eur_thermal_rating"
├── quality: str | None            # "high" | "medium" | "low" | "insufficient"
├── gem_capacity_mw: float | None  # always populated if available (for audit)
├── entsoe_matched: bool
├── entsoe_match_score: float | None
├── entsoe_matched_units: int | None
├── pypsa_thermal_mva: float | None
├── pypsa_bus_distance_km: float | None
├── to_dict() → dict
```

### 6.2 PypsaEurResult

```
PypsaEurResult
├── lat: float
├── lon: float
├── bus_match: BusMatch | None
├── export_capacity: ExportCapacity | None
├── quality: str                   # "high" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.3 BusMatch

```
BusMatch
├── bus_id: str
├── station_id: int
├── distance_km: float
├── voltage_kv: float
├── bus_count: int
├── bus_ids: list[str]
├── to_dict() → dict
```

### 6.4 ExportCapacity

```
ExportCapacity
├── capacity_mw: float | None      # s_nom * power_factor
├── thermal_mva: float
├── max_line_mva: float
├── max_voltage_kv: float
├── line_count: int
├── quality: str
├── to_dict() → dict
```

### 6.5 Extended GridResult

The existing `GridResult` in `analysis/grid_proximity.py` is extended:

```
GridResult (extended)
├── ... (existing fields) ...
├── grid_export_capacity_mw: float | None     # NEW
├── export_capacity_source: str | None        # NEW
├── export_capacity_quality: str | None       # NEW
├── ns02_comment: str | None                  # NEW
```

---

## 7. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Voltage non-negative | Semantic | `hv_line_voltage_kv >= 0` | Discard element |
| Voltage plausibility | Semantic | `hv_line_voltage_kv <= 1200` kV (highest AC voltage globally is 1150 kV) | Flag `low`, log warning |
| Distance non-negative | Semantic | `nearest_substation_km >= 0` | Internal assertion |
| Export capacity non-negative | Semantic | `grid_export_capacity_mw >= 0` | Flag `low` |
| Export capacity plausibility | Semantic | `grid_export_capacity_mw <= 50000` MW | Flag `low`, log warning |
| GEM capacity consistency | Cross-check | If ENTSO-E match exists: `|entsoe_mw - gem_mw| / gem_mw <= 1.0` | Log discrepancy, use ENTSO-E value |
| PyPSA-Eur bus distance | Spatial | `bus_match.distance_km <= max_distance_km` (50 km) | No bus match → fall back |
| Multi-voltage parse result | Schema | `_parse_voltage_kv` returns `float | None`, never raises | Unit test coverage |
| OSM geometry availability | Data quality | Lines with `out geom` should have `geometry` list | Fall back to centroid if empty |
| ENTSO-E fuzzy match score | Threshold | `score >= 70` for acceptance | Below threshold → unmatched |
| Bidding zone mapping | Schema | All 23 country codes map to valid EIC codes | Static assertion |

---

## 8. Operational Requirements

| Parameter | FIX-02-A (GEM) | FIX-02-B (ENTSO-E) | FIX-02-C (OSM) | FIX-02-D (PyPSA-Eur) |
|-----------|----------------|--------------------|-----------------|-----------------------|
| Network calls | 0 | Per S-13 spec (~115–230) | 1 Overpass query/site | 0 |
| Timeout | N/A | 30 s/request | 120 s | N/A |
| Rate limit | N/A | 400 req/min | 2 concurrent slots | N/A |
| Auth required | No | ENTSO-E API token | No | No |
| Per-site latency | ~0 ms | ~0 ms (zone lookup) | 2–5 s | ~10 ms |
| Batch overhead | None | ~1 min (zone ingestion) | Overpass throttling | ~1 s (CSV load) |
| Storage | 0 | ~5 MB cache | 0 | ~50 MB CSV files |

### Execution order

The four items must be executed in this order within the pipeline runner:

1. **Load PyPSA-Eur data** (once per batch — lazy load on first use)
2. **Ensure ENTSO-E zone data** (once per batch — `ingest_zones()`)
3. **Per site:**
   a. Fetch OSM power infrastructure (FIX-02-C)
   b. Look up GEM installed capacity (FIX-02-A)
   c. Look up ENTSO-E zone + per-unit match (FIX-02-B)
   d. Look up PyPSA-Eur nearest bus + export capacity (FIX-02-D)
   e. Apply priority cascade (§4.1)
   f. Persist to `site_infrastructure_v2`

---

## 9. Testing Strategy

### 9.1 Unit tests (no network, no DB)

| Test | What it tests | Fixture data |
|------|--------------|-------------|
| `test_parse_voltage_single` | `_parse_voltage_kv({"voltage": "400000"})` → `400.0` | Static |
| `test_parse_voltage_multi` | `_parse_voltage_kv({"voltage": "400000;220000"})` → `400.0` | Static |
| `test_parse_voltage_duplicate` | `_parse_voltage_kv({"voltage": "110000;110000"})` → `110.0` | Static |
| `test_parse_voltage_empty` | `_parse_voltage_kv({"voltage": ""})` → `None` | Static |
| `test_parse_voltage_invalid` | `_parse_voltage_kv({"voltage": "invalid"})` → `None` | Static |
| `test_parse_voltage_trailing_semi` | `_parse_voltage_kv({"voltage": "400000;"})` → `400.0` | Static |
| `test_nearest_point_distance` | Polyline distance < centroid distance for offset site | Synthetic polyline |
| `test_nearest_point_empty_geom` | Falls back to `float("inf")` | Empty list |
| `test_normalise_name` | Diacritics removed, suffixes stripped | "Bełchatów Power Plant" → "belchatow" |
| `test_fuzzy_match_exact` | "Rovinari" vs "Rovinari" → score 100 | Static |
| `test_fuzzy_match_partial` | "Rovinari" vs "Rovinari Group 3" → score >= 70 | Static |
| `test_fuzzy_match_no_match` | "Rovinari" vs "Cernavoda Unit 1" → score < 70 | Static |
| `test_pypsa_bus_found` | Spatial join finds nearest bus within 50 km | Synthetic CSV |
| `test_pypsa_bus_too_far` | No bus within 50 km → `None` | Synthetic CSV |
| `test_pypsa_export_capacity` | Sum of line s_nom × 0.95 | Synthetic lines CSV |
| `test_capacity_cascade_pypsa_wins` | PyPSA > ENTSO-E > GEM | All sources available |
| `test_capacity_cascade_entsoe_wins` | No PyPSA, ENTSO-E match available | PyPSA absent |
| `test_capacity_cascade_gem_fallback` | Only GEM available | Only GEM |
| `test_quality_determination` | All conditions in §4.3 | Various combinations |
| `test_provenance_comment_format` | `ns02_comment` contains expected source attributions | Constructed result |

### 9.2 Integration tests (mocked HTTP, test DB)

| Test | What it tests |
|------|--------------|
| `test_osm_relation_substations` | Query includes `relation["power"="substation"]`; response parsed correctly |
| `test_osm_line_geometry_distance` | `out geom` response → nearest-point distance < centroid distance |
| `test_gem_fallback_persists` | Site with `installed_capacity_mw=660` → `grid_export_capacity_mw=660` in DB |
| `test_entsoe_match_overwrites_gem` | ENTSO-E match → `grid_export_capacity_mw` updated, quality `"high"` |
| `test_pypsa_overwrites_entsoe` | PyPSA-Eur result → `grid_export_capacity_mw` from thermal rating |
| `test_full_cascade_rovinari` | Rovinari (RO): GEM 330 MW, ENTSO-E match, PyPSA-Eur bus → highest-confidence value wins |
| `test_full_cascade_no_pypsa` | Site with no PyPSA-Eur bus nearby → falls back to ENTSO-E or GEM |
| `test_ns02_quality_high` | All sources available → quality `"high"` |
| `test_ns02_quality_low` | Only GEM available → quality `"low"` |
| `test_ns02_comment_populated` | `ns02_comment` column is non-null and contains source attribution |

### 9.3 DB compatibility tests

| Test | What it tests |
|------|--------------|
| `test_entso_e_criterion_ids` | `entso_e/models.py` declares `CRITERION_IDS = ("NS-02",)` |
| `test_pypsa_eur_criterion_ids` | `pypsa_eur/models.py` declares `CRITERION_IDS = ("NS-02",)` |
| `test_ns02_seeded_in_criteria` | NS-02 exists in Alembic seed migration 005 |
| `test_persist_infrastructure_v2` | Writing all NS-02 fields to `site_infrastructure_v2` succeeds (no FK violation) |

---

## 10. Configuration

### 10.1 Additions to `config/default.yml`

```yaml
connectors:
  # ... existing connectors ...

  entso_e:
    # Per S-13 specification §11.1 — full config block
    api_url: "https://web-api.tp.entsoe.eu/api"
    security_token: null
    timeout_s: 30
    inter_request_delay_s: 0.2
    cache_dir: "sources/entso_e"
    cache_ttl_days: 180
    reference_year: 2025
    flow_sample_months: 1
    match_threshold: 70           # fuzzy match score for per-unit → site name
    bidding_zones:
      # ... (per S-13 §11.1, all 23 zones) ...
    interconnectors:
      # ... (per S-13 §11.1) ...
    nuclear_readiness_thresholds:
      # ... (per S-13 §11.1) ...

  pypsa_eur:
    data_dir: "sources/pypsa_eur"
    max_distance_km: 50
    min_voltage_kv: 110
    power_factor: 0.95
```

### 10.2 Environment variables

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `ENTSOE_SECURITY_TOKEN` | ENTSO-E API security token (overrides YAML) | Yes (for S-13) |

### 10.3 CLI invocation

```bash
# Full NS-02 pipeline (all sources)
python -m atoms_vs_ashes enrich grid --all

# OSM-only (quick, no API keys needed)
python -m atoms_vs_ashes enrich grid --all --osm-only

# With ENTSO-E zone ingestion
python -m atoms_vs_ashes enrich grid --all --ingest-entsoe --year 2025

# Single site
python -m atoms_vs_ashes enrich grid --site-id <uuid>
```

---

## 11. Effort Breakdown

| Item | Scope | Hours | Dependencies |
|------|-------|-------|-------------|
| FIX-02-A | GEM capacity wiring | 2 | None (immediate) |
| FIX-02-B | S-13 ENTSO-E connector + fuzzy matching | 16 | ENTSO-E API token |
| FIX-02-C | OSM Overpass power query fixes | 4 | None (immediate) |
| FIX-02-D | S-45 PyPSA-Eur static enrichment | 8 | PyPSA-Eur data download |
| **Total** | | **30** | |

### Recommended implementation sequence

1. **FIX-02-A** (2 h) — Immediate, zero dependencies. Provides a floor value for `grid_export_capacity_mw` across all sites from day one.
2. **FIX-02-C** (4 h) — Immediate, zero dependencies. Fixes OSM query accuracy for all existing infrastructure fields.
3. **FIX-02-D** (8 h) — Requires one-time data download (~200 MB). Provides site-level export capacity with highest spatial resolution.
4. **FIX-02-B** (16 h) — Requires ENTSO-E API token (free, instant registration). Largest effort but provides TSO-authoritative capacity data and zone-level grid context.

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| GEM nameplate capacity ≠ grid export capacity | Medium | GEM value is a conservative floor. Real grid connection capacity may be higher (multiple units aggregated at one substation) or lower (derating). Quality flag `"low"` signals this is a proxy. |
| ENTSO-E fuzzy matching false positives | Medium | Token-set matching with threshold 70 may match unrelated plants with similar names. Mitigated by restricting matching to units within the same bidding zone (same country). Manual review of low-confidence matches. |
| ENTSO-E fuzzy matching false negatives | Low | Plant names may differ significantly between GEM and ENTSO-E (language, transliteration). Mitigated by trying all `alternative_names` and by normalising diacritics/suffixes. |
| PyPSA-Eur data staleness | Low | PyPSA-Eur releases quarterly. For siting assessment, grid topology changes slowly. Recommend annual refresh. |
| PyPSA-Eur coverage gaps | Low | 35 European countries covered. All 23 in-scope countries are within coverage. Non-ENTSO-E countries (BY, AM) may have thinner coverage. |
| OSM `out geom` increases response size | Low | Geometry data for 768+ lines within 50 km adds ~5–10× to response size. Overpass may timeout for sites in dense grid areas. Mitigated by the existing 120 s timeout. If problematic, selectively request `out geom` only for the top-N nearest lines. |
| `rapidfuzz` dependency | Low | New dependency. C extension, no transitive dependencies. MIT licensed. Well-maintained (~6k GitHub stars). |
| Multi-voltage parsing edge cases | Low | Rare formats like `"400000 ; 220000"` (spaces around semicolons) or `"400/220 kV"` exist in OSM. The parser handles space-padded semicolons but not slash-separated values. Acceptable for screening — slash format is very rare. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | ENTSO-E API security token procurement | Yes (for FIX-02-B) | Free registration at `https://transparency.entsoe.eu/` → account settings → generate token. Instant. |
| 2 | PyPSA-Eur data bundle download | Yes (for FIX-02-D) | Manual download from `https://zenodo.org/records/15143557`. Extract `buses.csv` and `lines.csv` into `sources/pypsa_eur/`. |
| 3 | Rovinari/Bełchatów empty OSM results | No (may be test-mode artifact) | Investigate during FIX-02-C implementation. May be caused by rate limiting or query timeout during batch integration testing. |
| 4 | `lxml` in `pyproject.toml` | No | Verify presence; add if missing. Required by S-13 for XML parsing. |
| 5 | PyPSA-Eur `buses.csv` column name stability | No | Column names may vary between PyPSA-Eur versions. Pin to v0.6.0 format. Add version check in `loader.py`. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for ENTSO-E REST API | Yes (core dependency) |
| `lxml` | XML parsing with XPath for ENTSO-E CIM documents | Verify — add if missing |
| `rapidfuzz` | Fuzzy string matching for ENTSO-E per-unit → site name | **New** |
| `pandas` | CSV loading and spatial join for PyPSA-Eur | Yes (used by ingest) |

### 14.2 Source dependencies

| Dependency | Status | Blocking? |
|-----------|--------|-----------|
| ENTSO-E Transparency Platform REST API | Available; requires free API token | Yes (for FIX-02-B) |
| PyPSA-Eur data bundle v0.6.0 | Available on Zenodo | Yes (for FIX-02-D) |
| OSM Overpass API | Available; no auth | No (already in use) |
| GEM Coal Plant Tracker | Already ingested | No |

### 14.3 Internal dependencies

| Dependency | Status |
|-----------|--------|
| `SiteInfrastructureV2` model (migration 006) | Present |
| `sites.installed_capacity_mw` column | Present |
| `analysis/_provenance.py` (`ensure_data_source`, `write_observation`) | Present |
| `connectors/__init__.py` (must be updated to export new connectors) | Existing |

### 14.4 Downstream consumers

| Consumer | Uses |
|----------|------|
| NS-02 scoring/ranking module | `grid_export_capacity_mw`, `nearest_substation_km`, `hv_line_voltage_kv`, `ns02_quality` |
| DRV-03 Coal-to-Nuclear Synergy Composite | `grid_export_capacity_mw` (grid reuse benefit calculation) |
| NS-11 Coal-to-Nuclear Synergies | `grid_export_capacity_mw` (grid interconnection reuse) |

---

## 15. Acceptance Criteria

### 15.1 FIX-02-A (GEM Fallback)

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Site with `installed_capacity_mw=660` → `grid_export_capacity_mw=660.0` | Unit test |
| 2 | Site with `installed_capacity_mw=None` → `grid_export_capacity_mw=None` | Unit test |
| 3 | Quality flag set to `"low"` when GEM fallback is used | Unit test |
| 4 | `ns02_comment` mentions GEM source | Unit test |

### 15.2 FIX-02-B (ENTSO-E)

| # | Criterion | Verification |
|---|-----------|-------------|
| 5 | All acceptance criteria from S-13 §15 pass | S-13 test suite |
| 6 | Fuzzy match: "Rovinari" matches "Rovinari Group 3" (score >= 70) | Unit test |
| 7 | Fuzzy match: "Bełchatów" matches "Belchatow" after normalisation | Unit test |
| 8 | Matched units' capacity sum overwrites GEM fallback | Integration test |
| 9 | Unmatched site retains GEM fallback with quality upgraded to `"medium"` | Integration test |
| 10 | `rapidfuzz` installed and importable | Dependency check |

### 15.3 FIX-02-C (OSM Fixes)

| # | Criterion | Verification |
|---|-----------|-------------|
| 11 | `_parse_voltage_kv({"voltage": "400000;220000"})` → `400.0` | Unit test |
| 12 | `_parse_voltage_kv({"voltage": "invalid"})` → `None` | Unit test |
| 13 | Overpass query includes `relation["power"="substation"]` | Code inspection |
| 14 | Overpass query uses `out center geom` | Code inspection |
| 15 | `OsmElement` has `geometry` field | Code inspection |
| 16 | Line distance uses nearest-point when geometry available | Unit test |
| 17 | Line distance falls back to centroid when geometry absent | Unit test |

### 15.4 FIX-02-D (PyPSA-Eur)

| # | Criterion | Verification |
|---|-----------|-------------|
| 18 | `health_check()` returns `True` when CSV files exist | Unit test |
| 19 | `health_check()` returns `False` when CSV files missing | Unit test |
| 20 | Spatial join finds nearest bus for Tušimice (50.3928, 13.3278) | Integration test |
| 21 | Export capacity computed as `s_nom.sum() * 0.95` for connected lines | Unit test |
| 22 | No bus within `max_distance_km` → `PypsaEurResult.quality = "insufficient"` | Unit test |
| 23 | `CRITERION_IDS = ("NS-02",)` declared in `models.py` | Static test |

### 15.5 Pipeline Integration

| # | Criterion | Verification |
|---|-----------|-------------|
| 24 | Priority cascade: PyPSA-Eur > ENTSO-E match > ENTSO-E zone > GEM | Unit test |
| 25 | All NS-02 fields populated in `site_infrastructure_v2` after full pipeline run | Integration test |
| 26 | `ns02_quality` computed per §4.3 rules | Unit test |
| 27 | `ns02_comment` contains provenance for all contributing sources | Unit test |
| 28 | Batch enrichment commits per-site (failure isolation) | Integration test |
| 29 | Batch is resumable via `run_id` cache check | Integration test |
| 30 | `connectors/__init__.py` exports `EntsoEConnector` and `PypsaEurConnector` | Import test |
