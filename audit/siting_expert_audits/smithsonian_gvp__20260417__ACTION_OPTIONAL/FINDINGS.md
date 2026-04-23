# Siting expert audit — smithsonian_gvp

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `smithsonian_gvp` |
| **Screening hint** | Volcanic feature proximity (NH-07). |
| **Disposition folder** | `smithsonian_gvp__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/smithsonian_gvp_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh07_comment ILIKE '%gvp%' OR nh.nh07_comment ILIKE '%Smithsonian%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.289107+00:00` |
| **Generator note** | pick_site_ids filter="(nh.nh07_comment ILIKE '%gvp%' OR nh.nh07_comment ILIKE '%Smithsonian%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, CZ, HR, HU, ME, PL, RO, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/smithsonian_gvp_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Detmarovice power station | CZ | 49.91 | 18.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Ece power station | TR | 36.78 | 35.74 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Ploče power station | HR | 43.05 | 17.43 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Pocerady power station | CZ | 50.43 | 13.67 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Yatağan power station | TR | 37.33 | 28.1 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Bialystok power station | PL | 53.15 | 23.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Sanko Gölbaşı power station | TR | 37.82 | 37.72 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Yüksek Gölovası power station | TR | 37.37 | 35.71 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Hodonin power station | CZ | 48.85 | 17.12 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Ostrołęka power station | PL | 53.1 | 21.61 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Oroszlány power station | HU | 47.5 | 18.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Bugojno Thermal Power Project | BA | 44.05 | 17.45 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Maoce Power Station | ME | 43.36 | 19.36 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Tufanbeyli power station | TR | 38.19 | 36.27 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Kıvanç power station | TR | 36.34 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Ugljevik power station | BA | 44.68 | 18.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Opatovice power station | CZ | 50.12 | 15.79 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Laziska power station | PL | 50.13 | 18.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Zabrze power station | PL | 50.32 | 18.79 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | Braila power station | RO | 45.17 | 27.92 | high | low | zhu_global_1km | low | medium | low | high |

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
