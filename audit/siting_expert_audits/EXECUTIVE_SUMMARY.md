# Executive summary — siting expert audit programme (all connectors)

**Date of this summary:** 2026-04-17 (refreshed after full generator pass)  
**Audit batch token:** `20260417` (folder suffix `__20260417__ACTION_OPTIONAL`)  
**Canonical prompt:** [`prompts/sitingExpert.md`](../../prompts/sitingExpert.md)  
**Sample generator:** [`scripts/generate_siting_expert_audits.py`](../../scripts/generate_siting_expert_audits.py)

---

## Purpose

This folder tree implements the **30-step succession** from the siting expert / API-database plan: **one connector → one audit folder** containing `FINDINGS.md` and `SAMPLES.json`. The goal is domain review of **20 API-database samples per connector** against screening plausibility and integration quality, with disposition (`ACTION_REQUIRED` / `ACTION_OPTIONAL` / `NO_ACTION`) matching real findings once reviews are complete.

---

## Overall status (roll-up)

| Metric | Value |
| ------ | ----- |
| Connectors in programme | **30** (same order as `src/atoms_vs_ashes/connectors/__init__.py` `__all__`; `OverpassClient` → `osm`) |
| Folders present | **30** (`*__20260417__ACTION_OPTIONAL/`) |
| Samples per connector (`SAMPLES.json` → `samples`) | **20** each (stratified pick, with random **padding** when a filter matches fewer than 20 but at least 5 sites) |
| Machine `FINDINGS.md` | **30** — data tables + executive summary from `generate_siting_expert_audits.py` |
| Full human §H (domain judgement) | **1 / 30** — `zhu_liquefaction` pilot (`FINDINGS.md` includes lessons learned, severity, acceptance); other connectors await expert pass |

**Bottom line:** The batch **`20260417`** is **materialized end-to-end** (DB pull + JSON + machine-assisted `FINDINGS.md`). **Stratification SQL** was aligned with `site_*` ORM columns (e.g. no `nh03_source`, `ns02_source`, `hi01_source` — those filters were corrected). Remaining work is **human** §D–§H review per connector, **connector sample reports** under `docs/connector_reports/`, and any engineering follow-ups noted in each `FINDINGS.md`.

---

## Technical notes (this batch)

- **SQL filters:** Several earlier filters referenced non-existent columns (`nh06_source`, `ns02_source`, `hi02_source`, etc.); the generator now uses `*_comment` / `*_quality` patterns consistent with [`src/atoms_vs_ashes/db/models.py`](../../src/atoms_vs_ashes/db/models.py).
- **Padding:** If a stratified query returns 5–19 sites, additional sites are drawn at random (excluding duplicates) until 20 rows are assembled, so shortlists like hydrorivers/seveso still reach **n = 20**.
- **Superseded folders:** Previous `*__20260417__ACTION_REQUIRED/` trees (empty or stale) were removed after this successful run; **`ACTION_OPTIONAL`** here means “samples present — review depth TBD,” not “no issues.”

---

## Per-connector index (batch `20260417`)

All paths under `docs/siting_expert_audits/`. Each row links to the canonical **`ACTION_OPTIONAL`** folder for this batch.

| # | Slug | Audit folder | Samples | Expert review |
| --- | --- | --- | --- | --- |
| 1 | copernicus_dem | [`copernicus_dem__20260417__ACTION_OPTIONAL/`](copernicus_dem__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 2 | copernicus_ems | [`copernicus_ems__20260417__ACTION_OPTIONAL/`](copernicus_ems__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 3 | copernicus_era5 | [`copernicus_era5__20260417__ACTION_OPTIONAL/`](copernicus_era5__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 4 | corine | [`corine__20260417__ACTION_OPTIONAL/`](corine__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 5 | eea_industrial | [`eea_industrial__20260417__ACTION_OPTIONAL/`](eea_industrial__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 6 | efsm20_faults | [`efsm20_faults__20260417__ACTION_OPTIONAL/`](efsm20_faults__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 7 | egdi_geology | [`egdi_geology__20260417__ACTION_OPTIONAL/`](egdi_geology__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 8 | entso_e | [`entso_e__20260417__ACTION_OPTIONAL/`](entso_e__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 9 | eu_flood_risk | [`eu_flood_risk__20260417__ACTION_OPTIONAL/`](eu_flood_risk__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 10 | eurostat_gisco | [`eurostat_gisco__20260417__ACTION_OPTIONAL/`](eurostat_gisco__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 11 | eurostat_projections | [`eurostat_projections__20260417__ACTION_OPTIONAL/`](eurostat_projections__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 12 | geonames_dump | [`geonames_dump__20260417__ACTION_OPTIONAL/`](geonames_dump__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 13 | gfms | [`gfms__20260417__ACTION_OPTIONAL/`](gfms__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 14 | ghsl_pop | [`ghsl_pop__20260417__ACTION_OPTIONAL/`](ghsl_pop__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 15 | glofas_discharge | [`glofas_discharge__20260417__ACTION_OPTIONAL/`](glofas_discharge__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 16 | hydrorivers | [`hydrorivers__20260417__ACTION_OPTIONAL/`](hydrorivers__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 17 | natura2000 | [`natura2000__20260417__ACTION_OPTIONAL/`](natura2000__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 18 | noaa_ncei | [`noaa_ncei__20260417__ACTION_OPTIONAL/`](noaa_ncei__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 19 | onegeology | [`onegeology__20260417__ACTION_OPTIONAL/`](onegeology__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 20 | ourairports | [`ourairports__20260417__ACTION_OPTIONAL/`](ourairports__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 21 | osm | [`osm__20260417__ACTION_OPTIONAL/`](osm__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 22 | population | [`population__20260417__ACTION_OPTIONAL/`](population__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 23 | seismic_hazard | [`seismic_hazard__20260417__ACTION_OPTIONAL/`](seismic_hazard__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 24 | seveso | [`seveso__20260417__ACTION_OPTIONAL/`](seveso__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 25 | smithsonian_gvp | [`smithsonian_gvp__20260417__ACTION_OPTIONAL/`](smithsonian_gvp__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 26 | wdpa | [`wdpa__20260417__ACTION_OPTIONAL/`](wdpa__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 27 | wokam_karst | [`wokam_karst__20260417__ACTION_OPTIONAL/`](wokam_karst__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 28 | worldcover | [`worldcover__20260417__ACTION_OPTIONAL/`](worldcover__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 29 | wri_aqueduct | [`wri_aqueduct__20260417__ACTION_OPTIONAL/`](wri_aqueduct__20260417__ACTION_OPTIONAL/) | 20 | Machine-assisted |
| 30 | zhu_liquefaction | [`zhu_liquefaction__20260417__ACTION_OPTIONAL/`](zhu_liquefaction__20260417__ACTION_OPTIONAL/) | 20 | **Pilot — full §H** (human) |

**Pilot:** [`zhu_liquefaction__20260417__ACTION_OPTIONAL/FINDINGS.md`](zhu_liquefaction__20260417__ACTION_OPTIONAL/FINDINGS.md) is the reference **human-completed** §H audit (tables and narrative aligned with current `SAMPLES.json`).

---

## Interpretation for leadership

- **What is done:** All **30** connectors have **20-row** `SAMPLES.json` pulls and **machine-assisted** `FINDINGS.md` files suitable for expert review.
- **What remains:** **Domain sign-off** per connector (and **`docs/connector_reports/<slug>_sample_report.md`** where still missing — called out in each machine `FINDINGS.md`).
- **Risk:** **`ACTION_OPTIONAL` in folder names** reflects “data present / not an empty batch,” **not** a product sign-off — final disposition should follow each expert review.
