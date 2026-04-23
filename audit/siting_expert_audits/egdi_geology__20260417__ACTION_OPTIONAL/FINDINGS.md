# Siting expert audit — egdi_geology

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `egdi_geology` |
| **Screening hint** | OneGeology / EGDI geology context (NH-06). |
| **Disposition folder** | `egdi_geology__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/egdi_geology_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh06_comment ILIKE '%EGDI%' OR nh.nh06_comment ILIKE '%egdi%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.975247+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BY, CZ, MK, PL, RO, SI, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/egdi_geology_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Misis Adana power station | TR | 36.84 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Lüminer Enerji power station | TR | 40.89 | 26.9 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Te-Tol power station | SI | 46.06 | 14.55 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Marianske Hory power station | CZ | 49.86 | 18.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Sostanj power station | SI | 46.37 | 15.05 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Negotino power station | MK | 41.48 | 22.1 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Kangal power station | TR | 39.08 | 37.29 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Zarnowiec power station | PL | 54.79 | 18.09 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Çayırhan power station | TR | 40.1 | 31.7 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Filyos power station | TR | 41.58 | 32.06 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Bialystok power station | PL | 53.15 | 23.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Czestochowa CHP power station | PL | 50.79 | 19.14 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Hande power station | TR | 36.78 | 35.74 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | METES power station | TR | 36.24 | 33.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Oslomej power station | MK | 41.58 | 21 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Lelchitsy power station | BY | 51.79 | 28.32 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Piast Ruch Power Station | PL | 50.02 | 19.1 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Rovinari power station | RO | 44.91 | 23.13 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Pólnoc power station | PL | 53.96 | 18.71 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | Adamow power station | PL | 52.01 | 18.55 | high | low | zhu_global_1km | low | medium | low | high |

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
