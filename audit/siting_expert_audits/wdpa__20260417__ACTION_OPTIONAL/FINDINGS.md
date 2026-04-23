# Siting expert audit — wdpa

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `wdpa` |
| **Screening hint** | WDPA protected-area proximity (NS-08). |
| **Disposition folder** | `wdpa__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/wdpa_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.wdpa_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%wdpa%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.306450+00:00` |
| **Generator note** | pick_site_ids filter="(inf.wdpa_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%wdpa%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BA, CZ, HU, MD, ME, PL, RS, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/wdpa_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Zeltweg power station | AT | 47.25 | 15.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Sko-Energo power station | CZ | 50.42 | 14.93 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | İzdemir Enerji power station | TR | 38.74 | 26.93 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Kakanj Thermal Power Plant | BA | 44.09 | 18.11 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Kostolac power station | RS | 44.72 | 21.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Siersza power station | PL | 50.21 | 19.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Kuchurgan power station | MD | 46.63 | 29.94 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Zarnowiec power station | PL | 54.79 | 18.09 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Vresova TPS power station | CZ | 50.26 | 12.7 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Bar power station | ME | 42.1 | 19.1 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Mohacs power station | HU | 46 | 18.68 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Stalowa Wola power station | PL | 50.55 | 22.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Kongora Thermal Power Plant | BA | 43.65 | 17.33 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Mellach power station | AT | 46.91 | 15.49 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Polaniec power station | PL | 50.44 | 21.34 | high | medium | zhu_global_1km | low | medium | low | high |
| 16 | Belchatow power station | PL | 51.27 | 19.33 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Lodz-2 power station | PL | 51.74 | 19.45 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Kolubara A power station | RS | 44.48 | 20.29 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Kurakhov power station | UA | 47.99 | 37.24 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 20 | Wroclaw power station | PL | 51.12 | 17.02 | high | medium | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 10 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
