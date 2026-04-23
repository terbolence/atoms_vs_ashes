# Siting expert audit — seveso

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `seveso` |
| **Screening hint** | Seveso establishment proximity (HI-02). |
| **Disposition folder** | `seveso__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/seveso_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(hh.hi02_comment ILIKE '%seveso%' OR hh.hi02_comment ILIKE '%SEVESO%' OR hh.nearest_seveso_km IS NOT NULL)` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260413T204132_395ecad8` |
| **Extraction timestamp (UTC)** | `2026-04-17T20:00:29.671117+00:00` |
| **Generator note** | pick_site_ids filter="(hh.hi02_comment ILIKE '%seveso%' OR hh.hi02_comment ILIKE '%SEVESO%' OR hh.nearest_seveso_km IS NOT NULL)" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BG, CZ, HU, PL, RO, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/seveso_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Ruse Iztok power station | BG | 43.87 | 26.01 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | ZW Nowa power station | PL | 50.35 | 19.28 | high | medium | zhu_global_1km | low | medium | low | high |
| 3 | Jaworzno power station | PL | 50.21 | 19.23 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Slatina power station | RO | 44.43 | 24.36 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Giurgiu power station | RO | 43.88 | 25.93 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Zarnowiec power station | PL | 54.79 | 18.09 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Siersza power station | PL | 50.21 | 19.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 8 | Gdansk-2 power station | PL | 54.38 | 18.64 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Porici power station | CZ | 50.57 | 15.96 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Dobrotvir power station | UA | 50.21 | 24.37 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Kladno power station | CZ | 50.15 | 14.13 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Piast Ruch Power Station | PL | 50.02 | 19.1 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Kryvorizka power station | UA | 47.54 | 33.66 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 14 | Zofiowka Mine power station | PL | 49.96 | 18.63 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Lüminer Enerji power station | TR | 40.89 | 26.9 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | ZETES power stations | TR | 41.51 | 31.89 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Tiszapalkonya power station | HU | 47.92 | 21.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Kangal power station | TR | 39.08 | 37.29 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Kipas MMP power station | TR | 37.77 | 27.45 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Avdan power station | TR | 37.75 | 29.09 | high | low | zhu_global_1km | low | medium | low | medium |

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
