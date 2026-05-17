# Siting expert audit — ourairports

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `ourairports` |
| **Screening hint** | Airport proximity (HI-01). |
| **Disposition folder** | `ourairports__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/ourairports_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(hh.hi01_comment ILIKE '%OurAirports%' OR hh.hi01_comment ILIKE '%ourairports%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.200091+00:00` |
| **Generator note** | pick_site_ids filter="(hh.hi01_comment ILIKE '%OurAirports%' OR hh.hi01_comment ILIKE '%ourairports%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BG, CZ, PL, RO, RS, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/ourairports_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Yatağan power station | TR | 37.33 | 28.1 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Trakya Emba power station | TR | 41.95 | 28.04 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Kalush power station | UA | 49.07 | 24.32 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Siechnice power station | PL | 51.04 | 17.15 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Trypilska power station | UA | 50.13 | 30.75 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 6 | Mondi Steti power station | CZ | 50.46 | 14.38 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Riedersbach power station | AT | 48.03 | 12.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 8 | Kangal power station | TR | 39.08 | 37.29 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Diler (Akbayir) Elbistan power station | TR | 38.17 | 37.37 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Tekirdağ Malkara power station | TR | 40.64 | 27 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Vresova TPS power station | CZ | 50.26 | 12.7 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Maritsa Iztok-1 power station | BG | 42.16 | 25.91 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Gdynia-3 power station | PL | 54.55 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Kolubara B power station | RS | 44.47 | 20.28 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Çayırhan power station | TR | 40.1 | 31.7 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Vuglegirska power station | UA | 48.46 | 38.2 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 17 | Karvina power station | CZ | 49.82 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Albayrak Varaka Paper power station | TR | 39.56 | 27.97 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Vize power station | TR | 41.57 | 27.81 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Iasi-2 power station | RO | 47.15 | 27.72 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 8 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (experts/quality/siting_expert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
