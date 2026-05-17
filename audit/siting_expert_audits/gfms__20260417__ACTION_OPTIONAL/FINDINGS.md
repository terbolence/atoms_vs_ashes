# Siting expert audit — gfms

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `gfms` |
| **Screening hint** | Global flood monitoring (NH-08/09). |
| **Disposition folder** | `gfms__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/gfms_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh09_comment ILIKE '%gfms%' OR nh.nh08_comment ILIKE '%gfms%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.076468+00:00` |
| **Generator note** | pick_site_ids filter="(nh.nh09_comment ILIKE '%gfms%' OR nh.nh08_comment ILIKE '%gfms%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, CZ, MK, PL, SK, TR, UA, XK.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/gfms_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Jaworzno power station | PL | 50.21 | 19.23 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Mostecka Power Station | CZ | 50.5 | 13.64 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Kongora Thermal Power Plant | BA | 43.65 | 17.33 | high | low | zhu_global_1km | low | medium | low | high |
| 4 | Çan-2 power station | TR | 40.03 | 26.95 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Darnytska power station | UA | 50.45 | 30.64 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 6 | U.S. Steel Kosice Works power station | SK | 48.62 | 21.19 | high | medium | zhu_global_1km | low | medium | low | high |
| 7 | Helvacı power station | TR | 40.08 | 27.17 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Kosovo A power station | XK | 42.68 | 21.09 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Çankırı Orta power station | TR | 40.62 | 33.11 | high | low | zhu_global_1km | low | medium | low | medium |
| 10 | Pulawy ZAP Works power station | PL | 51.46 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Oslomej power station | MK | 41.58 | 21 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Diler (Akbayir) Elbistan power station | TR | 38.17 | 37.37 | high | low | zhu_global_1km | low | medium | low | medium |
| 13 | Leczna Power Station (Enea) | PL | 51.3 | 22.88 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Gliwice Works power station | PL | 50.32 | 18.63 | high | medium | zhu_global_1km | low | medium | low | high |
| 15 | Karapinar Konya Şeker power station | TR | 37.72 | 33.55 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Pocerady power station | CZ | 50.43 | 13.67 | high | low | zhu_global_1km | low | medium | low | high |
| 17 | İÇDAŞ Biga power station | TR | 40.44 | 27.13 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Stalowa Wola power station | PL | 50.55 | 22.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 19 | Chvaletice power station | CZ | 50.03 | 15.45 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Polaniec power station | PL | 50.44 | 21.34 | high | medium | zhu_global_1km | low | medium | low | high |

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
