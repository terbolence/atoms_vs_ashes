# Siting expert audit — wokam_karst

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `wokam_karst` |
| **Screening hint** | Karst susceptibility (NH-05). |
| **Disposition folder** | `wokam_karst__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/wokam_karst_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh05_comment ILIKE '%wokam%' OR nh.nh05_comment ILIKE '%WOKAM%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.322756+00:00` |
| **Generator note** | pick_site_ids filter="(nh.nh05_comment ILIKE '%wokam%' OR nh.nh05_comment ILIKE '%WOKAM%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, PL, RO, SI, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/wokam_karst_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Sanko Gölbaşı power station | TR | 37.82 | 37.72 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Cenal power station | TR | 40.42 | 27.32 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Meda power station | TR | 40.97 | 27.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Bandırma Elektrik power station | TR | 40.31 | 27.73 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Pólnoc power station | PL | 53.96 | 18.71 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | İzdemir Enerji power station | TR | 38.74 | 26.93 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Kardemir Karabük Demir Çelik power stat… | TR | 41.51 | 31.91 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Ugljevik power station | BA | 44.68 | 18.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Trbovlje power station | SI | 46.13 | 15.06 | high | medium | zhu_global_1km | low | medium | low | high |
| 10 | Chernihiv power station | UA | 51.45 | 31.26 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 11 | Lublin Power Station | PL | 51.21 | 22.55 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Iasi-2 power station | RO | 47.15 | 27.72 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Umut power station | TR | 41.13 | 37.16 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Babadere power station | TR | 39.61 | 26.19 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Rovinari power station | RO | 44.91 | 23.13 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Kangal Etyemez power station | TR | 39.08 | 37.3 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Zafer power station | TR | 41.6 | 32.51 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Halemba power station | PL | 50.23 | 18.85 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Oradea power station | RO | 47.08 | 21.89 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | HEMA Amasra power station | TR | 41.72 | 32.35 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 6 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
