# Siting expert audit — wri_aqueduct

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `wri_aqueduct` |
| **Screening hint** | Water stress (NS-01). |
| **Disposition folder** | `wri_aqueduct__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/wri_aqueduct_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns01_comment ILIKE '%wri_aqueduct%' OR inf.water_stress_label IS NOT NULL)` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.354019+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns01_comment ILIKE '%wri_aqueduct%' OR inf.water_stress_label IS NOT NULL)" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, HU, PL, RO, SK, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/wri_aqueduct_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Barbaros-1 power station | TR | 41.8 | 35.19 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | METES power station | TR | 36.24 | 33.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Seyitömer power station | TR | 39.57 | 29.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Adana Akdeniz power station | TR | 36.82 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Helvacı power station | TR | 40.08 | 27.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Bucharest North East power station | RO | 44.43 | 26.1 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Gerze power station | TR | 41.87 | 35.12 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Borsod power station | HU | 47.9 | 21.06 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | İÇDAŞ Bekirli power station | TR | 40.4 | 27.05 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Starobesheve power station | UA | 47.8 | 38.01 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 11 | Murcki-Staszic power station | PL | 50.18 | 19.01 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Çelikler Yumurtalık power station | TR | 36.87 | 35.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Enns Power Station | AT | 48.21 | 14.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Novaky power station | SK | 48.7 | 18.53 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Kangal power station | TR | 39.08 | 37.29 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Enyat Samsun power station | TR | 40.97 | 35.67 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | FPCU Feldioara | RO | 45.79 | 25.59 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Pecs power station | HU | 46.06 | 18.26 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Afşin-Elbistan power stations | TR | 38.35 | 37.03 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Zorlu Akçakoca power station | TR | 41.09 | 31.12 | high | low | zhu_global_1km | low | medium | low | high |

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
