# Siting expert audit — corine

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `corine` |
| **Screening hint** | Land cover / fragmentation (NS-04, NS-08). |
| **Disposition folder** | `corine__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/corine_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.dominant_land_class IS NOT NULL AND inf.ns04_quality IS NOT NULL)` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.920108+00:00` |
| **Generator note** | pick_site_ids filter='(inf.dominant_land_class IS NOT NULL AND inf.ns04_quality IS NOT NULL)' matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BG, ME, MK, PL, RO, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/corine_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Brikel power station | BG | 42.15 | 25.91 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Bitola power station | MK | 41.06 | 21.48 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Selena power station | TR | 36.92 | 36.05 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Vidin Works power station | BG | 43.95 | 22.85 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Brăila-Chișcani Thermal Power Plant | RO | 45.27 | 27.93 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Bolu Göynük power station | TR | 40.25 | 30.81 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Rybnik power station | PL | 50.13 | 18.52 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Ladyzhyn power station | UA | 48.71 | 29.22 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Orta Anadolu power station | TR | 40.62 | 33.11 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Legnica Power Station | PL | 51.21 | 16.16 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Habaş power station | TR | 38.77 | 26.95 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Sinop Akfen power station | TR | 41.95 | 34.83 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Poznan Karolin power station | PL | 52.44 | 16.99 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Meda power station | TR | 40.97 | 27.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Bacau CHP power station | RO | 46.53 | 26.94 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | EMBA Hunutlu power station | TR | 36.82 | 35.85 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Ruse Iztok power station | BG | 43.87 | 26.01 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Sliven power station | BG | 42.65 | 26.33 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Maritsa Iztok-4 power station | BG | 42.14 | 26 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Berane power station | ME | 42.84 | 19.86 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 7 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
