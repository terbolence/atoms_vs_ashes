<!-- man_hours: 1.0 -->
# Status: Completed

Execution notes, 2026-05-16:

- Created 47 ranking criterion state documents under `criteria/ranking/`.
- Applied specialist-prompt recommendations to formerly decision-needed criteria.
- Implemented low-risk NH ranking YAML/test changes for NH-03, NH-08, NH-09, NH-10, and the NH-10 parity contract.
- No live API, enrichment, web, or remote calls were made.

---
name: ranking criteria sweep
overview: "Audit every active ranking-phase criterion, decide whether any scoring/band/data issues need user decisions, and document the accepted final state under criteria/ranking/. The workflow mirrors the existing exclusionary sweep plan while using ranking-specific evidence: score-curve boundary tables, DB examples, monotonicity checks, band histograms, and composite-impact dry runs."
todos:
  - id: inventory
    content: Confirm full active ranking inventory from scoring specs/rubrics and identify dual-phase criteria.
    status: completed
  - id: scaffold
    content: Create criteria/ranking/ and a reusable ranking documentation template.
    status: completed
  - id: dual-phase
    content: Audit and document dual ranking plus exclusionary criteria first, cross-referencing existing exclusionary docs.
    status: completed
  - id: family-sweeps
    content: Run family-by-family ranking audits for NH/BF, RI, EP, HI, and NS criteria.
    status: completed
  - id: decisions
    content: For any identified issue, present the decision artifact and obtain user decisions before edits.
    status: completed
  - id: docs
    content: Document accepted current state or accepted final state for every ranking criterion under criteria/ranking/.
    status: completed
  - id: validation
    content: Run targeted examples, dry-runs, tests, audit logs, and man-hours updates after accepted changes.
    status: completed
isProject: false
---

# Ranking Criteria Sweep

## Scope

Audit every active criterion whose spec includes `ranking`, across the scoring specs and matching rubrics:

- [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ep_emergency_planning.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ep_emergency_planning.yaml) and matching rubric.
- [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/hi_human_induced.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/hi_human_induced.yaml) and matching rubric.
- [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ri_radiological.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ri_radiological.yaml) and matching rubric.
- [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/nh_natural_hazards.yaml) and matching rubric.
- [`/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml`](/Users/terbolence/projects/atoms_vs_ashes/config/scoring_specs/ns_non_safety.yaml) and matching rubric.

Active ranking inventory: `EP-01` through `EP-05`; `HI-01` through `HI-08`; `RI-01` through `RI-06`; `BF-02` and `NH-01` through `NH-14`; `NS-01` through `NS-13`. This is 47 criteria total. Include dual-phase criteria such as `EP-01`, `NH-02`, `NH-03`, `NH-04`, `NH-07`, and `NS-08` in the ranking sweep, but cross-reference any existing exclusionary docs instead of re-litigating closed exclusionary decisions unless ranking behavior is affected.

Create the documentation destination as [`/Users/terbolence/projects/atoms_vs_ashes/criteria/ranking/`](/Users/terbolence/projects/atoms_vs_ashes/criteria/ranking/) during execution. Use one Markdown file per criterion, named consistently as `ID - Title.md` unless the repository settles on a different criteria naming convention before implementation.

## Workflow Per Criterion

Follow the matrix-first ritual in [`/Users/terbolence/projects/atoms_vs_ashes/prompts/ScoringCriteriaSystemPrompt.md`](/Users/terbolence/projects/atoms_vs_ashes/prompts/ScoringCriteriaSystemPrompt.md), especially §C3, §D, §E4, §E7, §J, and §K:

1. Establish current behavior from spec YAML, rubric YAML, compiled `Criterion`, threshold metadata, matrix row, and tests.
2. Dispatch artifacts from the criterion phases. Every ranking criterion gets a score-curve boundary table; criteria with bands also get scored examples from the merged DB. Dual-phase criteria also include the relevant exclusionary, avoidance, basic-filter, or soft-flag artifact.
3. Establish metric truth from connector/source code, merge-context derivations, DB fields, units, and NULL semantics.
4. Compare current score bands, band recipes, pivots, weights, `participates_in_composite`, and GUI threshold metadata against the cited norm and project rationale.
5. Run ranking reverse checks: empty or saturated bands, suspicious default values, NULL-heavy slices, quality-label leakage into hard metrics, unit mismatches, non-monotonic curves, cliff transitions, and unexpected top-site movement.
6. Generate scored examples from the merged DB: two sites per band where available, including actual DB values, matched band, score, and verdict/flag context.
7. Produce a slim pre-edit package for user sign-off when changes are proposed: decision matrix, proposed score curve, transition note, DB examples, dry-run impact, and pending decisions.
8. If no problems are identified, recommend documenting the current accepted state directly under `criteria/ranking/` with evidence, examples, and residual caveats.
9. If issues are identified, stop and ask the user for the needed scoring/data/documentation decisions before editing YAML or finalizing the `criteria/ranking/` documentation.
10. After user decisions, implement narrowly scoped fixes, update tests and docs, then document the accepted final state in `criteria/ranking/`.

## Documentation Template

Each `criteria/ranking/<ID> - <Title>.md` file should capture the final accepted state, not just the investigation notes:

- Header with criterion ID, title, phase list, primary metric, source spec/rubric, and whether it participates in the composite.
- Current or final decision matrix: `was` / `now` if changed, or `current state accepted` if no change was needed.
- Score-curve boundary table with metric intervals, score bands, descriptors, pivot/recipe metadata, and DB band counts.
- Metric truth and data-quality note: source table/fields, units, derivations, NULL semantics, and any quality fields used for interpretation.
- Scored examples from the merged DB, including empty-band statements where applicable.
- Composite-impact note for changed criteria: affected site count, top movers, band shifts, and whether the effect matches the user-approved decision.
- Open follow-ups with `IMPROVEMENTS.md` IDs only for deferred connector/schema/report issues that are real but not blocking.
- Artifact footer listing landed files, tests run, audit log, and man-hours update once implementation is complete.

## Criterion-Specific Focus

- `EP` criteria: emergency-planning composites and route/special-population/geography metrics; check stale composite sub-scores, score saturation, and whether any dual `EP-01` exclusion mechanics distort ranking documentation.
- `HI` criteria: industrial, transport, military, EMI, fire, toxic-release, aircraft, and nuclear-neighbor hazards; check distance/source units, hazard-category thresholds, sparse connector data, and whether avoidance/review flags are correctly separated from score curves.
- `RI` criteria: atmospheric/water/groundwater dispersion and population-burden ranking; check that population-radius metrics, dispersion proxies, and projections have monotonic score curves and do not duplicate exclusionary or emergency-planning logic.
- `BF/NH` criteria: footprint, seismic, geotechnical, flooding, wind/weather, wildfire, and combined hazards; check dual-phase criteria for correct composite participation, verify threshold units, and detect hidden cliff transitions around pivots.
- `NS` criteria: cooling, grid, transport, land, infrastructure, ecological, socioeconomic, workforce, coal-to-nuclear, regulatory, and construction logistics; check proxy metrics, data-quality treatment, country comparability, and whether soft flags have no automatic score effect.

## Implementation Pattern After Sign-Off

- Create [`/Users/terbolence/projects/atoms_vs_ashes/criteria/ranking/`](/Users/terbolence/projects/atoms_vs_ashes/criteria/ranking/) if it does not exist.
- Update spec YAML and rubric YAML together only after a signed-off decision artifact.
- Add or adjust `band_recipe` only when it is norm-anchored, monotonic, and easier to validate than hand-written bands.
- Keep `threshold_metadata.yaml` in sync when score pivots or GUI-tunable thresholds change.
- Update [`/Users/terbolence/projects/atoms_vs_ashes/src/scripts/generate_scoring_examples.py`](/Users/terbolence/projects/atoms_vs_ashes/src/scripts/generate_scoring_examples.py) only when a criterion needs aliases, derived fields, non-scalar examples, or missing auxiliary columns.
- Do not regenerate [`/Users/terbolence/projects/atoms_vs_ashes/report/methodology/exclusionary_floors.md`](/Users/terbolence/projects/atoms_vs_ashes/report/methodology/exclusionary_floors.md) for ranking-only changes unless an `exclude` action is touched.
- Append lessons to [`/Users/terbolence/projects/atoms_vs_ashes/prompts/lessons_learned.md`](/Users/terbolence/projects/atoms_vs_ashes/prompts/lessons_learned.md) only for real defects or reusable process learnings.
- Write conversation audit logs under [`/Users/terbolence/projects/atoms_vs_ashes/audit/conversations/`](/Users/terbolence/projects/atoms_vs_ashes/audit/conversations/) and update man-hours when execution starts.

## Evidence Required Before Each Edit

- Current compiled bands, score direction, phase list, `participates_in_composite`, fail/flag conditions, and weight.
- DB band histogram and metric distribution for the active merged DB.
- Score-curve boundary samples at pivots, min/max, and near each band edge.
- Monotonicity or composite-consistency proof where applicable.
- Data blind-spot report covering NULL values, quality fields, connector coverage, and suspicious defaults.
- Proposed decision matrix and post-change score curve.
- Scored examples before and after edit for changed criteria.
- Composite-impact dry-run with site counts, band shifts, and top movers.
- Targeted tests for the changed criterion and drift/parity tests for any YAML/recipe mechanics.

## Validation

Run validation in layers after any accepted changes:

- Criterion-specific pytest coverage for bands, monotonicity, phase participation, and flags.
- Spec/rubric compiler parity checks.
- `generate_scoring_examples.py --criterion <ID>` for each documented criterion or each changed batch.
- DB dry-run for ranking impact, including per-band counts and top movers.
- GUI smoke only when threshold metadata, preview text, or threshold editor behavior changes.
- Broad scoring test sweep when shared scoring behavior, recipes, or compiler logic changes.

## Execution Order

1. Inventory and scaffolding: confirm the 47-criterion ranking inventory, create `criteria/ranking/`, and define the doc template.
2. Dual-phase safety-sensitive criteria: `EP-01`, `NH-02`, `NH-03`, `NH-04`, `NH-07`, `NS-08`.
3. Natural-hazard and basic-filter ranking: `BF-02`, `NH-01`, `NH-05`, `NH-06`, `NH-08`, `NH-09`, `NH-10`, `NH-11`, `NH-12`, `NH-13`, `NH-14`.
4. Radiological ranking: `RI-01` through `RI-06`.
5. Emergency-planning ranking-only criteria: `EP-02` through `EP-05`.
6. Human-induced ranking: `HI-01` through `HI-08`.
7. Non-safety ranking: `NS-01` through `NS-13`.
8. Roll up cross-criterion issues, update deferred improvements, audit logs, and man-hours.

## Stop Conditions

- Stop for user sign-off before editing any criterion where a scoring, band, metric, documentation, or data-semantics change is proposed.
- Stop and ask for decisions when evidence supports more than one defensible treatment of a metric, NULL value, quality label, or score boundary.
- Stop if ranking impact exceeds the user-approved envelope, especially if more than 5% of sites shift bands, top movers shift by two or more bands, or composite ranking changes materially.
- Stop if metric source, connector coverage, or NULL semantics cannot be proven from local code/DB evidence.
- Stop before any live API, enrichment refresh, remote call, or quota-consuming operation unless separately approved by the user for that exact action.
