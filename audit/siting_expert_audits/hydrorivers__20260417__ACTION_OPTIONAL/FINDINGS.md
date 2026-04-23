# Siting expert audit — hydrorivers

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `hydrorivers` |
| **Screening hint** | HydroRIVERS / river network (NS-01). |
| **Disposition folder** | `hydrorivers__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/hydrorivers_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns01_source = 'hydrorivers')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T20:00:29.419766+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns01_source = 'hydrorivers')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AL, CZ, HU, RO, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/hydrorivers_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Star Refinery Socar power station | TR | 38.82 | 26.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Porto Romano Power Station | AL | 41.37 | 19.43 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Atlas Enerji İskenderun power station | TR | 36.69 | 36.21 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Meda power station | TR | 40.97 | 27.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Tosyalı İskenderun power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | EMBA Hunutlu power station | TR | 36.82 | 35.85 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Adana Akdeniz power station | TR | 36.82 | 35.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Selena power station | TR | 36.92 | 36.05 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Ayas power station | TR | 36.82 | 35.87 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Atakaş power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Yumurtalık IC İçtaş power station | TR | 36.77 | 35.79 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Bakony power station | HU | 47.1 | 17.56 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Afşin-Elbistan power stations | TR | 38.35 | 37.03 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Brăila-Chișcani Thermal Power Plant | RO | 45.27 | 27.93 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Umut power station | TR | 41.13 | 37.16 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Detmarovice power station | CZ | 49.91 | 18.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | İsken Sugözü power station | TR | 36.84 | 35.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Çatalağzı power station | TR | 41.52 | 31.9 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Naren Karabiga power station | TR | 40.46 | 27.25 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Mintia-Deva power station | RO | 45.91 | 22.83 | high | low | zhu_global_1km | low | medium | low | high |

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
