# Siting expert audit — eu_flood_risk

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `eu_flood_risk` |
| **Screening hint** | EU flood / GLOFAS-related screening (NH-09). |
| **Disposition folder** | `eu_flood_risk__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/eu_flood_risk_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh09_comment ILIKE '%GLOFAS%' OR nh.nh09_comment ILIKE '%APSFR%' OR nh.nh09_comment ILIKE '%eu_flood%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.007053+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** CZ, HU, PL, RO, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/eu_flood_risk_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Yıldırım Elazığ power station | TR | 38.66 | 39.77 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Sko-Energo power station | CZ | 50.42 | 14.93 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Trypilska power station | UA | 50.13 | 30.75 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 4 | Çerkezköy power station | TR | 41.28 | 28 | high | low | zhu_global_1km | low | medium | low | high |
| 5 | Şırnak Silopi (CİNER) power station | TR | 37.31 | 42.59 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Babadere power station | TR | 39.61 | 26.19 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Melnik power station | CZ | 50.41 | 14.42 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Suluova power station | TR | 40.86 | 35.65 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Kangal Etyemez power station | TR | 39.08 | 37.3 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Siersza power station | PL | 50.21 | 19.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Bedzin power station | PL | 50.3 | 19.14 | high | medium | zhu_global_1km | low | medium | low | high |
| 12 | Banhida-II power station | HU | 47.57 | 18.37 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Silopi (Şırnak) power station | TR | 37.35 | 42.55 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Saray Tekirdağ power station | TR | 41.45 | 27.92 | high | low | zhu_global_1km | low | medium | low | high |
| 15 | Mersin Gülnar power station | TR | 36.33 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Braila power station | RO | 45.17 | 27.92 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | Kınık power station | TR | 39.08 | 27.45 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Kardemir Karabük Demir Çelik power stat… | TR | 41.51 | 31.91 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Şırnak Galata power station | TR | 37.47 | 42.39 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Myronivskyi power station | UA | 48.48 | 38.28 | insufficient | low | zhu_global_1km | low | medium | low | high |

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
