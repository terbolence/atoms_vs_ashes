# S-20: GHSL GHS-POP (Global Human Settlement Layer) — Integration Specification

**Source ID:** S-20
**Phase:** 1 — Exclusionary Screening
**Priority:** 🔴 P8 — Exclusionary/Avoidance (E8: Emergency Plan Feasibility, A12: Population Density)
**Estimated effort:** 16 h
**Criteria served:** RI-04a–d (population density at 5/16/25/80 km), RI-05a (city distance), RI-06a (population projection proxy), EP-01a (EPZ feasibility population), HI-03b (downwind population), NS-07c (noise/visual proxy), NS-09c (social vulnerability), NS-10c (housing pressure)
**Connector slug:** `ghsl_pop`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | GHS-POP R2023A — Global Human Settlement Population Grid |
| Provider | European Commission Joint Research Centre (JRC) |
| URL | `https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php`; download: `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/` |
| Protocol | HTTP/FTP download (tiled GeoTIFF) |
| Auth | **None required** (open access) |
| Format | GeoTIFF — 100 m resolution (Mollweide projection), also available at 1 km |
| Spatial coverage | Global — all 23 in-scope countries covered |
| Temporal coverage | Multi-epoch: 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030 |
| Update cadence | Major releases every 2–3 years (R2023A is current) |
| License | CC BY 4.0 |
| IAEA references | SSG-35 §4.42–4.55 (population distribution); NS-R-3 §3.54–3.60 (radiological impact assessment) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **GeoTIFF download (100 m) + zonal statistics** | **Preferred** | High | Download tiles covering study area. For each site, compute population within 5/16/25/80 km ring buffers using zonal statistics. Multi-epoch data enables projection assessment. |
| **GeoTIFF download (1 km) + zonal statistics** | **Fallback** | High | Lower resolution but much smaller download. Sufficient for 16/25/80 km radii; may lose precision at 5 km. |
| **GHSL API** | **Deferred** | Medium | JRC provides an experimental API. Less mature than direct raster access. |

### 2.2 Preferred extraction design

**Requirement:** For each site, compute population statistics within EPZ ring buffers:

1. **Download:** GHS-POP 100 m tiles for the study area bounding box (epoch 2020 primary, 2030 for projections)
2. **Buffer creation:** Create ring buffers at 5, 16, 25, 80 km using geodesic buffers (`buffer_ring_wgs84`)
3. **Zonal statistics:** For each ring, sum population pixels within the ring polygon
4. **Density computation:** `pop_density = pop_total / ring_area_km2`
5. **City detection:** Identify settlements > 50,000 population within 80 km (from aggregated grid cells)

### 2.3 Tile structure

GHS-POP R2023A 100 m tiles are in Mollweide projection (ESRI:54009), organized in a global tile grid. Tiles covering the study area (lat 35–60°N, lon 12–45°E) are approximately 20–30 tiles, ~2 GB total.

**Requirement:** Reproject site buffer polygons from EPSG:4326 to Mollweide for zonal statistics, OR reproject raster tiles to EPSG:4326 on-the-fly using `rasterio.warp`.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| RI-04a | Population density within 5 km | **Screening-grade** | `pop_density_5km` (persons/km²) | Screening |
| RI-04b | Population density within 16 km | **Screening-grade** | `pop_density_16km` | Screening |
| RI-04c | Population density within 25 km | **Screening-grade** | `pop_density_25km` | Screening |
| RI-04d | Population density within 80 km | **Screening-grade** | `pop_density_80km` | Screening |
| RI-05a | Nearest city > 50,000 | **Screening-grade** | `nearest_city_50k_km`, `nearest_city_name`, `nearest_city_pop` | Screening |
| RI-06a | Population projection proxy | **Ranking-grade** | 2020→2030 growth rate from multi-epoch data | Ranking |
| EP-01a | EPZ feasibility (population) | **Screening-grade** | `pop_total_5km` for EPZ feasibility composite | Screening |

**A-rule A12:** If `pop_density_5km > 1000` persons/km² → **CAUTION** (avoidance threshold).
**E-rule E8:** If `pop_density_5km > 5000` AND `road_density_km_per_km2 < 2` → **FAIL** (emergency plan infeasibility).

---

## 4. Regional Applicability

**Fact:** GHS-POP is global with consistent methodology. All 23 countries covered at 100 m resolution.

**Inference:** GHS-POP is based on census data disaggregated to built-up areas detected from Sentinel-2 imagery. Quality is high for EU countries (Eurostat census 2021 inputs) and moderate for non-EU countries (UN population estimates).

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** GHS-POP 100 m tiles for study area to `sources/population/ghsl/` (~2 GB)
2. **Mosaic:** Virtual raster (VRT) or in-memory mosaic of relevant tiles
3. **Buffer:** For each site, create geodesic ring buffers at 5/16/25/80 km
4. **Reproject:** Transform buffer polygons to Mollweide (source CRS) for zonal stats
5. **Compute:** Sum population pixels within each ring; compute density
6. **City detection:** Aggregate high-density cells into settlement clusters; identify > 50k
7. **Persist:** Write to `site_radiological` and `site_emergency_planning` columns

### 5.2 CRS handling

- **Source CRS:** ESRI:54009 (Mollweide equal-area) — GHS-POP native
- **Buffer CRS:** Geodesic buffers created in EPSG:4326, reprojected to Mollweide for zonal stats
- **Storage CRS:** EPSG:4326 for coordinates; population values are CRS-independent

### 5.3 Caching strategy

- Cache downloaded tiles indefinitely (static dataset per release)
- Pre-compute population grids for all 363 sites in batch mode

---

## 6. Database Persistence

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `site_radiological` | `pop_density_5km` | `Float` | Population density within 5 km ring |
| `site_radiological` | `pop_density_16km` | `Float` | Population density within 16 km ring |
| `site_radiological` | `pop_density_25km` | `Float` | Population density within 25 km ring |
| `site_radiological` | `pop_density_80km` | `Float` | Population density within 80 km ring |
| `site_radiological` | `pop_total_5km` | `Integer` | Total population within 5 km |
| `site_radiological` | `pop_total_16km` | `Integer` | Total population within 16 km |
| `site_radiological` | `pop_total_25km` | `Integer` | Total population within 25 km |
| `site_radiological` | `pop_total_80km` | `Integer` | Total population within 80 km |
| `site_radiological` | `nearest_city_50k_km` | `Float` | Distance to nearest city > 50k |
| `site_radiological` | `nearest_city_name` | `String` | Name of nearest city > 50k |
| `site_radiological` | `nearest_city_pop` | `Integer` | Population of nearest city > 50k |
| `site_radiological` | `pop_growth_rate_pct` | `Float` | 2020→2030 annual growth rate |
| `site_radiological` | `ri04_quality` | `String` | `"ghsl_pop_100m_r2023a"` |
| `site_radiological` | `ri04_comment` | `String` | Epoch used, methodology notes |
| `site_emergency_planning` | `ep01_population_score` | `Float` | Population component of EP feasibility |

---

## 7. Open Issues

1. **Mollweide projection handling:** GHS-POP uses Mollweide (equal-area), which is ideal for population density but requires careful reprojection for buffer operations. **Requirement:** Use `pyproj` for all CRS transforms; verify area preservation.

2. **City identification:** GHS-POP is a gridded product without named settlements. **Mitigation:** Cross-reference high-density clusters with GeoNames or OSM `place=city` nodes for city names and population figures.

3. **Multi-epoch consistency:** Using 2020 and 2030 epochs for growth rate computation assumes the projection methodology is consistent between epochs. **Fact:** JRC uses consistent disaggregation methodology across epochs. This is valid for screening-grade assessment.

---

## 8. API Validation Notes

**Date:** 2026-04-13
**Validated by:** Implementation engineer

### Source characteristics
- **Protocol:** HTTP/FTP download (no API rate limits). Download-based source — tiles cached locally, all queries are local raster operations.
- **CRS confirmed:** ESRI:54009 (Mollweide equal-area) as documented.
- **Resolution:** 100 m tiles (~100 MB each) and 1 km global file (~300 MB) both available.
- **Tile structure:** `GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_{tile_id}.tif` for 100 m; `GHS_POP_E{epoch}_GLOBE_R2023A_54009_1000_V1_0.tif` for 1 km global.
- **Auth:** None required (open access, CC BY 4.0). Confirmed.
- **Epochs available:** 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030. Confirmed.

### Rate limits
- **Not applicable.** Download-based source. No API rate limiting. Tiles are static files served via HTTP/FTP.
- **Courtesy:** Inter-request delay of 0.5s between tile downloads to avoid overloading JRC servers.

### Implementation notes
- **Zonal statistics approach:** Uses `rasterio.mask` for production path (accurate polygon masking). Pure-logic fallback via pixel-centre-in-polygon for testing.
- **Buffer CRS handling:** Geodesic buffers created in WGS84 via `buffer_circle_wgs84()`, then reprojected to Mollweide for zonal statistics. Area computed geodesically via `geodesic_area_ha()`.
- **Growth rate:** Compound annual growth rate (CAGR) from 25 km radius population at 2020 and 2030 epochs.
- **City detection:** Deferred to Phase 2 — requires cross-referencing with GeoNames or OSM place nodes. The `nearest_city` field is populated when external city data is available.
- **EP-01 population score:** Tiered scoring based on total population within 5 km EPZ: <1k→100, <5k→80, <20k→60, <50k→40, else→20.

### Connector structure
```
connectors/ghsl_pop/
├── __init__.py    # Public re-exports
├── models.py      # Result dataclasses, constants
├── parsers.py     # Pure zonal statistics (no I/O)
├── client.py      # GhslPopConnector: download, fetch, raster lifecycle
└── batch.py       # Batch enrichment, DB persistence
```

### CLI commands
- `atoms-vs-ashes enrich download-ghsl-pop [--epoch N] [--tile ID] [--force]`
- `atoms-vs-ashes enrich ghsl-pop [--site-id UUID] [--country CC] [--all] [--dry-run]`

### DB tables written
- `site_radiological`: RI-04 (pop density/total at 5/16/25/80 km), RI-05 (nearest city), RI-06 (growth rate)
- `site_emergency_planning`: EP-01 (population score component)
- `site_observations`: Quality flags for errors and high-density warnings
