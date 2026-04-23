# S-08: EU Flood Risk Maps (Floods Directive) — Integration Specification

**Source ID:** S-08
**Phase:** 1 — Exclusionary Screening
**Estimated effort:** 20 h
**Criteria served:** NH-08 (storm surge — Priority 1; tsunami — Priority 1), NH-09 (overtopping — Priority 1; ice hazard — Priority 2 fallback), EP-05 (concurrent hazard impact — supplementary)
**Connector slug:** `eu_flood_risk`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | EU Flood Risk Maps — JRC/GloFAS Global River Flood Hazard Maps + EEA Floods Directive Reference Spatial Datasets + EFAS |
| Providers | (1) European Commission, Joint Research Centre (JRC) / Copernicus Emergency Management Service — GloFAS flood hazard maps; (2) European Environment Agency (EEA) — Floods Directive reporting datasets (APSFR, UoM); (3) EFAS — European Flood Awareness System, operated by ECMWF; (4) EU Member States — national INSPIRE-compliant WMS/WFS services under Directive 2007/60/EC |
| URLs | JRC GloFAS flood hazard tiles: `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/`; EEA datahub: `https://www.eea.europa.eu/en/datahub/datahubitem-view/9b7b6eb4-ac38-40a8-bb91-7c92da523bc9`; EEA GeoPackage: `https://sdi.eea.europa.eu/webdav/datastore/public/eea_v_4326_100_k_floods-ref-data-under-fd_p_2011-now_v03_r00/`; APSFR WMS: `https://water.discomap.eea.europa.eu/arcgis/services/FloodsDirective/`; EFAS WMS-T: `https://european-flood.emergency.copernicus.eu/api/wms/`; Tile extents: `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/tile_extents.geojson` |
| Protocol | JRC GloFAS: HTTPS file download (GeoTIFF tiles); EEA APSFR: HTTPS download (GeoPackage) + ArcGIS REST/WMS; EFAS: WMS-T (OGC); National services: INSPIRE WMS/WFS (per-country, fragmented) |
| Auth | JRC GloFAS tiles: **none required** (open access). EEA datasets: **none required** (open access). EFAS archived (> 30 days): free via CDS with ECMWF account. EFAS real-time: restricted to partners. National INSPIRE: generally none, varies by country. |
| Formats | JRC GloFAS: GeoTIFF (32-bit float, water depth in metres; classified raster in categories 1–4). EEA: GeoPackage (vector polygons). EFAS: WMS tiles, GRIB2/NetCDF-4 (via CDS). National: WMS tiles, WFS GeoJSON, Shapefiles. |
| Spatial coverage | JRC GloFAS: **Global** at ~90 m resolution (3 arc seconds). Covers all 23 in-scope countries including non-EU (TR, UA, BY, AM, BA, RS, ME, XK, AL, MK, MD). EEA APSFR: EU Member States + EEA countries only (16 of 23 in-scope countries). National INSPIRE: EU members only. |
| Temporal coverage | JRC GloFAS: static hazard maps (statistical return periods). EEA APSFR: 2011–present (reporting cycles 1 and 2). EFAS: operational forecasts since 2012. National maps: updated every 6 years per Directive 2007/60/EC cycle (Cycle 1: 2013, Cycle 2: 2019, Cycle 3: 2025). |
| Update cadence | JRC GloFAS: version 2.1.2 (January 2026); updated irregularly. EEA APSFR: version 3.0 (March 2025); updated per Directive reporting cycle (~6 years). EFAS operational: twice daily. |
| License | JRC GloFAS: free and open Copernicus product, no restrictions. EEA: CC-BY 4.0. EFAS: Copernicus licence (EU Regulation 2021/696). National data: varies by country; generally open access for INSPIRE-mandated layers. |
| IAEA references | SSG-18 §4.42–4.60 (flooding evaluation); SSG-35 §A.19–A.30 (coastal and river flooding); NS-R-3 §3.23–3.27 (external flooding); NS-G-3.5 (flood hazard assessment); SSR-1 §5.24 (concurrent external events) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **JRC/GloFAS flood hazard GeoTIFFs — raster point sampling** | **Preferred (river flooding)** | High | Download GeoTIFF tiles covering the project region. For each site, sample flood water depth at 7 return periods (10, 20, 50, 75, 100, 200, 500 yr). ~90 m resolution. **Global coverage** — covers all 23 countries. Provides quantitative flood depth, not just binary hazard/no-hazard. |
| **EEA APSFR GeoPackage — vector intersection** | **Preferred (complementary)** | High | Download GeoPackage once. Check if each site falls within a designated Area of Potential Significant Flood Risk. Provides regulatory classification (high/medium/low probability) and flood source type. EU countries only — gap for TR, UA, BY, AM, BA, RS, ME, XK, AL, MK, MD. |
| **EFAS WMS-T — point query** | **Fallback (validation)** | Medium | WMS GetFeatureInfo at site location for EFAS flood awareness layers. Useful for current conditions and recent event context but not for return-period hazard assessment. Archived data (> 30 days) freely accessible; real-time restricted. |
| **National INSPIRE WMS/WFS** | **Rejected (for core connector)** | Low | Highly fragmented — each of 23+ countries has different endpoints, schemas, data models, and quality. Many only provide WMS (visual tiles without queryable attributes). Non-EU countries have no INSPIRE obligation. Deferred to N-06 (national flood authorities) in Phase 4. |
| **EFAS via CDS/EWDS (GRIB2/NetCDF)** | **Rejected (for this connector)** | Low | CDS provides operational flood forecast data, not static hazard maps. Queue-based access (same as S-04 CDS/ERA5). Forecast data is useful for validation but not for site-level hazard characterisation with return periods. |

### 2.2 Multi-source architecture

**Requirement:** The connector integrates two primary data sources, each serving distinct but complementary roles:

| Module | Data source | Criteria served | What it provides | Coverage |
|--------|------------|----------------|-----------------|----------|
| **Raster** | JRC/GloFAS flood hazard GeoTIFFs | NH-08 (partial), NH-09, EP-05 | Quantitative flood water depth at 7 return periods | Global (all 23 countries) |
| **Vector** | EEA APSFR GeoPackage | NH-08, NH-09, EP-05 | Regulatory flood risk designation (binary: in/out of APSFR) with probability scenario and source type | EU countries only (16 of 23) |

**Inference:** The JRC/GloFAS maps cover **riverine flooding only** — they do not include pluvial (rainfall), coastal (storm surge, tsunami), or groundwater flooding. The EEA APSFR dataset includes coastal and pluvial flood risk designations where member states have reported them. For NH-08 (coastal flooding sub-criteria), the EEA vector data provides the primary evidence; for NH-09 (river flooding), the JRC raster data provides quantitative depth.

**Fact:** The JRC/GloFAS README states: "The maps include inundation depth information and do not account for pluvial or coastal flooding." This is a critical limitation for NH-08 coastal sub-criteria.

### 2.3 JRC/GloFAS tile system

**Fact:** The JRC GloFAS flood hazard maps are organised in 271 tiles per return period. Tiles are GeoTIFF files at ~90 m resolution (3 arc seconds). The tile grid is documented in `tile_extents.geojson` (88 KB). Each return period folder (RP10, RP20, RP50, RP75, RP100, RP200, RP500) contains:
- `<tile_id>_depth.tif` — raw flood water depth in metres (float32)
- `<tile_id>_depth_reclass.tif` — classified depth (1: <1 m, 2: 1–<3 m, 3: 3–<10 m, 4: >10 m)

Additionally:
- `Permanent_WaterBodies/` — permanent water body masks (to distinguish permanent inundation from flood hazard)
- `Spurious_Depths/` — areas where modelling artefacts produce unrealistically high depths

**Requirement:** The connector must:
1. Download `tile_extents.geojson` to identify which tiles cover each site
2. Download only the tiles covering the 23-country bounding box (not all 271 global tiles)
3. For each site, identify the covering tile and sample flood depth at the 7 return periods
4. Also sample the permanent water body and spurious depth masks to flag unreliable values

### 2.4 EEA APSFR dataset

**Fact:** The EEA Floods Reference Spatial Dataset (version 3.0, March 2025) contains:
- **Areas of Potential Significant Flood Risk (APSFR)**: vector polygons designating flood-prone areas
- **Units of Management (UoM)**: administrative units responsible for flood risk management

The APSFR layer includes attributes for flood probability scenario (high, medium, low) and source type (river, coastal, pluvial, other). Available as GeoPackage download (~500 MB) from `https://sdi.eea.europa.eu/webdav/datastore/public/eea_v_4326_100_k_floods-ref-data-under-fd_p_2011-now_v03_r00/`.

**Requirement:** The connector must:
1. Download the APSFR GeoPackage once (cached locally)
2. Build a spatial index of APSFR polygons for the 23-country bounding box
3. For each site, determine if the site falls within any APSFR polygon
4. If within an APSFR, extract: probability scenario, source type, member state

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source module | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **NH-08** | Storm surge | Indirect (proxy) | `in_coastal_apsfr`, `coastal_apsfr_probability`, `coastal_distance_km` | Screening | Vector (APSFR) | **Fact:** JRC/GloFAS does not model coastal flooding. The EEA APSFR includes coastal flood risk areas where member states reported them. Coverage is EU-only and depends on national reporting quality. For non-EU countries (TR, UA, BY, AM, etc.), coastal flood assessment falls back to S-09 GFMS or N-05 national marine agencies. |
| **NH-08** | Tsunami | Indirect (proxy) | `in_coastal_apsfr`, `apsfr_source_types` | Screening (weak) | Vector (APSFR) | **Inference:** The Floods Directive does not explicitly mandate tsunami mapping, but some coastal member states include tsunami risk in their APSFR designations. This is a weak proxy. Dedicated tsunami hazard assessment requires additional sources (NEAMTHWS, national tsunami agencies). Flag evidence grade accordingly. |
| **NH-09** | Overtopping (river flooding) | Direct (primary) | `flood_depth_rp10_m`, `flood_depth_rp50_m`, `flood_depth_rp100_m`, `flood_depth_rp500_m`, `max_depth_m`, `flood_return_period_threshold`, `in_river_apsfr` | Screening + Ranking | Raster (GloFAS) + Vector (APSFR) | **Fact:** S-08 is the Priority 1 source for NH-09 overtopping. JRC/GloFAS provides flood depth at 7 return periods. A site with `flood_depth_rp100_m > 0` is within the modelled 100-year floodplain. APSFR provides complementary regulatory designation. |
| **NH-09** | Ice hazard | Indirect (proxy) | `in_apsfr`, `apsfr_source_types` | Ranking (weak) | Vector (APSFR) | **Fact:** Ice jam flooding is not separately modelled in JRC/GloFAS. Some national reports include ice hazard under river flooding. S-08 provides only a weak proxy; Priority 1 for ice hazard is N-03 national hydrological services (Phase 4). |
| **EP-05** | Concurrent hazard impact | Indirect (derived) | `flood_exposure_class`, `concurrent_flood_risk` | Ranking | Both | **Inference:** EP-05 concurrent hazard uses flood data from S-08 overlaid with infrastructure data (roads, bridges, power from I-2 OSM and S-12 SEVESO) to assess whether flooding degrades emergency response capability. The connector provides the flood component; the derived layer is computed in Phase 3. |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| E8 | NH-08 / NH-09 | Site within JRC 100-year floodplain with depth > 0.5 m | Exclude — site is within a flood hazard zone requiring structural protection beyond SMR design basis |
| A14 | NH-08 / NH-09 | Site within JRC 500-year floodplain (depth > 0) | Avoidance — site requires detailed flood hazard assessment to demonstrate adequate margins |
| A15 | NH-08 / NH-09 | Site within any EEA APSFR (high or medium probability) | Avoidance — regulatory designation of significant flood risk |
| — | NH-09 | Flood depth ranking | Lower depth at each return period scores better |

**Fact:** IAEA SSG-18 §4.51 requires that the design basis flood be assessed at return periods exceeding 10,000 years. The JRC/GloFAS maps extend only to 500-year return periods. This connector provides **screening-grade and ranking-grade** evidence, not characterization-grade. Detailed flood modelling for specific sites requires national hydrological data (N-06) and site-specific hydraulic studies (Stage 3+).

**Requirement:** The connector persists flood depth and regulatory designation data. Exclusionary decisions (E8, A14, A15) reside in the `screening/` module.

---

## 4. Regional Applicability

### 4.1 JRC/GloFAS coverage

| Country group | Countries | Coverage | Resolution | Notes |
|---------------|-----------|----------|------------|-------|
| All 23 in-scope | PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, LV, LT, AM, TR | **Complete** | ~90 m | JRC/GloFAS v2.1.2 covers the globe. All 23 countries are covered. River basins > 150 km² upstream area are modelled. |

**Fact:** GloFAS flood hazard maps model rivers with catchment areas > 150 km². Smaller streams and urban drainage systems are not represented. Sites near small rivers may show zero flood depth despite local flood risk.

### 4.2 EEA APSFR coverage

| Country group | Countries | Coverage | Notes |
|---------------|-----------|----------|-------|
| EU members | PL, CZ, SK, HU, AT, SI, HR, BG, RO, EE, LV, LT | **Complete** | Mandatory reporting under Directive 2007/60/EC. |
| EU candidates / EEA | BA, RS, ME, XK, AL, MK | **Partial to None** | Not required to report under Floods Directive. Some candidate countries voluntarily align with EU acquis. Coverage varies; XK likely absent. |
| Non-EU / non-EEA | TR, UA, BY, MD, AM | **None** | Outside Floods Directive scope. No APSFR data available from EEA. |

**Requirement:** For the 7 non-EU countries (TR, UA, BY, MD, AM, and potentially BA, RS, ME, XK, AL, MK), the connector must:
1. Use JRC/GloFAS raster data (available globally) as the primary flood hazard source
2. Write quality flag `medium` noting that regulatory APSFR designation is unavailable
3. Flag that coastal flood hazard data (NH-08) is incomplete for these countries from this source

### 4.3 Cross-border effects

**Inference:** River systems cross national borders (e.g., Danube, Tisa, Drin). The JRC/GloFAS raster data is boundary-agnostic — flood modelling follows hydrological basins, not political boundaries. The EEA APSFR data may show discontinuities at borders between countries with different reporting quality.

**Requirement:** Use JRC/GloFAS as the primary quantitative layer (continuous across borders). Use EEA APSFR as supplementary regulatory context only.

---

## 5. Integration Design

### 5.1 Component architecture

```
EuFloodRiskConnector
│
│  ── Data ingestion (run once per batch, cached) ──────────────────
├── __init__(settings)               # config from connectors.eu_flood_risk
├── health_check()                   # verify JRC FTP reachable + EEA download URL
├── _load_tile_index()
│     # download tile_extents.geojson → list[TileExtent]
│     # filter for tiles overlapping project bounding box
├── _download_tiles(return_periods, tile_ids)
│     # download GeoTIFF tiles for required return periods
│     # cache in sources/eu_flood_risk/glofas/
│     # also download permanent_water + spurious_depth tiles
├── _load_apsfr()
│     # download EEA APSFR GeoPackage → build spatial index
│     # cache in sources/eu_flood_risk/apsfr/
│     # index APSFR polygons for point-in-polygon queries
│
│  ── Raster module (JRC/GloFAS) ───────────────────────────────────
├── sample_flood_depth(lat, lon, return_period)
│     # identify covering tile → rasterio.sample() at (lon, lat)
│     # return depth_m (float, 0 = not inundated, nodata = outside model)
├── sample_all_return_periods(lat, lon)
│     # sample flood depth for all 7 return periods
│     # also sample permanent water body + spurious depth masks
│     # return FloodDepthProfile
├── _check_permanent_water(lat, lon)
│     # sample permanent water body tile → boolean
├── _check_spurious_depth(lat, lon)
│     # sample spurious depth tile → boolean
│
│  ── Vector module (EEA APSFR) ────────────────────────────────────
├── query_apsfr(lat, lon)
│     # point-in-polygon against APSFR spatial index
│     # return list[ApsfrDesignation] (may intersect multiple APSFRs)
│
│  ── Single-site API (core) ───────────────────────────────────────
├── fetch(lat, lon, **params) → EuFloodRiskResult
│     # orchestrates: sample_all_return_periods + query_apsfr
│     # classify flood hazard
│     # return combined result
│
│  ── Batch API (operates on DB sites) ─────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ────────────────────
├── _classify_flood_hazard(depth_profile, apsfr_designations)
│     # "exclusionary" | "avoidance" | "low" | "negligible"
├── _compute_flood_return_period_threshold(depth_profile)
│     # lowest return period with depth > 0 (i.e., first flood scenario)
├── _compute_flood_exposure_class(depth_profile)
│     # "high" | "moderate" | "low" | "negligible"
├── _determine_screening_flags(depth_profile, apsfr)
│     # ["E8", "A14", "A15"]
├── _parse_tile_extents(geojson) → list[TileExtent]
├── _parse_apsfr_gpkg(gpkg_path) → spatial index
├── _validate_result(result) → EuFloodRiskResult
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — single site

```
fetch(lat, lon) → EuFloodRiskResult
  │
  ├─ Ensure data loaded (tiles + APSFR, download if not cached)
  │
  ├─ Raster Module: sample_all_return_periods(lat, lon)
  │    ├─ Identify covering tile from tile_extents index
  │    ├─ FOR each return period in [10, 20, 50, 75, 100, 200, 500]:
  │    │    └─ rasterio.sample(tile_path, [(lon, lat)]) → depth_m
  │    ├─ _check_permanent_water(lat, lon) → is_permanent_water
  │    ├─ _check_spurious_depth(lat, lon) → is_spurious
  │    └─ Return FloodDepthProfile
  │
  ├─ Vector Module: query_apsfr(lat, lon)
  │    ├─ Point-in-polygon query against APSFR spatial index
  │    └─ Return list[ApsfrDesignation] (may be empty for non-EU countries)
  │
  ├─ Classify:
  │    ├─ _classify_flood_hazard(depth_profile, apsfr_list)
  │    ├─ _compute_flood_return_period_threshold(depth_profile)
  │    ├─ _compute_flood_exposure_class(depth_profile)
  │    └─ _determine_screening_flags(depth_profile, apsfr_list)
  │
  ├─ Validate:
  │    └─ _validate_result(result) → range checks, flag spurious depths
  │
  └─ Return EuFloodRiskResult
```

### 5.2b Data flow — batch enrichment

**Two-phase execution:**

**Phase A — Data ingestion (run once, cached locally):**
```
_load_tile_index() + _download_tiles() + _load_apsfr()
  │
  ├─ Download tile_extents.geojson → parse → filter tiles for project bbox
  │    Project bbox: lat 35–60, lon 12–45 → ~15–25 tiles per return period
  │
  ├─ Download GeoTIFF tiles for all 7 return periods + permanent water + spurious
  │    ~25 tiles × 9 layers = ~225 files
  │    Each tile ~50–200 MB → total ~5–15 GB for project region
  │    Incremental: only download if not cached or cache expired
  │
  ├─ Download EEA APSFR GeoPackage (~500 MB)
  │    Filter for project bbox during spatial index build
  │
  └─ Build raster tile index + APSFR spatial index
       (in-memory, ready for batch site queries)
```

**Phase B — Site-by-site enrichment:**
```
enrich_batch(session, run_id, ...) → BatchResult
  │
  ├─ Ensure data loaded (Phase A)
  ├─ Ensure DataSource provenance records
  │    → "jrc_glofas_flood_hazard_v2.1.2", "eea_apsfr_v3.0"
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    ├─ Cache check: SiteAttribute for (site_id, "NH-09", run_id)?
  │    │    → skip if cached
  │    ├─ fetch(site.latitude, site.longitude) → EuFloodRiskResult
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 3 SiteAttribute rows (NH-08, NH-09, EP-05)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()
  │    └─ Log "flood_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Raster sampling at a single point is extremely fast (~0.1 ms per tile per site). Once tiles are loaded into `rasterio` datasets, a 500-site batch completes in seconds. The bottleneck is the initial tile download (~5–15 GB), which is a one-time operation cached for the configured TTL.

### 5.3 CRS handling

**Fact:** JRC/GloFAS GeoTIFFs are in WGS84 (EPSG:4326). EEA APSFR GeoPackage is in EPSG:4326. All coordinates are natively compatible.

**Requirement:** No CRS transformation needed. Raster sampling uses `(lon, lat)` coordinate order. APSFR point-in-polygon queries use `(lon, lat)`. The project canonical CRS is EPSG:4326.

### 5.4 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| tile_extents.geojson | 365 days | 88 KB | Tile grid is static. |
| GloFAS GeoTIFF tiles (per return period) | 365 days | ~5–15 GB total for project bbox | Updated irregularly (~yearly). Flood hazard maps are statistical, not operational. |
| Permanent water body tiles | 365 days | ~500 MB | Static. |
| Spurious depth tiles | 365 days | ~500 MB | Static. |
| EEA APSFR GeoPackage | 180 days | ~500 MB | Updated per Directive reporting cycle (~6 years), but minor revisions may occur. |
| Site assessment (in DB) | 365 days | Per-row | Flood hazard at a fixed location changes only when underlying model is updated. |

**Requirement:** Cache directory: `sources/eu_flood_risk/`. Subdirectories: `glofas/RP10/`, `glofas/RP20/`, ..., `glofas/RP500/`, `glofas/Permanent_WaterBodies/`, `glofas/Spurious_Depths/`, `apsfr/`.

### 5.5 Error handling specifics

| Scenario | Handling |
|----------|----------|
| JRC FTP tile download fails (HTTP 5xx / timeout) | Retry 3× with backoff. If exhausted for one tile, skip that return period for affected sites. Write quality flag `low` for affected sites. Continue with other tiles. |
| GeoTIFF nodata at sample point | Site is outside the modelled river network (catchment < 150 km²). This is a valid result — set `flood_depth_m = None` (not zero). Write quality flag `high` — absence of flood hazard from major rivers is a confident finding. Small-stream flood risk remains from N-06 national data. |
| GeoTIFF reports spurious depth at sample point | Flag from `Spurious_Depths` mask. Set quality flag `low` with detail: "Spurious flood depth detected — model artefact suspected." Do not use for screening; use only APSFR for this site. |
| Site falls on permanent water body | Flag from `Permanent_WaterBodies` mask. Set quality flag `insufficient` with detail: "Site coincides with permanent water body — flood hazard assessment not applicable." This may indicate a data error in site coordinates. |
| EEA APSFR download fails | Retry 3×. If cached version exists, use stale cache with quality flag `medium`. If no cache, proceed with JRC/GloFAS raster data only. Write quality flag `medium` noting APSFR unavailable. |
| Site in non-EU country (no APSFR data) | Not an error. Set `apsfr_designations = []`. Write quality metadata noting "Non-EU country — APSFR not available." Quality flag remains `high` for JRC/GloFAS-derived results. |
| Raster tile not available for a return period | May occur if JRC removes or reorganises tiles. Log `flood_tile_missing`. Set that return period's depth to `None`. Write quality flag `medium` if > 2 return periods missing. |
| APSFR polygon geometry invalid | Log `flood_apsfr_invalid_geom`. Skip invalid polygons during spatial index build. |
| Flood depth > 10 m | Plausible for major river floodplains (e.g., Danube, Tisa). But verify against spurious depth mask. If not flagged as spurious, accept as valid. |

---

## 6. Result Dataclasses

### 6.1 EuFloodRiskResult (top-level)

```
EuFloodRiskResult
├── lat: float
├── lon: float
├── flood_depth: FloodDepthProfile
├── apsfr: list[ApsfrDesignation]              # may be empty for non-EU
├── hazard_class: str                          # "exclusionary" | "avoidance" | "low" | "negligible"
├── screening_flags: list[str]                 # ["E8", "A14", "A15"]
├── flood_exposure_class: str                  # "high" | "moderate" | "low" | "negligible"
├── flood_return_period_threshold: int | None  # lowest RP with depth > 0 (e.g., 50)
├── is_permanent_water: bool
├── is_spurious_depth: bool
├── coastal_flood_assessed: bool               # True if APSFR coastal data available
├── sources: list[str]                         # ["jrc_glofas_v2.1.2", "eea_apsfr_v3.0"]
├── quality: str                               # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 FloodDepthProfile

```
FloodDepthProfile
├── depth_rp10_m: float | None                 # flood depth at 10-year return period (m)
├── depth_rp20_m: float | None
├── depth_rp50_m: float | None
├── depth_rp75_m: float | None
├── depth_rp100_m: float | None
├── depth_rp200_m: float | None
├── depth_rp500_m: float | None
├── max_depth_m: float | None                  # maximum across all return periods
├── depth_class_rp100: int | None              # classified: 1=<1m, 2=1-3m, 3=3-10m, 4=>10m
├── tile_id: str | None                        # GloFAS tile that covers this site
├── resolution_m: float                        # ~90 m
├── model_version: str                         # "GloFAS v2.1.2"
├── to_dict() → dict
```

### 6.3 ApsfrDesignation

```
ApsfrDesignation
├── apsfr_id: str                              # unique APSFR identifier from EEA
├── country_code: str                          # ISO 3166-1 alpha-2
├── probability_scenario: str                  # "high" | "medium" | "low"
├── source_type: str                           # "river" | "coastal" | "pluvial" | "other"
├── unit_of_management: str | None             # UoM name
├── reporting_cycle: int                       # 1, 2, or 3
├── to_dict() → dict
```

### 6.4 TileExtent (internal)

```
TileExtent
├── tile_id: str
├── bbox: tuple[float, float, float, float]    # (min_lon, min_lat, max_lon, max_lat)
├── filename_template: str                     # e.g., "{tile_id}_depth.tif"
```

### 6.5 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` from `connectors.common`.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Criterion ID | Source module | Notes |
|---------------|-------------|--------|-------------|-------------|-------|
| Coastal flood data | `site_attributes` | `value_text` = `hazard_class`; `value_json` = APSFR coastal designations + metadata | `"NH-08"` | Vector (APSFR) | Primary coastal flood evidence. `value_numeric` = distance to nearest coastal APSFR boundary (null if no coastal APSFR). |
| River flood data | `site_attributes` | `value_numeric` = `depth_rp100_m`; `value_json` = full flood depth profile + APSFR river designations | `"NH-09"` | Both | Primary river flood evidence. Depth at 100-year RP as summary metric. Full profile in JSON. |
| Concurrent hazard | `site_attributes` | `value_text` = `flood_exposure_class`; `value_json` = summary for EP-05 overlay | `"EP-05"` | Both | Flood component for concurrent hazard analysis. The EP-05 composite is built in Phase 3. |
| Source provenance | `data_sources` | `name` | — | Both | `"jrc_glofas_flood_hazard"`, `"eea_apsfr_floods_directive"` |
| Quality flags | `data_quality_flags` | `level`, `detail` | Per criterion | Both | |

**Requirement:** Persist **three** `SiteAttribute` rows per site from this connector:
1. `criterion_id="NH-08"` — coastal flooding assessment (APSFR-based + quality metadata)
2. `criterion_id="NH-09"` — river flooding assessment (GloFAS depth profile + APSFR)
3. `criterion_id="EP-05"` — concurrent hazard flood component (exposure class)

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. Screening logic (E8, A14, A15) resides in the `screening/` module.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

```python
CRITERION_IDS = ("NH-08", "NH-09", "EP-05")
```

#### Alembic migration

**Fact:** All three criterion IDs (NH-08, NH-09, EP-05) are present in `005_seed_all_siting_criteria.py`. No new migration needed.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Flood depth non-negative | Semantic | `depth ≥ 0` for all return periods | Flag `insufficient` if negative (data error) |
| Flood depth monotonic | Semantic | `depth_rp10 ≤ depth_rp20 ≤ ... ≤ depth_rp500` | Flag `low` if non-monotonic — model inconsistency |
| Flood depth plausibility | Semantic | `depth ≤ 30 m` (highest plausible for European rivers) | Flag `low` if > 30 m and not marked as spurious |
| Permanent water check | Spatial | If `is_permanent_water = True`, flood assessment is inapplicable | Flag `insufficient` for flood criteria |
| Spurious depth check | Spatial | If `is_spurious_depth = True`, do not use depth for screening | Flag `low` with detail; use APSFR only |
| Coordinates in scope | Spatial | Site lat 35–60, lon 12–45 | Log warning; proceed |
| Tile coverage | Schema | Site has covering tile in tile_extents | If no tile covers site (e.g., small island), set depth to None with quality `medium` |
| APSFR country coverage | Coverage | Non-EU countries → no APSFR | Set APSFR empty, quality metadata `medium` for coastal assessment |
| Return period completeness | Coverage | All 7 return periods sampled | Flag `medium` if < 5 periods; `low` if < 3 |
| API response schema | Schema | GeoTIFF readable by rasterio; GeoPackage readable by fiona | Log `flood_parse_error`, write quality flag |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per tile download | 300 s | Configurable. GeoTIFF tiles can be 50–200 MB. |
| Timeout per GeoPackage download | 600 s | APSFR GeoPackage ~500 MB. |
| Retry policy | 3 attempts, exponential backoff (5s base, 120s max, jitter) | Larger base delay for large downloads. |
| Rate limiting | None required | JRC FTP and EEA download have no documented rate limits. Downloads are one-time per cache period. |
| Concurrency | Single-threaded for downloads; per-site sampling is sequential but fast | Downloads could be parallelised in future (multiple tiles simultaneously). |
| Tile downloads per run | ~50 tiles total (25 tiles × 2 layers: depth + depth_reclass, per 7 return periods — though only depth is needed for numeric extraction) | Only download raw depth tiles (not reclass) to reduce storage. Reclass values are derived in the connector. |
| Per-site computation | ~1 ms (7 rasterio point samples + 1 spatial index query) | Extremely fast after data is loaded. |
| Execution modes | 1. **Module-level**: `sample_flood_depth(lat, lon, rp)`, `query_apsfr(lat, lon)` | |
| | 2. **Single site**: `fetch(lat, lon)` → `EuFloodRiskResult` | |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | |
| Batch resumability | Cache check on `(site_id, "NH-09", run_id)` | |
| Idempotency | `session.merge()` + `uq_site_criterion_run` constraint | |
| Observability | Log events: `flood_tiles_downloading`, `flood_tiles_cached`, `flood_apsfr_loaded`, `flood_sample_ok`, `flood_permanent_water`, `flood_spurious_depth`, `flood_site_complete`, `flood_batch_progress`, `flood_batch_done` | Include `site_id`, `depth_rp100`, `hazard_class`, `elapsed_ms` |

### Timing estimate

| Sites | Download time (first run) | Per-site compute | Estimated wall time |
|-------|--------------------------|-----------------|-------------------|
| 1 | ~10–30 min (tiles + APSFR) | ~1 ms | ~10–30 min (download-dominated) |
| 10 | Cached | ~10 ms | ~1 s |
| 100 | Cached | ~100 ms | ~1 s |
| 500 | Cached | ~500 ms | ~1 s |

**Inference:** The initial data download is the primary time investment. After caching, batch enrichment is extremely fast — 500 sites in ~1 second. This connector benefits greatly from aggressive caching.

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseTileExtents` | `_parse_tile_extents(geojson)` → list[TileExtent] | Trimmed tile_extents.geojson with 3 European tiles |
| `TestFloodDepthProfile` | `FloodDepthProfile` monotonicity check and classification | Synthetic profiles: no flood, shallow, deep, non-monotonic |
| `TestClassifyFloodHazard` | `_classify_flood_hazard(profile, apsfr)` → hazard class | Edge cases: depth_rp100=0.49m (low), 0.51m (exclusionary), APSFR high probability |
| `TestComputeReturnPeriodThreshold` | First return period with depth > 0 | Profiles: RP10=0/RP50=0.5 → threshold=50; all zero → None |
| `TestFloodExposureClass` | Exposure classification from depth profile | High (>3m at RP100), moderate (0.5–3m), low (>0 but <0.5m), negligible (all zero) |
| `TestScreeningFlags` | E8/A14/A15 flag determination | Various depth + APSFR combinations |
| `TestResultStructure` | `EuFloodRiskResult.to_dict()` shape and types | Constructed results |
| `TestNonEuCountry` | Empty APSFR → quality metadata correct, hazard class from raster only | Site in Turkey with flood depth |
| `TestPermanentWater` | `is_permanent_water=True` → quality `insufficient` | |
| `TestSpuriousDepth` | `is_spurious_depth=True` → quality `low`, screening deferred to APSFR | |
| `TestValidation` | Range checks (depth ≥ 0, monotonicity, depth ≤ 30 m) | Edge-case values |

### 10.2 Integration tests (mocked HTTP / mock rasterio)

| Test | What it tests |
|------|--------------|
| `test_sample_flood_depth_with_mock_geotiff` | Mock rasterio dataset → `sample_flood_depth(lat, lon, 100)` returns correct depth |
| `test_sample_all_return_periods` | Mock 7 tiles → complete FloodDepthProfile |
| `test_query_apsfr_inside_polygon` | Mock APSFR spatial index → site inside river APSFR |
| `test_query_apsfr_outside` | Mock → site outside all APSFRs |
| `test_fetch_complete_flow` | Mock raster + vector → assembled EuFloodRiskResult |
| `test_tile_index_filtering` | Parse tile_extents → only European tiles selected |
| `test_stale_cache_fallback` | Mock download failure + cached tiles → uses cache, quality `medium` |
| `test_health_check` | Mock HTTP HEAD to JRC FTP → health_check returns True |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_three_attributes` | `enrich_site()` → 3 `SiteAttribute` rows (NH-08, NH-09, EP-05) + DataSource rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `flood_batch_progress` emitted at site 25 |
| `test_non_eu_country_quality_flags` | Turkish site → NH-08 quality `medium` (no coastal APSFR), NH-09 quality `high` (GloFAS available) |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness` | `CRITERION_IDS = ("NH-08", "NH-09", "EP-05")` all seeded | Static |
| `TestConnectorPersistLiveDB::test_eu_flood_risk_persist_succeeds` | Persist mock result → 3 SiteAttribute rows, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_TILE_EXTENTS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[20, 40], [30, 40], [30, 50], [20, 50], [20, 40]]]
            },
            "properties": {"tile_id": "N40E020"}
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[25, 42], [35, 42], [35, 48], [25, 48], [25, 42]]]
            },
            "properties": {"tile_id": "N42E025"}
        },
    ],
}

SAMPLE_FLOOD_DEPTH_PROFILE = FloodDepthProfile(
    depth_rp10_m=0.0,
    depth_rp20_m=0.0,
    depth_rp50_m=0.0,
    depth_rp75_m=0.12,
    depth_rp100_m=0.45,
    depth_rp200_m=1.20,
    depth_rp500_m=2.85,
    max_depth_m=2.85,
    depth_class_rp100=1,  # <1 m
    tile_id="N42E025",
    resolution_m=90.0,
    model_version="GloFAS v2.1.2",
)

SAMPLE_APSFR = ApsfrDesignation(
    apsfr_id="RO_APSFR_123",
    country_code="RO",
    probability_scenario="medium",
    source_type="river",
    unit_of_management="Danube Lower",
    reporting_cycle=2,
)
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  eu_flood_risk:
    # JRC/GloFAS flood hazard tiles
    glofas_base_url: "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard"
    tile_extents_url: "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/tile_extents.geojson"
    return_periods: [10, 20, 50, 75, 100, 200, 500]
    download_reclass_tiles: false       # only download raw depth tiles to save storage

    # EEA APSFR dataset
    apsfr_download_url: "https://sdi.eea.europa.eu/webdav/datastore/public/eea_v_4326_100_k_floods-ref-data-under-fd_p_2011-now_v03_r00/"
    apsfr_gpkg_filename: null           # auto-detect from directory listing

    # Cache settings
    cache_dir: "sources/eu_flood_risk"
    glofas_cache_ttl_days: 365
    apsfr_cache_ttl_days: 180
    tile_download_timeout_s: 300
    apsfr_download_timeout_s: 600
    timeout_s: 60                       # general HTTP timeout

    # Project bounding box for tile filtering
    project_bbox:
      min_lat: 35
      max_lat: 60
      min_lon: 12
      max_lon: 45

    # Screening thresholds
    exclusion_depth_rp100_m: 0.5        # E8: exclude if depth > 0.5 m at 100-yr RP
    avoidance_depth_rp500_m: 0.0        # A14: avoid if depth > 0 at 500-yr RP
    # A15: avoid if within high or medium probability APSFR (implemented in code)
```

### 11.2 CLI invocation examples

```bash
# Single site by ID
python -m atoms_vs_ashes enrich eu-flood-risk --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in specific countries
python -m atoms_vs_ashes enrich eu-flood-risk --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich eu-flood-risk --all

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich eu-flood-risk --all --run-id prev-run-2026-04-01

# Download tiles only (pre-cache, don't enrich)
python -m atoms_vs_ashes enrich eu-flood-risk --download-only

# Dry run (verify tile availability, don't download or persist)
python -m atoms_vs_ashes enrich eu-flood-risk --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.eu_flood_risk import EuFloodRiskConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EuFloodRiskConnector(settings) as connector:
    # Single site — raw result, no DB
    result = connector.fetch(lat=44.43, lon=26.10)
    print(result.flood_depth.depth_rp100_m)   # 0.45
    print(result.hazard_class)                 # "low"
    print(result.apsfr)                        # [ApsfrDesignation(...)]

    # Module-level access
    depth = connector.sample_flood_depth(lat=44.43, lon=26.10, return_period=100)
    apsfr = connector.query_apsfr(lat=44.43, lon=26.10)

    # Single site — fetch + persist
    with session_scope() as session:
        summary = connector.enrich_site(
            site_id=my_site_id, session=session, run_id="run-001"
        )

    # Batch — all Romanian and Bulgarian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO", "BG"]
        )
        print(batch.summary_line())

    # Batch — entire database
    with session_scope() as session:
        batch = connector.enrich_all(session, run_id="run-002")
        print(batch.summary_line())  # "500 sites: 498 ok, 0 failed, 2 cached (1.5 s)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| JRC/GloFAS covers **riverine flooding only** — no coastal, pluvial, or groundwater flooding | **High** | NH-08 (coastal flooding) relies on EEA APSFR vector data, which is EU-only and depends on national reporting quality. For non-EU countries, coastal flood assessment is incomplete from this connector alone. S-09 GFMS and S-10 Copernicus EMS provide complementary data. National marine agencies (N-05) are the authoritative source for coastal flooding. |
| GloFAS models rivers with catchments > 150 km² only | Medium | Small-stream and urban flood risk is not captured. Sites near small rivers may show zero GloFAS depth despite real flood exposure. Quality flag `medium` when nearest modelled river is > 5 km from site. National hydrological data (N-06) provides higher-resolution data. |
| EEA APSFR is unavailable for 7+ non-EU countries (TR, UA, BY, AM, MD, and potentially BA, RS, ME, XK, AL, MK) | **High** | JRC/GloFAS provides global river flood data for all countries. For non-EU countries, the APSFR regulatory classification is missing, but quantitative flood depth is available. Quality flag `medium` for coastal assessment in non-EU countries. |
| Initial tile download is large (~5–15 GB for project bbox) | Medium | One-time download, cached for 365 days. Implement download progress logging. Support `--download-only` CLI flag for pre-caching. Only download raw depth tiles, not reclass tiles. |
| GloFAS return periods max at 500 years — IAEA requires 10,000+ year assessment | Medium | This connector provides screening-grade and ranking-grade evidence. Design-basis flood modelling for 10,000+ year events requires site-specific hydraulic studies (Stage 3+). Document this limitation clearly. |
| GloFAS spurious depth artefacts in some areas | Medium | Use the provided `Spurious_Depths` mask to flag unreliable depths. Do not use flagged values for screening. Log and document. |
| APSFR quality varies significantly between member states | Medium | Some countries report comprehensively (RO, BG, PL); others minimally. The connector cannot assess reporting quality programmatically. Write provenance metadata including reporting cycle and country. |
| APSFR does not explicitly distinguish tsunami risk from storm surge | Low | The Floods Directive was not designed for tsunami hazard. Any coastal APSFR designation provides proxy evidence for NH-08 storm surge but weak evidence for tsunami. Dedicated tsunami sources are needed for NH-08 tsunami sub-criterion. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | JRC tile naming convention — need to map tile IDs to file paths | No | Parse `tile_extents.geojson` to get tile IDs; file path pattern is `RP{XX}/{tile_id}_depth.tif`. Verify at download time. |
| 2 | EEA APSFR GeoPackage layer names and attribute schema | No | Download GeoPackage and inspect with `fiona.listlayers()` and `fiona.open(layer).schema`. Layer names documented in EEA metadata PDF. |
| 3 | APSFR attribute names for probability scenario and source type | No | Determine exact field names from GeoPackage schema. Likely `probability`, `sourceType` or similar INSPIRE-harmonised names. Document during implementation. |
| 4 | Coastal flood gap for non-EU countries | No (acknowledged) | Coastal flood data for TR, UA, BY, AM requires S-09 GFMS, S-10 Copernicus EMS, or N-05 national marine agencies. S-08 provides only riverine data for these countries. Document limitation. |
| 5 | APSFR GeoPackage download URL may change with new EEA dataset versions | No | URL is configured in YAML. Monitor EEA datahub for version updates. |
| 6 | Tile download parallelism | No | Initial implementation downloads tiles sequentially. Future enhancement could parallelise with `httpx.AsyncClient` for 3–5× speedup on initial download. |
| 7 | GloFAS flood depth at exact site coordinates vs. site footprint | No | Current approach samples a single point at site coordinates. A nuclear site has a ~72.8 ha footprint. Future enhancement could sample a grid of points within the site footprint and take the maximum depth. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for tile and GeoPackage downloads | Already in project (core dependency) |
| `rasterio` | GeoTIFF reading and point sampling | Referenced in architect stack (S-01, S-05) |
| `fiona` | GeoPackage reading for APSFR vector data | May need to be added; verify in `pyproject.toml` |
| `shapely` | APSFR point-in-polygon spatial queries | Already in project (core dependency) |
| `rtree` | Spatial index for efficient APSFR polygon queries | Typically installed with shapely/fiona |

**Fact:** `rasterio`, `fiona`, and `shapely` are standard geospatial Python libraries. `rasterio` is already referenced in the architect stack for S-01 and S-05. `fiona` provides efficient GeoPackage/Shapefile reading. `rtree` enables fast spatial indexing for the ~100,000+ APSFR polygons.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| JRC GloFAS flood hazard tiles (FTP download) | Available, no registration required |
| JRC tile_extents.geojson | Available, no registration required |
| EEA APSFR GeoPackage | Available, no registration required |

### 14.3 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Screening module (NH-08/NH-09 exclusion, E8) | `depth_rp100_m` from `SiteAttribute` where `criterion_id="NH-09"` |
| Screening module (NH-09 avoidance, A14) | `depth_rp500_m` from `SiteAttribute.value_json` |
| Screening module (APSFR avoidance, A15) | `apsfr.probability_scenario` from `SiteAttribute.value_json` where `criterion_id="NH-08"` or `"NH-09"` |
| Scoring module (NH-08, NH-09 ranking) | Full flood depth profile and APSFR data from `SiteAttribute.value_json` |
| EP-05 composite (Phase 3) | `flood_exposure_class` from `SiteAttribute` where `criterion_id="EP-05"`, overlaid with infrastructure hazard data from S-12, I-2 OSM |
| S-09 GFMS connector | S-09 provides complementary flash flood and dam-break data. S-08 provides the primary river flood assessment; S-09 fills gaps. |
| S-10 Copernicus EMS connector | S-10 provides event-based flood mapping (activation-driven). S-08 provides statistical flood hazard maps. |
| NH-14 Combined Hazards (derived) | Flood + seismic compound hazard uses NH-09 flood from S-08 and NH-01 seismic from S-01. |

---

## 15. Acceptance Criteria

### 15.1 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector downloads and parses tile_extents.geojson, correctly identifies European tiles | Unit test with sample geojson |
| 2 | Connector downloads GeoTIFF tile and samples flood depth at a known coordinate | Integration test with mock rasterio dataset |
| 3 | Flood depth sampled correctly for all 7 return periods | Unit test with synthetic raster |
| 4 | Permanent water body and spurious depth masks correctly flagged | Unit test |
| 5 | APSFR point-in-polygon query correctly identifies site within/outside flood risk area | Unit test with synthetic APSFR polygons |
| 6 | Hazard classification correctly assigns "exclusionary" when depth_rp100 > 0.5 m | Unit test |
| 7 | Hazard classification correctly assigns "avoidance" when within high/medium APSFR | Unit test |
| 8 | Hazard classification correctly assigns "negligible" when no flood depth and no APSFR | Unit test |
| 9 | Non-EU country (Turkey) returns valid result with empty APSFR and quality `medium` for coastal | Unit test |
| 10 | `EuFloodRiskResult.to_dict()` contains all required fields | Unit test |
| 11 | Monotonicity check flags non-monotonic depth profiles | Unit test |
| 12 | Connector works with `settings=None` (uses defaults) | Unit test |
| 13 | All unit tests pass without network access | `pytest` run |

### 15.2 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 14 | `enrich_site()` persists 3 `SiteAttribute` rows (NH-08, NH-09, EP-05) + DataSource rows | DB integration test |
| 15 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 16 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 17 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 18 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 19 | `BatchResult` contains correct totals | Unit + integration test |
| 20 | Progress logging emits `flood_batch_progress` every 25 sites | Log-capture integration test |
| 21 | Download-only mode downloads tiles and APSFR without enriching any sites | Integration test |
| 22 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--download-only`, `--dry-run` flags | CLI integration test |

### 15.3 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 23 | `models.py` declares `CRITERION_IDS = ("NH-08", "NH-09", "EP-05")` | Code inspection + static import test |
| 24 | All 3 criterion IDs exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 25 | `models.py` is importable without DB or HTTP dependencies | Static test |
| 26 | `_persist_result` writes 3 `SiteAttribute` rows without FK violation | Live-DB test |
| 27 | `_ensure_data_source` creates DataSource records for both JRC and EEA | Live-DB test |
| 28 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test |

---

## 16. Flood Hazard Classification Logic

### 16.1 Hazard class determination

```
classify_flood_hazard(depth: FloodDepthProfile, apsfr: list[ApsfrDesignation]) → str:

  # Check for data reliability issues
  IF depth is spurious:
      # Fall back to APSFR-only classification
      IF any apsfr with probability_scenario in ("high", "medium"):
          RETURN "avoidance"
      RETURN "low"

  IF depth is permanent water:
      RETURN "exclusionary"  # site is in a river/lake

  # E8: Exclusionary — significant flood depth at 100-year RP
  IF depth.depth_rp100_m is not None AND depth.depth_rp100_m > exclusion_depth_rp100_m:
      RETURN "exclusionary"

  # A14: Avoidance — any flood depth at 500-year RP
  IF depth.depth_rp500_m is not None AND depth.depth_rp500_m > avoidance_depth_rp500_m:
      RETURN "avoidance"

  # A15: Avoidance — within high or medium probability APSFR
  IF any apsfr with probability_scenario in ("high", "medium"):
      RETURN "avoidance"

  # Check for low-probability flood exposure
  IF any(depth.depth_rp{rp}_m > 0 for rp in [10, 20, 50, 75, 100, 200, 500]):
      RETURN "low"

  # Check for low-probability APSFR designation
  IF any apsfr with probability_scenario == "low":
      RETURN "low"

  RETURN "negligible"
```

### 16.2 Flood exposure class determination

| Condition | Exposure class |
|-----------|---------------|
| `depth_rp100_m > 3.0` | `"high"` |
| `0.5 < depth_rp100_m ≤ 3.0` | `"moderate"` |
| `0 < depth_rp100_m ≤ 0.5` OR `depth_rp500_m > 0` | `"low"` |
| All depths = 0 or None, no APSFR | `"negligible"` |

### 16.3 Quality determination

| Condition | Quality level |
|-----------|--------------|
| All 7 return periods sampled + APSFR available (EU country) | `high` |
| All 7 return periods sampled, no APSFR (non-EU country) | `high` for NH-09 (river); `medium` for NH-08 (coastal gap) |
| Some return periods missing (< 5 of 7) | `medium` |
| Spurious depth flagged | `low` |
| Permanent water body | `insufficient` |
| All data unavailable | `insufficient` |
| APSFR only (no GloFAS data) | `medium` |

---

## 17. P14 Extension — A11 Flood Risk Avoidance

**Date:** 2026-04-13
**Priority:** P14 (reuse from P6)
**Criterion:** A11 — River / Coastal Flood Risk (Avoidance)

### Implementation

P14 extends the existing S-08 connector to serve criterion A11 (flood risk avoidance, SSG-18 §5; SSG-35 §3.25). No new data source or API is required — A11 reuses the same JRC/GloFAS raster and EEA APSFR vector data already fetched and persisted by P6 for NH-08/NH-09.

**Changes made:**

1. **`parsers.py` — `determine_screening_flags()`**: Added `A11` flag. Triggers when the site has any flood exposure: non-zero GloFAS depth at any return period, or falls within any APSFR designation regardless of probability scenario.

2. **`batch.py` — `_persist_result()`**: Added A11-specific `SiteObservation` when the A11 flag is triggered. Observation includes: GloFAS depth summary, APSFR designation count and type, hazard class, and exposure class. References IAEA SSG-18 §5.

3. **`models.py`**: Added `AVOIDANCE_CRITERION_A11 = "A11"` constant and documented A11 in the `CRITERION_IDS` comment.

### A11 Screening Logic

A11 is an **avoidance** criterion (not exclusionary). It triggers whenever the site has any flood exposure:

- Any GloFAS depth > 0 at any return period (RP10–RP500) → A11 triggered
- Site within any APSFR (high, medium, or low probability) → A11 triggered
- No flood depth and no APSFR → A11 not triggered

This is deliberately broader than E8 (exclusionary, depth > 0.5 m at RP100) and A14 (avoidance, depth > 0 at RP500). A11 captures all sites with any flood signal for avoidance-level review.

### DB Fields Served

A11 maps to the same `SiteNaturalHazards` columns already written by P6:
- `flood_zone_class` (hazard classification)
- `nearest_river_km` (0.0 if RP100 depth > 0)
- `nh09_quality`, `nh09_comment`

The LLM context builder (`llm/context.py`) already maps A11 to `{nh09_flood_zone_class, nh09_nearest_river_km, nh09_quality, nh09_comment}`. No context builder changes needed.
