<!-- man_hours: 1.8 -->
NH-08 - Coastal flooding (storm surge, tsunami) - A9 Final Policy

Phase: **[avoidance, ranking]** - Primary metric: `coast_distance_km`
aliasing `site_natural_hazards.distance_to_coast_km` - A-code: **A9**
(`avoidance_penalty`; verdict `caution`) - Pass mark: ranking >= 5.0 -
Status: **FINAL - CAUTION POLICY IMPLEMENTED**

## 1. User Decision

NH-08 / A9 is an avoidance caution, not a misleading pass/fail statement.
The criterion remains a Stage 1-2 screening signal for coastal flooding,
storm surge, and tsunami exposure. It does not approve, license, exclude, or
resolve Stage 3 design-basis flooding.

The implemented policy is:

- A measured `coast_distance_km < 10` with `elevation_m < 50` triggers A9
  as an avoidance **caution**.
- A missing `coast_distance_km` with `elevation_m < 50` and
  `country_is_landlocked != true` also triggers A9 as an avoidance
  **caution**, because local evidence cannot support a clear coastal-flood
  screening pass.
- `elevation_m >= 50` or `country_is_landlocked == true` remains a
  favourable screening branch unless other evidence contradicts it.
- Missing coast distance for a low-elevation coastal-country site should be
  reported as an unresolved coastal-flood limitation and routed to Stage 3
  coast-distance, storm-surge, and inundation confirmation.

## 2. Implemented Runtime State

The active scoring spec and legacy rubric now use the same A9 caution
expression:

`(coast_distance_km < 10 or (coast_distance_km is null and country_is_landlocked != true)) and elevation_m < 50`

Avoidance hits are promoted by the engine from `fail` to `caution`, so an
A9 hit keeps the site eligible while marking the coastal-flood issue for
Stage 3 follow-up.

The NH-08 bands are explicit rather than recipe-derived. This prevents the
previous distance-only `band_recipe` from shadowing the fixed high-elevation
and landlocked safe branches. The score-9/10 branch is:

`country_is_landlocked == true or coast_distance_km > 50 or elevation_m >= 50`

For low-elevation, non-landlocked sites with missing coast distance, no NH-08
band is treated as proven favourable. The ranking row can remain unscored at
the neutral pass-mark default, while the A9 avoidance verdict carries the
reader-facing caution.

## 3. Threshold-Control Policy

The previous threshold metadata exposed A9 as a single editable
`coast_distance_km < 10` control even though the real policy is compound:
coast distance, elevation, and landlocked context all matter. That control
has been removed from `config/scoring_specs/threshold_metadata.yaml` for now.

A future GUI control for A9 should be a compound coastal-flood editor, not a
single distance slider that rewrites the fail expression and loses the
elevation / missing-data caution logic.

## 4. Report-Description Contract

Report prose must surface NH-08 limitations when the evidence is unresolved.
For the `family_natural_hazards` specialist paragraph and residual-risk
register:

- Do not describe a missing `distance_to_coast_km` / `coast_distance_km`
  value as a clear pass.
- If NH-08 is unscored, low-quality, inconclusive, or A9 is a caution, state
  that coastal storm-surge / tsunami exposure is unresolved at Stage 1-2.
- Quote `elevation_m` if present in the bundle before explaining the
  consequence.
- Route coast-distance derivation, local coastal-flood mapping, storm-surge
  screening, tsunami trace review, and finished-floor / freeboard confirmation
  to Stage 3 characterization.
- Do not state that the site is rejected, flood-safe, or licensing-ready from
  NH-08 alone.

The report-writing prompt at
`report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md`
now carries this instruction explicitly.

## 5. Local Evidence Basis

The pre-decision audit found that the merged evidence base had
`distance_to_coast_km` unpopulated for the inspected site set, while
`elevation_m` was populated. Under the old expression,
`coast_distance_km < 10 and elevation_m < 50`, a NULL coast-distance
comparison could make a low-elevation coastal-country site look like an A9
pass. That was the misleading result the user decision corrected.

Examples from the audit included low-elevation coastal-country sites such as
Porto Romano Power Station, Varna power station, and Ploce power station,
where the persisted coast-distance value was NULL. Those cases now receive a
caution if they are evaluated with `country_is_landlocked == false` and
`elevation_m < 50`.

## 6. Files Carrying The Policy

- `config/scoring_specs/nh_natural_hazards.yaml` - active compiled scoring
  spec: explicit NH-08 bands and A9 missing-distance caution expression.
- `config/scoring_rubrics/nh_natural_hazards.yaml` - legacy rubric mirror.
- `config/scoring_specs/threshold_metadata.yaml` - A9 removed from the
  single-metric threshold surface.
- `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md`
  - report-facing instruction for NH-08 coastal-flood limitations.
- `tests/scoring/test_threshold_band_runtime.py` - focused regression tests
  for A9 caution and the high-elevation / landlocked safe branches.

Final status: **IMPLEMENTED - NH-08 / A9 is caution-oriented and
report-facing; Stage 3 coastal-flood conclusions remain out of scope.**
