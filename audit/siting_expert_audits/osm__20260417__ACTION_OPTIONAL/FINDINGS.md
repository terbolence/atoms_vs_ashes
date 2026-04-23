# Siting expert audit — osm

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `osm` |
| **Screening hint** | OSM transport / infrastructure (NS-03). |
| **Disposition folder** | `osm__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/osm_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns03_comment ILIKE '%Source: OSM Overpass API%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.218320+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns03_comment ILIKE '%Source: OSM Overpass API%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BG, CZ, PL, RO, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/osm_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Habaş power station | TR | 38.77 | 26.95 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Bobov Dol power station | BG | 42.29 | 23.03 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Slatina power station | RO | 44.43 | 24.36 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Malesice power station | CZ | 50.08 | 14.53 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Gerze power station | TR | 41.87 | 35.12 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Kryvorizka power station | UA | 47.54 | 33.66 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 7 | Hodonin power station | CZ | 48.85 | 17.12 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Adana Ceyhan power station | TR | 37.03 | 35.82 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Krakow-Leg power station | PL | 50.05 | 20.01 | high | medium | zhu_global_1km | low | medium | low | high |
| 10 | Mellach power station | AT | 46.91 | 15.49 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Miechowice power station | PL | 50.35 | 18.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Tunçbilek power station | TR | 39.62 | 29.47 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Güney Akdeniz power station | TR | 36.42 | 35.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Trinec-E3 power station | CZ | 49.68 | 18.67 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Adana Akdeniz power station | TR | 36.82 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Duernrohr power station | AT | 48.33 | 15.92 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Pulawy power station (Vattenfall) | PL | 51.42 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Gebze Çolakoğlu power station | TR | 40.78 | 29.54 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Plzen CHP power station | CZ | 49.75 | 13.4 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Trypilska power station | UA | 50.13 | 30.75 | insufficient | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 7 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
