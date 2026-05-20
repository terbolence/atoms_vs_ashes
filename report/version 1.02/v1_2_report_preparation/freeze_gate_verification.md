<!-- man_hours: 1.6 -->

# Version 1.2 Freeze Gate Verification

## Purpose

This note verifies the frozen analytical baseline required before version 1.2 report drafting and regeneration can proceed. It implements Step 1 of the controlling plan without running country/site regeneration, because the plan requires user confirmation before regeneration begins.

## Frozen Run IDs

| Anchor               | Frozen run ID       | Active-profile snapshot                                | Verification |
| -------------------- | ------------------- | ------------------------------------------------------ | ------------ |
| Scoring              | `score-2ffc8a70`    | `audit/.runtime/active_profile.score-2ffc8a70.yaml`    | Present      |
| Regional sensitivity | `sens-751884cf`     | `audit/.runtime/active_profile.sens-751884cf.yaml`     | Present      |
| National sensitivity | `nat-sens-139d3947` | `audit/.runtime/active_profile.nat-sens-139d3947.yaml` | Present      |

## Snapshot Parameter Check

| Parameter                             | Freeze requirement     | Snapshot value         | Status |
| ------------------------------------- | ---------------------- | ---------------------- | ------ |
| `run_label`                           | `baseline`             | `baseline`             | Match  |
| `db_profile`                          | `merged`               | `merged`               | Match  |
| `spec_dir`                            | `config/scoring_specs` | `config/scoring_specs` | Match  |
| `weight_profile`                      | `baseline`             | `baseline`             | Match  |
| `scope.smr_keys`                      | `nuscale_voygr6` only  | `nuscale_voygr6`       | Match  |
| `scoring.unscored_fallback_score`     | `5.0`                  | `5.0`                  | Match  |
| `scoring.top_n_per_country`           | `10`                   | `10`                   | Match  |
| `scoring.near_miss_gap_pct`           | `10.0`                 | `10.0`                 | Match  |
| Regional `sensitivity.mc_iterations`  | `10000`                | `10000`                | Match for regional run only |
| National sensitivity iteration basis  | `50000`                | User-corrected in this chat as `nat-sens-139d3947`, 50,000 iterations | Report-drafting control |
| `sensitivity.mc_seed`                 | `42`                   | `42`                   | Match  |
| `sensitivity.weight_perturbation_pct` | `20.0`                 | `20.0`                 | Match  |
| `sensitivity.mc_stability_band_width` | `1.0`                  | `1.0`                  | Match  |

The scoring and regional-sensitivity active-profile snapshots have the same shared baseline parameters. The national sensitivity run for report drafting is `nat-sens-139d3947` and, per the user's correction in this chat on 2026-05-18, it is a 50,000-iteration national sensitivity run. The active-profile YAML still records `sensitivity.mc_iterations: 10000`; that stale metadata must not be repeated as the national sensitivity iteration count in report drafting.

## Report-Drafting Sensitivity Control

Regional and national sensitivity runs both exist in the frozen dossier, but report drafting must use **national sensitivity**. For country choices, site stability, rank robustness, Stage 3 sequencing, Chapter 3, Chapter 4, Chapter 5, and Annex C, treat `nat-sens-139d3947` as the controlling sensitivity basis and describe it as the 50,000-iteration national sensitivity run. Forget regional sensitivity for report drafting unless the user explicitly reopens a narrow comparator exhibit later.

## Regeneration Manifest to Stage After User Acceptance

All regeneration must pin the frozen scoring run and national sensitivity run for country/site choices. Regional sensitivity is not a report-drafting basis under the current user instruction.

| Output class                               | Target path                                                                                         | Required basis                                    | Gate status                |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------- |
| Country bundles                            | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/data/`                     | `score-2ffc8a70`; `nat-sens-139d3947`             | Awaiting user confirmation |
| Selected-site bundles                      | Same Chapter 5 data area                                                                            | `score-2ffc8a70`; `nat-sens-139d3947`             | Awaiting user confirmation |
| Country status maps                        | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/`                  | Frozen country bundles                            | Awaiting user confirmation |
| Pareto and family charts                   | Chapter 5 figures                                                                                   | Frozen country/site bundles                       | Awaiting user confirmation |
| Chapter 4 numerical exhibits               | `report/version 1.02/output/report/chapters/04_results_and_findings.md` and figures                 | Frozen scoring and national sensitivity artefacts | Awaiting user confirmation |
| Chapter 3 scoring and sensitivity exhibits | `report/version 1.02/output/report/chapters/03_stage_2_site_selection.md` and Annex C               | Frozen scoring and national sensitivity artefacts | Awaiting user confirmation |
| Recommended top-five ledger                | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/recommended_top5_sites.md` | Frozen scoring and national sensitivity artefacts | Awaiting user confirmation |
| Methodology artefacts                      | `report/version 1.02/methodology/` and report annexes                                               | Frozen rubric and sensitivity basis               | Awaiting user confirmation |

## Blocking Gate

The freeze verification correction is recorded for the current tranche, but it is not itself user acceptance of the freeze gate. Regeneration is intentionally not started in this pass because the controlling plan requires user confirmation before rebuilding bundles, charts, maps, methodology artefacts, and scaffolds.
