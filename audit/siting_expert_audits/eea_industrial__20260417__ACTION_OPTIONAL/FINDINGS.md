# Siting expert audit — eea_industrial

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `eea_industrial` |
| **Screening hint** | Industrial hazardous facilities proximity (HI-02). |
| **Disposition folder** | `eea_industrial__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/eea_industrial_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(hh.hi02_comment ILIKE '%eea_industrial%' OR hh.hi02_comment ILIKE '%eea.europa%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.944738+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BG, CZ, ME, PL, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/eea_industrial_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Maoce Power Station | ME | 43.36 | 19.36 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Bolu Göynük power station | TR | 40.25 | 30.81 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Berane power station | ME | 42.84 | 19.86 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Albayrak Varaka Paper power station | TR | 39.56 | 27.97 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Ada Yumurtalık power station | TR | 36.84 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Slavyansk power station | UA | 48.87 | 37.77 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 7 | Kangal Etyemez power station | TR | 39.08 | 37.3 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Cenal power station | TR | 40.42 | 27.32 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Soma Kolin power station | TR | 39.32 | 27.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Belchatow power station | PL | 51.27 | 19.33 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Maritsa Iztok-1 power station | BG | 42.16 | 25.91 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Ilgın power station | TR | 38.26 | 31.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Riedersbach power station | AT | 48.03 | 12.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Plzenska energetika ELU III power stati… | CZ | 49.74 | 13.35 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Prunerov power station | CZ | 50.42 | 13.26 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Sarp Golvasi power station | TR | 37.37 | 35.71 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Detmarovice power station | CZ | 49.91 | 18.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Dinar power station | TR | 38.06 | 30.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Seyitömer power station | TR | 39.57 | 29.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Helvacı power station | TR | 40.08 | 27.17 | high | low | zhu_global_1km | low | medium | low | medium |

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
