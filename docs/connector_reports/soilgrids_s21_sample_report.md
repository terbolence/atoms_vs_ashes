# S-21 SoilGrids Connector — Sample Report

## Header

| Field | Value |
|-------|-------|
| Connector | S-21 SoilGrids (ISRIC) |
| Slug | `soilgrids` |
| Run date | 2026-04-19 |
| Run ID | `fix06_soilgrids_full_20260419` |
| Criteria served | NH-03 (soil_type), NH-06 (bearing_capacity_kpa) |
| Sites queried | 353 (10 cached from test run) |
| Sites with data | 310 / 363 (85.4%) |

## Methodology

The connector queries [ISRIC SoilGrids v2.0](https://www.isric.org/explore/soilgrids) via OGC WCS 2.0.1 at `maps.isric.org`. SoilGrids provides global soil property maps at 250 m resolution, derived from machine learning predictions trained on ~240,000 soil profile observations.

For each site:

1. **Coordinate transformation**: Site coordinates (WGS84 / EPSG:4326) are transformed to Interrupted Goode Homolosine (IGH, EPSG:152160) using pyproj.
2. **WCS GetCoverage**: Four layers are queried as small GeoTIFF windows (1 km × 1 km) centered on the projected coordinates: `clay_0-5cm_mean`, `sand_0-5cm_mean`, `silt_0-5cm_mean`, `bdod_0-5cm_mean`.
3. **Pixel extraction**: The center pixel is read from each GeoTIFF. If the center pixel is nodata (value = 0), the nearest valid pixel within the window is used.
4. **USDA texture classification**: Clay, sand, and silt percentages are used to classify the soil via the USDA texture triangle into one of 12 classes (clay, silty_clay, sandy_clay, silty_clay_loam, clay_loam, sandy_clay_loam, silt_loam, silt, loam, sandy_loam, loamy_sand, sand).
5. **Bearing capacity estimation**: A screening-grade bearing capacity (kPa) is derived from the USDA texture class using simplified Terzaghi/Meyerhof correlations, adjusted by the ratio of actual bulk density to a reference value of 1.5 g/cm³.

**Assumptions and proxies:**
- Soil properties at 0–5 cm depth are used as representative of the surface layer. This is appropriate for screening but does not capture deeper soil variation.
- Bearing capacity is a **derived proxy**, not a measured value. The Terzaghi/Meyerhof correlation provides an order-of-magnitude estimate suitable for siting screening. Site-specific geotechnical investigation is required for detailed assessment.
- The nearest-valid-pixel strategy introduces up to 500 m of spatial uncertainty at coverage edges.

## Metric legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `soil_type` | USDA class (string) | USDA texture triangle classification from clay/sand/silt percentages | SoilGrids has no data at site location |
| `bearing_capacity_kpa` | kPa | Terzaghi/Meyerhof lookup by texture class, adjusted by bulk density ratio | No texture data available → cannot compute |
| `clay_pct` | % | SoilGrids `clay_0-5cm_mean` (g/kg ÷ 10) | Layer returned nodata |
| `sand_pct` | % | SoilGrids `sand_0-5cm_mean` (g/kg ÷ 10) | Layer returned nodata |
| `silt_pct` | % | SoilGrids `silt_0-5cm_mean` (g/kg ÷ 10) | Layer returned nodata |
| `bulk_density_gcm3` | g/cm³ | SoilGrids `bdod_0-5cm_mean` (cg/cm³ ÷ 100) | Layer returned nodata |

## Quality grade legend

| Grade | Meaning |
|-------|---------|
| `medium` | All 4 WCS layers returned data; texture classification and bearing capacity computed successfully |
| `insufficient` | One or more WCS layers returned nodata at site location; `soil_type` and `bearing_capacity_kpa` are NULL |

## Bearing capacity lookup table

| USDA Texture Class | Base capacity (kPa) | Typical range | Notes |
|--------------------|--------------------:|---------------|-------|
| sand | 200 | 150–300 | High capacity, well-drained |
| loamy_sand | 150 | 100–200 | |
| sandy_loam | 150 | 100–200 | |
| sandy_clay_loam | 125 | 80–175 | |
| loam | 100 | 75–150 | Most common in dataset |
| clay_loam | 100 | 75–150 | |
| silty_clay_loam | 100 | 75–150 | |
| silt_loam | 75 | 50–100 | |
| clay | 75 | 50–100 | Low capacity, poor drainage |
| silty_clay | 75 | 50–100 | |
| silt | 50 | 25–75 | Lowest capacity |

Base values are adjusted by `bulk_density / 1.5`, clamped to [0.6, 1.5] multiplier.

## Sample data table (20+ representative sites)

| # | Site | Country | Lat | Lon | `soil_type` | Clay % | Sand % | Silt % | Bulk density | `bearing_capacity_kpa` | Quality |
|---|------|---------|-----|-----|-------------|--------|--------|--------|-------------|------------------------|---------|
| 1 | Porto Romano Power Station | AL | 41.3711 | 19.4252 | clay | 42.7 | 5.1 | 52.2 | 1.17 | 68.5 | medium |
| 2 | Mellach power station | AT | 46.9082 | 15.4923 | loam | 23.6 | 32.3 | 44.1 | 1.23 | 82.0 | medium |
| 3 | Zeltweg power station | AT | 47.2500 | 15.1667 | loam | 16.1 | 38.9 | 45.0 | 0.90 | 60.0 | medium |
| 4 | Banovici power station | BA | 44.4000 | 18.5333 | clay_loam | 29.2 | 32.6 | 38.2 | 1.23 | 82.0 | medium |
| 5 | Bobov Dol power station | BG | 42.2858 | 23.0328 | clay_loam | 29.2 | 27.1 | 43.7 | 1.33 | 88.7 | medium |
| 6 | Brăila-Chișcani TPP | RO | 45.2744 | 27.9291 | silty_clay_loam | 37.7 | 9.5 | 52.9 | 1.27 | 84.7 | medium |
| 7 | Doicești | RO | 45.0029 | 25.3972 | clay_loam | 31.8 | 35.3 | 32.9 | 1.32 | 88.0 | medium |
| 8 | FPCU Feldioara | RO | 45.7917 | 25.5889 | clay_loam | 39.5 | 22.0 | 38.5 | 1.31 | 87.3 | medium |
| 9 | Rovinari power station | RO | 44.9106 | 23.1348 | clay_loam | 29.8 | 39.3 | 30.9 | 1.33 | 88.7 | medium |
| 10 | Turceni power station | RO | 44.6697 | 23.4078 | clay_loam | 36.7 | 30.6 | 32.7 | 1.37 | 91.3 | medium |
| 11 | Konin power station | PL | 51.5622 | 18.2586 | loamy_sand | 6.8 | 80.5 | 12.7 | 1.33 | 133.0 | medium |
| 12 | Lom Power Station | BG | 43.7825 | 23.2175 | silty_clay_loam | 35.1 | 5.1 | 59.8 | 1.38 | 92.0 | medium |
| 13 | Duernrohr power station | AT | 48.3261 | 15.9233 | silty_clay_loam | 29.3 | 9.6 | 61.1 | 1.27 | 84.7 | medium |
| 14 | Gacko Thermal Power Plant | BA | 43.1721 | 18.5116 | loam | 21.0 | 33.3 | 45.7 | 1.18 | 78.7 | medium |
| 15 | Maritsa Iztok-1 power station | BG | 42.1573 | 25.9084 | clay_loam | 36.1 | 24.0 | 39.9 | 1.37 | 91.3 | medium |
| 16 | Ugljevik power station | BA | 44.6834 | 18.9685 | clay_loam | 28.7 | 34.1 | 37.2 | 1.32 | 88.0 | medium |
| 17 | Stanari Thermal Power Plant | BA | 44.7539 | 17.7924 | clay_loam | 28.3 | 33.6 | 38.1 | 1.33 | 88.7 | medium |
| 18 | Miljevina power station | BA | 43.5183 | 18.6521 | loam | 18.2 | 39.2 | 42.6 | 1.01 | 67.3 | medium |
| 19 | Sinop Akfen power station | TR | 42.0124 | 35.1512 | clay | 44.2 | 12.0 | 43.8 | 1.24 | 62.0 | medium |
| 20 | Silopi (Şırnak) power station | TR | 37.2524 | 42.4626 | silty_clay_loam | 35.9 | 11.6 | 52.5 | 1.22 | 81.3 | medium |

## Coverage notes

- **Global coverage**: SoilGrids v2.0 has near-global coverage at 250 m resolution, but coverage gaps exist in urban areas, water bodies, and some edge-of-tile locations.
- **53 sites with no data** (14.6%): Concentrated in Turkey (19 sites), Poland (12), Czech Republic (6), Ukraine (5), and scattered across 7 other countries. These sites fall on SoilGrids nodata pixels — likely urban/industrial footprints or edge-of-tile gaps.
- **`depth_to_bedrock_m`**: The `bdricm` (depth to bedrock) layer has been removed from SoilGrids v2.0 and is not available via WCS or file download. This field remains NULL for all sites.
- **`groundwater_depth_m`**: SoilGrids does not provide water table depth. This would require a separate data source (e.g., Fan et al. 2013 global water table model).
- **Bearing capacity limitation**: The proxy estimate is screening-grade only. Values range from 53.5–133.0 kPa across the dataset (mean 86.3, median 86.0). Site-specific geotechnical investigation is required for design-level assessment per SSG-9 Rev.1 §4.1–4.12.
- **Rate limiting**: The WCS endpoint (`maps.isric.org`) was queried at ~5 requests per 15 seconds with no rate-limiting observed. Full batch of 363 sites completed in 67 minutes.
