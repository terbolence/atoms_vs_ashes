<!-- man_hours: 2.2 -->
NH-08 - Coastal flooding (storm surge, tsunami) - A9 Final Policy

Phase: **[avoidance, ranking]** - Primary metric: `coast_distance_km`
aliasing `site_natural_hazards.distance_to_coast_km` - A-code: **A9**
(`avoidance_penalty`; verdict `caution`) - Pass mark: ranking >= 5.0 -
Status: **FINAL - S-38 COAST DISTANCE IMPLEMENTED**

## 1. User Decision

NH-08 / A9 is an avoidance caution, not a misleading pass/fail statement.
The criterion remains a Stage 1-2 screening signal for coastal flooding,
storm surge, and tsunami exposure. It does not approve, license, exclude, or
resolve Stage 3 design-basis flooding.

The implemented policy is:

- A measured S-38 `coast_distance_km < 10` with `elevation_m < 50`
  triggers A9 as an avoidance **caution**.
- A missing `coast_distance_km` is a data gap, not site-level coastal
  exposure. It must not trigger A9 by itself.
- A positive coastal proxy (`storm_surge_class` in `fluvial_proxy`,
  `moderate`, `high`, or `tsunami_zone_flag` in `moderate`, `high`) with
  `elevation_m < 50` triggers A9 as a caution.
- `elevation_m >= 50` or `country_is_landlocked == true` remains a
  favourable screening branch unless other evidence contradicts it.
- Inland river flooding remains NH-09. A low-elevation site in a coastal
  country, such as Braila on the Danube, should not be flagged as coastal
  flooding unless measured sea-coast distance or marine-hazard proxy evidence
  supports the flag.

## 2. Implemented Runtime State

The active scoring spec and legacy rubric now use the same A9 caution
expression:

`(coast_distance_km < 10 or storm_surge_class in ['fluvial_proxy', 'moderate', 'high'] or tsunami_zone_flag in ['moderate', 'high']) and elevation_m < 50`

Avoidance hits are promoted by the engine from `fail` to `caution`, so an
A9 hit keeps the site eligible while marking the coastal-flood issue for
Stage 3 follow-up.

The NH-08 bands are explicit rather than recipe-derived. S-38 Natural Earth
now supplies measured sea-coast distance to the existing
`site_natural_hazards.distance_to_coast_km` column. The score-9/10 branch is:

`country_is_landlocked == true or coast_distance_km > 50 or elevation_m >= 50`

For low-elevation, non-landlocked sites with missing coast distance and no
marine proxy, no NH-08 band is treated as proven favourable and no A9 caution
is created from missing data alone. Once S-38 has populated
`coast_distance_km`, inland sites can score through the measured-distance
branches.

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
- Route local coastal-flood mapping, storm-surge screening, tsunami trace
  review, and finished-floor / freeboard confirmation to Stage 3
  characterization.
- Do not state that the site is rejected, flood-safe, or licensing-ready from
  NH-08 alone.

The report-writing prompt at
`report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md`
now carries this instruction explicitly.

## 5. Local Evidence Basis

The S-38 dry run over 361 merged sites populated a measured sea-coast distance
for every site with valid coordinates. Anchor results:

- Braila power station: `distance_to_coast_km = 81.043`, so the Danube-side
  river setting is not a coastal-flooding A9 trigger.
- Porto Romano Power Station: `distance_to_coast_km = 1.836`, so low-lying
  coastal exposure remains cautionable.
- Varna power station: `distance_to_coast_km = 13.288`, so it is outside the
  project A9 <10 km distance pivot but remains an A9 caution because the GFMS
  near-coastal proxy sets `storm_surge_class = fluvial_proxy`.

## 6. Files Carrying The Policy

- `config/scoring_specs/nh_natural_hazards.yaml` - active compiled scoring
  spec: explicit NH-08 bands and measured-distance / proxy A9 expression.
- `config/scoring_rubrics/nh_natural_hazards.yaml` - legacy rubric mirror.
- `data/cartography/ne_50m_coastline.geojson` - vendored S-38 Natural Earth
  coastline asset.
- `src/atoms_vs_ashes/connectors/natural_earth/coastline.py` and
  `src/scripts/backfill_s38_coast_distance.py` - coast-distance computation
  and DB backfill path.
- `config/scoring_specs/threshold_metadata.yaml` - A9 removed from the
  single-metric threshold surface.
- `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md`
  - report-facing instruction for NH-08 coastal-flood limitations.
- `tests/scoring/test_threshold_band_runtime.py` - focused regression tests
  for A9 caution, missing-distance pass, and measured inland scoring.

Final status: **IMPLEMENTED - NH-08 / A9 is measured-distance and
proxy-oriented; Stage 3 coastal-flood conclusions remain out of scope.**
