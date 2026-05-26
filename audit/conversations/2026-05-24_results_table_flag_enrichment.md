# Results-Table Flag-Name Enrichment (v1.03)

**Date:** 2026-05-24
**Session ID:** results_table_flag_enrichment_70fff8fa

## Objective

Raise the quality of the v1.03 `atoms_vs_ashes_results_table` deliverable
so that every avoidance and exclusionary flag appears with its full
criterion name and code in **both** the country status map callouts and
the table's `Avoidance / failure note` column. Eliminate the 18
`Avoidance flag recorded; criterion codes unavailable.` fallback rows
present in the previous v1.03 build (whole Romanian tail + BA Gacko +
RS Morava + RO Mintia-Deva). User direction: the format is the full
criterion name with code in parentheses, e.g.
`Grid Connection (NS-02), Distance to Population Centres (RI-05)`.

Driving plan: `/Users/terbolence/.cursor/plans/results_table_flag_enrichment_70fff8fa.plan.md`.

## Key Decisions

- Source of per-site avoidance / exclusionary criteria for **every**
  ledger row is the country bundle, not the site bundle. The country
  bundle producer already has the right DB query shape (mirrors
  `_avoidance_pareto` and `_exclusionary_failure_pareto`); the new
  `_per_site_verdicts()` helper just regroups by `site_id`. This solves
  the previously fallback rows (no site bundle on disk for RO tail,
  BA Gacko, RS Morava, RO Mintia-Deva).
- Resolution precedence in `flag_note`: site bundle → country bundle
  `per_site_verdicts` → `failure_outcomes.csv` (legacy fallback,
  exclusionary only). Always rendered as `Name (CODE)` from the
  country-bundle `criteria_lookup`.
- Country status map PNG callouts cap at 3 flags for legibility; HTML
  popups carry the full list. RO map verified visually after rebuild.
- The Brasov assertion in `test_results_table_renders_actual_flag_codes`
  was tightened from the legacy CSV expectation
  (`EP-01, NH-05`) to the canonical v1.03 scoring run answer
  (`EP-01` only). NH-05 was a floor criterion in the older
  `20260425b` extract that no longer triggers under the corrected
  rubric in `score-c2a90942`.
- All work uses frozen run identifiers (`score-c2a90942`,
  `nat-sens-b1a62885`, sensitivity stamp `20260523`); no new scoring
  or sensitivity run executed. No live API calls.

## Files Changed

- `src/atoms_vs_ashes/reporting/country_bundle.py` — new
  `_per_site_verdicts()` helper; `build_country_bundle` emits new
  `per_site_verdicts` top-level key (sorted, deterministic).
- `scripts/results_table_flags.py` — added `_country_bundle()`,
  `_country_site_id()`, `_criteria_lookup_for()`, `_format_named()`,
  `_per_site_codes_from_country_bundle()`, `named_flags()`; rewrote
  `flag_note()` with new precedence and `Name (CODE)` rendering.
- `src/scripts/_country_profile_outputs.py` — `_ledger_row()` now
  accepts `per_site_verdicts` + `criteria_lookup` and emits
  `avoidance_named` / `hard_fail_named` for each row; both call sites
  (`write_country` and `write_figures_only`) pass the country bundle's
  blocks through.
- `src/scripts/_country_profile_map.py` — `_callout_text()` appends a
  capped `flags: …` line for `avoidance-flag` and `hard-fail` rows;
  `_popup_html()` adds `Avoidance flags:` / `Exclusionary flags:`
  lines with the full list. New `CALLOUT_FLAG_LIMIT = 3` constant.
- `tests/test_country_bundle_per_site_verdicts.py` — 4 new pure-logic
  unit tests (stub session, no DB) for `_per_site_verdicts` grouping,
  dedup, empty-result, and byte-stable ordering.
- `tests/scripts/test_country_profile_map_callouts.py` — 6 new unit
  tests for `_callout_text` flag inclusion, 3-flag cap, full-pass
  no-flag-line, missing-keys safety, and `_popup_html` full-list.
- `tests/scripts/test_v1_2_build_deliverables.py` —
  `test_results_table_renders_actual_flag_codes` rewritten against
  v1.03 format; new `test_results_table_has_no_unresolved_fallback_rows`
  iterates every published-country ledger row and asserts no
  `criterion codes unavailable` text remains.
- `audit/feature_completion_matrices/2026-05-24_results_table_flag_enrichment.md` —
  Feature Completion Matrix opened before implementation; closed in
  this session with §8 final trace.
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/*_country_bundle.json` —
  17 in-scope bundles regenerated (idempotent on existing keys; new
  `per_site_verdicts` key added).
- `report/version 1.03/output/report/bundles/feedback_rerun_20260509/*_country_bundle.json` —
  20 feedback-rerun bundles regenerated.
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/figures/*_site_status_map.{png,html}` —
  16 country status maps re-rendered with named-flag callouts and
  full-list popups (`figures-only` mode preserves country prose).
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}` —
  rebuilt; 0 `criterion codes unavailable` rows; 81 site rows; 16
  status-map images embedded.

## Verification

- `grep -c "criterion codes unavailable" .../atoms_vs_ashes_results_table.md` →
  **0**.
- `cross_chapter_numeric_lint.py --strict` → `0 findings (clean)`.
- `lint_ledger_consistency.py` → `0 findings (clean)`.
- `audit_ovidiu_closure_evidence.py` → all 10 checks PASS.
- `pytest tests/test_country_bundle_per_site_verdicts.py
 tests/scripts/test_country_profile_map_callouts.py
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_renders_actual_flag_codes
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_has_no_unresolved_fallback_rows
 tests/scripts/test_v1_2_build_deliverables.py::test_results_table_scope_rules
 tests/reporting/test_run_profile_provenance.py` → 29/29 passed.
- Spot-checks of rebuilt table:
  `RO Mintia-Deva → Avoidance flags: Toxic/Gas Releases (HI-03)`;
  `RO Govora → Avoidance flags: Grid Connection (NS-02), Distance to
Population Centres (RI-05)`; `BA Gacko Thermal Power Plant →
Avoidance flags: Aircraft Crash (HI-01), Grid Connection (NS-02),
Distance to Population Centres (RI-05)`.

## Outcome

**Completed.** All nine plan to-dos closed. Feature Completion Matrix
`audit/feature_completion_matrices/2026-05-24_results_table_flag_enrichment.md`
shows every applicable surface as `Implemented` with §8 final trace
filled in. No follow-ups; out-of-scope items (specialist Chapter 5
prose, human DOCX QA, scripts/report_format_config.py default path)
remain on the v1.03 finalisation track unchanged.
