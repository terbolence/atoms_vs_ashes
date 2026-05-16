# Assumption register — Atoms-vs-Ashes Phase 1.x

This register lists every load-bearing assumption made by the
pre-screening pipeline (data acquisition → scoring → sensitivity
audit). It is the primary artefact reviewers should consult when they
want to challenge a result, because every numerical answer in the
project ultimately rests on a subset of these statements.

Each assumption carries:

- **ID** — stable handle, cited from code, audit reports, and reviewer
  responses.
- **Domain** — which pipeline stage it constrains.
- **Rationale** — why we adopted it (data limitation, regulatory
  precedent, project scope).
- **Impact-if-wrong** — qualitative description of how the headline
  rankings would shift if the assumption fails.
- **Mitigation / re-test** — how the project guards against the risk
  (data refresh cadence, sensitivity dimension, replacement plan).

This register is **versioned with the rubric**: any rubric change must
update or add an assumption; the audit pack will not pass review with a
silent change.

---

## Scope assumptions

### A-SCOPE-01 — Pre-screening only, not detailed siting
- **Domain:** entire pipeline.
- **Statement:** every result is fit for **pre-screening** (long-list /
  short-list) and not for permit-quality detailed siting. Detailed
  siting requires site-walk surveys, geophysical campaigns, deterministic
  PSHA / PFDHA, and a regulator-led environmental impact assessment.
- **Rationale:** SSR-1 §3 separates site evaluation into successive
  iterations of increasing fidelity; this project covers only the first
  iteration (regional screening).
- **Impact-if-wrong:** users mistake a Band A site for an "approved"
  site. Risk reduced by language in every report.
- **Mitigation:** every per-country MD ends with the screening-only
  caveat; the SSR-1 traceability matrix (`ssr1_traceability.md`) marks
  every Requirement with explicit ``coverage`` (full / partial /
  screening_only / out_of_scope).

### A-SCOPE-02 — Climate-change horizon out of scope
- **Domain:** ranking criteria with climatological inputs (NH-09 river
  flooding, NH-10 extreme winds, NH-11 extreme precipitation, NH-12
  extreme temperatures, RI-01 atmospheric dispersion).
- **Statement:** all hazards use **historical climatology** (last
  available reference period). Projected RCP/SSP scenarios are not
  applied at this stage.
- **Rationale:** SSR-1 acknowledges climate-change scenarios but does
  not yet mandate a single horizon; the screening rubric stays
  comparable across reference periods.
- **Impact-if-wrong:** sites near the boundary of flood/heat hazard
  bands could move ±1 band under a 2070 horizon.
- **Mitigation:** flagged as a Phase 1.7 follow-up; the sensitivity
  suite already exposes the relevant ±25 % threshold perturbation that
  is a first-order proxy for shifted climatology.

### A-SCOPE-03 — Region: 17-country pan-European study area
- **Statement:** the candidate-site population is restricted to AT, BA,
  BG, BY, CZ, HR, HU, LV, MD, ME, MK, PL, RO, RS, SK, TR, UA. Other
  IAEA member states are out of scope.
- **Impact-if-wrong:** none for in-scope ranking; project deliverables
  do not claim regional completeness for any other country.

---

## Data-architecture assumptions

### A-DATA-01 — API-primary / LLM-fallback hierarchy
- **Domain:** every column in `merged_*` tables.
- **Statement:** for any field that a first-party API or open-data
  source provides, the API value is authoritative; LLM-curated values
  are used only when the API has no value. Raw LLM responses
  (un-curated) never enter `merged_*`.
- **Rationale:** API datasets carry version metadata, licence, and a
  reproducible snapshot — they are auditable. LLM outputs are not
  reproducible without the prompt + model snapshot.
- **Impact-if-wrong:** scores depend on model knowledge cut-off; risk
  is bounded by the curation gate before promotion to `merged_*`.
- **Mitigation:** every score row carries a ``provenance_source``
  column; the score-provenance hierarchy is documented in
  [`sensitivity_analysis.md` §9](./sensitivity_analysis.md#9-score-provenance-hierarchy).

### A-DATA-02 — Merged DB is the single source of truth for scoring
- **Statement:** the scoring engine never reads from `atoms_vs_ashes`
  (API-only) or `atoms_vs_ashes_llm` (LLM-only) directly. Only
  `atoms_vs_ashes_merged`. The merge step (``scripts.build_merged_db`` +
  ``scripts.promote_llm_to_merged``) is the only place where the API /
  LLM hierarchy is enforced.
- **Impact-if-wrong:** silent score divergence between profiles.
- **Mitigation:** every score row stores ``run_id``; the rescore CLI
  refuses to write into the wrong DB.

### A-DATA-03 — Site geometry is a single representative point
- **Statement:** each site is represented by a single (lat, lon)
  coordinate; the rubric's distance-based criteria measure to that
  point.
- **Rationale:** at pre-screening fidelity, polygon-aware buffers add
  computation cost without changing band assignments.
- **Impact-if-wrong:** for very-large host sites the EPZ buffer might
  intersect more constraints than the point measurement suggests.
- **Mitigation:** detailed siting will recompute against the actual
  cooling-tower / containment footprint.

---

## Rubric / scoring assumptions

### A-RUBRIC-01 — 0–10 ranking scale with ±1 uncertainty for low-quality rows
- **Statement:** every criterion produces a continuous 0–10 score; for
  rows whose source is flagged ``quality = low``, the Monte Carlo
  uncertainty band is ``score ± 1`` (uniform). High-quality rows have
  zero-width uncertainty.
- **Rationale:** matches the EPRI Siting Guide convention; the ±1 band
  is conservative for screening-grade data.
- **Impact-if-wrong:** MC stability is over-estimated for high-quality
  rows; this is the conservative direction for a screening study.
- **Mitigation:** declared quality is itself a stored column —
  reviewers can re-run MC with a different dispersion model.

### A-RUBRIC-02 — Hard safety floor at 5.0 for exclusionary criteria
- **Domain:** NH-02, NH-03, NH-04, NH-05, NH-07, NH-10, EP-01, NS-01,
  NS-08.
- **Statement:** any site whose ranking score falls **strictly below**
  5.0 on an exclusionary criterion is excluded from composite ranking
  by a synthetic ``E*:floor`` verdict.
- **Rationale:** stops a site from "redeeming" a near-fail metric by
  scoring well elsewhere — required by the IAEA expert review.
- **Impact-if-wrong:** prior to the floor, ~7 % more pairs survived to
  ranking; the floor tightens but does not contradict the underlying
  E-code condition.
- **Mitigation:** documented in [`exclusionary_floors.md`](./exclusionary_floors.md);
  unit-tested in `tests/scoring/test_safety_floor_pipeline.py`.

### A-RUBRIC-03 — Failed sites keep their 0–10 scores for transparency
- **Statement:** sites that fail a hard E-code or safety floor still
  get all per-criterion ranking scores written to ``ranking_scores``,
  but their composite is ``NULL`` and they never enter banding or
  national shortlists.
- **Rationale:** auditability — reviewers can see how badly a failed
  site fails and on which axis.
- **Impact-if-wrong:** none for ranking; reduces scoring transparency
  if reverted.

### A-RUBRIC-04 — Per-criterion weights are MCDA "swing weights" once normalised
- **Statement:** the published `weight_factor` × `normalised_weight_pct`
  values are interpreted as *importance to the decision*; the
  swing-weight audit (`swing_weight_audit.md`) re-normalises by
  observed score range so reviewers can verify the declared importance
  matches the discriminating power in the data.
- **Impact-if-wrong:** the headline ranking is robust to weight
  perturbation (Phase B.1) — confirmed by Jaccard@10 % ≥ 0.85 on every
  ±20 % profile.

---

## Sensitivity-suite assumptions

### A-SENS-01 — Per-category ±20 % weight envelope is the regulatory band
- **Source:** project requirements `06_scoring_matrix.md` §8.4; EPRI
  Siting Guide 3002023910.
- **Impact-if-wrong:** wider envelopes would expose more borderline
  pairs as unstable; the suite is parameterised so the band can be
  widened cheaply.

### A-SENS-02 — N = 10 000 Monte Carlo iterations is sufficient
- **Statement:** convergence of mean / p05 / p95 is verified at N =
  10 000 against N = 1 000 and N = 3 000; differences are below 0.5 %
  in all reported metrics.
- **Mitigation:** the driver still ships the smaller presets so
  reviewers can re-test convergence themselves.

### A-SENS-03 — RNG seed = 42 (and pair-specific derivation)
- **Statement:** every Monte Carlo draw is seeded from
  ``f"{site_id}:{smr_key}:42"`` so the entire suite is bit-reproducible.
- **Impact-if-wrong:** reproduction failures would be detected at
  rerun; production seed is fixed in code.

### A-SENS-04 — Country-balance ``max_share`` flag at 40 %
- **Statement:** if any single country's share of the regional top-20
  exceeds 40 %, the suite emits a country-balance flag.
- **Rationale:** soft signal of data-coverage bias rather than a hard
  rule; reviewers decide whether to redistribute scoring effort.

### A-SENS-05 — High criterion-pair correlation flagged at |ρ| ≥ 0.70
- **Statement:** any pair with Pearson **or** Spearman magnitude
  ≥ 0.70 is flagged as potentially double-counting an axis.
- **Rationale:** rule of thumb from MCDA literature (Tervonen et al.
  2007); reviewers decide whether the redundancy is intentional.
- **Mitigation:** [`criterion_correlation.md`](./criterion_correlation.md)
  documents the latest flagged pairs.

---

## Reporting / scope-management assumptions

### A-REPORT-01 — Country shortlist size: K = 10 minimum, 30 % otherwise
- **Statement:** every country MD ranks at least the top 10 sites
  (fewer only if the country has fewer scored sites): K = n if n < 10
  else K = min(n, max(10, ⌈0.30·n⌉)).
- **Rationale:** small countries (e.g. ME, MK) cannot offer a
  statistically meaningful 30 % slice; the floor of 10 forces a
  comparable narrative everywhere.

### A-REPORT-02 — Stamp-aligned artefacts
- **Statement:** every audit + report artefact within a single suite
  run shares the same ``YYYYMMDD`` stamp; orphan stamps trigger a
  follow-up rerun rather than partial regeneration.
- **Rationale:** prevents reviewers reading a regional MD from an
  earlier stamp than the country MDs that purport to refine it.

### A-REPORT-03 — Out-of-scope items are recorded, not hidden
- **Statement:** any IAEA SSR-1 Requirement that the project does not
  cover (e.g. operational monitoring, QA system) is listed in the
  traceability matrix with ``coverage: out_of_scope`` and a rationale,
  rather than being silently omitted.

### A-REPORT-04 — Pre-`034` runs are CSV-only by design
- **Domain:** persisted analytics tables introduced by Alembic
  revision `034_persist_analytics` (`runs`, `dataset_snapshot`,
  `composite_score_components`, `site_bands`,
  `country_rankings_summary`, `country_site_rankings`,
  `oat_importance`, `weight_profile_stability`,
  `threshold_sensitivity`, `failure_outcomes`, `failure_aggregates`,
  `swing_weights`, `criterion_correlations`,
  `country_balance_check`).
- **Statement:** the headline reference runs `20260423` and
  `20260425` were generated **before** revision 034 was authored; for
  those stamps the CSV trees under `audit/post_processing/06_scoring/`
  and `report/output/sensitivity/<stamp>/` remain authoritative. The
  new tables are populated from the **next** pipeline invocation
  onward (forward-only); no historical backfill is performed.
- **Rationale:** backfilling synthetic `run_id`s would either invent
  provenance (defeating the purpose of `runs` / `dataset_snapshot`)
  or require re-executing the pipeline with the original rubric and
  data snapshot, which is out of scope for this revision.
- **Impact-if-wrong:** none for ranking; the only consequence is
  that `inspect_run --run-id <pre_034>` returns empty result sets
  for the analytics queries. The CSVs cover the same axes.
- **Mitigation:** the `inspect_run` CLI documents the forward-only
  behaviour; `composite_rankings.run_id` keeps a non-validated FK to
  `runs.run_id` so historical rows survive without breaking the
  constraint.

---

## Change log

| Stamp     | Change                                                                  |
| --------- | ----------------------------------------------------------------------- |
| 2026-04-25 | Initial assumption register seeded after IAEA expert-review fixes.     |
| 2026-04-25 | Added A-REPORT-04 (pre-034 runs are CSV-only by design).               |
