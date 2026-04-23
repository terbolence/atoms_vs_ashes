# Phase 1 — API DB anomaly sweep

_Generated 2026-04-21 10:59 UTC by `scripts/scan_api_db_anomalies.py`._

**DB scanned:** `atoms_vs_ashes` (live, post-snapshot)  
**Snapshot:** `backups/atoms_vs_ashes_raw_20260421.dump` (pg_dump custom)  
**Snapshot DB:** `atoms_vs_ashes_raw_20260421` (read-only restore)  
**Mode:** `dry-run`  
**Run id:** `phase1_sweep_20260421_105903`  
**Bounds source:** engineering common sense (this script's `BOUNDS` dict). 
Phase 3 `report/business_logic.md` will adopt and formalise them.

## Methodology

Each row in every domain table (sites, site_natural_hazards, site_human_hazards, site_radiological, site_emergency_planning, site_infrastructure_v2) is checked against three families of rules:

1. **Scalar bounds** — common-sense per-column min/max from `BOUNDS` dict.
2. **JSON / raw-response triangulation** — the persisted scalar must agree, 
   within 5 % relative tolerance, with the source-of-truth value in the 
   originating JSONB column (`spectral_accel_json`, `n2k_result_json`, 
   `wdpa_result_json`) or in the relevant `site_raw_responses.response_body`.
3. **Implausible-given-context** — compound rules that combine multiple 
   columns (e.g. cooling flow vs installed capacity).

## Summary

- Total findings: **96**
- Auto-fix candidates: **0**
- Escalations (human review needed): **96**
- Fixes applied this run: **0** (dry-run)
- Total prior `phase1_fix` rows in `audit_log` (all runs): **7**

### Findings per check

| Check | Action default | Findings |
|---|---|---:|
| `BOUND::slope_angle_deg` | escalate | 3 |
| `CONTEXT::cooling_flow_too_low_for_capacity` | escalate | 6 |
| `CONTEXT::favourable_area_implausibly_small` | escalate | 19 |
| `CONTEXT::grid_export_equals_capacity_fallback` | escalate | 64 |
| `CONTEXT::slope_too_steep` | escalate | 3 |
| `NULL::wildfire_uncovered_BULK` | escalate | 1 |

### Findings per criterion

| Criterion | Findings |
|---|---:|
| NH-04 | 6 |
| NH-13 | 1 |
| NS-01 | 6 |
| NS-02 | 64 |
| NS-04 | 19 |

## Escalations (human review required)

These findings cannot be deterministically fixed from data on hand. 
They are recorded here so Phase 3 (business logic) and Phase 5 (LLM 
enrichment) can either patch them with cross-source evidence or accept 
`insufficient` quality with a documented fallback.

### NH-04 — 6 finding(s)

| Check | Site | Country | Column | Observed | Bound / expected | Notes |
|---|---|---|---|---|---|---|
| `BOUND::slope_angle_deg` | Zeltweg power station | AT | `slope_angle_deg` | `26.02` | `[0.0, 25.0] deg` | IAEA SSG-9 ranks > 25 deg as severe |
| `BOUND::slope_angle_deg` | Trbovlje power station | SI | `slope_angle_deg` | `27.25` | `[0.0, 25.0] deg` | IAEA SSG-9 ranks > 25 deg as severe |
| `BOUND::slope_angle_deg` | Silopi (Şırnak) power station | TR | `slope_angle_deg` | `31.48` | `[0.0, 25.0] deg` | IAEA SSG-9 ranks > 25 deg as severe |
| `CONTEXT::slope_too_steep` | Zeltweg power station | AT | `slope_angle_deg` | `26.02` | `<= 25 deg (IAEA SSG-9 severe band starts here)` | dem_cog_max=49.12 gee_mean=None quality=copernicus_dem_30m fusion=None; primary slope is the max-in-30 m buffer, not the mean — likely overstated. Re-pull GEE mean slope at finer buffer. |
| `CONTEXT::slope_too_steep` | Trbovlje power station | SI | `slope_angle_deg` | `27.25` | `<= 25 deg (IAEA SSG-9 severe band starts here)` | dem_cog_max=58.41 gee_mean=None quality=copernicus_dem_30m fusion=None; primary slope is the max-in-30 m buffer, not the mean — likely overstated. Re-pull GEE mean slope at finer buffer. |
| `CONTEXT::slope_too_steep` | Silopi (Şırnak) power station | TR | `slope_angle_deg` | `31.48` | `<= 25 deg (IAEA SSG-9 severe band starts here)` | dem_cog_max=88.96 gee_mean=None quality=copernicus_dem_30m fusion=None; primary slope is the max-in-30 m buffer, not the mean — likely overstated. Re-pull GEE mean slope at finer buffer. |

### NH-13 — 1 finding(s)

| Check | Site | Country | Column | Observed | Bound / expected | Notes |
|---|---|---|---|---|---|---|
| `NULL::wildfire_uncovered_BULK` | 363 sites | ? | `wildfire_combustible_pct` | `NULL on 363 of 363 rows` | `0..100 % from CORINE class 311-324` | Connector-wide gap — not a per-site anomaly. CorineConnector never populated wildfire_combustible_pct. First 8 sites: Porto Romano Power Station (AL), Duernrohr power station (AT), Enns Power Station (AT), Mellach power station (AT), Riedersbach power station (AT), St Andrae power station (AT), Timelkam power station (AT), Voitsberg power station (AT). Two paths: (a) re-run CORINE batch with the wildfire-class aggregator enabled; (b) accept as `insufficient` quality in business_logic ladder and use NH-12 + NH-10 as proxy for wildfire risk. |

### NS-01 — 6 finding(s)

| Check | Site | Country | Column | Observed | Bound / expected | Notes |
|---|---|---|---|---|---|---|
| `CONTEXT::cooling_flow_too_low_for_capacity` | Patnow power station | PL | `cooling_flow_m3s` | `0.78` | `>= 5 m3/s for 1718.00 MW (rule of thumb)` | cap=1718.00 MW, source=small_river 'Kanał Zrzutowy' @ 0.49 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |
| `CONTEXT::cooling_flow_too_low_for_capacity` | Vuglegirska power station | UA | `cooling_flow_m3s` | `0.99` | `>= 5 m3/s for 1200.00 MW (rule of thumb)` | cap=1200.00 MW, source=small_river 'Luhan' @ 1.36 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |
| `CONTEXT::cooling_flow_too_low_for_capacity` | Maritsa Iztok-2 power station | BG | `cooling_flow_m3s` | `0.66` | `>= 5 m3/s for 2162.00 MW (rule of thumb)` | cap=2162.00 MW, source=small_river 'HYRIV-20564375' @ 0.22 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |
| `CONTEXT::cooling_flow_too_low_for_capacity` | Maritsa Iztok-3 power station | BG | `cooling_flow_m3s` | `0.69` | `>= 5 m3/s for 1608.00 MW (rule of thumb)` | cap=1608.00 MW, source=small_river 'Sokolitsa' @ 0.74 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |
| `CONTEXT::cooling_flow_too_low_for_capacity` | Karapinar Konya Şeker power station | TR | `cooling_flow_m3s` | `0.14` | `>= 5 m3/s for 2000.00 MW (rule of thumb)` | cap=2000.00 MW, source=small_river 'HYRIV-20660735' @ 11.36 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |
| `CONTEXT::cooling_flow_too_low_for_capacity` | Kryvorizka power station | UA | `cooling_flow_m3s` | `0.54` | `>= 5 m3/s for 2925.00 MW (rule of thumb)` | cap=2925.00 MW, source=small_river 'HYRIV-20439786' @ 2.78 km, ns01_quality=hydrorivers_global — HydroRIVERS likely snapped to a tributary; needs GloFAS main-stem re-pull. |

### NS-02 — 64 finding(s)

| Check | Site | Country | Column | Observed | Bound / expected | Notes |
|---|---|---|---|---|---|---|
| `CONTEXT::grid_export_equals_capacity_fallback` | Kuchurgan power station | MD | `grid_export_capacity_mw` | `1400` | `!= installed_capacity_mw (1400.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Irmak power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Tosyalı İskenderun power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Ada Yumurtalık power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Astoria Ceyhan power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | EMBA Hunutlu power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Gerze power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Karapinar Konya Şeker power station | TR | `grid_export_capacity_mw` | `2000` | `!= installed_capacity_mw (2000.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | METES power station | TR | `grid_export_capacity_mw` | `2000` | `!= installed_capacity_mw (2000.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Dobrotvir power station | UA | `grid_export_capacity_mw` | `1110` | `!= installed_capacity_mw (1110.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Yüksek Gölovası power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Bandırma Karat power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Atlas Enerji İskenderun power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Babadere power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Ağan power station | TR | `grid_export_capacity_mw` | `1580` | `!= installed_capacity_mw (1580.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | İskenderun power station | TR | `grid_export_capacity_mw` | `2000` | `!= installed_capacity_mw (2000.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Kahramanmaraş Anadolu power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Amasra Bartın power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Ada Yesildag Enerji power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Alpu power station | TR | `grid_export_capacity_mw` | `1080` | `!= installed_capacity_mw (1080.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Deniz power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | İsken Sugözü power station | TR | `grid_export_capacity_mw` | `1210` | `!= installed_capacity_mw (1210.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Zorlu Soma power station | TR | `grid_export_capacity_mw` | `1220` | `!= installed_capacity_mw (1220.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Bandırma Elektrik power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Zaporizhia power station | UA | `grid_export_capacity_mw` | `1250` | `!= installed_capacity_mw (1250.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Burshtyn power station | UA | `grid_export_capacity_mw` | `3166` | `!= installed_capacity_mw (3166.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Çayırhan power station | TR | `grid_export_capacity_mw` | `1420` | `!= installed_capacity_mw (1420.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Cenal power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Mert power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Ladyzhyn power station | UA | `grid_export_capacity_mw` | `1800` | `!= installed_capacity_mw (1800.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Çelikler Yumurtalık power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Sanko Yumurtalık power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Kirazlıdere power complex | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Sarp Golvasi power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Kryvorizka power station | UA | `grid_export_capacity_mw` | `2925` | `!= installed_capacity_mw (2925.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Slavyansk power station | UA | `grid_export_capacity_mw` | `1540` | `!= installed_capacity_mw (1540.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Güreci power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Yeşilovacık power station | TR | `grid_export_capacity_mw` | `1254` | `!= installed_capacity_mw (1254.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Filyos power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Zmiivska power station | UA | `grid_export_capacity_mw` | `2270` | `!= installed_capacity_mw (2270.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Sinop Akfen power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Güney Akdeniz power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Çalışkan Ceyhan power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Afşin-Elbistan power stations | TR | `grid_export_capacity_mw` | `9283` | `!= installed_capacity_mw (9283.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Akdeniz Enerji power station | TR | `grid_export_capacity_mw` | `1600` | `!= installed_capacity_mw (1600.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Biga power station | TR | `grid_export_capacity_mw` | `1540` | `!= installed_capacity_mw (1540.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Naren Karabiga power station | TR | `grid_export_capacity_mw` | `1960` | `!= installed_capacity_mw (1960.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | HEMA Amasra power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | İÇDAŞ Bekirli power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Şevketiye Lapseki power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Karaburun power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Trakya Emba power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Kurakhov power station | UA | `grid_export_capacity_mw` | `1532` | `!= installed_capacity_mw (1532.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Luganskaya power station | UA | `grid_export_capacity_mw` | `1420` | `!= installed_capacity_mw (1420.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Prydniprovska power station | UA | `grid_export_capacity_mw` | `2455` | `!= installed_capacity_mw (2455.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Trypilska power station | UA | `grid_export_capacity_mw` | `1225` | `!= installed_capacity_mw (1225.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Kireçlik power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Zafer power station | TR | `grid_export_capacity_mw` | `1320` | `!= installed_capacity_mw (1320.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | Yumurtalık IC İçtaş power station | TR | `grid_export_capacity_mw` | `1200` | `!= installed_capacity_mw (1200.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| `CONTEXT::grid_export_equals_capacity_fallback` | ZETES power stations | TR | `grid_export_capacity_mw` | `3450` | `!= installed_capacity_mw (3450.00)` | ns02_quality=insufficient; perfect equality at >1000 MW is the connector's no-NTC fallback. Confirm vs ENTSO-E zone NTC value before treating this as the SMR's grid export ceiling. |
| … 4 more rows truncated ||||||  |

### NS-04 — 19 finding(s)

| Check | Site | Country | Column | Observed | Bound / expected | Notes |
|---|---|---|---|---|---|---|
| `CONTEXT::favourable_area_implausibly_small` | Bitola power station | MK | `favourable_area_ha` | `0` | `>= 1 % of buildable (145.73 ha)` | buildable=145.73, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Ploče power station | HR | `favourable_area_ha` | `0` | `>= 1 % of buildable (238.74 ha)` | buildable=238.74, favourable_pct=34.30, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Namal power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (151.51 ha)` | buildable=151.51, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Zeltweg power station | AT | `favourable_area_ha` | `0` | `>= 1 % of buildable (39.04 ha)` | buildable=39.04, favourable_pct=0.20, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Mariovo power station | MK | `favourable_area_ha` | `0` | `>= 1 % of buildable (151.22 ha)` | buildable=151.22, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Babadere power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (224.39 ha)` | buildable=224.39, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Çan-2 power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (28.48 ha)` | buildable=28.48, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Mostecka Power Station | CZ | `favourable_area_ha` | `0` | `>= 1 % of buildable (6.65 ha)` | buildable=6.65, favourable_pct=76.00, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Güreci power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (151.51 ha)` | buildable=151.51, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Legnica Power Station | PL | `favourable_area_ha` | `0` | `>= 1 % of buildable (6.25 ha)` | buildable=6.25, favourable_pct=93.20, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Lodz-2 power station | PL | `favourable_area_ha` | `0` | `>= 1 % of buildable (6.39 ha)` | buildable=6.39, favourable_pct=99.80, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Szczecin power station | PL | `favourable_area_ha` | `0` | `>= 1 % of buildable (9.61 ha)` | buildable=9.61, favourable_pct=66.40, ns04_quality=high — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Çan (18 Mart) power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (81.20 ha)` | buildable=81.20, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Biga power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (31.04 ha)` | buildable=31.04, favourable_pct=0.50, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Naren Karabiga power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (15.30 ha)` | buildable=15.30, favourable_pct=0.30, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Evrese power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (11.23 ha)` | buildable=11.23, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Şevketiye Lapseki power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (254.45 ha)` | buildable=254.45, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Karaburun power station | TR | `favourable_area_ha` | `0.36` | `>= 1 % of buildable (36.40 ha)` | buildable=36.40, favourable_pct=1.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |
| `CONTEXT::favourable_area_implausibly_small` | Zafer power station | TR | `favourable_area_ha` | `0` | `>= 1 % of buildable (5.34 ha)` | buildable=5.34, favourable_pct=0.00, ns04_quality=medium — favourable_area should never be 100× smaller than buildable when CORINE assigns any non-zero %. |

## Audit-log: previously applied Phase 1 fixes

Every row below is one ``audit_log`` entry created by a previous 
``--apply`` run of this scanner.  They are reproduced here so the 
report is a complete record even when the current dry-run finds 
zero new auto-fix candidates.

| Table | Message | Before | After |
|---|---|---|---|
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=145.73, buildable_area_ha=145.73 | `{"patch_count": null}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=1.58, buildable_area_ha=1.58 | `{"patch_count": null}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=0.02, buildable_area_ha=0.02 | `{"patch_count": null}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=28.48, buildable_area_ha=28.48 | `{"patch_count": null}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=81.20, buildable_area_ha=81.20 | `{"patch_count": null}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=1.90, buildable_area_ha=1.90 | `{"patch_count": 0}` | `{"patch_count": 1}` |
| `site_infrastructure_v2` | [NULL::patch_count_derivable] largest_contiguous_ha=11.23, buildable_area_ha=11.23 | `{"patch_count": null}` | `{"patch_count": 1}` |

## Next steps

1. **Re-run with `--apply`** to commit the auto-fixes (or run again in 
   dry-run with the same DB to verify zero new findings).
2. **Phase 2** (build `atoms_vs_ashes_merged`) consumes the cleaned API DB.
3. **Phase 3** (`report/business_logic.md`) formalises every bound used here 
   and adds a fallback ladder for each escalation.
4. **Phase 5** (LLM enrichment) uses LLM narratives to patch escalations 
   where `data_sources` and `confidence` justify it.
