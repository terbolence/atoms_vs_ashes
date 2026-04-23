# S-23 BDTICM Depth-to-Bedrock — Connector Report

| Field               | Value                                                                                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Connector**       | `BdticmBedrockConnector`                                                                                                                        |
| **Slug**            | `bdticm_bedrock`                                                                                                                                |
| **Run date**        | 2026-04-18                                                                                                                                      |
| **Criteria served** | NH-06 (Foundation conditions)                                                                                                                   |
| **Source**          | SoilGrids v1 (2017-03) BDTICM_M_250m_ll.tif                                                                                                     |
| **Reference**       | Shangguan, W., Hengl, T., et al. (2017). _Mapping the global depth to bedrock for land surface modeling._ J. Adv. Model. Earth Syst., 9, 65–88. |

---

## Methodology

The connector point-samples the **BDTICM** (absolute depth to bedrock) global GeoTIFF from SoilGrids v1 (2017-03 release) hosted at ISRIC. The raster was produced using ensemble machine learning (Random Forest + Gradient Boosting Tree) trained on ~1.3 million soil profile observations and ~1.6 million borehole records, combined with 155 environmental covariates (DEM derivatives, lithologic units, MODIS data).

- **Access method**: GDAL `/vsicurl/` remote sampling — no local download of the 8.5 GB raster required
- **CRS**: EPSG:4326 (WGS84)
- **Resolution**: ~250 m
- **Value units**: centimeters (converted to metres for DB storage)
- **NoData**: -32768

Each site is sampled at its (lon, lat) coordinate using `rasterio.sample()`. The raw value in centimeters is divided by 100 to produce `depth_to_bedrock_m`.

---

## Metric legend

| Metric               | Unit | Derivation                     | Null means                                                        |
| -------------------- | ---- | ------------------------------ | ----------------------------------------------------------------- |
| `depth_to_bedrock_m` | m    | BDTICM raster value (cm) / 100 | Raster nodata at site (coastal edge, water body, or coverage gap) |

---

## Quality grade legend

| Grade    | Meaning                                                                                                    |
| -------- | ---------------------------------------------------------------------------------------------------------- |
| `medium` | Value sampled from 250 m global raster; screening-grade — suitable for ranking, not for engineering design |
| `low`    | Sampling failed (nodata, non-positive value, or raster error)                                              |

---

## Sample data (20 Romanian sites, sorted by depth)

| #   | Site                                    | Lat     | Lon     | Depth (m) | Geological context                                |
| --- | --------------------------------------- | ------- | ------- | --------- | ------------------------------------------------- |
| 1   | Slatina power station                   | 44.4297 | 24.3642 | 16.28     | Olt valley alluvial plain                         |
| 2   | Mintia-Deva power station               | 45.9128 | 22.8261 | 17.62     | Mureș valley terraces                             |
| 3   | Brașov power station                    | 45.6623 | 25.6468 | 17.83     | Brașov Depression, intramontane basin             |
| 4   | Galați Power Station                    | 45.4233 | 28.0425 | 19.35     | Lower Danube plain, thick alluvium                |
| 5   | Doicești power station                  | 45.0029 | 25.3972 | 20.70     | Sub-Carpathian piedmont (Dâmbovița valley)        |
| 6   | Romag Termo power station               | 44.6778 | 22.6860 | 22.48     | Mehedinți Plateau foothills                       |
| 7   | Arad power station                      | 46.2224 | 21.3288 | 22.59     | Western Plain (Pannonian Basin edge)              |
| 8   | Isalnița power station                  | 44.3876 | 23.7182 | 22.93     | Jiu–Olt interfluve plain                          |
| 9   | Paroșeni power station                  | 45.3661 | 23.2614 | 23.05     | Jiu valley graben (Petroșani Basin)               |
| 10  | Rovinari power station                  | 44.9106 | 23.1348 | 23.25     | Oltenia lignite basin, Pliocene clays             |
| 11  | Turceni power station                   | 44.6697 | 23.4078 | 23.40     | Jiu valley downstream, Neogene sediments          |
| 12  | Craiova II power station                | 44.3429 | 23.8108 | 23.65     | Wallachian Plain (Getic Piedmont)                 |
| 13  | Govora power station                    | 45.0390 | 24.2876 | 26.25     | Sub-Carpathian depression (Vâlcea)                |
| 14  | Giurgiu power station                   | 43.8798 | 25.9268 | 26.96     | Danube floodplain, southern Wallachia             |
| 15  | Bucharest North East power station      | 44.4325 | 26.1039 | 29.08     | Wallachian Plain, deep Quaternary fill            |
| 16  | Târgu Jiu Thermal Plant                 | 45.0342 | 23.2747 | 30.53     | Jiu corridor, transition to hills                 |
| 17  | **Brăila-Chișcani Thermal Power Plant** | 45.2744 | 27.9291 | **30.91** | **Danube floodplain — thick Quaternary alluvium** |
| 18  | Oradea power station                    | 47.0847 | 21.8929 | 31.35     | Western Plain, Pannonian Basin sediments          |
| 19  | **FPCU Feldioara**                      | 45.7917 | 25.5889 | **32.26** | **Transylvanian Basin, deep sedimentary fill**    |
| 20  | Bacău CHP power station                 | 46.5305 | 26.9409 | 35.87     | Moldavian Sub-Carpathian foredeep                 |

---

## Distribution statistics

| Statistic           | Value  |
| ------------------- | ------ |
| N (sites with data) | 358    |
| Min                 | 0.2 m  |
| Max                 | 57.1 m |
| Mean                | 20.7 m |
| Median              | 21.3 m |
| Std dev             | 7.4 m  |
| P10                 | 10.9 m |
| P25                 | 16.4 m |
| P75                 | 25.2 m |
| P90                 | 29.0 m |

### Depth bins

| Depth range | Sites | %     |
| ----------- | ----- | ----- |
| 0–2 m       | 3     | 0.8%  |
| 2–5 m       | 3     | 0.8%  |
| 5–10 m      | 27    | 7.5%  |
| 10–15 m     | 39    | 10.9% |
| 15–20 m     | 84    | 23.5% |
| 20–25 m     | 110   | 30.7% |
| 25–30 m     | 66    | 18.4% |
| 30–40 m     | 24    | 6.7%  |
| 40–50 m     | 1     | 0.3%  |
| 50–60 m     | 1     | 0.3%  |

---

## Coverage notes

- **358/363 sites** populated (98.6%)
- **5 NULL sites**: 4 in Turkey (Güney Akdeniz, Biga, Naren Karabiga, Şırnak Silopi) and 1 in Bulgaria (Varna). These fall on raster nodata pixels — coastal/edge locations or water body cells.
- **6 shallow-bedrock sites** (<5 m): all in Turkey. These trigger a `SiteObservation` noting potential excavation difficulties per SSG-9 Rev.1 §4.1–4.12.
- **Country coverage**: 100% for 18/20 countries. Turkey: 97% (4 NULL out of 146). Bulgaria: 93% (1 NULL out of 15).
- **Limitation**: The BDTICM raster is from 2017 (SoilGrids v1). The underlying training data (soil profiles + boreholes) has a global median prediction error of ~5 m. Values are screening-grade only — site-specific geotechnical investigation is required for design-level assessment.
