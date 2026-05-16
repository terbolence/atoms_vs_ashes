<!-- man_hours: 0.3 -->
# NS-04 — Site topography / grading

Status: **accepted current state** for the ranking phase.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-04 — Site topography / grading |
| Phases | `[ranking]` |
| Primary metric | `favourable_land_pct` |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` |
| Weight | factor 6; normalised 2.1% |
| Related flag | `sanity_task2` review flag when `favourable_area_ha < 1.0 and site_area_ha > 50` |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is the primary metric sourced? | Yes. `favourable_land_pct` is present in the DB model, context, LLM persist mapping, CORINE/WorldCover parsers, and coverage report. | Accept current state. |
| Are bands monotonic? | Yes. Higher favourable-land percentage always scores higher. | Accept current state. |
| Is the review flag score-changing? | No. `sanity_task2` is a `review_flag`; it does not change the ranking band. | Accept current state. |
| Is coverage sufficient for documentation? | `coverage_latest.md` reports 100% NS-04 coverage across the tracked fields. | Accept current state. |

## Score Bands

| Score | `favourable_land_pct` condition | Descriptor |
| ---: | --- | --- |
| 9-10 | `> 80` | Very favourable grading/topography proxy. |
| 7-8 | `>= 60` | Generally favourable. |
| 5-6 | `>= 40` | Pass-mark band. |
| 3-4 | `>= 20` | Limited favourable land; grading and drainage complexity likely. |
| 1-2 | `< 20` | Poor topography/land-cover proxy for site preparation. |

The score band is direct and does not use a band recipe. The review flag is separate and surfaces suspicious curation cases rather than re-banding the score.

## Metric Truth And Data Quality

Source fields are `site_infrastructure_v2.favourable_land_pct`, `favourable_area_ha`, and `favourable_area_method`, with supporting `dominant_land_class`, `dominant_class_pct`, `moderate_land_pct`, and `unfavourable_land_pct`. CORINE and WorldCover parsers write the percentage metrics; `analysis/site_topography.py` also writes the same topography proxy.

`favourable_land_pct = NULL` means no source evidence reached the ranking context; it would fall through to the pass-mark default as unscored. The current coverage report shows 100% coverage for the active NS-04 fields.

## Examples

The local PL feedback bundle shows scored NS-04 rows with `score_0_10 = 5.5`, `quality_flag = high`, `confidence = high`, and band `"40-60 %."`, demonstrating that the current bundle path matches the YAML band ladder. Broader country-bundle coverage shows NS-04 as a fully sourced infrastructure criterion in `coverage_latest.md`.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-04 phase, primary metric, bands, review flag, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-04 rank-only rationale.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing bands and data anchor.
- `src/atoms_vs_ashes/db/models.py`: `favourable_land_pct`, `favourable_area_ha`, and related infrastructure fields.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: 100% NS-04 coverage line.

## Artifact Footer

Documentation-only ranking pass. No scoring specs, rubrics, code, tests, audit logs, or man-hours registry entries were changed.
