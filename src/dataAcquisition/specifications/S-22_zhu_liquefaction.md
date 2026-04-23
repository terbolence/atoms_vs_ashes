# S-22: Zhu Global Liquefaction Susceptibility — Integration Specification

**Source ID:** S-22
**Phase:** 1 — Exclusionary Screening
**Priority:** 🔴 P5 — Exclusionary (E2: Massive Soil Liquefaction)
**Estimated effort:** 4 h
**Criteria served:** NH-03a (liquefaction susceptibility index)
**Connector slug:** `zhu_liquefaction`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Global Liquefaction Susceptibility Map (Zhu et al., 2017) |
| Provider | USGS / Jing Zhu et al. — published in Earthquake Spectra |
| URL | USGS ScienceBase: `https://www.sciencebase.gov/catalog/item/5a51b0d6e4b0d05ee8c4d7a7`; direct GeoTIFF download available |
| Protocol | HTTP download (GeoTIFF raster) |
| Auth | **None required** (public domain, USGS) |
| Format | GeoTIFF (global raster, ~1 km resolution) |
| Spatial coverage | Global — all 23 in-scope countries covered |
| Temporal coverage | Static model based on VS30, water table depth, PGA, and distance to coast/rivers |
| Update cadence | Static (published 2017); no planned updates |
| License | Public domain (USGS) |
| IAEA references | SSG-9 Rev. 1 §4.1–4.12 (liquefaction); SSG-35 Table I-1 criterion NH-03 |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **GeoTIFF raster download + point sampling** | **Preferred** | High | Download once (~200 MB global). Sample at each site's (lon, lat) using `rasterio.sample()`. Returns liquefaction probability index (0–1). |
| **USGS Earthquake Hazards API** | **Rejected** | Low | No direct API for this dataset. |

### 2.2 Preferred extraction design

1. **Download:** One-time download of global GeoTIFF to `sources/liquefaction/zhu_global_liquefaction.tif`
2. **Sample:** For each site, use `rasterio.sample([(lon, lat)])` to extract liquefaction probability
3. **Classify:** Map probability to susceptibility class:
   - `< 0.1` → `"very_low"`
   - `0.1–0.3` → `"low"`
   - `0.3–0.5` → `"moderate"`
   - `0.5–0.7` → `"high"`
   - `> 0.7` → `"very_high"`
4. **Combine with PGA:** Liquefaction risk = f(susceptibility, PGA). If S-01 PGA data available, compute combined liquefaction potential.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support Level | Derived Variable | Evidence Grade |
|-----------|--------------|---------------|-----------------|---------------|
| NH-03a | Liquefaction susceptibility | **Screening-grade** | `liquefaction_suscept` (class), raw probability value | Screening |

**E-rule E2:** If `liquefaction_suscept` = `"very_high"` AND `pga_475yr_g > 0.1` → **FAIL** (exclusionary). If `"high"` AND `pga_475yr_g > 0.2` → **FAIL**.

---

## 4. Regional Applicability

**Fact:** Global raster — all 23 countries covered with consistent methodology.

**Inference:** Resolution (~1 km) is appropriate for screening-grade assessment. Site-specific geotechnical investigation (Stage 3) would supersede this for final decisions.

---

## 5. Integration Design

### 5.1 Data flow

1. **Download:** GeoTIFF to `sources/liquefaction/` (one-time, cached indefinitely)
2. **Open:** `rasterio.open()` with CRS verification (should be EPSG:4326)
3. **Sample:** Point query at (lon, lat) for each site
4. **Classify:** Map raw probability to susceptibility class
5. **Persist:** Write to `site_natural_hazards.liquefaction_suscept` and raw value to `SiteObservation`

### 5.2 CRS handling

- **Source CRS:** EPSG:4326 (WGS84)
- **Sampling:** Direct point query in native CRS (no reprojection needed)

---

## 6. Database Persistence

| Table | Column | Type | Source |
|-------|--------|------|--------|
| `site_natural_hazards` | `liquefaction_suscept` | `String` | Susceptibility class (`very_low` to `very_high`) |
| `site_natural_hazards` | `nh03_quality` | `String` | `"zhu_global_1km"` |
| `site_natural_hazards` | `nh03_comment` | `String` | Raw probability value, classification thresholds used |

---

## 7. Open Issues

1. **Model vintage:** The Zhu (2017) model uses VS30 and water table depth inputs that may not reflect local conditions. **Mitigation:** Flag as screening-grade; recommend site-specific geotechnical assessment for sites with `"high"` or `"very_high"` susceptibility.

2. **PGA dependency:** Full liquefaction potential assessment requires combining susceptibility with seismic PGA (S-01). **Requirement:** If PGA data is available, compute combined liquefaction potential index. If not, report susceptibility alone.

---

## 8. API Validation Notes

**Date:** 2026-04-13
**Validated by:** Implementation engineer

### 8.1 Spec deviations discovered

1. **Source URL:** The ScienceBase item (`5a51b0d6e4b0d05ee8c4d7a7`) returns 403 Forbidden. The actual usable dataset is hosted on **Zenodo** (DOI: 10.5281/zenodo.2583746) by Zorn & Koks (2019), who derived a static susceptibility map from the Zhu et al. (2017) methodology.

2. **File format:** The raster contains **pre-classified integer values** (1–5), not continuous probability (0–1) as the spec described. Cell values:
   - `0` = no data (water bodies)
   - `1` = very low
   - `2` = low
   - `3` = moderate
   - `4` = high
   - `5` = very high

   **Impact:** No probability-to-class mapping is needed. The raster is already classified. The spec's §2.2 step 3 (threshold-based classification) is unnecessary.

3. **File size:** ~442 MB (spec estimated ~200 MB).

4. **Filename:** `liquefaction_v1_deg.tif` (not `zhu_global_liquefaction.tif` as spec §2.2 suggested).

5. **Model inputs:** The Zhu (2017) model uses **PGV** (peak ground velocity), not PGA, as the shaking intensity parameter. The static susceptibility map from Zorn & Koks does not include a shaking term — it represents susceptibility independent of any specific earthquake event.

### 8.2 Download details

- **URL:** `https://zenodo.org/records/2583746/files/liquefaction_v1_deg.tif?download=1`
- **Auth:** None required
- **CRS:** EPSG:4326 (confirmed)
- **Resolution:** ~0.008333° (~1 km at equator)
- **Coverage:** Global land areas
- **No rate limiting** (single file download from Zenodo CDN)

### 8.3 Implementation decisions

- **Deviation from spec §2.2:** Raster values are integers 1–5, not probabilities. Classification step removed; direct integer-to-class mapping used instead.
- **Deviation from spec §5.1 step 4:** "Classify" step is a simple lookup, not a threshold comparison.
- **E2 screening rule** (§3): Deferred to a separate screening check that combines NH-03 (this connector) with NH-01 PGA data (S-01 connector). The connector only enriches the susceptibility column.
- **Combined liquefaction potential** (§7 issue 2): Deferred. Requires both S-01 PGA and S-22 susceptibility to be populated. Will be implemented as a screening check that reads both columns.

### 8.4 Batch validation results (2026-04-13)

| Step | Sites | Result | Elapsed |
|------|-------|--------|---------|
| Dry run | 0 | Raster OK, CRS EPSG:4326, nodata=255, dtype=uint8 | — |
| Smoke (3) | 3 | 3/3 ok | 0.2 s |
| Small (20) | 20 | 20/20 ok | 0.2 s |
| Full (363) | 363 | **363/363 ok, 0 failed** | **1.1 s** |

**Performance:** ~3 ms/site average (first site ~45 ms for raster open). Purely local I/O — no network calls, no rate limiting. The full 363-site batch completes in ~1 second.

**Distribution across 363 sites:**

| Class | Count | % |
|-------|-------|---|
| moderate | 150 | 41.3% |
| very_low | 137 | 37.7% |
| high | 62 | 17.1% |
| NULL (water body pixel) | 9 | 2.5% |
| low | 4 | 1.1% |
| very_high | 1 | 0.3% |

**E2 candidates (high + very_high):** 63 sites (17.4%) — these will require PGA cross-check for exclusionary decision.

**NULL sites (9):** All coastal Turkish power plants where the ~1 km raster resolution places the site coordinates in a water body pixel. `SiteObservation` records written for all 9. These sites need manual review or higher-resolution data.

### 8.5 Raster metadata (actual)

- **Nodata value:** 255 (uint8), not 0 as Zenodo description implied. Value 0 represents water bodies / no-data on land.
- **Dimensions:** 33,212 × 13,313 pixels
- **Bounds:** -180° to +180° lon, -56° to +84° lat
- **File size on disk:** 421.8 MB
