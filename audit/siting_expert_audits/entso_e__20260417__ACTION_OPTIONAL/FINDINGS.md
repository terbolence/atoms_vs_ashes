# Siting expert audit — entso_e

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `entso_e` |
| **Screening hint** | Grid capacity and substation context (NS-02). |
| **Disposition folder** | `entso_e__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/entso_e_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(inf.ns02_comment ILIKE '%entsoe%' OR inf.ns02_comment ILIKE '%ENTSO%' OR inf.ns02_comment ILIKE '%Transparency%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T182246_8e5713dd` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.989924+00:00` |
| **Generator note** | pick_site_ids filter="(inf.ns02_comment ILIKE '%entsoe%' OR inf.ns02_comment ILIKE '%ENTSO%' OR inf.ns02_comment ILIKE '%Transparency%')" matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BY, CZ, ME, MK, PL, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/entso_e_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `prompts/sitingExpert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Miechowice power station | PL | 50.35 | 18.84 | high | medium | zhu_global_1km | low | medium | low | high |
| 2 | Negotino power station | MK | 41.48 | 22.1 | high | low | zhu_global_1km | low | medium | low | high |
| 3 | Silopi (Şırnak) power station | TR | 37.35 | 42.55 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Orhaneli power station | TR | 39.95 | 28.87 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Starobesheve power station | UA | 47.8 | 38.01 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 6 | Bar power station | ME | 42.1 | 19.1 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Yeşilovacık power station | TR | 36.2 | 33.66 | high | low | zhu_global_1km | low | medium | low | medium |
| 8 | Karvina power station | CZ | 49.82 | 18.48 | high | medium | zhu_global_1km | low | medium | low | high |
| 9 | Pulawy ZAP Works power station | PL | 51.46 | 21.97 | high | medium | zhu_global_1km | low | medium | low | high |
| 10 | İsken Sugözü power station | TR | 36.84 | 35.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 11 | Kıvanç power station | TR | 36.34 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 12 | Zaporizhia power station | UA | 47.51 | 34.63 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 13 | Leczna Power Station (Enea) | PL | 51.3 | 22.88 | high | medium | zhu_global_1km | low | medium | low | high |
| 14 | Alpu power station | TR | 39.9 | 30.86 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Atakaş power station | TR | 36.7 | 36.2 | high | low | zhu_global_1km | low | medium | low | medium |
| 16 | Luganskaya power station | UA | 48.75 | 39.26 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 17 | Yumurtalık IC İçtaş power station | TR | 36.77 | 35.79 | high | low | zhu_global_1km | low | medium | low | medium |
| 18 | Lelchitsy power station | BY | 51.79 | 28.32 | high | low | zhu_global_1km | low | medium | low | high |
| 19 | Yeniköy power station | TR | 37.14 | 27.87 | high | low | zhu_global_1km | low | medium | low | high |
| 20 | Kandilli power station | TR | 41.34 | 31.51 | high | low | zhu_global_1km | low | medium | low | high |

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
