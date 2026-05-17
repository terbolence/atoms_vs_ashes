<!-- man_hours: 0.7 -->
# Merged DB And NS-05 Site Area Source Of Truth

## Task

Implement the user's clarified decision:

1. The UI and scoring runner must use the canonical `merged` database only.
2. `NS-05 / A15` Site Footprint Adequacy must use `sites.site_area_ha` as its area indicator.
3. Reporting/site-profile data should use `site_area_ha` for the surface-area number and mention `favourable_area_ha` as the larger expansion envelope where available.

## Current State

- The CLI default `--db-profile` is `api`, which allowed a recent scoring run to write to `atoms_vs_ashes` rather than `atoms_vs_ashes_merged`.
- The GUI Run Profile page still lets users select `api`, `llm`, or `merged`.
- `Settings.DatabaseSettings.db` defaults to `atoms_vs_ashes`, so code paths that do not set `POSTGRES_DB` still read/write the API DB.
- `NS-05/A15` is currently wired to `largest_contiguous_ha < 14` in scoring specs/rubrics and threshold metadata.
- In `atoms_vs_ashes_merged`, Doicesti has `sites.site_area_ha = 40.00` but stale `site_infrastructure_v2.largest_contiguous_ha = 0.16`, so the current A15 expression still flags it.

## Implementation Plan

1. Create the project Feature Completion Matrix before code edits.
2. Force defaults and UI controls to `merged`:
   - `Settings.DatabaseSettings.db` default -> `atoms_vs_ashes_merged`.
   - CLI `--db-profile` default/help -> `merged`.
   - Run Profile UI removes profile choice and returns `db_profile = "merged"`.
   - GUI runner defensively passes `--db-profile merged`.
3. Rewire `NS-05/A15`:
   - `config/scoring_specs/ns_non_safety.yaml` and `config/scoring_rubrics/ns_non_safety.yaml` use `sites.site_area_ha` for A15 and include `site_infrastructure_v2.favourable_area_ha` for expansion evidence.
   - `config/scoring_specs/threshold_metadata.yaml` uses metric `site_area_ha` for `NS-05/A15`.
   - Adjust bands to use `site_area_ha` for adequacy and `favourable_area_ha` for expansion/upside.
4. Ensure reporting/export surfaces expose both:
   - `site_area_ha` as the site footprint/surface area.
   - `favourable_area_ha` as the expansion envelope.
5. Add/update tests:
   - CLI default is merged.
   - Run Profile UI contract returns merged.
   - NS-05 A15 does not flag when `site_area_ha >= 14` even if `largest_contiguous_ha` is stale/tiny.
   - Site bundle/report data exposes `site_area_ha` and `favourable_area_ha`.
6. Run focused tests/lints.
7. Update audit log, plan mirrors, feature matrix, and man-hours metadata.

## Execution Notes

- Implemented merged-only GUI/runner behavior and changed CLI/default DB to
  `atoms_vs_ashes_merged`.
- Rewired `NS-05/A15` to `site_area_ha < 14` and retained
  `favourable_area_ha` only as expansion-envelope report context.
- Added focused regression coverage and reran scoring on merged DB only:
  `ns05-sitearea-20260517T1440Z`.
- Verified Doicesti persisted as A15 `pass` with measured
  `{"site_area_ha": 40.0}` despite stale `largest_contiguous_ha = 0.16`.
