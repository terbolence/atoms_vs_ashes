# Siting expert audit — onegeology

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `onegeology` |
| **Screening hint** | OneGeology map context (NH-06). |
| **Disposition folder** | `onegeology__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/onegeology_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh06_comment ILIKE '%OneGeology%' OR nh.nh06_comment ILIKE '%onegeology%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.183222+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BY, CZ, HU, PL, RO, SI, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/onegeology_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Çalışkan Ceyhan power station | TR | 36.94 | 35.99 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Pulawy power station (Grupa Azoty) | PL | 51.42 | 21.97 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Prerov power station | CZ | 49.45 | 17.43 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Aksa Akrilik power station | TR | 40.69 | 29.41 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Şırnak Silopi (CİNER) power station | TR | 37.31 | 42.59 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Dobrotvir power station | UA | 50.21 | 24.37 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Meda power station | TR | 40.97 | 27.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Brasov power station | RO | 45.66 | 25.65 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Kipas MMP power station | TR | 37.77 | 27.45 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Chvaletice power station | CZ | 50.03 | 15.45 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Mecsek Hills power station | HU | 46.1 | 18.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Trbovlje power station | SI | 46.13 | 15.06 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Kardemir Karabük Demir Çelik power stat… | TR | 41.51 | 31.91 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Starobesheve power station | UA | 47.8 | 38.01 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 15 | Zelwa power station | BY | 53.15 | 24.82 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Şevketiye Lapseki power station | TR | 40.4 | 26.79 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Güneybatı Anadolu power station | TR | 37.31 | 27.78 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Adamow power station | PL | 52.01 | 18.55 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Diler (Akbayir) Elbistan power station | TR | 38.17 | 37.37 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Yunus Emre power station | TR | 39.98 | 31.64 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 8 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (experts/quality/siting_expert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
