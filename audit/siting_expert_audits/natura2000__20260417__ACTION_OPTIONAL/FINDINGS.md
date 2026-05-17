# Siting expert audit — natura2000

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `natura2000` |
| **Screening hint** | Natura 2000 proximity (NS-08). |
| **Disposition folder** | `natura2000__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/natura2000_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.n2k_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%natura%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.147849+00:00` |
| **Generator note** | pick_site_ids filter="(inf.n2k_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%natura%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BG, CZ, PL, RO, SK.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/natura2000_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Puchaczow power station | PL | 51.3 | 22.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Romag Termo power station | RO | 44.68 | 22.69 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Siersza power station | PL | 50.21 | 19.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Gdansk-2 power station | PL | 54.38 | 18.64 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Vojany I power station | SK | 48.55 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Iasi-2 power station | RO | 47.15 | 27.72 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | St Andrae power station | AT | 46.75 | 14.82 | high | medium | zhu_global_1km | low | medium | low | high |
| 8 | Stalowa Wola power station | PL | 50.55 | 22.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Kozienice power station | PL | 51.58 | 21.55 | high | medium | zhu_global_1km | low | medium | low | high |
| 10 | Leczna Power Station (Enea) | PL | 51.3 | 22.88 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Ruse Iztok power station | BG | 43.87 | 26.01 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Lodz-2 power station | PL | 51.74 | 19.45 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Zabrze power station | PL | 50.32 | 18.79 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Gdynia-3 power station | PL | 54.55 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Pocerady power station | CZ | 50.43 | 13.67 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Krakow-Leg power station | PL | 50.05 | 20.01 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Hodonin power station | CZ | 48.85 | 17.12 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Gubin Power Project | PL | 51.95 | 14.73 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Pulawy ZAP Works power station | PL | 51.46 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | Vresova TPS power station | CZ | 50.26 | 12.7 | high | low | zhu_global_1km | low | medium | low | high |

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
