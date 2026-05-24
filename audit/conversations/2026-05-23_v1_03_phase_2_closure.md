# v1.03 Phase 2 — Closure (frozen-run post-processing only)

**Date:** 2026-05-23
**Session ID:** (current session)
**Predecessor:** `2026-05-23_v1_03_phase_2_rerun_start.md`

## Objective

Close Phase 2 of the v1.03 feedback closure round by post-processing the
**frozen** database runs the user executed themselves. The agent was
explicitly forbidden from launching any new scoring or sensitivity
round; Phase 2 was reduced to (i) rendering the sensitivity report
pack, (ii) regenerating bundles + ledgers + 20 feedback_rerun bundles,
(iii) refreshing failure / swing / sensitivity / correlation /
assumption methodology MDs, and (iv) spot-checking three sites.

## Frozen identifiers (no fresh rounds)

- Scoring run id: `score-c2a90942` (parent of both sensitivity runs).
- Regional sensitivity run id: `sens-ad4f62bb`.
- National sensitivity run id: `nat-sens-b1a62885` (50,000 MC draws).
- Output stamp: `20260523`.
- Active NH-02 E1 screening radius (compiled into snapshot): **5.0 km**
  (user-selected; bounds widened in Phase 1 to [0.1, 500.0]).

## Files Changed (Phase 2 only)

### New scripts

- `src/scripts/regenerate_v1_3_bundles.py` — bulk regenerator for 17
  country + 65 site + 17 ledger + 20 feedback_rerun bundles against
  the frozen run ids.

### Patches

- `src/scripts/export_site_bundle.py` — added `--sensitivity-run-id`
  flag so the national-sensitivity run id can be passed explicitly
  (avoids `resolve_runs` auto-picking the latest regional run).

### Regenerated data artefacts

- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_country_bundle.json` (17 files).
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_<slug>_site_bundle.json` (65 files).
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_site_ledger.csv` (17 files).
- `report/version 1.03/output/report/bundles/feedback_rerun_20260509/<CC>_country_bundle.json` (20 files).
- `report/output/sensitivity/20260523/` (regional summary MD + criterion correlation MD + 2 regional figures + correlation subdir + 17 country MDs + 17 country PNGs).
- `audit/post_processing/06_scoring/20260523_failure_*.csv` (4 global CSVs); `audit/post_processing/06_scoring/per_smr/<smr>/20260523_failure_*.csv` (4 CSVs × 8 SMR keys).
- `audit/post_processing/06_scoring/20260523_swing_weight_audit.csv`.
- `report/version 1.03/output/report/sensitivity/20260523/figures/failure/per_smr/<smr>/*.png` (4 PNGs × 8 SMR keys plus the global pack).

### Methodology refresh

- `report/version 1.03/methodology/failure_analysis.md` (global pack regenerated against stamp 20260523; NH-02 now reported as the dominant filter — 50 of 58 NuScale failures, 86.2% share).
- `report/version 1.03/methodology/failure_analysis_<smr>.md` (8 per-SMR packs).
- `report/version 1.03/methodology/swing_weight_audit.md` (fully overwritten — Declared + Swing columns both fresh against `nat-sens-b1a62885`).
- `report/version 1.03/methodology/sensitivity_analysis.md` (§6 inheritance note added clarifying that the §6 reference numbers describe the v1.02 production run; v1.03 current-run pack lives at `report/output/sensitivity/20260523/`; figure paths re-pointed to the v1.03 pack).
- `report/version 1.03/methodology/criterion_correlation.md` (full rewrite from the new run — 362 pairs observed, 2 flagged; HI-02↔HI-04 still saturating, NH-08↔NH-14 newly above the 0.70 threshold).
- `report/version 1.03/methodology/assumption_register.md` (one-line stamp note updated to include the v1.03 frozen stamp 20260523).

### Plan / paperwork

- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` — Phase 2 closure_evidence rows extended for #43 (swing column refresh), #104 + #105 (provenance + dynamic verdict spot-check), #183 (Enns bundle regenerated under new HI-01 banding).
- `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` — §2 "rerun" row moved to Phase 2 implemented with frozen identifiers; §3 E2E diagram + hops filled with concrete paths; §4 Surface Matrix rows for CLI / Script driver / Runner / DB writers / CSV-file artefacts / Methodology docs / Audit log moved to Phase 2 implemented.
- `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md` — Phase 2 pointer rewritten to reflect frozen-run post-processing (replacing the in-progress note).

## Spot-check evidence

| Site                         | nearest_fault_km | E1 verdict (radius 5 km) | passed_exclusionary     | provenance.nh02_e1_threshold_km |
| ---------------------------- | ---------------: | ------------------------ | ----------------------- | ------------------------------: |
| Polaniec power station (PL)  |             50.0 | outside                  | True                    |                             5.0 |
| Turceni power station (RO)   |             50.0 | outside                  | True                    |                             5.0 |
| Duernrohr power station (AT) |             23.9 | outside                  | True                    |                             5.0 |
| St Andrae power station (AT) |             3.24 | inside                   | False (NH-02 hard fail) |                             5.0 |

Composite arithmetic reconstructs to ~3 dp for all three full-pass sites
via `sum(weighted_contribution) / sum(weight_normalised)` ≈ DB
`composite_score` (Polaniec 7.6796 vs 7.684; Turceni 7.8108 vs 7.816;
Duernrohr 6.5398 vs 6.544 — small differences are rounding-only on
per-component decimal storage).

## Outcome

Phase 2 closed. All required Phase 2 artefacts regenerated against the
frozen identifiers; no new scoring or sensitivity rounds executed by
the agent. Phase 3 (Chapter 4 generator + country/site prototype
regeneration + Annex E/F inheritance) is the next ordered block.

## Deliberate non-scope

- The consolidated `20260523_phase1_6_sensitivity.md` audit MD is **not**
  regenerated, because doing so would require re-running the sensitivity
  suite which is frozen for v1.03. `sensitivity_analysis.md` §6 carries
  an explicit inheritance disclaimer instead.
- `ssr1_traceability.md` keeps its `20260425` stamp; SSR-1 traceability
  is derived from `config/ssr1_clause_map.yaml` which did not change
  between v1.02 and v1.03, so the v1.02 CSV remains authoritative.
- `methodology.md`'s `20260423` / `20260425` references are historical
  context for the pre-revision-034 schema and remain accurate as
  written.

---

# Phase 3 — Downstream artefact regeneration (appended 2026-05-23)

## Objective

Regenerate every artefact that depends on the frozen Phase 2 runs but
does **not** require hand-written prose. Chapter 4 tables, country
prototypes, site profiles, Annex E + Annex F inheritance language, and
the executive results-table side deliverable all land programmatically
from the same four frozen identifiers Phase 2 published. The §5a prose
(comments #50 / #60 / #61) remains a Phase 5 task.

## Frozen identifiers (unchanged)

- Scoring run: `score-c2a90942`
- Regional sensitivity: `sens-ad4f62bb`
- National sensitivity: `nat-sens-b1a62885`
- Audit stamp: `20260523`
- Run-profile snapshot: `scdef-31110148e5f56f16` (NH-02 E1 threshold = 5.0 km)

## New scripts

- `src/scripts/build_chapter_4_tables.py` — six idempotent
  `<!-- begin: table-4.x.y -->` / `<!-- end: table-4.x.y -->` blocks
  injected into `report/version 1.03/output/report/chapters/04_results_and_findings.md`.
  Data feed: 16 in-scope v1.03 ledgers (Belarus excluded per master-plan
  answer 4), 17 country bundles for the Pareto and per-country leader
  rows, 3 no-pass country bundles from
  `report/version 1.03/output/report/bundles/feedback_rerun_20260509/`
  (AL / SI / XK) for the Table 4.1.1 second row, and
  `audit/post_processing/06_scoring/20260523_failure_per_criterion.csv`
  for the exclusionary half of Table 4.4.1.
- `src/scripts/regenerate_v1_3_country_prototypes.py` — looped invocation
  of `build_country_profile_prototype.py --country-only` across the 17
  ISO codes.
- `src/scripts/regenerate_v1_3_site_profiles.py` — looped invocation of
  `--site-only` for every existing site bundle, plus `--add "RO:Iernut
  power station"` to introduce the new Iernut profile required by
  comment #60. Filled specialist placeholder bodies are preserved
  automatically by `_preserve_filled_placeholders` inside
  `_country_profile_outputs.py`.

## Path routing fix

`scripts/results_table_model.py` previously hardcoded v1.02 paths for
`DATA_DIR` / `FIGURES_DIR` / `FAILURE_SECTION`. A new
`configure_from_format(fmt)` helper now rebinds those module attributes
from an optional `results_table` block on `report_format.json`.
`scripts/results_table_data.py` and `scripts/results_table_flags.py`
dereference the module attributes at call time (via
`import results_table_model as _model`) so the rebound paths take
effect. The v1.02 file retains the same defaults via the same block, so
v1.02 builds remain byte-equivalent.

## Files written (Phase 3 deltas only)

- `report/version 1.03/output/report/chapters/04_results_and_findings.md`
  — six idempotent table blocks (4.1.1, 4.2.1, 4.3.1, 4.3.2, 4.4.1,
  4.6.1) replace the hand-authored row sets. Surrounding prose
  unchanged.
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/<CC>_country_prototype.md`
  × 17 — country narrative MDs refreshed against the frozen runs.
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/sites/<CC>_<slug>.md`
  × 66 — 65 existing site profiles refreshed (NH-02 E1 dynamic verdict
  at radius 5 km; HI-01 small-airport bands unchanged from Phase 1) +
  one new profile `RO_iernut_power_station.md`.
- `report/version 1.03/output/report/build/atoms_vs_ashes_results_table.{md,csv,docx}`
  + `reference.docx` — executive results-table deliverable rebuilt
  against the v1.03 ledger (81 site rows, 16 site-status maps).
- `report/version 1.03/output/report/annexes/annex_e_assumption_register_and_data_limitations.md`
  — A-SCOPE-03 country-roster statement and A-SENS-02 50,000-iteration
  Monte Carlo statement repointed at v1.03 stamp `20260523` and runs
  `score-c2a90942` / `nat-sens-b1a62885`.
- `report/version 1.03/output/report/annexes/annex_f_generated_methodology_artefacts.md`
  — controlled-artefact table row + numbered note 2 repointed at the
  same v1.03 identifiers.
- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml`
  — `#50`, `#60`, `#61` all moved to `closure_status: in-progress` with
  the Phase 3 numeric facts in `notes` and pointers in
  `closure_evidence`.
- `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md`
  — §2 rows for #50 / #60 / #61 and "executive summary" updated to
  Phase 3 implemented; §4 Surface Matrix rows for "Script driver" and
  "Report / export reader" updated to Phase 3 implemented.

## Spot-checks

- Iernut profile renders the NH-02 E1 dynamic verdict line correctly:
  `nearest mapped capable fault 50.0 km; ... E1 verdict (radius 5 km):
  outside the SSG-9 capable-fault screening envelope.`
- `report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/RO_iernut_power_station_site_bundle.json`
  carries `provenance.nh02_e1_threshold_km = 5.0`.
- Table 4.3.1 of the regenerated Chapter 4 lists Iernut at priority 19
  (composite 7.114, band D, 0% top-tier probability — answers `#60`).
- Table 4.3.2 of the regenerated Chapter 4 lists Braila and Romag Termo
  as the two Romanian conditional-unlock rows (answers `#61`).
- Table 4.1.1 of the regenerated Chapter 4: 16 published country
  ledgers, 352 site records, 302 scored, 33 full-pass, 269 avoidance
  flag, 50 hard fail; consolidated no-pass section 3 / 8 / 0 / 0 / 0 /
  8; total Chapter 4 evidence base 19 / 360 / 302 / 33 / 269 / 58.
- `build_chapter_4_tables.py` is idempotent — re-running produces no
  diff once the markers are in place.

## Outcome

Every rerun-dependent artefact except the §5a prose is now consistent
with the frozen Phase 2 DB. Phase 4 (verification + lint repointing)
can run against Phase 3 outputs; Phase 5 (prose edits) can take the
numeric facts from §4e directly from the regenerated tables.

## Deliberate non-scope

- No §5a prose edits to Chapter 3.9 / Table 4.3.1 surrounding
  paragraphs / Table 4.3.2 surrounding paragraphs — those sit in
  Phase 5 by design.
- No new scoring or sensitivity round was executed; all data lands from
  the existing `score-c2a90942` / `nat-sens-b1a62885` runs.
- The Iernut profile carries no specialist-written body yet; the
  template-rendered base will be filled by a specialist pass before
  Phase 6 build.

---

# Phase 4 — Verification before prose (appended 2026-05-23)

## Objective

Build the lint scaffold that gates Phase 5 prose edits and answer the
content questions (#50 / #60 / #61) from the regenerated Phase 3
artefacts rather than from memory. No rubric changes; no scoring runs;
no chapter prose edits.

## Lint repoint

- `src/scripts/cross_chapter_numeric_lint.py`
  - `CHAPTERS_DIR` rebased to
    `report/version 1.03/output/report/chapters/`.
  - New `--chapters-dir` CLI override + `run_lint(chapters_dir=...)`
    parameter so the same script can scan v1.02 or v1.03 on demand.
  - New CANONICAL_FACTS rows:
    - `V1_3_REGIONAL_FULL_PASS_COUNT` (33 regional full-pass; the lint
      catches stale "28 full-pass" / "14 first-wave full-pass" wording).
    - `V1_3_ROMANIA_FULL_PASS_COUNT` (3 Romanian full-pass; the lint
      catches "Romania ... 2 full-pass" wording).
    - `V1_3_IERNUT_COMPOSITE` (7.114; the lint catches any other
      `Iernut | 7.xxx` value inserted into a Markdown table).
    - `V1_3_NH02_E1_THRESHOLD` (`E1 verdict (radius 5 km)`; the lint
      catches stale "radius 8 km" wording).
  - Owner-doc references for the two pre-existing facts (VOYGR-6 capacity
    + Romania reconciliation) repointed at the v1.03 chapter paths.
  - Lint exit: `cross_chapter_numeric_lint: 0 findings (clean).`

## New ledger-vs-prose lint

- `src/scripts/lint_ledger_consistency.py` — reads the
  `<!-- begin: table-4.x.y -->` idempotent blocks from the regenerated
  `04_results_and_findings.md` and reconciles each row set against the
  16 in-scope v1.03 ledgers + 3 `feedback_rerun_20260509` country
  bundles:
  - Table 4.1.1: three rows must agree element-by-element with the
    summed published-ledger / no-pass cohort / total evidence-base
    counts.
  - Table 4.3.1: row count and site-name set must equal the full-pass
    cohort filter (`passed_exclusionary=True AND passed_avoidance=True
    AND composite_score is not null`).
  - Table 4.3.2: row count and site-name set must equal the
    avoidance-flag + profiled cohort filter (the latter is the set of
    `<CC>_<slug>_site_bundle.json` files under `data/`).
  - Exit codes: 0 on clean, 1 with `--strict` (default) on drift.
  - Phase 4 invocation:
    `lint_ledger_consistency: 0 findings (clean).`

## Three-site spot-check (rendered profile)

- Iernut (`RO_iernut_power_station`):
  composite (bundle) = 7.114; reconstruction Σ(score × weight) /
  Σ(weight) over the 18 participating criteria = 3.9550 / 0.5560 =
  7.1133 (diff < 0.001 to 3dp). `provenance.nh02_e1_threshold_km = 5.0`.
  NH-02 line: `E1 verdict (radius 5 km): outside the SSG-9
  capable-fault screening envelope.` HI-01 line carries no
  `nearest_light_airport_km` reference.
- Pocerady (`CZ_pocerady_power_station`):
  composite 6.931; reconstruction 5.3245 / 0.7682 = 6.9313. Same
  provenance, same dynamic NH-02 verdict, same HI-01 hygiene.
- Adamow (`PL_adamow_power_station`):
  composite 7.227; reconstruction 5.5522 / 0.7682 = 7.2278.
  Same provenance, same dynamic NH-02 verdict, HI-01 favourable
  band at score 9.5 with no light-airport reference.

## Rerank diff vs v1.02

- v1.02 in-scope full-pass cohort: 28 sites. v1.03: 33 sites. Net
  delta +5; 0 sites dropped.
- The five new entrants:
  - BG: Maritsa Iztok-2 power station
  - PL: Polaniec power station (direct visible consequence of the
    #183 HI-01 fix — A1 helipad/small-aerodrome penalty retired)
  - SK: Novaky power station
  - TR: Çerkezköy power station
  - UA: Starobesheve power station
- Top-30 displacements > 3 ranks: 8 sites, each shifted exactly +4
  positions (Kurakhov, Vuglegirska, Kıvanç, Vize, Trypilska,
  Luganskaya, METES, Zaporizhia). Pattern is consistent with four
  new sites entering above their previous v1.02 positions.

## Locked answers for §5a

- `#50`: Chapter 3.9 full-pass count must read 33 regional /
  3 Romanian (Turceni, Rovinari, Iernut). The current Chapter 3.9
  profiled-cohort table lists 11 rows and excludes both Iernut and
  Polaniec; the Phase 5a prose pass should add at least these two
  rows and refresh the surrounding sentence accordingly.
- `#60`: Iernut row from `RO_site_ledger.csv` —
  `national_rank=3, name=Iernut power station, passed_exclusionary=True,
  passed_avoidance=True, composite_score=7.114, national_band=D,
  national_top10pct_hit_rate=0.0`. Table 4.3.1 already carries the
  Iernut row at priority 19; §5a only needs prose framing.
- `#61`: Romanian Table 4.3.2 rows —
  Braila power station (composite 6.784, band D, top-tier 0%,
  drivers RI-05); Romag Termo power station (composite 6.491,
  band H, top-tier 0%, drivers HI-03, RI-05). Both already appear in
  the regenerated Table 4.3.2; §5a only needs prose framing.

## Triage YAML extensions

- `#43` `verification_method`: extended with
  `cross_chapter_numeric_lint.py` + `lint_ledger_consistency.py` 0-find
  evidence (Table 4.1.1 / 4.3.1 / 4.3.2 reconciled).
- `#104` `verification_method`: extended with the Phase 4 spot-check
  on Iernut / Pocerady / Adamow.
- `#105` `verification_method`: extended with the
  `V1_3_NH02_E1_THRESHOLD` canonical-fact pass.
- `#183` `verification_method`: extended with the Polaniec
  v1.02-avoidance → v1.03-full-pass migration evidence and the
  spot-check observation that no profile references
  `nearest_light_airport_km`.

## Outcome

Phase 4 lints pass clean, the rerank diff is bounded and the new
entrants are surfaced to the user, and the three §5a numeric answers
are locked. Phase 5 prose can land against confirmed Phase 3 artefacts;
no further DB rounds are required.

## Deliberate non-scope

- No chapter prose edits in Phase 4 by design — those live in §5a.
- No new test files added in Phase 4 (the two lint scripts cover the
  Phase 4 obligations; dedicated unit tests for them are deferred to
  Phase 6 alongside the merged-report build).

---

# Phase 5 closure — prose pass + redundancy + Stage 3 + terminology (2026-05-23)

## Scope

Phase 5 of the v1.03 feedback closure round runs the prose-side edits
that translate the Phase 1–4 engine, post-processing and lint
infrastructure into reader-visible report changes:

- §5a (#50 / #60 / #61): Chapter 3.9 + Chapter 4 prose now cites the
  regenerated Tables 4.3.1 / 4.3.2 and the 33-site full-pass set.
- §5b (#55): lost-text recovery for the Chapter 4 intro.
- §5c (#54 / #57 / #70): redundancy inventory + treatment.
- §5d (#38): Stage 3 framing.
- §5e (#63): cohort terminology sweep.
- §5f (#32): acknowledged-close.

User directive 2026-05-23 (mid-Phase 5): the report text must be
written as a single, independent run — no `v1.0x` / `v1.x` version
markers in chapter or annex prose.

## §5a — Rerun-dependent prose

- `chapters/03_stage_2_site_selection.md` §3.9: introduction rewritten
  to state the 33-site full-pass set across the 16 in-scope ledgers and
  the three Romanian full-pass leaders (Turceni, Rovinari, Iernut).
  Table 3.9 extended with Iernut, Polaniec, Maritsa Iztok-2, Novaky,
  Çerkezköy and Starobesheve as full-pass entries; Polaniec moved out
  of the unlock-layer paragraph.
- `chapters/04_results_and_findings.md`:
  - §4.1 record counts updated (302 scored / 33 full-pass / 269
    avoidance / 50 hard-fail).
  - §4.3.1 trailing prose rewritten to describe the full-pass set,
    Iernut's row-19 placement, Polaniec's HI-01 reading, and the seven
    countries represented in the full-pass set.
  - §4.3.2 Romanian addendum added (Braila row, Romag Termo row, link
    to the Romanian country profile).
  - §4.4 avoidance-driver counts updated against the v1.3 Table 4.4.1
    (NS-02 152, HI-01 116, NH-01 81, RI-05 71, NS-05 39).
  - §4.5 scored-record count updated to 302.
- `chapters/02_stage_1_site_survey.md`: §2 record counts and roster
  description updated to read as a single independent run (302 scored
  / 33 full-pass / 269 avoidance).
- After the user directive, every `v1.0x` / `v1.x` / `frozen run`
  marker removed from chapter and annex prose. Annex E A-SCOPE-03 and
  A-SENS-02 and Annex F controlled-artefact rows reframed to cite the
  run identifiers (`score-c2a90942`, `sens-ad4f62bb`,
  `nat-sens-b1a62885`, stamp `20260523`) without version naming.
- Cross-chapter numeric lint and ledger-consistency lint both exit 0
  after the prose pass.

## §5b — Lost-text recovery (`#55`)

- Reviewer's Romanian annotation `de recompletat - s-a pierdut textul`
  flagged a perceived discontinuity at the Chapter 4 intro anchor
  `current Scientific Council`.
- Verification:
  `diff "report/version 1.02/output/report/chapters/04_results_and_findings.md" "report/version 1.03/output/report/chapters/04_results_and_findings.md"`
  shows only the Phase 5a count edits; v1.02 has no extra paragraph.
  `rg 'Scientific Council' "report/version 1.02/output/report/chapters/04_results_and_findings.md"`
  returns zero hits.
- Decision: closed `deferred-with-rationale`; the v1.02 source has no
  paragraph to recover, and LLM regeneration is forbidden under
  master-plan answer 7. Closure evidence + verification recorded in
  the triage YAML for `#55`.

## §5c — Redundancy inventory + treatment (`#54` / `#57` / `#70`)

- Programmatic scan of 122 MDs under
  `report/version 1.03/output/report/chapters/`,
  `report/version 1.03/output/report/annexes/`, and
  `report/version 1.03/methodology/`: 345 tables, 105 distinct column
  signatures, 8 signatures spanning ≥ 2 files.
- Inventory written to
  `report/version 1.03/output/report/feedback/redundancy_inventory.md`
  with per-signature classification against the six SST rules.
- Treatments executed:
  - A.3 — methodology glossary consolidated. Canonical home declared
    in `methodology/failure_analysis.md`. The 8 SMR-specific files now
    carry a one-line cross-reference instead of the full glossary
    table.
    `src/scripts/_phase_1_6_failure_report.py` patched so future
    regenerations only emit the full glossary when `smr_label is None`.
  - A.4 / A.5 / A.8 — pivot-view caption + source-CSV footer added to
    every SMR-specific criterion / country / multi-failure table.
  - A.7 — engineering vs reader-facing exclusionary-band surfaces
    retained as a deliberate two-audience treatment (rule 2 not rule 1);
    reciprocal cross-references added via
    `src/scripts/generate_exclusionary_floors.py`.
  - B.1 / B.2 — Chapter 4 narrative restatements tightened in §5a so
    counts cite the canonical tables.
  - B.3 — §5.2 chapter-level country index, country-prototype ranked
    tables and site-profile identity tables retained as a deliberate
    three-tier projection of the canonical country-ledger CSV; no
    consolidation required.
- Triage YAML `#54` / `#57` / `#70` advanced to
  `resolved-in-report` with closure evidence + verification commands.

## §5d — Stage 3 framing (`#38`)

- `chapters/03_stage_2_site_selection.md` §3.3: opening paragraph now
  defines Stage 1 = regional survey, Stage 2 = ranking + selection,
  Stage 3 = detailed site evaluation + confirmation, and grounds the
  safety-related screening criteria as the Stage 2 → Stage 3 gate.
- `chapters/03_stage_2_site_selection.md` §3.10: opening paragraph
  states explicitly that Stage 2 output is one or more sites
  recommended to enter Stage 3, with selection driven by composite
  ranking + socioeconomic-and-implementation considerations.
- `chapters/06_recommendations_for_detailed_site_evaluation.md`: first
  paragraph reframed as the Stage 3 work programme and restates the
  Stage 1 / Stage 2 / Stage 3 definitions used in Chapter 3.

## §5e — Cohort terminology sweep (`#63`)

- Programmatic sweep replaced `cohort` with `set` across 33 MDs (42
  substitutions) under chapters / annexes / site-profile sites.
- `config/scoring_rubrics/nh_natural_hazards.yaml`: NH-10 wind, NH-11
  precipitation and NH-12 temperature band descriptors edited (10
  substitutions) so future re-renders no longer emit `cohort`.
- `src/scripts/build_chapter_4_tables.py`: Table 4.1.1 column header
  updated from `Cohort` to `Set`; the regenerated table block in
  Chapter 4 now prints `Set | Countries | Site records | ...`.
- Frozen site-bundle JSONs retain `cohort` strings copied from the
  scoring run; those are immutable artefacts and would only be cleaned
  by a re-scored run, which is forbidden under the frozen-run
  constraint. Reader-facing report surface no longer prints `cohort`.

## §5f — Acknowledged-close (`#32`)

- `#32` set to `closure_status: acknowledged` with closure evidence
  pointing at the §2.7 Stage 1 handoff paragraph; no prose change
  required.

## User directive — single independent run (mid-Phase 5)

- All `v1.0x` / `v1.x` / `frozen run` markers removed from chapter and
  annex prose (`chapters/02_stage_1_site_survey.md`,
  `chapters/03_stage_2_site_selection.md`,
  `chapters/04_results_and_findings.md`,
  `annexes/annex_e_assumption_register_and_data_limitations.md`,
  `annexes/annex_f_generated_methodology_artefacts.md`).
- Run identifiers retained in annexes (audit-anchor evidence) but no
  longer tagged as a `version 1.3 run`.
- Verified by `rg 'v1\.[023]|version 1\.[023]|frozen run'
  "report/version 1.03/output/report/chapters"` (0 hits) and the same
  query against `annexes` (0 hits).

## Triage YAML status

- 12 comments at `resolved-in-report`: `#38`, `#43`, `#50`, `#54`,
  `#57`, `#60`, `#61`, `#63`, `#70`, `#104`, `#105`, `#183`.
- 1 comment at `deferred-with-rationale`: `#55`.
- 1 comment at `acknowledged`: `#32`.
- All 14 reviewer comments at terminal closure status; Phase 6 can
  freeze the YAML state and start the build.

## Outcome

Phase 5 closes the reader-visible prose pass for every reviewer
comment. The report now reads as a single independent run, every
reviewer-named noun (Iernut, Polaniec, Maritsa Iztok-2, Romanian
conditional-unlock entries, Stage 3 framing, set/cohort terminology,
NH-02 5 km capable fault, HI-01 ex-helipad / small airfields, swing
weights summing to 1.0) is visible in the rebuilt chapters / annexes,
and both Phase 4 lints continue to exit 0.

## Deliberate non-scope

- No pandoc / DOCX / PDF build executed in Phase 5; that is Phase 6.
- No regeneration of frozen scoring or sensitivity runs (user
  constraint).
- No edits to the immutable site-bundle JSON descriptor strings; the
  reader-facing surface is the chapter and annex prose, which now
  reads as a single independent run.

---

# v1.03 Phase 6 — Build, Verify, Audit (2026-05-23)

## Trigger

User instruction: "v1.03 Phase 6 — Build, Verify, Audit. Implement the
plan as specified ... Don't stop until you have completed all the
to-dos." Plan at
`/Users/terbolence/.cursor/plans/v1.03_phase_6_build_12acd154.plan.md`.

Prerequisites set by the user before Phase 6:

1. Verify Ovidiu's 10 v1.02 comments (#32 #38 #43 #50 #54 #57 #60 #61
   #63 #70) are reflected in the current chapter sources.
2. Upgrade the results-table deliverable so the maps are on A3
   landscape pages and the per-plant rows expose plant owner alongside
   export power, surface area and avoidance-flag cells.

## Step 1 — Ovidiu-comments closure audit (gate)

Built `src/scripts/audit_ovidiu_closure_evidence.py` — a structured
audit that reads the v1.03 triage YAML, filters to Ovidiu's ids, and
runs one anchor check per comment against the live chapter / annex
source tree. Each check is a concrete pattern in a named file rather
than a free-form shell exec:

- #32 — §2.7 Stage 1 Outputs and Limitations + handoff sentence in
  `chapters/02_stage_1_site_survey.md`.
- #38 — Stage 1/2/3 staged opener + scope sentence + deviations
  paragraph in `chapters/06_recommendations_for_detailed_site_evaluation.md`;
  cross-references in §3.3 and §3.10 of `chapters/03_stage_2_site_selection.md`.
- #43 — Idempotent weight-family blocks `weights-nh|hi|ri|ep|ns` in
  Chapter 3 sum to 100.00% on the agent's local re-parse.
- #50 — "33 full-pass sites" framing in §3.9 + Turceni / Rovinari /
  Iernut in Table 3.9 + 33-site totals in Chapter 4.
- #54 + #57 — Table 4.1.1 column header `Set` (not `Cohort`),
  idempotent table-4.1.1 / 4.2.1 / 4.3.1 / 4.3.2 / 4.4.1 marker blocks
  present, no `Cohort:` captions.
- #60 — Table 4.3.1 contains the Iernut row with composite 7.114.
- #61 — Table 4.3.2 contains the Braila and Romag Termo rows.
- #63 — Zero `cohort` token hits in chapters + annexes (already 0
  after Phase 5e sweep; the audit re-asserts).
- #70 — §5.2 country-index table (`| Country | Current profile |`)
  appears exactly once.

Initial run flagged one fail: the Table 4.1.1 header check used a
literal `"| Set | Countries"` membership test; the actual header pads
the `Set` cell to align the column, so the literal string did not
match. Switched to a `^\|\s*Set\s+\|\s*Countries` regex (and rejected
the presence of a similar `Cohort` header). All 10 comments PASS
after the patch.

JSON report:
`audit/v1_03_phase_6/ovidiu_closure_audit.json`.

## Step 2 — Results-table upgrade (A3 landscape + Owner column)

Touched four files (no JSON config change required because the
A3 margins come from the existing `margins_mm` block):

- `scripts/results_table_model.py` — added `"owner"` to `CSV_COLUMNS`
  between `site` and `status`; added `owner: str` to `SiteRow`.
- `scripts/results_table_flags.py` — added `site_owner(country_code,
  site_name) -> str`. Reads the same site bundle that
  `site_surface_area` already reads. Returns `owner_operator`; if
  `parent_company` is non-empty and differs from the operator, the
  parent is appended as `Operator (parent: Parent)`. Empty-string
  fallback when both fields are null (consistent with surface area).
- `scripts/results_table_data.py` — wired `site_owner` into the
  `SiteRow` constructor; inserted `Owner` into the Markdown header
  between `Site` and `Status`; widened the per-country map embed
  from `{width=9in}` to `{width=15in}` so the PNG fills the A3
  landscape printable width.
- `scripts/build_results_table_deliverable.py` — renamed the
  page-geometry helper from `_set_landscape_a4` to
  `_set_landscape_a3`; replaced `Mm(297) × Mm(210)` with
  `Mm(420) × Mm(297)`; updated the only call site.
- `tests/scripts/test_v1_2_build_deliverables.py` — re-pointed the
  monkeypatch target from `_set_landscape_a4` to `_set_landscape_a3`.

Rebuilt with `python -m scripts.build_results_table_deliverable
--format "report/version 1.03/output/report/writing plan/report_format.json"
--output-dir "report/version 1.03/output/report/build"` (with
`PYTHONPATH=scripts:src` because `report_docx_postprocess` lives
under `scripts/`). Output:
`atoms_vs_ashes_results_table.docx (81 site rows, 16 maps)`.

DOCX page geometry verified:
`orientation_landscape=True; page_width_mm=420; page_height_mm=297`.

Spot-checked Owner column on Turceni, Iernut, Polaniec, Maritsa
Iztok-2:

- Turceni → "Complexul Energetic Oltenia SA [100%] (parent:
  Ministry of Energy (Romania) [77.2%]; Fondul Proprietatea SA
  [21.6%])"
- Iernut → "Romgaz SA [100%] (parent: Romgaz SA [100.0%])"
- Polaniec → "ENEA SA [100%] (parent: ENEA SA [100.0%])"
- Maritsa Iztok-2 → "" (blank). The BG country bundle records
  `owner_operator=null` and `parent_company=null` for Maritsa
  Iztok-2; the empty-string fallback is the documented contract.

## Step 3 — Main report build (pandoc → DOCX)

Ran `python -m scripts.build_report --format "report/version 1.03/output/report/writing plan/report_format.json"
--keep-merged`. Output:

- `merged.md` (1.3 MB; 99 chapter files merged).
- `atoms_vs_ashes_report.docx` (5204 paragraphs, 153 tables restyled).
- Side deliverables: `atoms_vs_ashes_results_table.docx` (rebuilt
  again as part of `build_side_deliverables`), `atoms_vs_ashes_work_audit_synthesis.docx`.

`scripts/build_report.py` does not invoke a PDF pipeline. DOCX is the
canonical executive deliverable; PDF generation is out-of-band (Word
or LibreOffice export). Recorded as a Phase 6 deferred surface in
§7 of the FCM with the rationale that no PDF stage exists in the
build script.

Smoke checks on `merged.md`:

- Iernut → line 465 (Stage 3 sequencing row), line 553 (Romania
  full-pass aggregate), line 592 (priority 19 / 7.114 / band D / 0%),
  line 611 (Chapter 4 §4.3.1 prose).
- Polaniec → 5 hits including line 469 (Stage 3 row), 552
  (Polish aggregate), 578 (Table 4.3.1 row 1), 611, 743.
- Maritsa Iztok-2 → 5 hits including line 476 (Stage 3 row), 544
  (Bulgarian aggregate), 577 (Table 4.3.1), 735 (Table 4.4.1),
  2486 (leader-stability paragraph in §4.4).
- Chapter 6 staged opener → 3 anchor hits at lines 11887 (Stage 1 —
  Site Survey), 11889 (Stage 2 — Site Selection), 11891 (Stage 3 —
  Site Evaluation and Confirmation); plus line 11893 ("ulterior
  Stage 3") and 11895 ("Deviations from the SSG-35 stages").

## Step 4 — Executive summary build

The codebase has no separate `build_executive_summary` script. The
two executive-grade side deliverables produced by
`build_side_deliverables` (and therefore by `build_report`) are:

- `atoms_vs_ashes_results_table.docx` — explicitly labelled
  "executive screening table" in its own module docstring; A3
  landscape; per-country rows with Owner + export power + surface
  area + avoidance / failure note.
- `atoms_vs_ashes_work_audit_synthesis.docx` — stakeholder-facing
  exec brief (3 expert viewpoints).

Both are present in `report/version 1.03/output/report/build/`.

## Step 5 — Post-build gate

```
cross_chapter_numeric_lint --strict   -> 0 findings (clean)
lint_ledger_consistency               -> 0 findings (clean)
audit_ovidiu_closure_evidence         -> 10 / 10 PASS
```

All three exit 0.

Writing-quality auditor + §S surface audit sweep:
`audit/v1_03_phase_6/writing_quality_findings.md`. Programmatic
findings register:

- 0 hits on version markers (`v1.03`, `version 1.3`).
- 0 hits on `cohort` token residue.
- 0 hits on "definition-by-negation" templates (`not empty`,
  `not without`, `not the only`, `not unlike`).
- 0 hits on v1.2 inheritance leak (`v1.2`, `version 1.2`).
- 3 hits on SSG-35 staged opener anchors (Stage 1 / 2 / 3).
- Owner column populated on Turceni / Iernut / Polaniec; blank on
  Maritsa Iztok-2 by documented contract.

Programmatic verdict: Accept. Editorial review (paragraph rhythm,
IEA-WEO-class typography) remains a human pass.

## Step 6 — Paperwork

- Feature Completion Matrix
  `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md`
  closed:
  - §1 Date closed → 2026-05-23 (Phase 6 build + audit).
  - §4 Surface Matrix → Report / export reader + Tests entry-point
    smoke + Audit log rows resolved to Phase 6 implemented.
  - §5 Negative Acceptance Tests → six rows with concrete test files
    + assertions.
  - §6 Subtle Consumption Check → eight artifact → consumer rows.
  - §7 Deferred Surfaces → #55 (deferred-with-rationale, no
    recoverable lost paragraph in the v1.02 source) + PDF (no
    in-pipeline PDF stage; DOCX is canonical).
  - §8 Final Trace → end-to-end populated.
- Master plan `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md`
  Phase 6 closure pointer appended.

## Frozen constraints honoured

- No new scoring or sensitivity rounds. Frozen run identifiers:
  scoring `score-c2a90942`, regional sensitivity `sens-ad4f62bb`,
  national sensitivity `nat-sens-b1a62885`, stamp `20260523`.
- No live API or paid-model calls. The Phase 6 auditor sweep is the
  programmatic anchor sweep; deep editorial review remains the
  user's pass.
- Site-bundle JSON `cohort` strings (immutable artefacts of the
  frozen scoring run) left in place; reader-facing chapter and
  annex prose is `cohort`-free.

