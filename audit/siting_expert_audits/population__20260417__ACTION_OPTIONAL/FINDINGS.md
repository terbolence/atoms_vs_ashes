# Siting expert audit — population

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `population` |
| **Screening hint** | OSM ring population (RI-04). |
| **Disposition folder** | `population__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/population_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(rd.ri04_comment ILIKE '%Overpass%' OR rd.ri04_comment ILIKE '%OSM%' OR rd.pop_density_5km IS NOT NULL)` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.243732+00:00` |
| **Generator note** | pick_site_ids filter="(rd.ri04_comment ILIKE '%Overpass%' OR rd.ri04_comment ILIKE '%OSM%' OR rd.pop_density_5km IS NOT NULL)" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** CZ, HU, PL, RO, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/population_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Czestochowa CHP power station | PL | 50.79 | 19.14 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Turceni power station | RO | 44.67 | 23.41 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Ada Yumurtalık power station | TR | 36.84 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Soma Kolin power station | TR | 39.32 | 27.75 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Plana Nad Luznici power station | CZ | 49.37 | 14.7 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Eti Maden Bandirma power station | TR | 40.33 | 27.99 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Opalenie power station | PL | 53.74 | 18.82 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Yumurtalık IC İçtaş power station | TR | 36.77 | 35.79 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | HEMA Amasra power station | TR | 41.72 | 32.35 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Zafer power station | TR | 41.6 | 32.51 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Oroszlány power station | HU | 47.5 | 18.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Tusimice power station | CZ | 50.38 | 13.34 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Opatovice power station | CZ | 50.12 | 15.79 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Ant Enerji power station | TR | 37.37 | 28.03 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Saltukova power station | TR | 41.52 | 32.09 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Muğla power station | TR | 37.15 | 27.8 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Kireçlik power station | TR | 41.37 | 31.59 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Yeniyurt power station | TR | 36.89 | 36.15 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Hodonin power station | CZ | 48.85 | 17.12 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Trinec-E3 power station | CZ | 49.68 | 18.67 | high | medium | zhu_global_1km | low | medium | low | high |

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
