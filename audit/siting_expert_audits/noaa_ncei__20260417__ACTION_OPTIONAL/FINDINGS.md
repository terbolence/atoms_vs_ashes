# Siting expert audit — noaa_ncei

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `noaa_ncei` |
| **Screening hint** | NOAA climate extremes (NH-10–12). |
| **Disposition folder** | `noaa_ncei__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/noaa_ncei_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh10_comment ILIKE '%noaa%' OR nh.nh11_comment ILIKE '%noaa%' OR nh.nh12_comment ILIKE '%noaa%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.167178+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BA, CZ, PL, RO, RS, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/noaa_ncei_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Braila power station | RO | 45.17 | 27.92 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Târgu Jiu Thermal Plant | RO | 45.03 | 23.27 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Barbaros-1 power station | TR | 41.8 | 35.19 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Afşin-Elbistan power stations | TR | 38.35 | 37.03 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Gacko Thermal Power Plant | BA | 43.17 | 18.51 | high | low | zhu_global_1km | low | medium | low | high |
| 6 | Şırnak Silopi (CİNER) power station | TR | 37.31 | 42.59 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Galati Power Station | RO | 45.42 | 28.04 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | FPCU Feldioara | RO | 45.79 | 25.59 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Bacau CHP power station | RO | 46.53 | 26.94 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Kilikya power station | TR | 36.83 | 35.87 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Güreci power station | TR | 40.34 | 26.68 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Laziska power station | PL | 50.13 | 18.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Sko-Energo power station | CZ | 50.42 | 14.93 | high | low | zhu_global_1km | low | medium | low | high |
| 14 | Akdeniz Enerji power station | TR | 36.2 | 33.67 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Tisova power station | CZ | 50.15 | 12.61 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Zeltweg power station | AT | 47.25 | 15.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Glinica power station | BA | 43.33 | 17.8 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Bursa power station | TR | 39.9 | 29.18 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Morava power station | RS | 44.22 | 21.16 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | St Andrae power station | AT | 46.75 | 14.82 | high | medium | zhu_global_1km | low | medium | low | high |

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
