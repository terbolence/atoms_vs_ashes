# Siting expert audit — ghsl_pop

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `ghsl_pop` |
| **Screening hint** | GHSL population density (RI-04, EP-01). |
| **Disposition folder** | `ghsl_pop__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/ghsl_pop_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(rd.ri04_quality::text ILIKE '%ghsl%' OR rd.ri04_comment ILIKE '%GHSL%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.093858+00:00` |
| **Generator note** | pick_site_ids filter="(rd.ri04_quality::text ILIKE '%ghsl%' OR rd.ri04_comment ILIKE '%GHSL%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BG, CZ, PL, RS, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/ghsl_pop_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Irmak power station | TR | 39.79 | 26.33 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Namal power station | TR | 40.34 | 26.68 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | İÇDAŞ Biga power station | TR | 40.44 | 27.13 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Marianske Hory power station | CZ | 49.86 | 18.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Pocerady power station | CZ | 50.43 | 13.67 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Kolubara B power station | RS | 44.47 | 20.28 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Zuevskaya power station | UA | 48.03 | 38.29 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 8 | Kemerköy power station | TR | 37.04 | 27.9 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Uluköy power station | TR | 38.2 | 30.27 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Ladyzhyn power station | UA | 48.71 | 29.22 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Tosyalı İskenderun power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Teyo Tufanbeyli power station | TR | 38.23 | 36.25 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Kedzierzyn CCS Project | PL | 50.35 | 18.23 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Tekirdağ Malkara power station | TR | 40.64 | 27 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Adamow power station | PL | 52.01 | 18.55 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Ruse Iztok power station | BG | 43.87 | 26.01 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Pólnoc power station | PL | 53.96 | 18.71 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Astoria Ceyhan power station | TR | 36.91 | 35.96 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Kütahya Domaniç power station | TR | 39.8 | 29.61 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Tunçbilek power station | TR | 39.62 | 29.47 | high | low | zhu_global_1km | low | medium | low | medium |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 6 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (experts/quality/siting_expert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
