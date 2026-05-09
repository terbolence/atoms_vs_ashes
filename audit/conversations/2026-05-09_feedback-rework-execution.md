<!-- man_hours: 0.5 -->
# Feedback rework execution -- 13-stage gated plan, offline wave landed

**Date:** 2026-05-09
**Session ID:** feedback-rework-execution-ff6b91ad

## Objective

Run the gated 13-stage execution plan
(`/Users/terbolence/.cursor/plans/feedback_rework_execution_ff6b91ad.plan.md`)
that wraps the eight feedback sub-plans (SP-A through SP-H) in a strictly
sequential, user-permission-gated pipeline. Land everything that does
not require live-API or live-DB work; document gated stages as cancelled
with the reason and the resumption protocol.

## Stages executed (offline)

- **Stage 0** -- Sign-offs: flipped `sign_off: yes` on
  `feedback_lessons_learnt.md` plus all 18 SP-D band proposals
  (`SP-D_band_proposals/{EP-01, HI-01, HI-02, HI-04, HI-05, HI-06, HI-08,
  NH-03, NH-04, NH-05, NH-07, NH-08, NH-09, NH-11, NH-12, NH-13, NH-14,
  RI-04}.md`); updated `00_master.plan.md` "Current status" section.
- **Stage 1 -- SP-A quick wins**: 7 site profiles patched to drop the
  `924 MWe` / `12-module` / `VOYGR-12` narrative (RO Brăila / Rovinari /
  Romag Termo NS-02 rows + 7 family-interpretation prose blocks);
  Romania row in Table 4.1.1 reconciled with country-level full-pass
  count (#568); ack #8 / #12 marked for next extractor pass; #574
  routed to SP-H backlog. `rg "924 MW|VOYGR-12|12-module"
  report/output/chapters/*.md` -> 0 matches.
- **Stage 2 -- SP-H backlog**: status block added; backlog already
  carried #72, four engineering follow-ups (cross-chapter lint, triage
  `action` enum, anchor heuristic, optional Pareto-per-country),
  #15 / #574 reviewer clarifications.
- **Stage 3 -- SP-B EPRI scaffold**: `--weight-basis` flag wired into
  `score run` -> `execute_score_run` -> `_assert_basis_populated` ->
  `weight_normalisation(basis=...)`; `epri` / `s_and_l` raise
  `NotImplementedError` until rubric YAML carries `weight_factors[basis]`;
  swap protocol documented in
  `report/sites_evaluation/02_master_weights.md` SP-B section.
  Numerical EPRI values still pending the user-supplied source document.
- **Stage 4 -- SP-C methodology + RI-04 dual mode**: Chapter 3 §3.3
  Stage 1 / Stage 2 boundary paragraph + §3.5 RI-04 dual-mode
  paragraph already authored in prior wave; this stage added the
  structured `notes:` field on the RI-04 rubric YAML
  (`config/scoring_rubrics/ri_radiological.yaml`) mirrored to specs.
  To preserve compiler parity, `notes: str | None` was promoted to a
  first-class field on `Criterion` (`scoring/rubric.py`) and on
  `CriterionTemplate` (`criterion_spec/schema.py`); compiler now
  propagates it.
- **Stage 5 -- SP-E engine + renderer semantics**: renderer
  `_verdicts_and_scores_by_family` now propagates `quality_flag` from
  the `ranking_scores` row and parses the matched-band descriptor out
  of `RankingScore.justification` JSON; `_family_section` produces three
  distinct strings (pass-mark band / unscored / favorable). Two new
  acceptance tests cover the favorable + pass-mark branches.
  Engine semantics for case (b) unchanged because the existing
  `notes=["unscored"]` -> `quality_flag = "unscored"` -> composite-skip
  flow already met FB-LL-01 / FB-LL-02 acceptance.
- **Stage 6 -- SP-D rubric closure + 18-anchor regression**: prior
  session's offline wave (NH-03, NH-05, HI-02, HI-04/05/08, RI-04,
  others) confirmed; per-criterion `## Verification (2026-05-09)` block
  appended to all 18 signed proposals citing the green test suite + the
  Stage 8b on-DB regression as the canonical follow-up.
- **Stage 7a -- SP-F connector code (partial)**: `OurAirports` dataclasses
  (`NearbyAirport`, `AirportProximityResult`) extended with explicit
  `airport_class`, `runway_length_m`, `nearest_airport_class`,
  `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`
  fields; `compute_proximity_result` populates the class + scheduled
  service direct from the matched record. Runway-length parsing,
  OSM military classifier, and the Alembic migration deferred -- they
  pair cleanly with the live re-enrichment fetch in Stage 7b.
- **Stage 8a -- Cross-chapter numeric lint**: new
  `src/scripts/cross_chapter_numeric_lint.py` with three canonical
  facts (VOYGR-6 capacity, Romania full-pass reconciliation, study
  region count); `tests/scripts/test_cross_chapter_numeric_lint.py`
  marked `slow`; lint runs clean against the current report.

## Stages cancelled (consent / live-side gates)

- **Stage 7b -- SP-F H7 re-enrichment** (363 sites x 2 connectors,
  per-batch dry-run / smoke-3 / batch-20 / country / full): cancelled
  because each batch step requires its own runAPIs.md Sec.C card per
  workspace rule `live-api-safety.mdc`. No live API hits issued.
- **Stage 8b -- SP-G scoring rerun + bundle exports**: cancelled
  because the canonical rerun should run after Stage 7b's freshly
  enriched data lands; running on the pre-rework DB would write a
  baseline that does not reflect the SP-D / SP-F changes.
- **Stage 8c -- SP-G profile regeneration + Pareto**: cancelled --
  downstream of 8b; the Austrian Pareto already carries the
  "instance of a per-country diagnostic, not a region-wide aggregate"
  caption (line 51 of `AT_country_prototype.md`), so the FB-LL-07
  default outcome is already in place.

## Files changed

- `report/output/feedback/plans/feedback_lessons_learnt.md` --
  `sign_off: yes`.
- `report/output/feedback/plans/SP-D_band_proposals/{EP-01, HI-01,
  HI-02, HI-04, HI-05, HI-06, HI-08, NH-03, NH-04, NH-05, NH-07,
  NH-08, NH-09, NH-11, NH-12, NH-13, NH-14, RI-04}.md` --
  `sign_off: yes` + `## Verification (2026-05-09)` block.
- `report/output/feedback/plans/00_master.plan.md` -- "Current status"
  + dependency-graph nodes updated.
- `report/output/feedback/plans/{SP-A_quick_wins, SP-B_epri_weights,
  SP-C_methodology, SP-D_rubric_bands, SP-E_engine_semantics,
  SP-F_connector_refinements, SP-H_backlog}.plan.md` -- per-plan
  status section added.
- `report/output/chapters/05_country_and_site_profiles/sites/{RO_braila,
  RO_rovinari, RO_romag_termo, BA_banovici, BA_gacko, AT_voitsberg,
  AT_timelkam, AT_riedersbach}_power_station.md` -- VOYGR-6 narrative
  cleanup.
- `report/output/chapters/04_results_and_findings.md` -- Romania row
  reconciliation.
- `report/sites_evaluation/02_master_weights.md` -- SP-B swap protocol.
- `config/scoring_rubrics/ri_radiological.yaml` +
  `config/scoring_specs/ri_radiological.yaml` -- RI-04 `notes:` block.
- `src/atoms_vs_ashes/scoring/rubric.py` -- `Criterion.notes`.
- `src/atoms_vs_ashes/criterion_spec/schema.py` --
  `CriterionTemplate.notes`.
- `src/atoms_vs_ashes/criterion_spec/compiler.py` -- `notes`
  propagation.
- `src/atoms_vs_ashes/scoring/_cli.py` -- `--weight-basis` flag.
- `src/atoms_vs_ashes/scoring/_cli_run.py` -- `_assert_basis_populated`
  guard + bundle-load path.
- `src/scripts/_site_profile_markdown.py` -- `quality_flag` +
  `band_descriptor` propagation; three-way render branch.
- `src/atoms_vs_ashes/connectors/ourairports/{models, parsers}.py` --
  scaffold fields for SP-F.
- `src/scripts/cross_chapter_numeric_lint.py` -- new (Stage 8a).
- `tests/scripts/test_cross_chapter_numeric_lint.py` -- new slow test.
- `tests/scripts/test_site_profile_unscored_rendering.py` -- two new
  cases for favorable + pass-mark branches.
- `pyproject.toml` -- `slow` marker added.
- `prompts/lessons_learned.md` -- LL-030 + LL-031 appended.

## Outcome

**Completed offline wave.** `pytest tests/scoring/
tests/scripts/test_site_profile_unscored_rendering.py` -> **94/94**;
`pytest tests/test_connectors_ourairports.py
tests/test_smoke_ourairports.py` -> **49/49**;
`pytest tests/scripts/test_cross_chapter_numeric_lint.py -m slow` ->
**1/1**. `python src/scripts/cross_chapter_numeric_lint.py` -> 0
findings. The 18 SP-D band proposals are signed and verified offline,
the EPRI mechanism is loud-fail, the renderer three-way distinction is
plumbed, and the cross-chapter lint is wired.

**Deferred (consent-gated).** Stage 7b live re-enrichment requires the
per-batch runAPIs Sec.C card to be presented for each of: dry-run,
smoke (3 sites), batch 20, country (~24), full (363). Stages 8b
(scoring rerun + bundle exports) and 8c (profile regeneration + Pareto)
follow downstream once 7b lands. The plan + the SP-G plan document the
exact resumption protocol; the user reopens the gate by replying with
explicit consent + the chosen batch size.
