<!-- man_hours: 2.4 -->
---
sub_plan: SP-B
title: EPRI weight basis swap (named profile)
specialist_prompts:
  primary: prompts/coal_to_nuclear_suitable_sites_scoring_audit.md
  supporting:
    - prompts/sitingExpert.md
    - prompts/expert_iaea_epri_criterion_matrix_author.md
mandatory_reads_first:
  - prompts/lessons_learned.md
  - report/output/feedback/plans/feedback_lessons_learnt.md
  - config/scoring_rubrics/
  - src/atoms_vs_ashes/scoring/rubric.py
  - report/sites_evaluation/02_master_weights.md
honors_feedback_lessons: [FB-LL-09]
gates: [feedback_lessons_learnt.md sign_off, "EPRI source document name from user"]
comment_ids: ["1929454976", "72", "77", "117"]
blocks: ["SP-D"]
---

# SP-B — EPRI weight basis swap

## Status (2026-05-09)

**Mechanism landed.** All four scaffold steps below are now in code: (1) `Criterion.weight_factors` and `Criterion.weight_basis_source` Pydantic fields exist on the rubric model; (2) `weight_normalisation(bundle, profile=..., basis=...)` and `weight_basis_resolution(bundle, basis=...)` both shipped in [`rubric.py`](../../../../src/atoms_vs_ashes/scoring/rubric.py) (~L288-339); (3) the CLI `atoms-vs-ashes score run` now accepts `--weight-basis epri | s_and_l | baseline`, threaded through `execute_score_run` -> `_assert_basis_populated` -> `run_scoring` -> `ScoringEngine`; (4) `composite_rankings.weight_profile` already segregates runs. The basis guard `_assert_basis_populated` raises `NotImplementedError("weight_basis 'epri' not populated on any criterion in <rubric_dir>; ...")` so accidental use is loud (FB-LL-09 acceptance). The swap protocol is documented in [`report/sites_evaluation/02_master_weights.md`](../../../sites_evaluation/02_master_weights.md) §"SP-B EPRI weight swap protocol". Sensitivity-pipeline `--profile epri` mode is the only remaining sub-step; the suite already accepts `--weight-profile-base` and the basis guard can be reused once the source doc lands. **Numerical EPRI / S&L values remain pending the canonical source document the user will hand over.**

The apex change Bogdan named in #1929454976. SP-D rubric edits depend on the named-profile mechanism being in place.

## Mechanism (engineering scope, no value judgements)

1. Extend each criterion in [`config/scoring_rubrics/*.yaml`](../../../../config/scoring_rubrics/) with optional `weight_factors:` mapping `{baseline: <current weight>, epri: <epri weight>, s_and_l: <if known>}`. The existing `weight_factor:` field becomes the `baseline` value for backward compatibility.
2. Extend [`src/atoms_vs_ashes/scoring/rubric.py`](../../../../src/atoms_vs_ashes/scoring/rubric.py) `weight_normalisation(profile=...)` to accept basis names (`epri`, `s_and_l`) in addition to the perturbation profiles (`baseline`, `w_plus_20`, `w_minus_20`). When called with `profile="epri"`, it reads `weight_factors.epri` and falls back to `weight_factors.baseline` with a logged warning.
3. Each criterion gets a new `weight_basis_source:` field naming the document (paragraph + table) that justified the weight under each basis.
4. The sensitivity audit pipeline ([`src/atoms_vs_ashes/scoring/_swing_weights.py`](../../../../src/atoms_vs_ashes/scoring/_swing_weights.py)) gains a `--profile epri` mode and produces a side-by-side delta report.

## Values (out of scope until user provides EPRI source)

The actual EPRI numerical weights cannot be sourced without the canonical EPRI document the project will cite. The triage YAML and FB-LL-09 record this as a hard input from the user. SP-B execution stops at the mechanism + scaffolding step until the source is named.

Recommended canonical sources to evaluate (user to choose):
- EPRI Report 3002023910 (Site Selection / Owner-Operator Requirements for SMR), or
- EPRI Site Selection Guide (latest revision), or
- A specific EPRI workshop deliverable cited in [`report/sites_evaluation/02_master_weights.md`](../../../../report/sites_evaluation/02_master_weights.md).

## Acceptance

- Every criterion in `config/scoring_rubrics/*.yaml` carries `weight_factors.baseline` (= current `weight_factor`) and a `weight_basis_source.baseline` reference.
- `weight_normalisation(profile="epri")` returns a normalised distribution for any subset of criteria that have `weight_factors.epri` populated (others fall back to baseline with a warning).
- The renderer prints `weight 0.0308 (basis: <source>)` per criterion bullet (FB-LL-09 acceptance).
- A migration script preserves run reproducibility: `runs.weight_profile` column or equivalent records which basis was used.

## Cross-links

- T1 in master plan.
- FB-LL-09 (weight provenance must be visible per criterion).
- Promoted-LL candidate "weight-basis migration must use named profiles" (close-out todo).

## Out of scope for SP-B

- Changing baseline weight values in place — never overwrite, always add a new profile.
- Re-banding any criterion — that is SP-D's job, gated on Phase 0.6 sign-off.
