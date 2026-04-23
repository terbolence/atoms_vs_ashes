# Siting expert audit — geonames_dump

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `geonames_dump` |
| **Screening hint** | GeoNames city / population context (RI-05). |
| **Disposition folder** | `geonames_dump__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/geonames_dump_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(rd.ri05_comment ILIKE '%GeoNames%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.058727+00:00` |
| **Generator note** | pick_site_ids filter="(rd.ri05_comment ILIKE '%GeoNames%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, MK, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/geonames_dump_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Bandırma III power station | TR | 39.38 | 27.53 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Gölovası power station | TR | 36.85 | 35.9 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Bandırma Elektrik power station | TR | 40.31 | 27.73 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Silopi (Şırnak) power station | TR | 37.35 | 42.55 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | METES power station | TR | 36.24 | 33.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Zuevskaya power station | UA | 48.03 | 38.29 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 7 | Helvacı power station | TR | 40.08 | 27.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Kangal Etyemez power station | TR | 39.08 | 37.3 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Oslomej power station | MK | 41.58 | 21 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Yeniköy power station | TR | 37.14 | 27.87 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Cherkasy power station | UA | 49.39 | 32.07 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 12 | Banovici power station | BA | 44.4 | 18.53 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Sarp Golvasi power station | TR | 37.37 | 35.71 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Kurakhov power station | UA | 47.99 | 37.24 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 15 | Akdeniz Enerji power station | TR | 36.2 | 33.67 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Bursa power station | TR | 39.9 | 29.18 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Teyo Tufanbeyli power station | TR | 38.23 | 36.25 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Ada Yumurtalık power station | TR | 36.84 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Mariovo power station | MK | 41.12 | 21.81 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Çan-2 power station | TR | 40.03 | 26.95 | high | low | zhu_global_1km | low | medium | low | medium |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 4 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
