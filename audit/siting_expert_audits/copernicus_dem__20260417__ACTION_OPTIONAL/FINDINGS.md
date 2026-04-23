# Siting expert audit — copernicus_dem

## 1. Review scope

| Field                       | Value                                                                  |
| --------------------------- | ---------------------------------------------------------------------- |
| **Connector slug**          | `copernicus_dem`                                                       |
| **Screening hint**          | Terrain / elevation proxies (NH-04, NS-04) via Copernicus DEM.         |
| **Disposition folder**      | `copernicus_dem__20260417__ACTION_OPTIONAL`                            |
| **Connector sample report** | `docs/connector_reports/copernicus_dem_sample_report.md` — **missing** |

## 2. Sample intake

| Field                          | Value                                                                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Database profile**           | `api` → `atoms_vs_ashes`                                                                                           |
| **Generator**                  | `scripts/generate_siting_expert_audits.py`                                                                         |
| **Stratification SQL**         | `(nh.nh04_quality = 'copernicus_dem_30m' OR inf.ns04_quality = 'copernicus_dem_30m')`                              |
| **Sample count**               | **20**                                                                                                             |
| **Run ID (payload)**           | `20260417T195638_3e2d06c1`                                                                                         |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.868412+00:00`                                                                                 |
| **Generator note**             | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** AL, AT, BG, CZ, PL, RO, TR.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/copernicus_dem_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| #   | Site                          | CC  | Lat   | Lon   | nh01_quality | nh02_quality | nh03_quality   | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | ----------------------------- | --- | ----- | ----- | ------------ | ------------ | -------------- | ------------ | ------------ | ------------ | ------------ |
| 1   | Bobov Dol power station       | BG  | 42.29 | 23.03 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 2   | Aliağa Enka power station     | TR  | 38.75 | 26.91 | high         | low          | zhu_global_1km | low          | medium       | low          | medium       |
| 3   | Lublin Power Station          | PL  | 51.21 | 22.55 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 4   | Sko-Energo power station      | CZ  | 50.42 | 14.93 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 5   | Mostecka Power Station        | CZ  | 50.5  | 13.64 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 6   | Bydgoszcz power station       | PL  | 53.1  | 18.09 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 7   | Porto Romano Power Station    | AL  | 41.37 | 19.43 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 8   | Skawina power station         | PL  | 49.98 | 19.81 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 9   | Katowice PKE power station    | PL  | 50.29 | 19.05 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 10  | Yenidere power station        | TR  | 37.46 | 28.67 | high         | low          | zhu_global_1km | low          | medium       | low          | medium       |
| 11  | Vize power station            | TR  | 41.57 | 27.81 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 12  | Gorzow power station          | PL  | 52.75 | 15.27 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 13  | Oradea power station          | RO  | 47.08 | 21.89 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 14  | Barbaros-1 power station      | TR  | 41.8  | 35.19 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 15  | Mellach power station         | AT  | 46.91 | 15.49 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 16  | Galati Power Station          | RO  | 45.42 | 28.04 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 17  | ZW Nowa power station         | PL  | 50.35 | 19.28 | high         | medium       | zhu_global_1km | low          | medium       | low          | high         |
| 18  | Malesice power station        | CZ  | 50.08 | 14.53 | high         | low          | zhu_global_1km | low          | medium       | low          | high         |
| 19  | Gebze Çolakoğlu power station | TR  | 40.78 | 29.54 | high         | low          | zhu_global_1km | low          | medium       | low          | medium       |
| 20  | Kıvanç power station          | TR  | 36.34 | 33.4  | high         | low          | zhu_global_1km | low          | medium       | low          | medium       |

## 5. Aggregate diagnostics

| Metric                                | Value                                                                                                                                                                                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unique countries                      | 7                                                                                                                                                                                                                                                   |
| Connector error rows (sum over sites) | 0                                                                                                                                                                                                                                                   |
| Auto table columns                    | site_natural_hazards.nh01_quality, site_natural_hazards.nh02_quality, site_natural_hazards.nh03_quality, site_natural_hazards.nh04_quality, site_natural_hazards.nh05_quality, site_natural_hazards.nh06_quality, site_natural_hazards.nh07_quality |

## 6. Human follow-up (prompts/sitingExpert.md §D–§H)

- Validate domain plausibility for each criterion touched by this connector.
- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.
- Close gaps: connector sample report, automated tests, and schema notes.

## 7. Machine generation note

This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. Expert judgement and final acceptance remain human.
