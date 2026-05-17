<!-- man_hours: 1.0 -->
# Tier 1 Data OK Auditor Review

Review timestamp: 2026-05-17

Scope: implemented Tier 1 Data OK scoring repair for `HI-07`, `NH-10`, and `NH-12`, including scoring specs/rubrics, context derivations, GUI/report unscored handling, read-only audit artifacts, tests, and scored-site examples.

Audit basis:

- `experts/quality/auditor.md` section S for user-visible surface coverage.
- `experts/quality/siting_expert.md` plausibility ranges for wind and temperature metrics.
- Read-only artifacts under `audit/post_processing/06_scoring/20260517_tier1_data_ok_*`.
- Scored example Markdown files generated from the local DB using `src/scripts/generate_scoring_examples.py`.

## Conformance Matrix

| Area | Evidence | Status | Notes |
| --- | --- | --- | --- |
| Literal request coverage | `audit/feature_completion_matrices/2026-05-17_tier1_data_ok_scoring.md` | Conformant | Matrix exists and names GUI/CLI/engine/persistence/consumer/test surfaces. |
| Scoring source of truth | `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_specs/nh_natural_hazards.yaml`, rubric mirrors | Conformant after fix | HI-07 sparse bands were adjusted during this audit; spec/rubric parity is test-covered. |
| Context vocabulary | `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/scripts/generate_scoring_examples.py` | Conformant after fix | The example generator now resolves `site_human_induced` to `SiteHumanHazards` and applies derived context before scoring examples. |
| User-visible examples | `20260517_tier1_data_ok_hi07_scored_examples.md`, `..._nh10_...`, `..._nh12_...` | Conformant after fix | Examples include site name, country, coordinates, engine-visible fields, score, and verdict. Markdown cells are escaped so DB comments do not break tables. |
| GUI/report unscored handling | Results drawer/site-detail tests and consumer paths in the feature matrix | Conformant | Unscored rows are surfaced as unscored rather than displayed as a real `5.0` score. |
| DB write gate | No score run, migration, backfill, or enrichment run executed | Conformant | Persisted before/after rescore remains consent-gated. |

## Band Plausibility Review

### HI-07

Initial audit finding: the implemented HI-07 ladder produced no local examples in `9-10` or `7-8`, even though sparse completed-search examples existed. The example rows also showed that the persisted `transmitter_count` comments describe "Total within 25 km", while the scoring key remains the legacy alias `transmitter_count_10km`.

Fix applied:

- Documented `transmitter_count_10km` as a legacy scoring alias over the available transmitter search-count proxy, not a verified 10 km-only field.
- Changed favorable bands to require both low count and distance from the nearest transmitter:
  - `9-10`: completed search, count `<= 5`, and nearest transmitter `> 10 km` or null.
  - `7-8`: completed search, count `<= 10`, and nearest transmitter `> 5 km` or null.
- Preserved lower bands for dense/nearby proxies and kept `transmitter_power_class` deferred.

Example sanity check:

- `Barbaros-1 power station` and `Miljevina power station` now score `9.5`; both have only 4-5 transmitter-like features and nearest transmitter distance above 16 km.
- `Güney Akdeniz power station` remains `1.5` because the nearest transmitter is 0.73 km despite a low count.
- `Opole power station` remains `1.5` due to both high count and very close nearest transmitter.

Disposition: acceptable as ranking-grade count/proximity proxy, with the caveat that power class, frequency, antenna height, and radiated power are not measured.

### NH-10

The observed `max_wind_speed_ms` range is 5.41-14.44 m/s. The siting-expert plausibility reference for a 50-year gust is 15-50 m/s, so these values remain explicitly caveated as smoothed ERA5 monthly-means gust evidence, not design-basis gusts.

Example sanity check:

- `Rovinari power station` at 5.41 m/s scores `9.5`, which is consistent with the lowest relative exposure in this local proxy.
- `Skawina power station` at 10.55 m/s scores `3.5`, a higher relative proxy exposure.
- `Bandırma III power station` and `Tusimice power station` at roughly 12.5-12.8 m/s score `1.5`, representing the high local proxy tail.

Disposition: acceptable for relative ranking only. The 49 m/s envelope is correctly retained as a review flag, not an exclusion or proof of design adequacy.

### NH-12

The observed temperature tails are physically plausible for the project scope: `extreme_temp_max_c` 19.54-33.32 C and `extreme_temp_min_c` -12.29 to 7.93 C. The aggregate uses separate heat and cold tails and caps at 5 when either tail is severe.

Example sanity check:

- `Berane power station` scores `7.5`: low heat tail but moderate cold tail.
- `Kangal power station` scores `5.0`: mild high-temperature tail but severe cold tail, so the cap correctly prevents a high aggregate score.
- `Yıldırım Elazığ power station` scores `3.5`: elevated heat and cold-stress tails are both visible.

Disposition: acceptable as a screening-grade relative thermal-stress ranking proxy. It is not a site-specific HVAC, ultimate heat sink, or design-basis temperature assessment.

## Findings And Fixes

| Severity | Finding | Fix |
| --- | --- | --- |
| Medium | `src/scripts/generate_scoring_examples.py` did not resolve `site_human_induced` and did not apply derived context, so it could not generate HI-07 examples through the same vocabulary as scoring. | Added table alias support, derived-context application, composite metric fallback, site-name/coordinate output, and tests. |
| Medium | Generated examples could be invalid Markdown because DB comments contain `|`. | Added Markdown cell escaping and regenerated all Tier 1 examples. |
| Medium | HI-07 sparse/distant completed-search examples were scored only 5-6 and no local examples occupied the 9-10 or 7-8 favorable bands. | Adjusted favorable HI-07 bands and regenerated audit/example artifacts. |
| Low | HI-07 and NH rubric mirrors had small metadata/comment hygiene issues. | Removed duplicate HI-07 weight metadata and restored Tier 1 NH-10/NH-12 section-symbol references in the rubric mirror. |

## Example Files

- `audit/post_processing/06_scoring/20260517_tier1_data_ok_hi07_scored_examples.md`
- `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh10_scored_examples.md`
- `audit/post_processing/06_scoring/20260517_tier1_data_ok_nh12_scored_examples.md`

## Acceptance Decision

Accept with conditions.

The implemented logic, examples, and user-visible surfaces are acceptable for local read-only validation. The remaining condition is a persisted before/after DB rescore for the target run/SMR, which requires explicit user consent because it writes `runs`, `ranking_scores`, `composite_rankings`, `screening_verdicts`, snapshots, and audit rows.

## End-to-End Trace

`CLI/GUI scoring: src/atoms_vs_ashes/scoring/_cli.py and src/atoms_vs_ashes/gui/screen_pages/04_run_dashboard.py -> src/atoms_vs_ashes/scoring/_cli_run.py / src/atoms_vs_ashes/gui/_runner.py -> src/atoms_vs_ashes/scoring/engine.py + merge_context_derivations.py + bands.py using config/scoring_{rubrics,specs}/{hi_human_induced,nh_natural_hazards}.yaml -> ranking_scores/composite_rankings/screening_verdicts plus audit/post_processing/06_scoring/20260517_tier1_data_ok_* read-only artifacts -> Results/report/export consumers in src/atoms_vs_ashes/gui/_results_* + src/atoms_vs_ashes/reporting/site_bundle.py + src/scripts/_site_profile_*.py -> tests/scoring/test_tier1_data_ok_bands.py, tests/scripts/test_audit_tier1_data_ok.py, consumer unscored rendering tests`
