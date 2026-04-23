# Siting expert audit — copernicus_era5

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `copernicus_era5` |
| **Screening hint** | Climate means and extremes (NH-10–12, NS-01, RI-01). |
| **Disposition folder** | `copernicus_era5__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/copernicus_era5_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh10_comment ILIKE '%ERA5%' OR nh.nh11_comment ILIKE '%ERA5%' OR nh.nh12_comment ILIKE '%ERA5%' OR rd.ri01_comment ILIKE '%ERA5%' OR inf.ns01_comment ILIKE '%copernicus_era5%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.903788+00:00` |
| **Generator note** | pick_site_ids filter="(nh.nh10_comment ILIKE '%ERA5%' OR nh.nh11_comment ILIKE '%ERA5%' OR nh.nh12_comment ILIKE '%ERA5%' OR rd.ri01_comment ILIKE '%ERA5%' OR inf.ns01_comment ILIKE '%copernicus_era5%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, CZ, HU, PL, RO, SI, SK, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/copernicus_era5_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Konya Karapınar power station | TR | 37.61 | 33.59 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Pecs power station | HU | 46.06 | 18.26 | high | medium | zhu_global_1km | low | medium | low | high |
| 3 | Romag Termo power station | RO | 44.68 | 22.69 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | METES power station | TR | 36.24 | 33.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Opatovice power station | CZ | 50.12 | 15.79 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Ada Yesildag Enerji power station | TR | 36.38 | 33.93 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Kakanj Thermal Power Plant | BA | 44.09 | 18.11 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Saltukova power station | TR | 41.52 | 32.09 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | İskenderun power station | TR | 36.59 | 36.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Tufanbeyli power station | TR | 38.19 | 36.27 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Skawina power station | PL | 49.98 | 19.81 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Novaky power station | SK | 48.7 | 18.53 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Lodz-2 power station | PL | 51.74 | 19.45 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Zafer power station | TR | 41.6 | 32.51 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Borsod power station | HU | 47.9 | 21.06 | high | medium | zhu_global_1km | low | medium | low | high |
| 16 | Hodonin power station | CZ | 48.85 | 17.12 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Ergene power station | TR | 41.24 | 27.7 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Biga power station | TR | 40.47 | 27.29 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Çalışkan Ceyhan power station | TR | 36.94 | 35.99 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Te-Tol power station | SI | 46.06 | 14.55 | high | medium | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 8 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
