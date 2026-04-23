# S-22 Zhu Global Liquefaction Susceptibility — Connector Report

| Field | Value |
|-------|-------|
| **Connector** | `ZhuLiquefactionConnector` |
| **Slug** | `zhu_liquefaction` |
| **Run date** | 2026-04-18 (re-confirmed 2026-04-19) |
| **Criteria served** | NH-03 (liquefaction susceptibility) |
| **Source** | Zorn & Koks (2019) global liquefaction susceptibility map, derived from Zhu et al. (2017) |
| **Reference** | Zhu, J., et al. (2017). *An updated geospatial liquefaction model for global application.* Bull. Seismol. Soc. Am., 107(3), 1365–1385. |
| **Raster** | `liquefaction_v1_deg.tif` — Zenodo record 2583746 (~442 MB, ~1 km resolution) |

---

## Methodology

The connector downloads and locally caches the Zorn & Koks (2019) global GeoTIFF, then point-samples it at each site's (lon, lat) coordinates using `rasterio`. Each raster pixel holds an integer susceptibility class 1–5; value 0 indicates no_data (water bodies or outside model domain).

- **CRS**: EPSG:4326 (WGS84)
- **Resolution**: ~1 km (~0.008333°)
- **Model inputs**: VS30 (shear-wave velocity proxy), compound topographic index (water table proxy), distance to rivers, Holocene deposits flag — all at global scale
- **No API key required** — static file download from Zenodo

---

## Metric legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| `liquefaction_suscept` | class string | Raster pixel value mapped via CLASS_MAP | Site falls on raster `no_data` pixel (value = 0); outside model domain or water body |
| `nh03_quality` | string | Always `zhu_global_1km` when populated | — |
| `nh03_comment` | text | Raw value + class + threshold legend + source | — |

---

## Susceptibility class legend

| Raster value | Class | Meaning for siting | Typical geological context |
|---|---|---|---|
| 1 | `very_low` | Negligible liquefaction concern at screening level | Competent rock, consolidated upland soils, cohesive clays |
| 2 | `low` | Low susceptibility; site-specific assessment may confirm negligible risk | Stiff soils, older alluvium, dense sands above water table |
| 3 | `moderate` | Moderate susceptibility; geotechnical investigation required during detailed assessment | Mixed alluvium, shallow water table, sub-Carpathian piedmont sediments |
| 4 | `high` | High susceptibility; significant liquefaction potential under design earthquake | Holocene alluvial plains, river terraces, saturated loose sands/silts |
| 5 | `very_high` | Very high susceptibility; near-certain liquefaction triggering under moderate shaking | Recent deltaic/coastal deposits, saturated fine sands with shallow water table |
| 0 | `no_data` | Outside model domain — not classified | Coastal water bodies, offshore pixels, model coverage gap |

> **Important**: These are **susceptibility** classes (inherent soil predisposition), not **probability of liquefaction**. Actual triggering depends on earthquake PGA. Sites with `high` susceptibility and low PGA (e.g. Turceni: PGA₄₇₅ = 0.08 g) may have lower actual risk than the class alone implies.

---

## Quality grade legend

| Grade | Meaning |
|-------|---------|
| `zhu_global_1km` | Value sampled from Zhu/Zorn global raster at ~1 km resolution. Screening-grade only — not a substitute for site-specific geotechnical investigation per SSG-9 Rev.1 §4.1–4.12 |

---

## Sample data — all 24 Romanian sites

| # | Site | Lat | Lon | Raster value | Class | Geological context |
|---|------|-----|-----|---|---|---|
| 1 | Arad power station | 46.2224 | 21.3288 | 4 | **high** | Western Plain — Pannonian Basin alluvium, shallow water table |
| 2 | Bacău CHP power station | 46.5305 | 26.9409 | 4 | **high** | Moldavian Sub-Carpathian foredeep — Siret river alluvium |
| 3 | Braila power station (1) | 45.1650 | 27.9234 | 4 | **high** | Danube floodplain — Holocene saturated alluvium |
| 4 | Braila power station (2) | 45.1650 | 27.9234 | 4 | **high** | Danube floodplain — Holocene saturated alluvium |
| 5 | Brăila-Chișcani Thermal Power Plant | 45.2744 | 27.9291 | 3 | **moderate** | Danube floodplain margin — mixed alluvium/cohesive soils |
| 6 | Brașov power station | 45.6623 | 25.6468 | 3 | **moderate** | Brașov Depression intramontane basin |
| 7 | Bucharest North East power station | 44.4325 | 26.1039 | 3 | **moderate** | Wallachian Plain — Quaternary loess and alluvium |
| 8 | Craiova II power station | 44.3429 | 23.8108 | 3 | **moderate** | Getic Piedmont — mixed Neogene/alluvial cover |
| 9 | Doicești power station | 45.0029 | 25.3972 | 3 | **moderate** | Sub-Carpathian piedmont — Dâmbovița valley alluvium |
| 10 | FPCU Feldioara | 45.7917 | 25.5889 | 4 | **high** | Transylvanian Basin — Olt valley alluvial terrace |
| 11 | Galați Power Station | 45.4233 | 28.0425 | 4 | **high** | Lower Danube plain — thick Holocene alluvium |
| 12 | Giurgiu power station | 43.8798 | 25.9268 | 3 | **moderate** | Southern Wallachia — Danube floodplain terrace |
| 13 | Govora power station | 45.0390 | 24.2876 | 3 | **moderate** | Vâlcea Sub-Carpathian depression — mixed sediments |
| 14 | Iași-2 power station | 47.1473 | 27.7172 | 4 | **high** | Moldavian Plateau — Bahlui river alluvial plain |
| 15 | Isalnița power station | 44.3876 | 23.7182 | 3 | **moderate** | Jiu–Olt interfluve plain |
| 16 | Mintia-Deva power station | 45.9128 | 22.8261 | 3 | **moderate** | Mureș valley alluvial terrace |
| 17 | Oradea power station | 47.0847 | 21.8929 | 4 | **high** | Western Plain — Criș river alluvium, high water table |
| 18 | Paroșeni power station | 45.3661 | 23.2614 | 1 | **very_low** | Petroșani Basin graben — consolidated carboniferous strata |
| 19 | Romag Termo power station | 44.6778 | 22.6860 | 1 | **very_low** | Mehedinți Plateau foothills — competent limestone/dolomite |
| 20 | Rovinari power station | 44.9106 | 23.1348 | 1 | **very_low** | Oltenia lignite basin — stiff Pliocene lacustrine clays |
| 21 | Slatina power station | 44.4297 | 24.3642 | 1 | **very_low** | Olt valley — competent Neogene terrace gravels |
| 22 | Suceava power station | 47.6519 | 26.2983 | 1 | **very_low** | Moldavian Plateau — consolidated Sarmatian sands/clays |
| 23 | Târgu Jiu Thermal Plant | 45.0342 | 23.2747 | 3 | **moderate** | Jiu corridor transition zone |
| 24 | Turceni power station | 44.6697 | 23.4078 | 4 | **high** | Jiu valley — Neogene/Quaternary alluvial mix |

---

## Coverage notes

- **354/363 sites** populated (97.5%)
- **9 NULL sites**: all Turkish coastal/port stations (Biga, Çatalağzı, Amasra, Naren Karabiga, Ağan, Cenal, Güney Akdeniz, İÇDAŞ Biga, Star Refinery Socar). These fall on raster `no_data` pixels (value = 0) — Aegean/Black Sea coastline and industrial port zones outside the Zhu model domain. **Not fixable.**
- **Romania distribution**: very_low: 5 (21%), moderate: 9 (37%), high: 10 (42%). No `very_high` sites in Romania.
- **Project-wide distribution**: moderate 150 (41.3%), very_low 137 (37.7%), high 62 (17.1%), low 4 (1.1%), very_high 1 (0.3%), NULL 9 (2.5%)
- **Resolution limitation**: At ~1 km, the raster averages over heterogeneous geology. Sites on the boundary of alluvial and competent terrain may receive a class that reflects the dominant landscape rather than the precise foundation footprint. Site-specific geotechnical investigation is required for any site rated `moderate` or higher.
