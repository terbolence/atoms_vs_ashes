<!-- man_hours: 0.7 -->
# Conversation Log: Merged DB And NS-05 Site Area Source Of Truth

## User Request

The user clarified that the merged database is the canonical database for
scoring work, and asked to implement the following:

- The UI should only use the merged DB setting.
- `NS-05/A15` should use `site_area_ha` as the criterion indicator.
- Report surface-area numbers should use `site_area_ha`.
- `favourable_area_ha` should be mentioned as the larger expansion
  envelope where available.

## Findings

- `NS-05/A15` still evaluated `largest_contiguous_ha < 14`.
- Doicesti in the merged DB had `site_area_ha = 40.0` but stale
  `largest_contiguous_ha = 0.16`, which explained the continued A15 flag.
- The CLI default and GUI runner still allowed non-merged DB profiles.

## Implementation

- Pinned GUI, runner, national runner, run-profile schema, and CLI default
  behavior to `merged`.
- Rewired `NS-05/A15` specs, legacy rubrics, threshold metadata, prompts,
  LLM schema/context, and report bundles to use `site_area_ha` as the
  adequacy indicator and `favourable_area_ha` as expansion context.
- Added focused regression tests for the stale-contiguous-area case, merged
  DB runner behavior, run-profile coercion, CLI default, and report bundle
  land-area summary.

## Verification

- Focused pytest command passed: 39 tests.
- IDE lints reported no errors for edited files.
- Reran scoring against the merged DB only:
  `ns05-sitearea-20260517T1440Z`.
- Verification query for Doicesti returned:
  `site_area_ha = 40.0`, `largest_contiguous_ha = 0.16`,
  `favourable_area_ha = 49.32`, `A15 verdict = pass`,
  `measured_value = {"site_area_ha": 40.0}`, `NS-05 score = 7.5`.
