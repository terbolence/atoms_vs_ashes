# Connector Inventory, API Keys & Progress Rollup

Authoritative status for all programmable data sources. Migrated from former §1.3–1.5 of the monolithic data source access plan (2026-04-17 refresh — reconciled with codebase ground truth).

---

## 1. Per-source connector inventory (master table)

*Est. hours* are planning estimates, not spent effort.

| Source | Category | Status | Est. hours |
| ------ | -------- | ------ | ---------- |
| **Existing connectors** | | | |
| I-1 CORINE WFS | Existing | ✅ Implemented | 0 |
| I-2 OSM Overpass (base) | Existing | ✅ Implemented | 0 |
| I-3 WorldPop / Population | Existing | ✅ Implemented | 0 |
| I-4 GEM Coal Plant Tracker (base) | Existing | ✅ Implemented | 0 |
| **Original API connectors (S-01 to S-17)** | | | |
| S-01 GEM/SHARE Seismic | Phase 1 | ✅ Implemented (`connectors/seismic_hazard`) | 0 (done) |
| S-02 EGDI | Phase 1 | ✅ Implemented | 0 (done) |
| S-03 OneGeology | Phase 1 | ✅ Implemented (`connectors/onegeology`) | 0 (done) |
| S-04 Copernicus CDS / ERA5 | Phase 2 | ✅ Implemented (`connectors/copernicus_era5`) | 0 (done) |
| S-05 Copernicus Sentinel Hub | Phase 2 | 📋 Spec done · ⏳ Pending | 24 |
| S-06 Google Earth Engine | Phase 2 | ⏸️ Implemented but **disabled** (`connectors.earth_engine.enabled: false`; optional `pip install '.[earth-engine]'`) | 0 |
| S-07 Smithsonian GVP | Phase 1 | ✅ Implemented (`connectors/smithsonian_gvp`) | 0 (done) |
| S-08 EU Flood Risk Maps | Phase 1 | ✅ Implemented | 0 (done) |
| S-09 GFMS | Phase 2 | ✅ Implemented (`connectors/gfms`) | 0 (done) |
| S-10 Copernicus EMS | Phase 1 | ✅ Implemented | 0 (done) |
| S-11 NOAA NCEI | Phase 2 | ✅ Implemented (`connectors/noaa_ncei`) | 0 (done) |
| S-12 EU SEVESO III | Phase 1 | ✅ Implemented | 0 (done) |
| S-13 ENTSO-E | Phase 1–2 | ✅ Implemented | 0 (done) |
| S-14 Natura 2000 WFS | Phase 1 | ✅ Implemented (`connectors/natura2000`) | 0 (done) |
| S-15 WDPA | Phase 1 | ✅ Implemented (`connectors/wdpa`) | 0 (done) |
| S-16 Eurostat GISCO | Phase 1 | ✅ Implemented (`connectors/eurostat_gisco`) | 0 (done) |
| S-17 Eurostat Projections / NSOs | Phase 2 | ✅ Implemented (`connectors/eurostat_projections`) | 0 (done) |
| **Newly identified (S-18 to S-44)** | | | |
| S-18 EFSM20 Seismogenic Faults | Phase 1 | ✅ Implemented (`connectors/efsm20_faults`) | 0 (done) |
| S-19 Copernicus DEM (GLO-30) | Phase 1 | ✅ Implemented | 0 (done) |
| S-20 GHSL GHS-POP | Phase 1 | ✅ Implemented (`connectors/ghsl_pop`) | 0 (done) |
| S-21 SoilGrids | Phase 2 | ⏳ Pending | 10 |
| S-22 Zhu Liquefaction | Phase 1 | ✅ Implemented (`connectors/zhu_liquefaction`) | 0 (done) |
| S-23 ELSUS v2 + NASA Landslides | Phase 2 | ⏳ Pending | 8 |
| S-24 USGS VS30 | Phase 2 | ⏳ Pending | 4 |
| S-25 WOKAM Karst | Phase 1 | ✅ Implemented (`connectors/wokam`) | 0 (done) |
| S-26 Copernicus EGMS | Phase 2 | ⏳ Pending | 10 |
| S-27 GEM Fossil Trackers | Phase 2 | ⏳ Pending | 8 |
| S-28 Copernicus Marine + Storm Surge | Phase 2 | ⏳ Pending | 16 |
| S-29 EU-Hydro + HydroSHEDS | Phase 2 | ✅ Implemented (`connectors/hydrorivers`) | 0 (done) |
| S-30 GloFAS v4 (CDS) | Phase 2 | ✅ Implemented (`connectors/glofas_discharge`) | 0 (done) |
| S-31 GRanD Dams | Phase 2 | ⏳ Pending | 4 |
| S-32 JRC Global Surface Water | Phase 2 | ⏳ Pending | 6 |
| S-33 WRI Aqueduct 4.0 | Phase 2 | ✅ Implemented (`connectors/wri_aqueduct`) | 0 (done) |
| S-34 ESWD Severe Weather | Phase 3 | ⏳ Pending | 6 |
| S-35 EFFIS + FIRMS Fire | Phase 2 | ⏳ Pending | 10 |
| S-36 ESA WorldCover | Phase 2 | ✅ Implemented | 8 |
| S-37 EEA Industrial Emissions | Phase 1 | ✅ Implemented | 0 (done) |
| S-38 Natural Earth | Phase 2 | ⏳ Pending | 2 |
| S-39 OurAirports | Phase 1 | ✅ Implemented (`connectors/ourairports`) | 0 (done) |
| S-40 OpenSky Network | Phase 3 | ⏳ Pending | 8 |
| S-41 ERA RINF Railway | Phase 3 | ⏳ Pending | 6 |
| S-42 World Bank WDI | Phase 2 | ⏳ Pending | 8 |
| S-43 IAEA CNPP/PRIS | Phase 2 | ⏳ Pending | 10 |
| S-44 Eurobarometer | Phase 3 | ⏳ Pending | 4 |
| S-45 PyPSA-Eur Grid Topology | Phase 2 | ⏳ Pending | 8 |
| **Fix / orchestration** | | | |
| FIX-03 OSM Site Area Enrichment | Phase 1 | ⚠️ Partial (CLI `site-area` registered; `buildable_area_ha` 99.7%, `largest_contiguous_ha` 68.9%, `patch_count` 0%) | — |
| FIX-04 OSM Avoidance Batch (military) | Phase 1 | 📋 Spec done · ⏳ Pending | 8 |
| FIX-02 NS-02 Grid Pipeline (remainder) | Phase 1–2 | ⚠️ Partial (S-13 / OSM shipped) | — |
| **Phase 3 extensions** | | | |
| EXT-01 I-2 OSM Enhanced queries | Phase 3 | ⏳ Pending | 40 |
| EXT-02 I-4 GEM Enhanced synergy | Phase 3 | ⏳ Pending | 8 |
| **Internal derived layers** | | | |
| DRV-01 NH-14 NaTech Composite | Phase 3 | ⏳ Pending | 12 |
| DRV-02 EP Composite Scoring | Phase 3 | ⏳ Pending | 16 |
| DRV-03 Coal-to-Nuclear Synergy | Phase 3 | ⏳ Pending | 8 |
| **National sources** | | | |
| N-01 to N-21 | Phase 4 | ⏳ Pending | 168 |

**Totals (remaining programmable implementation, rough):** sum ⏳ rows in this table + Phase 4 national hours; refresh after each connector ships.

---

## 2. API keys and live reports

| API | Key type | Registration | Used for |
| --- | -------- | -------------- | -------- |
| WDPA / Protected Planet | Free token | https://api.protectedplanet.net/ | S-15 (batch + API) |
| ENTSO-E Transparency | Free token | https://transparency.entsoe.eu/ | S-13 |
| GeoNames | Free username | https://www.geonames.org/login | Optional population fallback |
| Copernicus CDS | Free account | https://cds.climate.copernicus.eu/ | S-04, S-28, S-30 |
| Copernicus Sentinel Hub | Copernicus account | https://dataspace.copernicus.eu/ | S-05 |

**Reports:** `python scripts/report_enrichment_coverage.py --write-report` → `reports/coverage_latest.md`. **Effort / tokens:** `python scripts/report_effort_metrics.py --write-report` → `reports/effort_latest.md`.

---

## 3. Progress summary (rollup)

*Updated 2026-04-17 — reconciled with codebase (connector directories + CLI registration).*

| Category | Total | Spec done | Implemented in code | Remaining work |
| -------- | ----- | --------- | --------------------- | -------------- |
| Existing connectors (I-1–I-4) | 4 | — | 4 | 0 |
| S-01–S-17 original API set | 17 | 17 | **16** (S-01, S-02, S-03, S-04, S-06, S-07, S-08, S-09, S-10, S-11, S-12, S-13, S-14, S-15, S-16, S-17) | **1** (S-05 Sentinel Hub) |
| S-18–S-45 new sources | 28 | many | **14** (S-18, S-19, S-20, S-22, S-25, S-29, S-30, S-33, S-36, S-37, S-39 + GeoNames dump, HydroRIVERS, GloFAS) | See §1 |
| FIX / DRV / EXT / National | — | partial | partial (FIX-03 CLI wired, partial fill) | FIX-04, DRV-*, EXT-*, N-* |

**Total connector packages:** 31 directories under `src/atoms_vs_ashes/connectors/` (30 connectors + `http_audit.py` utility).

**GeoNames cities5000 (local dump)** — `connectors/geonames_dump`: `enrich download-geonames-cities`, `enrich geonames-ri05` for RI-05 gap-fill without live GeoNames API calls.
