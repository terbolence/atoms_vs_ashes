# FIX-01: Existing Controller Fixes & Expansions — Integration Specification

> **STATUS:** Specification complete — Implementation pending
> **Scope:** All five implemented controllers (I-1 through I-4, S-02) and their analysis wiring

**Source ID:** FIX-01
**Phase:** 1 (fixes) / 2–3 (expansions)
**Estimated effort:** 80 h (see §11 breakdown)
**Controllers affected:** I-1 CORINE, I-2 OSM Overpass, I-3 Population, I-4 GEM Coal Plant Tracker, S-02 EGDI Geology
**Criteria affected:** NH-13, NS-04, NS-05, NS-06, NS-07, NS-08, NS-10, NS-11, NS-13, EP-01, EP-03, RI-04, RI-05, RI-06, HI-01–HI-07

---

## 1. Purpose

This specification addresses three categories of work on the five already-implemented controllers:

1. **Interface compliance fixes** — bring I-1, I-2, I-3, I-4 into alignment with the project's connector interface pattern (§C2 of `experts/connectors/software_architect.md`), including `CRITERION_IDS`, `validate()`, `persist()`, settings integration, and DB-compatibility test coverage.
2. **Pipeline wiring fixes** — register orphaned analysis modules (`proximity_land.py`), correct criterion-ID labelling, fix persistence-model inconsistencies (RI-04 as `SiteAttribute`), and align `source_refs` provenance.
3. **Criterion coverage expansions** — add analysis modules and connector methods to serve the sub-criteria that the data source access plan assigns to these controllers but that are not yet implemented.

**Requirement:** EXT-01 (OSM Enhanced Queries, 40 h) and EXT-02 (GEM Enhanced Synergy, 8 h) from the data source access plan are **out of scope** for this specification. They are standalone Phase 3 extensions that add entirely new query families and synergy calculations. This specification covers everything *short of* those major expansions: the fixes, the wiring, and the criterion coverage that should already work given the existing connector capabilities.

---

## 2. Current State Assessment

### 2.1 Interface Compliance Audit

| Requirement | I-1 CORINE | I-2 OSM | I-3 Population | I-4 GEM Ingest | S-02 EGDI |
|-------------|:----------:|:-------:|:---------------:|:--------------:|:---------:|
| `CRITERION_IDS` constant | Missing | Missing | Missing | Missing | Present |
| `health_check()` | Present | Present | Present | N/A (not a class) | Present |
| `fetch(lat, lon)` | `fetch(bbox)` variant | `query()` + domain methods | Present | N/A | Present |
| `validate()` | Missing | Missing | Missing | N/A | Partial (in parsers) |
| `persist()` | Missing (in analysis/) | Missing (in analysis/) | Missing (in analysis/) | N/A (writes Site rows) | Present (in batch.py) |
| `close()` / context manager | Present | Present | Present | N/A | Present |
| Reads `settings._yaml` | Yes (corine config) | **No** (hardcoded default URL) | Yes (population config) | Uses `Settings.source_files` | Yes (egdi_geology config) |
| Structured logging | Partial (no event names) | Partial (no event names) | Partial (no event names) | Minimal | Full compliance |
| `DataSource` provenance | Missing | Missing | Missing | AuditLog only | Present |
| `DataQualityFlag` writes | Missing | Missing | Missing | Missing | Present |
| DB compat test coverage | **Not covered** | **Not covered** | **Not covered** | **Not covered** | Covered |

### 2.2 Criterion Coverage Audit

**Fact:** The data source access plan §2.1 assigns these criteria to the existing controllers:

| Controller | §2.1 Criteria Assigned | Currently Served | Gap |
|------------|----------------------|-----------------|-----|
| I-1 CORINE | NH-13, NS-05, NS-07, NS-08, EP-03 | NS-05 (orphaned) | NH-13, NS-07, NS-08, EP-03, plus NS-05 not wired |
| I-2 OSM | HI-01–HI-08, EP-01–EP-04, NS-02–NS-06, NS-08, NS-10, NS-13 | EP-01 (partial) | All except EP-01; EP-01 itself has labelling/methodology issues |
| I-3 Population | RI-04, RI-06, EP-01, NS-07 | RI-04 (screening only), RI-05 (attribute), EP-01 (via emergency_plan) | RI-04 not as SiteAttribute; RI-06, NS-07 missing |
| I-4 GEM | NS-05, NS-06, NS-10, NS-11 | Site rows only | NS-05, NS-06, NS-10, NS-11 all missing |
| S-02 EGDI | NH-02, NH-03, NH-04, NH-05, NH-06, RI-03 | All six | None (fully served) |

**Inference:** The §3.1–3.5 sub-criterion mapping shows that many of the "gap" criteria above are assigned to I-1/I-2/I-3/I-4 as **Priority 2 or Priority 3 (fallback)** sources, with new S-18+ connectors as Priority 1. The expansions in this spec should therefore be implemented as **fallback/supplement** analysis paths that can be superseded when the Priority 1 connectors arrive.

### 2.3 Wiring Defects

**Defect W-01:** `ProximityLandAnalysis` (`analysis/proximity_land.py`) is not imported or registered in `screening/__init__.py`. NS-05 `SiteAttribute` rows are never produced by the standard screening pipeline.

**Defect W-02:** `OverpassClient.__init__()` does not read `settings._yaml`. The `connectors.osm.overpass_url` config key exists in `config/default.yml` but is ignored when `OverpassClient` is instantiated directly (e.g., in `emergency_plan.py`).

**Defect W-03:** `EmergencyPlanCheck` uses sub-score labels `"EP-02"` through `"EP-05"` internally to name sub-components of the EP-01 composite score. These overlap with the actual criterion IDs EP-02 through EP-05 defined in the `criteria` table, creating a traceability conflict. When the plan's actual EP-02/EP-03/EP-04/EP-05 criteria are implemented as separate `SiteAttribute` rows, these labels will collide.

**Defect W-04:** `epz_population.py` stores RI-04 as `ScreeningResult` only, not as `SiteAttribute`. The project's data model expects `SiteAttribute` rows for all criteria to enable downstream scoring and ranking. RI-04 population density values (at all four radii) should also be persisted as a `SiteAttribute` with `value_json` containing the ring-by-ring breakdown.

**Defect W-05:** `EmergencyPlanCheck` uses `pop_result.total_population_80km` (population summed across all rings up to 80 km) as the denominator when scoring special-population density, but the OSM amenity queries use a 25 km EPZ radius. This means special-population density is computed against a population catchment 3.2× larger than the facility catchment, systematically underestimating the metric.

**Defect W-06:** `EmergencyPlanCheck.source_refs` records `"osm_overpass (roads, amenities, waterways)"` but omits the Population connector, which feeds the composite's EP-05 population sub-score. Provenance is incomplete.

**Defect W-07:** None of I-1, I-2, or I-3 write `DataSource` provenance records when their results are persisted. The `source_id` FK on `SiteAttribute` is left as `NULL` for all criteria served by these controllers.

**Defect W-08:** None of I-1, I-2, or I-3 write `DataQualityFlag` records when source data is missing, incomplete, or low-quality. Missing data is silently dropped or defaults to zero.

---

## 3. Fix Specifications

### 3.1 FIX-01-A: Interface Compliance — CRITERION_IDS Constants

**Requirement:** Every controller that produces `SiteAttribute` rows must expose a `CRITERION_IDS` tuple in a `models.py` file discoverable by `test_connector_db_compatibility.py`.

**Implementation:**

| Controller | File to create/modify | `CRITERION_IDS` value | Notes |
|-----------|----------------------|----------------------|-------|
| I-1 CORINE | `connectors/corine_models.py` or refactor to `connectors/corine/models.py` | `("NH-13", "NS-05", "NS-07", "NS-08", "EP-03")` | Full §2.1 assignment; implemented criteria will be a subset initially |
| I-2 OSM | `connectors/osm_models.py` or refactor to `connectors/osm/models.py` | See §3.1.1 below | Large set; only include criteria with implemented analysis modules |
| I-3 Population | `connectors/population_models.py` or refactor to `connectors/population/models.py` | `("RI-04", "RI-05", "RI-06")` | RI-06 added as expansion target |
| I-4 GEM | `ingest/models.py` | `("NS-05", "NS-06", "NS-10", "NS-11")` | These are §2.1 targets; EXT-02 scope excluded |

**Inference:** The DB compatibility test (`test_connector_db_compatibility.py`) scans `connectors/*/models.py` paths specifically. I-1, I-2, I-3 must either be refactored into package directories (like EGDI) or the test scanner must be extended to find `models.py` at non-package paths. The recommended approach is to **refactor I-1, I-2, and I-3 into package directories** consistent with the EGDI pattern. I-4 lives under `ingest/`, so its `CRITERION_IDS` requires extending the scanner.

#### 3.1.1 I-2 OSM CRITERION_IDS (phased)

The data source access plan assigns ~25 sub-criteria to I-2 OSM across HI, EP, NS, and RI families. The `CRITERION_IDS` constant should initially include only the criteria that have analysis modules wired:

- **Phase 1 (this spec):** `("EP-01", "HI-01", "HI-06", "HI-07", "NS-02", "NS-05")`
- **Phase 3 (EXT-01):** Expanded to full set when enhanced queries are implemented

### 3.2 FIX-01-B: OSM Settings Integration

**Requirement:** `OverpassClient` must read its configuration from `settings._yaml` via the standard pattern.

**Implementation:**

```python
class OverpassClient:
    def __init__(self, settings: Any | None = None, *, overpass_url: str | None = None) -> None:
        cfg: dict = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("osm", {})
        self._base_url = overpass_url or cfg.get("overpass_url", DEFAULT_OVERPASS_URL)
        self._timeout = cfg.get("timeout_s", DEFAULT_TIMEOUT)
        # ... rest of init
```

**Requirement:** All callers of `OverpassClient()` in `analysis/` modules must pass `settings` when available. `emergency_plan.py` must accept `settings` in its constructor and forward it to `OverpassClient`.

### 3.3 FIX-01-C: Register ProximityLandAnalysis in Screening Pipeline

**Requirement:** `screening/__init__.py` must import and register `ProximityLandAnalysis` so that NS-05 `SiteAttribute` rows are produced during standard screening runs.

**Implementation:**
- Add import of `ProximityLandAnalysis` to `screening/__init__.py`
- Wire it into the screening runner with the same pattern as `epz_population` and `emergency_plan`
- Ensure `ProximityLandAnalysis.assess_and_persist()` is called for each site during enrichment

### 3.4 FIX-01-D: EP-01 Sub-Score Label Collision

**Requirement:** Rename internal sub-score keys in `emergency_plan.py` to avoid collision with actual criterion IDs EP-02 through EP-05.

**Implementation:**

| Current Label | New Label | Rationale |
|--------------|-----------|-----------|
| `"EP-02"` (roads) | `"ep01_roads"` | Avoids collision with criterion EP-02 (Evacuation Routes) |
| `"EP-03"` (special populations) | `"ep01_special_pop"` | Avoids collision with criterion EP-03 (Physical Geography) |
| `"EP-04"` (geography) | `"ep01_geography"` | Avoids collision with criterion EP-04 (Special Populations) |
| `"EP-05"` (population) | `"ep01_population"` | Avoids collision with criterion EP-05 (Concurrent Hazard Impact) |

**Requirement:** Update `EP01SubScore` dataclass and all references. Existing `value_json` in the database from prior runs will have old keys; the code must handle both schemas during a transition period (read tolerance).

### 3.5 FIX-01-E: RI-04 Dual Persistence

**Requirement:** `epz_population.py` must persist RI-04 as both `ScreeningResult` (for pass/fail verdicts) and `SiteAttribute` (for ranking/scoring).

**Implementation:**

```python
# After the existing ScreeningResult merge for RI-04:
session.merge(
    SiteAttribute(
        site_id=site.site_id,
        criterion_id="RI-04",
        value_numeric=max_ring_density,  # densest ring value
        value_json={
            "ring_densities": {
                "5km": density_5,
                "16km": density_16,
                "25km": density_25,
                "80km": density_80,
            },
            "max_density_ring": max_ring_label,
            "max_density_value": max_ring_density,
            "verdict": verdict.value,
            "threshold_persons_per_km2": threshold,
        },
        run_id=run_id,
        cache_status="fresh",
    )
)
```

### 3.6 FIX-01-F: EP-01 Population Radius Consistency

**Requirement:** The special-population density calculation in `emergency_plan.py` must use a population denominator consistent with the EPZ radius used for OSM facility queries.

**Implementation:**
- Replace `pop_result.total_population_80km` with the population from the ring matching `epz_radius_km` (default 25 km)
- If the Population connector does not return a 25 km ring directly, interpolate from the nearest available rings
- Document the methodological choice in the `value_json` output

### 3.7 FIX-01-G: DataSource Provenance Records

**Requirement:** Every analysis module that persists `SiteAttribute` rows must also ensure a `DataSource` record exists and link it via `source_id`.

**Implementation:** Create a shared utility:

```python
# analysis/_provenance.py
def ensure_data_source(
    session: Session,
    name: str,
    url: str,
    description: str | None = None,
) -> uuid.UUID:
    """Ensure a DataSource row exists, return its source_id."""
    existing = session.query(DataSource).filter_by(name=name).first()
    if existing:
        existing.last_fetched = datetime.utcnow()
        return existing.source_id
    ds = DataSource(
        source_id=uuid.uuid4(),
        name=name,
        url=url,
        description=description,
        last_fetched=datetime.utcnow(),
    )
    session.add(ds)
    session.flush()
    return ds.source_id
```

Each analysis module must call this and set `source_id` on all `SiteAttribute` rows:

| Module | DataSource `name` | DataSource `url` |
|--------|-------------------|------------------|
| `proximity_land.py` | `"corine_clc2018_wfs"` | From `connectors.corine.wfs_url` config |
| `epz_population.py` | `"osm_overpass_population"` | From `connectors.population.overpass_url` or `connectors.osm.overpass_url` config |
| `emergency_plan.py` | `"osm_overpass_emergency"` | Same |

### 3.8 FIX-01-H: DataQualityFlag Writes

**Requirement:** Analysis modules must write `DataQualityFlag` records when:
- Source data is missing or empty (level: `insufficient`)
- Source data is partial or has known gaps (level: `low`)
- Source data covers only part of the analysis radius (level: `medium`)

**Implementation per module:**

| Module | Conditions triggering flags |
|--------|----------------------------|
| `proximity_land.py` | WFS returns 0 features for the buffer; Natura 2000 / WDPA check fails; CORINE coverage doesn't extend to full analysis radius |
| `epz_population.py` | Population connector returns 0 populated places; GeoNames fallback not configured; ring population is 0 for inner rings |
| `emergency_plan.py` | Road density query returns 0 ways; no hospitals/clinics within EPZ; waterway query fails |

### 3.9 FIX-01-I: Structured Logging Event Names

**Requirement:** All analysis modules and connectors must use structured log event names following the pattern `<source>_<action>`.

**Implementation:**

| Module | Events to add |
|--------|--------------|
| `corine.py` | `corine_fetch_ok`, `corine_fetch_error`, `corine_parse_error`, `corine_health_ok`, `corine_health_error` |
| `osm.py` | `osm_query_ok`, `osm_query_error`, `osm_health_ok`, `osm_health_error` |
| `population.py` | `population_fetch_ok`, `population_fetch_error`, `population_health_ok` |
| `proximity_land.py` | `proximity_land_assess_ok`, `proximity_land_assess_error`, `proximity_land_persist_ok` |
| `epz_population.py` | `epz_population_screen_ok`, `epz_population_screen_error`, `epz_population_persist_ok` |
| `emergency_plan.py` | `emergency_plan_assess_ok`, `emergency_plan_assess_error`, `emergency_plan_persist_ok` |

Each event must include `site_id`, `criterion_id`, `run_id`, and `elapsed_ms` in the structlog context.

---

## 4. Package Refactoring Specification

### 4.1 Rationale

**Fact:** S-02 EGDI is structured as a package directory (`connectors/egdi_geology/`) with separate `models.py`, `client.py`, `batch.py`, `parsers.py`. This is the only connector discoverable by `test_connector_db_compatibility.py`.

**Fact:** I-1, I-2, I-3 are single-file modules. Their lack of `models.py` means they are invisible to the DB compatibility scanner.

**Requirement:** Refactor I-1, I-2, I-3 into package directories to enable:
1. `CRITERION_IDS` discovery by the test scanner
2. Separation of connector logic, models/dataclasses, and batch/persistence logic
3. Consistent structure across all connectors

### 4.2 Target Directory Structure

```
connectors/
├── __init__.py                    # Updated exports
├── corine/                        # I-1 (was corine.py)
│   ├── __init__.py
│   ├── client.py                  # CorineConnector class
│   ├── models.py                  # CRITERION_IDS, SiteClassification, RingClassification
│   └── batch.py                   # persist logic (extracted from proximity_land.py)
├── osm/                           # I-2 (was osm.py)
│   ├── __init__.py
│   ├── client.py                  # OverpassClient class
│   ├── models.py                  # CRITERION_IDS, OsmElement, result dataclasses
│   └── batch.py                   # persist logic (new)
├── population/                    # I-3 (was population.py)
│   ├── __init__.py
│   ├── client.py                  # PopulationConnector class
│   ├── models.py                  # CRITERION_IDS, PopulatedPlace, RingPopulation, PopulationResult
│   └── batch.py                   # persist logic (extracted from epz_population.py)
├── egdi_geology/                  # S-02 (unchanged)
│   ├── __init__.py
│   ├── client.py
│   ├── models.py
│   ├── batch.py
│   └── parsers.py
└── seismic_hazard/                # S-01 (already structured)
    ├── __init__.py
    ├── client.py
    ├── models.py
    └── batch.py
```

### 4.3 Migration Strategy

1. Create package directory, move class into `client.py`, extract dataclasses into `models.py`
2. Add re-exports in package `__init__.py` to preserve backward compatibility:
   ```python
   from .client import CorineConnector
   from .models import CRITERION_IDS, SiteClassification, RingClassification
   ```
3. Update `connectors/__init__.py` imports
4. Update all callers in `analysis/` and `screening/`
5. Run full test suite to verify no import breakage

### 4.4 I-4 GEM Coal Plant Tracker — No Package Refactor

**Inference:** I-4 lives under `ingest/`, not `connectors/`. It is a procedural ingest module, not a connector class. Refactoring it into the connector pattern is not warranted at this stage. Instead:

1. Add `CRITERION_IDS` to a new `ingest/models.py` file
2. Extend `test_connector_db_compatibility.py` scanner to also check `ingest/models.py`
3. Create a new `analysis/coal_site_analysis.py` module for the criteria I-4 should serve

---

## 5. Criterion Expansion Specifications

These expansions add analysis logic for criteria that the existing connectors can already serve (data is fetchable) but that have no analysis module wired.

### 5.1 EXP-A: I-1 CORINE — NH-13 Wildfire Context (Fallback)

**Criterion:** NH-13 (Forest/Wildfire)
**Sub-criteria served:** NH-13b (combustible vegetation / WUI proxy)
**Role:** Priority 2 fallback — S-35 EFFIS+FIRMS (P1) and S-36 ESA WorldCover (P1) not yet implemented
**Evidence grade:** Ranking-grade (CORINE 100 m MMU is too coarse for screening-grade wildfire assessment)

**Implementation:**
- New analysis method `assess_wildfire_context()` in `analysis/proximity_land.py` or a new `analysis/wildfire_context.py`
- Use existing `CorineConnector.fetch()` to retrieve CORINE features within the analysis buffer
- Classify CLC codes into combustible vegetation categories:
  - **High combustibility:** 3.1.1 (Broad-leaved forest), 3.1.2 (Coniferous forest), 3.1.3 (Mixed forest), 3.2.2 (Moors and heathland), 3.2.4 (Transitional woodland-shrub)
  - **Medium combustibility:** 3.2.1 (Natural grasslands), 3.2.3 (Sclerophyllous vegetation), 2.4.3 (Land principally occupied by agriculture, with significant areas of natural vegetation)
  - **Low/none:** All other codes
- Compute percentage of buffer area in each combustibility class at EPZ radii (5, 16, 25 km)
- Derive Wildland-Urban Interface (WUI) proxy: intersection of residential CORINE classes (1.1.x) with combustible vegetation classes within 1 km
- Persist as `SiteAttribute(criterion_id="NH-13")` with `value_numeric` = max combustible percentage, `value_json` = ring-by-ring breakdown

**Limitation (Fact):** CORINE covers EU + EEA countries only. For 11 non-EU in-scope countries (UA, BY, MD, AM, TR, AL, BA, ME, XK, MK, RS), a `DataQualityFlag(level="insufficient")` must be written. S-36 ESA WorldCover will provide global coverage when implemented.

### 5.2 EXP-B: I-1 CORINE — NS-08 Ecological Sensitivity (Supplement)

**Criterion:** NS-08 (Ecological Sensitivity)
**Sub-criteria served:** NS-08d (habitat fragmentation proxy)
**Role:** Priority 2 — S-14 Natura 2000 (P1) and S-15 WDPA (P1) not yet implemented for NS-08a/b; CORINE provides land-cover-based fragmentation proxy

**Implementation:**
- New analysis method or module `analysis/ecological_sensitivity.py`
- Use `CorineConnector.fetch()` to retrieve features within 25 km buffer
- Compute landscape fragmentation metrics:
  - **Patch density:** number of distinct natural/semi-natural patches per km²
  - **Largest patch index:** area of largest contiguous natural patch / total buffer area
  - **Edge density:** total perimeter of natural patches / buffer area (m/ha)
- Natural/semi-natural = CLC codes 3.x.x and 4.x.x (forests, scrub, wetlands, water bodies)
- Persist as `SiteAttribute(criterion_id="NS-08")` with `value_json` containing fragmentation metrics

**Open Issue:** The `proximity_land.py` module already fetches Natura 2000 features via direct `httpx` calls. When S-14 is implemented as a proper connector, the Natura 2000 logic in `proximity_land.py` should be refactored to use it. Flag this as a technical debt item.

### 5.3 EXP-C: I-1 CORINE — NS-04 Land Cover Within Footprint

**Criterion:** NS-04 (Site Topography)
**Sub-criteria served:** NS-04c (land cover within footprint)
**Role:** Priority 1 (existing) — S-36 ESA WorldCover supplements for non-EU

**Implementation:**
- Use `CorineConnector.fetch()` at site footprint scale (buffer = max(site_area_ha converted to radius, 500 m))
- Classify land cover within the immediate footprint:
  - **Favourable:** Artificial (1.x.x — already disturbed), Arable (2.1.x), Pasture (2.3.x)
  - **Moderate:** Mixed agriculture (2.4.x), Natural grassland (3.2.1)
  - **Unfavourable:** Forest (3.1.x), Wetland (4.x.x), Water (5.x.x), Protected via cross-reference
- Compute dominant land cover class and percentage of unfavourable cover
- Persist as `SiteAttribute(criterion_id="NS-04")` with `value_json`

### 5.4 EXP-D: I-1 CORINE — NS-13 Laydown Area Proxy

**Criterion:** NS-13 (Construction Logistics)
**Sub-criteria served:** NS-13c (laydown area availability proxy)
**Role:** Priority 2 — I-2 OSM is P1 for NS-13 via EXT-01

**Implementation:**
- Use `CorineConnector.fetch()` within 5 km of site
- Identify contiguous areas of low-value land cover suitable for temporary construction facilities:
  - CLC 1.2.1 (Industrial/commercial), 1.3.1 (Mineral extraction), 1.3.3 (Construction sites), 1.4.2 (Sport/leisure), 2.1.x (Arable), 2.3.1 (Pastures)
- Compute total available area in hectares, largest contiguous patch
- Persist as `SiteAttribute(criterion_id="NS-13")` with `value_numeric` = total available ha

### 5.5 EXP-E: I-2 OSM — HI-01 Airport Proximity (Existing Capability)

**Criterion:** HI-01 (Aircraft Crash)
**Sub-criteria served:** HI-01a (distance to airports/heliports)
**Role:** Priority 2 fallback — S-39 OurAirports is P1; I-2 OSM is listed as P2

**Implementation:**
- New Overpass QL template in `OverpassClient`:
  ```
  fetch_airports(lat, lon, radius_km=80) -> list[OsmElement]
  ```
  Query: `node["aeroway"~"aerodrome|helipad"](around:{radius_m},{lat},{lon});`
  Plus: `way["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});`
- New analysis method in `analysis/aviation_hazard.py`:
  - Compute distance to nearest airport/helipad using `haversine_km`
  - Classify by airport type (international, regional, helipad) based on OSM tags (`iata`, `icao`, `aeroway` value)
  - Persist as `SiteAttribute(criterion_id="HI-01")`

### 5.6 EXP-F: I-2 OSM — HI-06 Military Proximity (Existing Tags)

**Criterion:** HI-06 (Military Installations)
**Sub-criteria served:** HI-06a (military area distance)
**Role:** Priority 1 — I-2 OSM is the primary source for this sub-criterion

**Implementation:**
- New Overpass QL template:
  ```
  fetch_military_areas(lat, lon, radius_km=25) -> list[OsmElement]
  ```
  Query: `way["landuse"="military"](around:{radius_m},{lat},{lon});` + `relation["landuse"="military"](...)` + `node["military"](...)` (captures bases, danger areas, ranges)
- Analysis: compute distance to nearest military installation, count within EPZ
- Persist as `SiteAttribute(criterion_id="HI-06")` with `value_numeric` = distance km, `value_json` = list of installations with types and distances

### 5.7 EXP-G: I-2 OSM — HI-07 Electromagnetic Interference (Existing Tags)

**Criterion:** HI-07 (Electromagnetic Interference)
**Sub-criteria served:** HI-07a (high-power transmitter proximity)
**Role:** Priority 1 — I-2 OSM is the primary source

**Implementation:**
- New Overpass QL template:
  ```
  fetch_transmitters(lat, lon, radius_km=25) -> list[OsmElement]
  ```
  Query: `node["man_made"~"mast|tower|antenna"](around:...)` + `node["tower:type"~"communication|transmission"](...)` + `way["power"="substation"]["substation"="transmission"](...)` (high-power sources)
- Analysis: compute distance to nearest transmitter, classify by type and estimated power
- Persist as `SiteAttribute(criterion_id="HI-07")`

### 5.8 EXP-H: I-2 OSM — NS-02 Grid Connection (Existing Power Tags)

**Criterion:** NS-02 (Grid Connection)
**Sub-criteria served:** NS-02a (HV line/substation distance)
**Role:** Priority 1 (existing) for NS-02a — S-13 ENTSO-E provides P1 for NS-02b/c

**Implementation:**
- New Overpass QL template (may already be partially available via existing queries):
  ```
  fetch_power_infrastructure(lat, lon, radius_km=50) -> list[OsmElement]
  ```
  Query: `way["power"="line"]["voltage"](around:...)` + `node["power"="substation"](around:...)` + `node["power"="plant"](around:...)`
- Filter by voltage level: ≥110 kV = HV, ≥220 kV = EHV, ≥400 kV = UHV
- Analysis: distance to nearest HV+ line, distance to nearest substation, voltage at nearest point
- Persist as `SiteAttribute(criterion_id="NS-02")` with `value_numeric` = distance to nearest HV substation km

### 5.9 EXP-I: I-3 Population — RI-06 Population Projections (Proxy)

**Criterion:** RI-06 (Population Projections)
**Sub-criteria served:** RI-06a (projected density trend 60y)
**Role:** Priority 3 fallback — S-20 GHSL (P1) and S-17 Eurostat (P2) not yet implemented

**Inference:** The Population connector cannot directly provide projections (OSM/GeoNames are snapshot-in-time). However, a proxy can be derived:

**Implementation:**
- New analysis module `analysis/population_projection.py`
- Use I-3 `PopulationConnector.fetch()` for current population rings
- Apply country-level growth rates from a static lookup table (UN WPP medium-variant projections embedded as a constant dict)
- Compute projected 2085 density at each ring as: `current_density × (1 + annual_growth_rate) ^ 60`
- Persist as `SiteAttribute(criterion_id="RI-06")` with `value_json` containing current, projected, growth rate, source = "UN WPP 2024 medium variant"
- Write `DataQualityFlag(level="low", detail="proxy projection from country-level growth rate, not spatial model")`

**Open Issue:** This is a crude proxy. S-20 GHSL (multi-epoch gridded) and S-17 Eurostat (sub-national projections) are far superior. The proxy should be clearly labelled as fallback-grade.

### 5.10 EXP-J: I-4 GEM — NS-05 Land Availability (Coal Site Reuse)

**Criterion:** NS-05 (Land Availability)
**Sub-criteria served:** NS-05a partial (contiguous land area at coal sites)
**Role:** Priority 2 supplement — I-2 OSM is listed as P1 for NS-05a

**Implementation:**
- New analysis module `analysis/coal_site_analysis.py`
- Query existing `Site` records where `plant_type IN ('coal', 'lignite')` and `status IN ('retired', 'mothballed', 'planned_closure')`
- For each coal site, use `site_area_ha` (from OSM boundary ingest) as the baseline land area
- Compare against SMR land requirement (`screening.smr_types[ref].land_ha` from config, default 72.8 ha)
- Derive a land sufficiency score: `available_area / required_area`
- Persist as `SiteAttribute(criterion_id="NS-05")` for the coal site, with `value_numeric` = sufficiency ratio

**Requirement:** This must not conflict with CORINE-based NS-05 from `proximity_land.py`. Use `source_id` to distinguish the two assessments. The CORINE assessment provides "adjacent developable land" while this provides "existing site footprint reuse."

### 5.11 EXP-K: I-2 OSM — NS-05 Contiguous Land (Existing Capability)

**Criterion:** NS-05 (Land Availability)
**Sub-criteria served:** NS-05a (contiguous land area >= SMR footprint)
**Role:** Priority 1 — I-2 OSM listed as P1 for NS-05a in §3.5

**Fact:** `ingest/osm_area.py` already fetches plant boundaries via Overpass and computes `site_area_ha`. `screening/land_area.py` uses this for BF-02. However, this is currently only for coal plant sites from the GEM tracker.

**Implementation:**
- Extend `osm_area.py` or create `analysis/land_availability.py` to assess land contiguity for any site (not just coal plants)
- For non-coal sites (supplementary sites), query OSM for `landuse` polygons around the site coordinates
- Identify the largest contiguous polygon of buildable land use (industrial, commercial, brownfield, farmland) containing or adjacent to the site point
- Persist as `SiteAttribute(criterion_id="NS-05")` with `value_numeric` = contiguous area ha

---

## 6. Analysis Module Wiring Updates

### 6.1 Screening Pipeline Registration

Update `screening/__init__.py` to register all analysis modules:

| Module | Registration Status | Action |
|--------|-------------------|--------|
| `epz_population` | Registered | No change |
| `emergency_plan` | Registered | No change |
| `proximity_land` | **Not registered** | Register (FIX-01-C) |
| `wildfire_context` | New (EXP-A) | Register |
| `ecological_sensitivity` | New (EXP-B) | Register |
| `aviation_hazard` | New (EXP-E) | Register |
| `military_proximity` | New (EXP-F) | Register |
| `transmitter_proximity` | New (EXP-G) | Register |
| `grid_proximity` | New (EXP-H) | Register |
| `population_projection` | New (EXP-I) | Register |
| `coal_site_analysis` | New (EXP-J) | Register |
| `land_availability` | New (EXP-K) | Register |

### 6.2 Enrichment Order

Analysis modules must execute in dependency order:

1. **Population** (`epz_population`) — provides RI-04, RI-05
2. **Land proximity** (`proximity_land`) — provides NS-05 (CORINE)
3. **Emergency plan** (`emergency_plan`) — provides EP-01 (depends on population)
4. **All others** — independent, can run in any order

---

## 7. Test Specifications

### 7.1 DB Compatibility Test Updates

**Requirement:** Extend `test_connector_db_compatibility.py` to:

1. **Scanner extension:** Add `ingest/models.py` to the scan path in `_connector_criterion_ids()`
2. **Parametrized tests:** Add test cases for I-1, I-2, I-3, I-4 `CRITERION_IDS`
3. **Live DB tests:** Add persist-path tests for the new analysis modules:
   - `test_corine_persist_succeeds` — verify NS-05, NH-13, NS-04, NS-08, NS-13 SiteAttribute creation
   - `test_osm_persist_succeeds` — verify EP-01, HI-01, HI-06, HI-07, NS-02, NS-05 creation
   - `test_population_persist_succeeds` — verify RI-04, RI-05, RI-06 creation
   - `test_coal_site_persist_succeeds` — verify NS-05 (coal reuse variant) creation

### 7.2 Unit Tests for New Analysis Modules

Each expansion (EXP-A through EXP-K) requires:

| Test file | Test scope |
|-----------|-----------|
| `tests/test_analysis_wildfire_context.py` | CLC code classification, combustibility percentages, WUI proxy, edge cases (no forest, 100% forest) |
| `tests/test_analysis_ecological_sensitivity.py` | Fragmentation metrics, patch counting, natural vs artificial classification |
| `tests/test_analysis_aviation_hazard.py` | Airport distance calculation, type classification, empty result handling |
| `tests/test_analysis_military_proximity.py` | Military area distance, tag parsing, no-results handling |
| `tests/test_analysis_transmitter_proximity.py` | Transmitter classification, distance calculation |
| `tests/test_analysis_grid_proximity.py` | HV line distance, voltage parsing, substation identification |
| `tests/test_analysis_population_projection.py` | Growth rate application, 60-year projection arithmetic, country lookup |
| `tests/test_analysis_coal_site.py` | Sufficiency ratio, status filtering, area comparison |
| `tests/test_analysis_land_availability.py` | Land contiguity assessment, buildable classification |

All tests must:
- Use mock/fixture data (no network calls)
- Test empty/missing response handling (verify `DataQualityFlag` creation)
- Test edge cases (site at country border, zero population, no features returned)
- Verify `SiteAttribute` row structure (criterion_id, value_json schema)

### 7.3 Integration Test Updates

Update existing test files:

| Test file | Changes |
|-----------|---------|
| `tests/test_analysis_proximity_land.py` | Add test for pipeline registration; verify NS-05 SiteAttribute is produced when run from screening pipeline |
| `tests/test_analysis_epz_population.py` | Add assertion that RI-04 SiteAttribute is created (not just ScreeningResult); verify value_json schema |
| `tests/test_analysis_emergency_plan.py` | Verify sub-score labels are `ep01_*` (not `EP-0x`); verify source_refs includes population connector |

---

## 8. Configuration Updates

### 8.1 `config/default.yml` Additions

```yaml
connectors:
  osm:
    overpass_url: "https://overpass-api.de/api/interpreter"
    timeout_s: 120
    inter_request_delay_s: 1.0
    max_retries: 3

  # Existing corine block — add cache_ttl_days:
  corine:
    wfs_url: "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WFSServer"
    layer_name: "Corine:CLC18_WM"
    timeout_s: 30
    cache_ttl_days: 180

  # Existing population block — add timeout:
  population:
    geonames_username: null  # Set via GEONAMES_USERNAME env var
    overpass_url: "https://overpass-api.de/api/interpreter"
    timeout_s: 120
    cache_ttl_days: 30

analysis:
  wildfire_context:
    buffer_radii_km: [5, 16, 25]
    high_combustibility_clc: ["311", "312", "313", "322", "324"]
    medium_combustibility_clc: ["321", "323", "243"]
  aviation_hazard:
    search_radius_km: 80
    airport_classification:
      international_tags: ["iata"]
      regional_tags: ["icao"]
  military_proximity:
    search_radius_km: 25
  transmitter_proximity:
    search_radius_km: 25
  grid_proximity:
    search_radius_km: 50
    min_voltage_kv: 110
  population_projection:
    projection_horizon_years: 60
    # UN WPP 2024 medium variant — country-level annual growth rates
    # Embedded in code as constant; override here if needed
  coal_site_analysis:
    min_status: ["retired", "mothballed", "planned_closure"]
    smr_reference: "voygr6"
```

### 8.2 No New Alembic Migrations Required

**Fact:** All criterion IDs used by the expansions (NH-13, NS-04, NS-05, NS-08, NS-13, HI-01, HI-06, HI-07, NS-02, RI-04, RI-05, RI-06, EP-01) are already seeded in migrations 002–005. No new Alembic migration is needed.

---

## 9. Data Flow Diagrams

### 9.1 I-1 CORINE — Current vs Target

```
CURRENT:
  CorineConnector.fetch() → SiteClassification
      ↓
  proximity_land.py → SiteAttribute(NS-05) [ORPHANED — not wired]

TARGET:
  CorineConnector.fetch() → SiteClassification
      ↓
  proximity_land.py ─────→ SiteAttribute(NS-05) + DataSource + DataQualityFlag
  wildfire_context.py ───→ SiteAttribute(NH-13) + DataSource + DataQualityFlag
  ecological_sensitivity.py → SiteAttribute(NS-08) + DataQualityFlag
  site_topography.py ────→ SiteAttribute(NS-04)
  laydown_area.py ───────→ SiteAttribute(NS-13)
      ↓
  All registered in screening/__init__.py
```

### 9.2 I-2 OSM — Current vs Target

```
CURRENT:
  OverpassClient.query() → OsmElement[]
      ↓
  emergency_plan.py → SiteAttribute(EP-01) [partial, label collision]

TARGET:
  OverpassClient(settings=settings).query() → OsmElement[]
      ↓
  emergency_plan.py ─────→ SiteAttribute(EP-01) [labels fixed, provenance added]
  aviation_hazard.py ────→ SiteAttribute(HI-01)
  military_proximity.py ─→ SiteAttribute(HI-06)
  transmitter_proximity.py → SiteAttribute(HI-07)
  grid_proximity.py ─────→ SiteAttribute(NS-02)
  land_availability.py ──→ SiteAttribute(NS-05)
      ↓
  All with DataSource + DataQualityFlag
```

### 9.3 I-3 Population — Current vs Target

```
CURRENT:
  PopulationConnector.fetch() → PopulationResult
      ↓
  epz_population.py → ScreeningResult(RI-04) + SiteAttribute(RI-05)

TARGET:
  PopulationConnector.fetch() → PopulationResult
      ↓
  epz_population.py ─────→ ScreeningResult(RI-04) + SiteAttribute(RI-04) + SiteAttribute(RI-05)
  population_projection.py → SiteAttribute(RI-06) [proxy, low quality]
      ↓
  All with DataSource + DataQualityFlag
```

---

## 10. S-02 EGDI — Assessment

**Fact:** EGDI is the most complete implementation. It follows the package pattern, has `CRITERION_IDS`, has `batch.py` with `_persist_result`, writes `DataSource` and `DataQualityFlag` records, and passes DB compatibility tests.

**Requirement:** No structural fixes needed. Minor improvements:

| Item | Current | Recommended |
|------|---------|-------------|
| Structured log event names | Present and compliant | No change |
| `validate()` method | In `parsers.py`, not on connector class | **Low priority:** consider adding `validate()` delegation on `EgdiGeologyConnector` for interface completeness |
| Criterion coverage | NH-02, NH-03, NH-04, NH-05, NH-06, RI-03 | Fully aligned with §2.1 — no expansion needed |
| Non-EU coverage | EGDI covers EU/EEA primarily | `DataQualityFlag(level="insufficient")` for non-EU sites — verify this is implemented |

---

## 11. Effort Estimates

### 11.1 Fixes (Priority 1 — must be done before any new connectors)

| ID | Task | Effort | Dependencies |
|----|------|--------|-------------|
| FIX-01-A | CRITERION_IDS + package refactoring (I-1, I-2, I-3) | 8 h | None |
| FIX-01-B | OSM settings integration | 2 h | FIX-01-A |
| FIX-01-C | Register ProximityLandAnalysis | 1 h | None |
| FIX-01-D | EP-01 sub-score label collision | 3 h | None |
| FIX-01-E | RI-04 dual persistence | 2 h | None |
| FIX-01-F | EP-01 population radius consistency | 2 h | None |
| FIX-01-G | DataSource provenance records | 4 h | FIX-01-A |
| FIX-01-H | DataQualityFlag writes | 4 h | FIX-01-G |
| FIX-01-I | Structured logging event names | 3 h | None |
| | **Fix subtotal** | **29 h** | |

### 11.2 Expansions (Priority 2 — after fixes, before Phase 2 connectors)

| ID | Task | Effort | Dependencies |
|----|------|--------|-------------|
| EXP-A | NH-13 wildfire context (CORINE) | 4 h | FIX-01-A, FIX-01-C |
| EXP-B | NS-08 ecological sensitivity (CORINE) | 4 h | FIX-01-A |
| EXP-C | NS-04 land cover within footprint | 3 h | FIX-01-A |
| EXP-D | NS-13 laydown area proxy | 3 h | FIX-01-A |
| EXP-E | HI-01 airport proximity (OSM) | 4 h | FIX-01-A, FIX-01-B |
| EXP-F | HI-06 military proximity (OSM) | 3 h | FIX-01-A, FIX-01-B |
| EXP-G | HI-07 transmitter proximity (OSM) | 3 h | FIX-01-A, FIX-01-B |
| EXP-H | NS-02 grid connection (OSM) | 4 h | FIX-01-A, FIX-01-B |
| EXP-I | RI-06 population projection proxy | 4 h | FIX-01-A, FIX-01-E |
| EXP-J | NS-05 coal site reuse (GEM) | 3 h | None |
| EXP-K | NS-05 contiguous land (OSM) | 4 h | FIX-01-A, FIX-01-B |
| | **Expansion subtotal** | **39 h** | |

### 11.3 Testing (included in estimates above, broken out for visibility)

| Task | Effort (within estimates above) |
|------|--------------------------------|
| DB compat test scanner extension | 2 h (in FIX-01-A) |
| Fix regression tests | 3 h (across fixes) |
| Expansion unit tests | 7 h (across expansions) |
| Integration test updates | 3 h |
| | **Test subtotal: ~15 h** |

### 11.4 Total

| Category | Hours |
|----------|-------|
| Fixes | 29 h |
| Expansions | 39 h |
| **Total** | **68 h** |
| Contingency (15%) | 10 h |
| **Grand total** | **~80 h** |

---

## 12. Implementation Order

**Constraint:** Fixes must be completed before expansions. Within each category, order by dependency.

### Phase 1a: Interface & Wiring Fixes (Sprint 1)

1. FIX-01-A — Package refactoring + CRITERION_IDS (8 h)
2. FIX-01-B — OSM settings integration (2 h) — depends on A
3. FIX-01-C — Register ProximityLandAnalysis (1 h)
4. FIX-01-D — EP-01 label collision (3 h)
5. FIX-01-E — RI-04 dual persistence (2 h)
6. FIX-01-F — EP-01 population radius (2 h)

### Phase 1b: Provenance & Observability Fixes (Sprint 1 continued)

7. FIX-01-G — DataSource provenance (4 h) — depends on A
8. FIX-01-H — DataQualityFlag writes (4 h) — depends on G
9. FIX-01-I — Structured logging (3 h)

### Phase 2a: CORINE Expansions (Sprint 2)

10. EXP-A — NH-13 wildfire context (4 h)
11. EXP-B — NS-08 ecological sensitivity (4 h)
12. EXP-C — NS-04 land cover (3 h)
13. EXP-D — NS-13 laydown area (3 h)

### Phase 2b: OSM Expansions (Sprint 2 continued)

14. EXP-E — HI-01 airport proximity (4 h)
15. EXP-F — HI-06 military proximity (3 h)
16. EXP-G — HI-07 transmitter proximity (3 h)
17. EXP-H — NS-02 grid connection (4 h)
18. EXP-K — NS-05 contiguous land (4 h)

### Phase 2c: Population & GEM Expansions (Sprint 3)

19. EXP-I — RI-06 population projection (4 h)
20. EXP-J — NS-05 coal site reuse (3 h)

---

## 13. Acceptance Criteria

### 13.1 Fix Acceptance

| # | Criterion | Verification |
|---|-----------|-------------|
| A1 | All five controllers have `CRITERION_IDS` discoverable by DB compat test | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` passes |
| A2 | `OverpassClient` reads config from `settings._yaml` | Unit test: instantiate with mock settings, verify URL override |
| A3 | NS-05 `SiteAttribute` rows appear after standard screening run | Integration test: run screening pipeline against test site, query `site_attributes WHERE criterion_id='NS-05'` |
| A4 | EP-01 sub-scores use `ep01_*` prefix | Unit test: parse `value_json`, assert no keys matching `^EP-0[2-5]$` |
| A5 | RI-04 has both `ScreeningResult` and `SiteAttribute` | Integration test: query both tables for same `site_id + run_id` |
| A6 | EP-01 special-pop density uses consistent EPZ radius | Unit test: verify denominator matches `epz_radius_km` config |
| A7 | All `SiteAttribute` rows have non-null `source_id` | DB query: `SELECT COUNT(*) FROM site_attributes WHERE source_id IS NULL AND run_id = :test_run` = 0 |
| A8 | `DataQualityFlag` rows exist for missing-data scenarios | Unit test: feed empty response to each analysis module, assert flag creation |
| A9 | All connectors emit structured log events | Unit test: capture structlog output, verify event names match `<source>_<action>` pattern |

### 13.2 Expansion Acceptance

| # | Criterion | Verification |
|---|-----------|-------------|
| B1 | NH-13 `SiteAttribute` from CORINE contains combustibility percentages | Unit test: mock CORINE features with known CLC codes, verify classification |
| B2 | NS-08 `SiteAttribute` contains fragmentation metrics | Unit test: mock natural vs artificial patches, verify patch density calculation |
| B3 | HI-01, HI-06, HI-07, NS-02 `SiteAttribute` rows contain distance values | Unit test: mock OSM elements at known coordinates, verify haversine distance |
| B4 | RI-06 `SiteAttribute` contains projection and `DataQualityFlag(level="low")` | Unit test: verify 60-year projection arithmetic and flag creation |
| B5 | NS-05 from coal site analysis and from CORINE are distinguishable by `source_id` | DB query: two distinct `source_id` values for NS-05 on a coal site |
| B6 | All new analysis modules are registered in screening pipeline | Integration test: run enrichment, verify all expected `criterion_id` values appear |
| B7 | Non-EU sites receive `DataQualityFlag(level="insufficient")` for CORINE-dependent criteria | Unit test: site at lat/lon in Turkey, verify flag |

---

## 14. Risks and Open Issues

| # | Risk / Issue | Mitigation |
|---|-------------|-----------|
| 1 | Package refactoring (FIX-01-A) breaks existing imports across the codebase | Provide backward-compatible re-exports in package `__init__.py`; run full test suite after refactoring |
| 2 | EP-01 label rename (FIX-01-D) breaks existing `value_json` in production database | Add read-tolerance for old key format; document migration path for existing data |
| 3 | CORINE WFS availability is intermittent (EEA service outages) | Existing retry logic in `CorineConnector`; DataQualityFlag for fetch failures |
| 4 | OSM data quality varies by country (military, transmitter, grid tags are sparse in some regions) | DataQualityFlag with level based on feature count; document known gaps per country |
| 5 | Population projection proxy (EXP-I) is very crude | Clearly mark as fallback-grade; low DataQualityFlag; will be superseded by S-20 GHSL and S-17 Eurostat |
| 6 | `proximity_land.py` contains embedded Natura 2000 and WDPA HTTP calls that will duplicate S-14/S-15 connectors | Flag as tech debt; refactor to use S-14/S-15 when those connectors are implemented |
| 7 | I-4 GEM ingest is not a connector class; adding `CRITERION_IDS` to `ingest/models.py` requires DB-compat test scanner extension | Extend scanner; document the pattern for future non-connector persistence modules |

---

## 15. Relationship to Other Specifications

| Spec | Relationship |
|------|-------------|
| **EXT-01** (I-2 OSM Enhanced Queries) | This spec (FIX-01) prepares the OSM connector for EXT-01 by refactoring to package structure, adding settings integration, and fixing the EP-01 foundation. EXT-01 adds ~12 new sub-criteria query families on top. |
| **EXT-02** (I-4 GEM Enhanced Synergy) | This spec adds the `coal_site_analysis.py` foundation. EXT-02 adds synergy scoring and infrastructure reuse assessment. |
| **S-14** (Natura 2000 WFS) | NS-08 expansion (EXP-B) is a CORINE-based fallback; S-14 will provide authoritative Natura 2000 data. Refactor `proximity_land.py` embedded Natura calls when S-14 is implemented. |
| **S-20** (GHSL GHS-POP) | RI-04 (dual persistence fix) and RI-06 (proxy expansion) will be superseded by GHSL's 100 m gridded population. The `SiteAttribute` schema is designed to accommodate both sources. |
| **S-36** (ESA WorldCover) | NH-13, NS-04, NS-08, NS-13 expansions provide EU-only coverage via CORINE. S-36 provides global 10 m land cover for non-EU countries. |
| **S-39** (OurAirports) | HI-01 expansion (EXP-E) uses OSM as Priority 2. S-39 provides authoritative airport data as Priority 1. |
| **DRV-02** (EP Composite Scoring) | EP-01 fixes (FIX-01-D/F) clean up the foundation that DRV-02 will replace with a multi-layer composite. |

---

## 16. Glossary

| Term | Definition |
|------|-----------|
| **Controller** | Generic term for any implemented data access module (connector class or ingest function) |
| **Connector** | A class following the project's connector interface pattern (§C2) |
| **Analysis module** | A module under `analysis/` that consumes connector outputs and persists `SiteAttribute`/`ScreeningResult` rows |
| **Wiring** | The registration and invocation of analysis modules from the screening pipeline |
| **Fallback-grade** | Data or analysis that serves as a placeholder until a higher-quality source is implemented |
| **Priority N source** | The Nth-preferred data source for a sub-criterion, as assigned in `Data Source Access Plan/criterion_family_mapping.md` §3.x |
