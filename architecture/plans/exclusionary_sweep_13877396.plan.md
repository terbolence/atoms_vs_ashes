---
name: exclusionary sweep
overview: Run the NH-04/NH-07 verification-and-fix process across every remaining exclusionary criterion in the UI/specs, with explicit checks for both over-failing false positives and under-catching false negatives. Already-reviewed NH-02, NH-04, and NH-07 are excluded from the active sweep.
todos:
  - id: inventory
    content: Confirm active exclusionary criteria inventory and excluded already-reviewed criteria.
    status: completed
  - id: ns08
    content: Run §O pre-edit analysis for NS-08, including false-positive and false-negative DB checks.
    status: in_progress
  - id: ep01
    content: Run §O pre-edit analysis for EP-01, including stale composite and trauma-distance checks.
    status: pending
  - id: nh03
    content: Run §O pre-edit analysis for NH-03, including remedy/NULL false-negative checks.
    status: pending
  - id: ns01
    content: Run §O pre-edit analysis for NS-01, including dry-cooling and cooling-source NULL semantics.
    status: pending
  - id: nh10
    content: Run §O pre-edit analysis for NH-10, including wind metric/unit verification.
    status: pending
  - id: per-criterion-fixes
    content: After each sign-off, implement focused fixes, tests, examples, docs, audit log, and man-hours.
    status: pending
isProject: false
---

# Remaining Exclusionary Criteria Sweep

## Scope

Active criteria to analyze and, if needed, fix:

- `EP-01 — Emergency-plan feasibility (composite)` in [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ep_emergency_planning.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ep_emergency_planning.yaml)
- `NH-03 — Geotechnical: settlement and liquefaction` in [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml)
- `NH-10 — Extreme winds` in [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml)
- `NS-01 — Cooling water / ultimate heat sink` in [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml)
- `NS-08 — Ecological sensitivity (Natura 2000 / WDPA)` in [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml)

Excluded as already covered by prior work:

- `NH-02 — Seismic: Surface Rupture`
- `NH-04 — Geotechnical: Slope Stability`
- `NH-07 — Volcanism`

## Workflow Per Criterion

For each active criterion, run the same process used for NH-04/NH-07 under [`/Users/terbolence/projects/atoms_vs_ashes/experts/scoring/scoring_criterion_review.md`](/Users/terbolence/projects/atoms_vs_ashes/experts/scoring/scoring_criterion_review.md):

1. Establish current behavior from spec YAML, rubric YAML, compiled `Criterion`, threshold metadata, and DB fields.
2. Establish metric truth from connector/source code and DB schema: what the metric actually measures, what NULL means, and whether helper aliases or derived context alter interpretation.
3. Compare the current fail expression, score bands, pass mark, and GUI threshold metadata against the cited norm and project rationale.
4. Run the reverse check explicitly: identify sites that currently pass but may satisfy the normative fail condition or sit in a data-quality blind spot that could hide a true fail.
5. Generate scored examples from the merged DB: two sites per band where available, including the actual DB values, matched bands, score, and fail/review verdict.
6. Produce the slim §O output for user sign-off before editing: decision matrix, proposed scoring bands, transition note, scored examples, pending decisions.
7. Only after sign-off, implement narrowly scoped fixes and update tests, docs, lessons learned, and audit artifacts.

## Criterion-Specific Focus

### `EP-01`

- Current hard fail: `ep01_composite_score < 30 or nearest_trauma_center_km > 60`.
- Check whether the composite score and trauma-center distance are both correctly sourced and persisted.
- Reverse check: sites with missing/stale EP sub-scores, stale `ep01_composite_score`, or `nearest_trauma_center_km` NULL/incorrectly permissive.
- Known risk to account for: existing broad tests indicate a pre-existing `run_fix09_ep01_composite_recalc.py` import failure around `composite_from_sub_scores`; do not conflate that with criterion behavior until verified.

### `NH-03`

- Current hard fail: `liquefaction_suscept in ['high', 'very_high'] and has_remedy == false`.
- Check whether `has_remedy` is actually present in scoring context or derived, and whether NULL is intentionally treated as pass/review rather than fail.
- Reverse check: high/very-high susceptibility rows with `has_remedy` missing, `nh03_quality` low, or remediation assumptions only present in text fields.
- Decide whether missing remedy evidence should remain charitable, become a review flag, or hard-fail under the project standard.

### `NH-10`

- Current hard fail: `max_wind_speed_ms > 49`.
- Check whether `max_wind_speed_ms` is maximum gust, sustained wind, return-period wind, or connector proxy; verify unit conversion against the 177 km/h descriptor.
- Reverse check: sites with missing wind values, suspiciously low defaults, or values just below 49 m/s that may require a review band.
- Check whether `threshold_metadata.yaml` has a matching user-tunable threshold; if absent, plan whether to add one.

### `NS-01`

- Current hard fail: `cooling_source_type in ['none', null] and dry_cooling_viable == false`.
- Check whether `cooling_source_type` NULL means no source found, not searched, or not applicable; check whether `dry_cooling_viable` is computed, user-assumed, or defaulted.
- Reverse check: sites with no cooling source but `dry_cooling_viable` NULL, stale, or default-true; sites where water stress/drought sub-scores imply infeasibility but do not trigger E9.
- Decide whether missing dry-cooling evidence should be `review_flag`, no-data, or fail.

### `NS-08`

- Current hard fail: `site_within_strict_protected == true`.
- Check whether the scoring context actually derives `site_within_strict_protected` from `n2k_nearest_distance_km` / `wdpa_nearest_distance_km`, and whether strict category is available or merely approximated by distance ≤ 0.
- Reverse check: sites with zero or near-zero protected-area distance but missing boolean, NULL distances with unresolved connector quality, and natural-land high-percentage sites that might require review rather than fail.
- Decide whether E7 should remain boolean-only or also include explicit distance/category logic in the fail expression.

## Implementation Pattern After Sign-Off

- Update spec YAML and rubric YAML together.
- Add or adjust `band_recipe` only when it is truly single-pivot and norm-anchored.
- Add `derive_expr_from_recipe: true` only when the exclusion expression can be safely derived from the same pivot as the score-5 boundary.
- Add `null_policy: best` only when connector-NULL means confirmed absence within a known search radius; otherwise leave NULL as missing data or add a review flag.
- Update [`/Users/terbolence/projects/atoms_vs_ashes/src/scripts/generate_scoring_examples.py`](/Users/terbolence/projects/atoms_vs_ashes/src/scripts/generate_scoring_examples.py) only if a criterion needs new aliases, cross-table fields, or non-scalar examples.
- Regenerate [`/Users/terbolence/projects/atoms_vs_ashes/report/methodology/exclusionary_floors.md`](/Users/terbolence/projects/atoms_vs_ashes/report/methodology/exclusionary_floors.md).
- Append one concise lesson per real defect to [`/Users/terbolence/projects/atoms_vs_ashes/experts/quality/lessons_learned.md`](/Users/terbolence/projects/atoms_vs_ashes/experts/quality/lessons_learned.md).
- Mirror the accepted plan to `audit/plans/` and `architecture/plans/`, write a conversation audit log, and update man-hours.

## Evidence Required Before Each Edit

- Current compiled bands and fail conditions.
- Current DB histogram and current fail/pass counts.
- Reverse false-negative report: rows that pass today but likely should fail or be reviewed.
- Proposed decision matrix and post-change bands.
- Scored examples from DB before and after edit.
- Targeted tests for the changed criterion.
- Drift guard / propagation tests where pivots or recipes are involved.

## Validation

Run in layers:

- Targeted criterion tests: criterion_spec + scoring tests touching the changed criterion.
- DB dry-run/count query proving false positives and false negatives before/after.
- `generate_scoring_examples.py --criterion <ID>` after each edit.
- Broad pytest sweep excluding only already-confirmed pre-existing failures, with those failures named in the audit footer.
- GUI smoke for threshold widgets whenever threshold metadata or recipe pivots change.

## Execution Order

1. `NS-08` — likely simple boolean/derived-context check; high value for false-negative review.
2. `EP-01` — high operational importance; may expose stale composite data issues.
3. `NH-03` — categorical + remedy semantics require careful NULL/review handling.
4. `NS-01` — composite water/dry-cooling semantics likely need source interpretation.
5. `NH-10` — numeric threshold/pivot candidate; check units and threshold metadata.

## Stop Conditions

- Stop for user sign-off before editing each criterion.
- Stop if the metric source is ambiguous or connector NULL semantics are not provable from code/DB evidence.
- Stop before any live API or remote call. This sweep should be local-only unless the user separately approves a live data refresh.
