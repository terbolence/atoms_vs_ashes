# Siting expert audit — copernicus_ems

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `copernicus_ems` |
| **Screening hint** | CEMS-based hazard layers (NH-08/09/10 family). |
| **Disposition folder** | `copernicus_ems__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/copernicus_ems_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh09_comment ILIKE '%CEMS%' OR nh.nh08_comment ILIKE '%CEMS%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.883966+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BG, CZ, LV, PL, RS, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/copernicus_ems_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Kıvanç power station | TR | 36.34 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Ladyzhyn power station | UA | 48.71 | 29.22 | high | medium | zhu_global_1km | low | medium | low | high |
| 3 | Siersza power station | PL | 50.21 | 19.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Adana Ceyhan power station | TR | 37.03 | 35.82 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Uluköy power station | TR | 38.2 | 30.27 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Swiecie Pulp Mill power station | PL | 53.39 | 18.37 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Kurzeme power station | LV | 57.41 | 21.59 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Leczna Power Station (Enea) | PL | 51.3 | 22.88 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Bandırma Elektrik power station | TR | 40.31 | 27.73 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Diler (Akbayir) Elbistan power station | TR | 38.17 | 37.37 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Opalenie power station | PL | 53.74 | 18.82 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Zabrze power station | PL | 50.32 | 18.79 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Karvina power station | CZ | 49.82 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Lom Power Station | BG | 43.78 | 23.22 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Gubin Power Project | PL | 51.95 | 14.73 | high | medium | zhu_global_1km | low | medium | low | high |
| 16 | Aksa Akrilik power station | TR | 40.69 | 29.41 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Hakan Enerji power station | TR | 36.84 | 35.89 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Polat power station | TR | 39.62 | 29.44 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Tisova power station | CZ | 50.15 | 12.61 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Kolubara B power station | RS | 44.47 | 20.28 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 7 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (experts/quality/siting_expert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
