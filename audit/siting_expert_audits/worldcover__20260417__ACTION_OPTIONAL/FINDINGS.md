# Siting expert audit — worldcover

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `worldcover` |
| **Screening hint** | ESA WorldCover land cover (NS-04). |
| **Disposition folder** | `worldcover__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/worldcover_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns04_comment ILIKE '%WorldCover%' OR inf.ns04_quality::text ILIKE '%worldcover%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.337408+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns04_comment ILIKE '%WorldCover%' OR inf.ns04_quality::text ILIKE '%worldcover%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, RS, TR, UA, XK.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/worldcover_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Kolubara B power station | RS | 44.47 | 20.28 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Sanko Yumurtalık power station | TR | 36.88 | 35.89 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Atakaş power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Eti Maden Bandirma power station | TR | 40.33 | 27.99 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Vuglegirska power station | UA | 48.46 | 38.2 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 6 | Gebze Çolakoğlu power station | TR | 40.78 | 29.54 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Nikola Tesla power station | RS | 44.67 | 20.16 | high | medium | zhu_global_1km | low | medium | low | high |
| 8 | Soma power station | TR | 39.19 | 27.64 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Bugojno Thermal Power Project | BA | 44.05 | 17.45 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Meda power station | TR | 40.97 | 27.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Ece power station | TR | 36.78 | 35.74 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Kosovo B power station | XK | 42.69 | 21.06 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Ilgın power station | TR | 38.26 | 31.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Kemerköy power station | TR | 37.04 | 27.9 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Çerkezköy power station | TR | 41.28 | 28 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Tekirdağ Malkara power station | TR | 40.64 | 27 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Kolubara A power station | RS | 44.48 | 20.29 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Štavalj Power Station | RS | 43.27 | 2 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Avdan power station | TR | 37.75 | 29.09 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Hande power station | TR | 36.78 | 35.74 | high | low | zhu_global_1km | low | medium | low | medium |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 5 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
