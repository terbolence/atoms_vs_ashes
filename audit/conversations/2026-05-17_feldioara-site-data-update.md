# FPCU Feldioara manual site data update

**Date:** 2026-05-17

## Objective

Update merged DB entry for FPCU Feldioara with settled site area (345 ha), installed capacity (160 MW), and grid characterization note (400 kV ~7 km, export headroom context).

## Key Decisions

- `site_area_ha` confirmed at 345 ha (already resolved from llm_web_observation).
- `installed_capacity_mw` and `operating_capacity_mw` set to 160 MW.
- `grid_export_capacity_mw` left NULL — corridor ~1 GW potential documented in `ns02_comment` and `site_observations` only, not used as measured export capacity.
- OSM nearest-HV fields (3.31 km, 110 kV) unchanged; manual note distinguishes 400 kV asset at ~7 km.

## Files Changed

- `config/default.yml` — supplementary site entry extended with capacity, area, grid note in `extended_data`.
- Merged DB `sites`, `site_infrastructure_v2`, `site_observations`, `audit_log` for site `18ecb024-ee4f-4045-8254-5e95d61dea8c`.

## Outcome

Completed — run_id `manual_feldioara_20260517`.
