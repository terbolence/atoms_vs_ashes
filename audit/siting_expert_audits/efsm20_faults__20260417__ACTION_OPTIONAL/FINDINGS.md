# Siting expert audit — efsm20_faults

## 1. Review scope

| Field | Value |
| --- | --- |
| **Connector slug** | `efsm20_faults` |
| **Screening hint** | Fault proximity and seismic line sources (NH-02). |
| **Disposition folder** | `efsm20_faults__20260417__ACTION_OPTIONAL` |
| **Connector sample report** | `docs/connector_reports/efsm20_faults_sample_report.md` — **missing** |

## 2. Sample intake

| Field | Value |
| --- | --- |
| **Database profile** | `api` → `atoms_vs_ashes` |
| **Generator** | `scripts/generate_siting_expert_audits.py` |
| **Stratification SQL** | `(nh.nh02_source ILIKE '%efsm20%')` |
| **Sample count** | **20** |
| **Run ID (payload)** | `20260417T195638_3e2d06c1` |
| **Extraction timestamp (UTC)** | `2026-04-17T19:59:38.959989+00:00` |
| **Generator note** | pick_site_ids filter=None matched 20 sites; domain rows batched per table; pruned to quality/source/value columns. |

## 3. Executive summary (machine-assisted)

**Samples:** 20 site(s). **Countries:** BA, BG, LV, PL, RS, SI, TR, UA.
No connector error rows in these samples (still review observation text). **Site observation rows (capped in JSON):** 100 total.
Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H).
**Documentation:** `docs/connector_reports/efsm20_faults_sample_report.md` is **missing** — add per workspace connector-report rule before calling implementation complete.

**Suggested disposition:** `ACTION_OPTIONAL` — confirm after human review per `experts/quality/siting_expert.md`.

## 4. Per-sample table

| # | Site | CC | Lat | Lon | nh01_quality | nh02_quality | nh03_quality | nh04_quality | nh05_quality | nh06_quality | nh07_quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Kıvanç power station | TR | 36.34 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 2 | Mersin Gülnar power station | TR | 36.33 | 33.4 | high | low | zhu_global_1km | low | medium | low | medium |
| 3 | Iztek Ceyhan Komur power station | TR | 37.03 | 35.82 | high | low | zhu_global_1km | low | medium | low | medium |
| 4 | Bandırma III power station | TR | 39.38 | 27.53 | high | low | zhu_global_1km | low | medium | low | medium |
| 5 | Çebi Enerji power station | TR | 41.01 | 27.96 | high | low | zhu_global_1km | low | medium | low | medium |
| 6 | Kurzeme power station | LV | 57.41 | 21.59 | high | low | zhu_global_1km | low | medium | low | high |
| 7 | Kramatorskaya power station | UA | 48.75 | 37.57 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 8 | Štavalj Power Station | RS | 43.27 | 2 | high | low | zhu_global_1km | low | medium | low | high |
| 9 | Katowice PKE power station | PL | 50.29 | 19.05 | high | medium | zhu_global_1km | low | medium | low | high |
| 10 | Te-Tol power station | SI | 46.06 | 14.55 | high | medium | zhu_global_1km | low | medium | low | high |
| 11 | Ant Enerji power station | TR | 37.37 | 28.03 | high | low | zhu_global_1km | low | medium | low | high |
| 12 | Lom Power Station | BG | 43.78 | 23.22 | high | low | zhu_global_1km | low | medium | low | high |
| 13 | Deniz power station | TR | 38.75 | 26.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 14 | Kahramanmaraş Anadolu power station | TR | 38.35 | 37.01 | high | low | zhu_global_1km | low | medium | low | medium |
| 15 | Kamengrad Thermal Power Plant | BA | 44.77 | 16.67 | high | low | zhu_global_1km | low | medium | low | high |
| 16 | Ilgın power station | TR | 38.26 | 31.91 | high | low | zhu_global_1km | low | medium | low | medium |
| 17 | Kurakhov power station | UA | 47.99 | 37.24 | insufficient | medium | zhu_global_1km | low | medium | low | high |
| 18 | Darnytska power station | UA | 50.45 | 30.64 | insufficient | low | zhu_global_1km | low | medium | low | high |
| 19 | İsken Sugözü power station | TR | 36.84 | 35.88 | high | low | zhu_global_1km | low | medium | low | medium |
| 20 | Maritsa 3 power station | BG | 42.05 | 25.62 | high | low | zhu_global_1km | low | medium | low | high |

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
