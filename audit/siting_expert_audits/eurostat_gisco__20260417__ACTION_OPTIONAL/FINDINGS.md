# Siting expert audit — eurostat_gisco

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `eurostat_gisco` |
| **Screening hint** | Large-city proximity and GISCO urban boundaries (RI-05). |
| **Disposition folder** | `eurostat_gisco__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/eurostat_gisco_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(rd.ri05_quality = 'gisco_urau_2021')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.024318+00:00` |
| **Generator note** | pick_site_ids filter="(rd.ri05_quality = 'gisco_urau_2021')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, BG, CZ, HU, PL, RO.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/eurostat_gisco_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Galati Power Station | RO | 45.42 | 28.04 | high | low | zhu_global_1km | low | medium | low | high |
| 2 | Oradea power station | RO | 47.08 | 21.89 | high | medium | zhu_global_1km | low | medium | low | high |
| 3 | Zeran power station | PL | 52.29 | 20.99 | high | medium | zhu_global_1km | low | medium | low | high |
| 4 | Stalowa Wola power station | PL | 50.55 | 22.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Karvina power station | CZ | 49.82 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 6 | Mohacs power station | HU | 46 | 18.68 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | ZW Nowa power station | PL | 50.35 | 19.28 | high | medium | zhu_global_1km | low | medium | low | high |
| 8 | Maritsa Iztok-1 power station | BG | 42.16 | 25.91 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Turceni power station | RO | 44.67 | 23.41 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Bacau CHP power station | RO | 46.53 | 26.94 | high | low | zhu_global_1km | low | medium | low | high |
| 11 | Pomorzany power station | PL | 53.39 | 14.52 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Vidin Works power station | BG | 43.95 | 22.85 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Siekierki power station | PL | 52.19 | 21.09 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Oroszlány power station | HU | 47.5 | 18.27 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Slatina power station | RO | 44.43 | 24.36 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Malesice power station | CZ | 50.08 | 14.53 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Torony power station | HU | 47.24 | 16.54 | high | medium | zhu_global_1km | low | medium | low | high |
| 18 | Pulawy power station (Vattenfall) | PL | 51.42 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Czeczott power station | PL | 49.97 | 18.95 | high | medium | zhu_global_1km | low | medium | low | high |
| 20 | St Andrae power station | AT | 46.75 | 14.82 | high | medium | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 6 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
