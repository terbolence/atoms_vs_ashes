# Siting expert audit — seismic_hazard

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `seismic_hazard` |
| **Screening hint** | Seismic hazard (NH-01). |
| **Disposition folder** | `seismic_hazard__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/seismic_hazard_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh01_source ILIKE '%efehr%' OR nh.nh01_source ILIKE '%ESHM%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.260734+00:00` |
| **Generator note** | pick_site_ids filter="(nh.nh01_source ILIKE '%efehr%' OR nh.nh01_source ILIKE '%ESHM%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, BY, CZ, HU, PL, RO, SK, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/seismic_hazard_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Tusimice power station | CZ | 50.38 | 13.34 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Vresova TPS power station | CZ | 50.26 | 12.7 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Gacko Thermal Power Plant | BA | 43.17 | 18.51 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Adana Ceyhan power station | TR | 37.03 | 35.82 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Borsod power station | HU | 47.9 | 21.06 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Amasra Bartın power station | TR | 41.73 | 32.35 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Zuevskaya power station | UA | 48.03 | 38.29 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 8 | Atakaş power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Isalnita power station | RO | 44.39 | 23.72 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Şırnak Silopi (CİNER) power station | TR | 37.31 | 42.59 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Helvacı power station | TR | 40.08 | 27.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Yüksek Gölovası power station | TR | 37.37 | 35.71 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Zelwa power station | BY | 53.15 | 24.82 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Kladno power station | CZ | 50.15 | 14.13 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Güneybatı Anadolu power station | TR | 37.31 | 27.78 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Burnaz power station | TR | 36.49 | 36.19 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Karapinar Konya Şeker power station | TR | 37.72 | 33.55 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Martinska power station | SK | 49.06 | 18.91 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Gorzow power station | PL | 52.75 | 15.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | Zafer power station | TR | 41.6 | 32.51 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 9 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
