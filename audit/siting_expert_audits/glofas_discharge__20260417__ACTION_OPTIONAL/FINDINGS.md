# Siting expert audit — glofas_discharge

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `glofas_discharge` |
| **Screening hint** | River discharge context (NS-01). |
| **Disposition folder** | `glofas_discharge__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/glofas_discharge_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns01_source = 'glofas_discharge')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:39.114719+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns01_source = 'glofas_discharge')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AT, CZ, HU, PL, RO, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/glofas_discharge_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Detmarovice power station | CZ | 49.91 | 18.46 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Orta Anadolu power station | TR | 40.62 | 33.11 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Ilgın power station | TR | 38.26 | 31.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Voitsberg power station | AT | 47.05 | 15.16 | high | medium | zhu_global_1km | low | medium | low | high |
| 5 | Cherkasy power station | UA | 49.39 | 32.07 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 6 | Bandırma III power station | TR | 39.38 | 27.53 | high | low | zhu_global_1km | low | medium | low | medium |
| 7 | Zafer power station | TR | 41.6 | 32.51 | high | low | zhu_global_1km | low | medium | low | high |
| 8 | Ece power station | TR | 36.78 | 35.74 | high | low | zhu_global_1km | low | medium | low | medium |
| 9 | Pribram power station | CZ | 49.7 | 14 | high | low | zhu_global_1km | low | medium | low | high |
| 10 | Puchaczow power station | PL | 51.3 | 22.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Plzen CHP power station | CZ | 49.75 | 13.4 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Bialystok power station | PL | 53.15 | 23.17 | high | medium | zhu_global_1km | low | medium | low | high |
| 13 | Lodz-2 power station | PL | 51.74 | 19.45 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Gönen power station | TR | 40.1 | 27.65 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Stalowa Wola power station | PL | 50.55 | 22.08 | high | medium | zhu_global_1km | low | medium | low | high |
| 16 | Mohacs power station | HU | 46 | 18.68 | high | medium | zhu_global_1km | low | medium | low | high |
| 17 | Zorlu Akçakoca power station | TR | 41.09 | 31.12 | high | low | zhu_global_1km | low | medium | low | high |
| 18 | Lüminer Enerji power station | TR | 40.89 | 26.9 | high | low | zhu_global_1km | low | medium | low | medium |
| 19 | Çalışkan Ceyhan power station | TR | 36.94 | 35.99 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Giurgiu power station | RO | 43.88 | 25.93 | high | low | zhu_global_1km | low | medium | low | high |

## 5. Aggregate diagnostics

| Metric | Value |
| --- | --- |
| Unique countries | 7 |
| Connector error rows (sum over sites) | 0 |
| Auto table columns | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (experts/quality/siting_expert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
