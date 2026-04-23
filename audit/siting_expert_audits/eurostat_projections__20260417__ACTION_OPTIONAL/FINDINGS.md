# Siting expert audit — eurostat_projections

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `eurostat_projections` |
| **Screening hint** | Population projection context (RI-06). |
| **Disposition folder** | `eurostat_projections__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/eurostat_projections_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(rd.ri06_comment ILIKE '%eurostat%' OR rd.ri06_comment ILIKE '%Europop%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.043139+00:00` |
| **Generator note** | pick_site_ids filter="(rd.ri06_comment ILIKE '%eurostat%' OR rd.ri06_comment ILIKE '%Europop%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** CZ, PL, RO, RS, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/eurostat_projections_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Polaniec power station | PL | 50.44 | 21.34 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Doicesti power station | RO | 45 | 25.4 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Gdansk-2 power station | PL | 54.38 | 18.64 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Gubin Power Project | PL | 51.95 | 14.73 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Miechowice power station | PL | 50.35 | 18.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Gebze Çolakoğlu power station | TR | 40.78 | 29.54 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Uluköy power station | TR | 38.2 | 30.27 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Katowice PKE power station | PL | 50.29 | 19.05 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Orta Anadolu power station | TR | 40.62 | 33.11 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Trebovice power station | CZ | 49.83 | 18.21 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Aksa Akrilik power station | TR | 40.69 | 29.41 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Vresova TPS power station | CZ | 50.26 | 12.7 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Gönen power station | TR | 40.1 | 27.65 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Pulawy power station (Grupa Azoty) | PL | 51.42 | 21.97 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Zlin power station | CZ | 49.23 | 17.65 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Gorzow power station | PL | 52.75 | 15.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Oradea power station | RO | 47.08 | 21.89 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Nikola Tesla power station | RS | 44.67 | 20.16 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | DOSAB cogeneration plant | TR | 40.24 | 28.96 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Namal power station | TR | 40.34 | 26.68 | high | low | zhu_global_1km | low | medium | low | medium |

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
