# S-19: Copernicus DEM (GLO-30) — Integration Specification

**Source ID:** S-19
**Phase:** 1 — Exclusionary Screening
**Priority:** 🔴 P13 — Exclusionary/Suitability (E3: Slope Stability)
**Estimated effort:** 12 h
**Criteria served:** NH-04a (slope gradient / terrain ruggedness), NH-08d (tsunami elevation proxy), RI-01d (terrain channeling), EP-03a (topographic barriers), NS-04a/b (earthworks proxy, drainage micro-topography)
**Connector slug:** `copernicus_dem`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Copernicus DEM GLO-30 (Global 30-meter Digital Elevation Model) |
| Provider | European Space Agency (ESA) / Copernicus Programme |
| URL | AWS Open Data: `https://registry.opendata.aws/copernicus-dem/`; Copernicus Space Data: `https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model` |
| Protocol | S3 COG (Cloud-Optimized GeoTIFF) tiles on AWS; HTTP download from Copernicus |
| Auth | **None required** (AWS Open Data — public S3 bucket `copernicus-dem-30m`) |
| Format | Cloud-Optimized GeoTIFF (COG), 1°×1° tiles, ~30 m resolution |
| Spatial coverage | Global (between 90°N and 90°S) — all 23 in-scope countries covered |
| Temporal coverage | Based on TanDEM-X SAR data (2011–2015); edited with ICESat-2 and other sources |
| Update cadence | Annual incremental updates |
| License | Free and open access (Copernicus data policy) |
| IAEA references | SSG-35 Table I-1 criterion NH-04 (slope stability); SSG-9 Rev. 1 (terrain effects on seismic hazard) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **AWS S3 COG tiles — windowed read via rasterio** | **Preferred** | High | Read only the tile(s) covering each site's buffer zone. COG format enables efficient partial reads without downloading full tiles. No auth needed. |
| **Copernicus Space Data Ecosystem download** | **Fallback** | Medium | Full tile download. Requires Copernicus account. Larger data transfer. |
| **Sentinel Hub DEM API** | **Deferred** | Medium | Requires Sentinel Hub account (S-05). Unnecessary overhead for point/buffer DEM queries. |

### 2.2 Preferred extraction design

**Requirement:** For each site, extract a DEM patch covering a 5 km buffer around the site coordinates:

1. **Tile identification:** Compute which 1°×1° COG tile(s) cover the site's 5 km buffer
2. **Windowed read:** Use `rasterio` with S3 VSICURL to read only the relevant window from the COG
3. **Slope computation:** Compute slope gradient from DEM using `numpy.gradient()` or `richdem`
4. **Elevation extraction:** Site elevation at point; min/max/mean within buffer
5. **Terrain ruggedness:** Compute TRI (Terrain Ruggedness Index) within 1 km buffer

### 2.3 S3 path pattern

```
s3://copernicus-dem-30m/Copernicus_DSM_COG_10_{N|S}{lat:02d}_00_{E|W}{lon:03d}_00_DEM/
  Copernicus_DSM_COG_10_{N|S}{lat:02d}_00_{E|W}{lon:03d}_00_DEM.tif
```

Example for a site at 45.27°N, 27.93°E:
```
s3://copernicus-dem-30m/Copernicus_DSM_COG_10_N45_00_E027_00_DEM/Copernicus_DSM_COG_10_N45_00_E027_00_DEM.tif
```

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| NH-04a | Slope gradient | **Screening-grade** | `slope_angle_deg` (max slope within 1 km buffer) | Screening |
| NH-08d | Tsunami elevation proxy | **Screening-grade** | Site elevation (coastal sites < 10 m flagged) | Screening |
| RI-01d | Terrain channeling | **Ranking-grade** | TRI and valley/ridge classification | Ranking |
| EP-03a | Topographic barriers | **Ranking-grade** | Terrain barrier index for evacuation routes | Ranking |
| NS-04a | Earthworks proxy | **Ranking-grade** | Cut/fill volume proxy from elevation variance | Ranking |
| NS-04b | Drainage micro-topography | **Ranking-grade** | Local drainage direction and accumulation | Ranking |

**E-rule E3:** If `slope_angle_deg > 15°` within the nuclear island footprint → **CAUTION**. If `> 30°` → **FAIL** (exclusionary, massive slope instability).

---

## 4. Regional Applicability

**Fact:** Copernicus DEM GLO-30 is global with consistent 30 m resolution. All 23 countries fully covered.

---

## 5. Integration Design

### 5.1 Data flow

1. **Identify tiles:** Compute tile IDs from site lat/lon + 5 km buffer extent
2. **Read:** `rasterio.open()` with `/vsicurl/` or `/vsis3/` prefix for S3 COG access
3. **Window:** Read only the buffer-extent window from each tile
4. **Compute:** Slope, elevation stats, TRI from DEM array
5. **Persist:** Write derived values to `site_natural_hazards` and `site_infrastructure_v2`

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (WGS84) with heights in EGM2008 geoid
- **Slope computation:** Reproject to local UTM zone for accurate gradient calculation, then convert back
- **Storage CRS:** EPSG:4326 for coordinates; derived values are dimensionless (degrees, meters)

### 5.3 Caching strategy

- Cache downloaded tiles locally in `sources/dem/copernicus_glo30/` (365-day TTL)
- For batch processing, pre-download all tiles covering the 23-country bounding box (~500 tiles, ~15 GB)

---

## 6. Database Persistence

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `sites` | `elevation_m` | `Float` | DEM value at site point |
| `site_natural_hazards` | `slope_angle_deg` | `Float` | Maximum slope within 1 km buffer |
| `site_natural_hazards` | `nh04_quality` | `String` | `"copernicus_dem_30m"` |
| `site_natural_hazards` | `nh04_comment` | `String` | Elevation stats, TRI, slope distribution |
| `site_infrastructure_v2` | `ns04_quality` | `String` | `"copernicus_dem_30m"` |

---

## 7. Open Issues

1. **Tile download size:** Pre-downloading all tiles for the study area is ~15 GB. **Mitigation:** Use COG windowed reads via S3 for on-demand access; only cache tiles for frequently queried areas.

2. **Slope computation accuracy:** Computing slope from a 30 m DEM on WGS84 coordinates requires careful handling of pixel size variation with latitude. **Requirement:** Reproject to local UTM zone before gradient computation.

3. **Vegetation canopy bias:** Copernicus DEM is a Digital Surface Model (DSM), not a bare-earth DTM. In forested areas, elevation may be biased upward by canopy height. **Mitigation:** For slope stability assessment, DSM is conservative (overestimates slope in forested terrain). Document this limitation.

---

## 8. API Validation Notes

**Date:** 2026-04-13
**Validated by:** Implementation engineer (automated)

### Connectivity
- AWS S3 public bucket `copernicus-dem-30m` accessible via HTTPS without authentication
- COG tiles served via CloudFront CDN from `https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/`
- `/vsicurl/` access via rasterio/GDAL works for windowed reads (confirmed with Romania test tile N45_E027)

### Tile naming
- Confirmed: `Copernicus_DSM_COG_10_{N|S}{lat:02d}_00_{E|W}{lon:03d}_00_DEM/Copernicus_DSM_COG_10_{N|S}{lat:02d}_00_{E|W}{lon:03d}_00_DEM.tif`
- Tile labels correspond to the SW corner of each 1°×1° cell (floor of latitude, floor of longitude)
- CRS confirmed: EPSG:4326, heights in EGM2008 geoid

### Rate limits
- **No rate limiting detected.** AWS S3 public bucket served via CloudFront CDN.
- HEAD requests return 200 consistently with sub-500ms latency from EU
- No `X-RateLimit-*`, `Retry-After`, or similar headers observed
- **Recommendation:** Use courtesy delay of 0.1–0.5s between batch requests to avoid overwhelming shared infrastructure

### Response format
- GeoTIFF, single band, Float32 elevation values in metres
- Nodata value: varies by tile (typically -32767.0 or similar)
- Resolution: ~30 m (1 arcsecond)
- Tile dimensions: ~3601 × 3601 pixels per 1°×1° tile

### Implementation notes
- Slope computation uses UTM reprojection for accurate metric gradients (Horn's method via `numpy.gradient`)
- TRI computed using Riley et al. (1999) 3×3 neighbourhood method
- Fallback to approximate 30 m pixel size if UTM reprojection fails
- DSM limitation documented in persistence comments (conservative for slope stability)
- All 23 in-scope countries fully covered (global dataset)
