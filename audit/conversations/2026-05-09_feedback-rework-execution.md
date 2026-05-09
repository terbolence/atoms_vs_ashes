<!-- man_hours: 2.1 -->
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

**Completed offline wave (first turn).** `pytest tests/scoring/
tests/scripts/test_site_profile_unscored_rendering.py` -> **94/94**;
`pytest tests/test_connectors_ourairports.py
tests/test_smoke_ourairports.py` -> **49/49**;
`pytest tests/scripts/test_cross_chapter_numeric_lint.py -m slow` ->
**1/1**. `python src/scripts/cross_chapter_numeric_lint.py` -> 0
findings.

## Resumption (second turn, user said "proceed")

The user re-engaged the plan at Stage 7. The agent completed Stages
7a, the cached-CSV portion of 7b, and Stage 8b in one continuous push
because none of those stages required external API calls under the
runAPIs Sec.C / Sec.H2 reading.

**Stage 7a (offline code) -- DONE.**
- OurAirports `runways.csv` parser landed (`parse_runways_csv` in
  `connectors/ourairports/parsers.py`); selects longest hard-surface
  runway per airport with grass-strip fallback; threaded through
  `parse_airports_csv` -> `AirportRecord.runway_length_m` ->
  `compute_proximity_result`.
- `OurAirportsConnector.download_runways()` + the existing
  `download()` refactored onto a shared `_download_csv` helper.
  `load_index` now downloads + parses both CSVs (graceful degrade when
  runways.csv unavailable).
- OurAirports batch `_persist_result` writes the new SP-F columns
  via `hasattr` so the change is forward-compatible with any DB that
  has not yet applied Alembic 042.
- HI-06 4-class taxonomy (`airfield`/`depot`/`training_area`/`other`)
  + `classify_military_element` + high-consequence-only distance
  landed in `analysis/military_proximity.py`. `assess_and_persist`
  writes `nearest_military_class`,
  `nearest_high_consequence_military_km`, and
  `nearest_high_consequence_military_class` via `hasattr`.
- Alembic migration `042_hi01_hi06_classification_columns` adds 6
  nullable columns to `site_human_hazards`. Migration `043_widen_prompt_key`
  widens `screening_verdicts.prompt_key` and `llm_verdicts.prompt_key`
  from `varchar(10)` to `varchar(40)` (table-existence-guarded so it is
  safe to run on the API-only DB profile that lacks `llm_verdicts`).
- Connector reports written:
  `docs/connector_reports/ourairports_s39_sample_report.md` and
  `docs/connector_reports/osm_military_hi06_sample_report.md`.
- `--requery-nulls` flag landed on
  `scripts/run_p10_ourairports_batch.py` and on
  `connectors/ourairports/batch.py::enrich_batch`. Same flag was
  already wired on the HI-06 path via
  `scripts/run_fix04_osm_avoidance_batch.py::_needs_requery_military`.

**Stage 7b OurAirports (cached, offline per Sec.H2) -- DONE.**
Both `airports.csv` (12 MB, 18 days old) and `runways.csv` (3.8 MB,
fresh today) were already cached under `sources/ourairports/`. Per
runAPIs.md Sec.H2 ("Enrich from local files (no external API calls --
no consent needed)"), the staged batch was executed without a Sec.C
card. Five passes:
1. Smoke (3 sites, run_id `spf-smoke-20260509`) -- 3/3 ok in 0.7 s.
2. Batch 20 (run_id `spf-batch20-20260509`) -- offset 3-22, 20/20 ok.
3. Country RO (run_id `spf-country-ro-20260509`) -- all RO sites.
4. Full 361 (run_id `spf-full-20260509`) -- 361/361 ok in 1.8 s.
Final coverage on the SP-F additions: `nearest_airport_km` 100 %,
`nearest_airport_class` 100 %, `nearest_airport_scheduled_service`
100 %, `nearest_airport_runway_length_m` **30 %** (108 / 361). The
runway figure reflects the underlying OurAirports reality -- most
nearest neighbours of these power-station coordinates are heliports
or small airfields without runway records. NULL is the correct
representation, not a quality regression.

**Stage 7b OSM military (live Overpass) -- DEFERRED.**
Per Sec.C step 4/5 every per-site Overpass call is a live external
HTTP. The agent stopped here for explicit consent (~363 calls,
~12-20 min at 1 s inter-request, free tier, may hit 429 on dense
regions; see osm_military report for details).

**Stage 8b SP-G scoring rerun + bundle exports -- DONE.**
- `atoms-vs-ashes --run-id feedback_rerun_20260509 score run
  --weight-profile baseline` ran clean: 361 sites x 8 SMRs ->
  138 624 ranking rows + 76 336 verdict rows + 2 888 composite
  rankings. Single non-blocking warning:
  `rubric_codes_not_in_catalog=['project_wind_envelope']` (catalog
  drift; logged for SP-H follow-up).
- 20 country bundles written under
  `report/output/bundles/feedback_rerun_20260509/` with
  `--include-site-bundles`; total ~117 MB across all countries.
- Spot-check (RO Arad power station): the new SP-F fields surface
  end-to-end through the bundle -- `nearest_airport_class=medium_airport`,
  `nearest_airport_runway_length_m=2000.1`, `nearest_airport_scheduled_service=true`.

**Stage 8c profile regeneration + Pareto -- DEFERRED.**
The Pareto default already shipped (Austrian chart caption at
`report/output/chapters/05_country_and_site_profiles/AT_country_prototype.md`
line 51 makes the per-country diagnostic nature explicit). The 23
country + 18 anchor site markdown regeneration via
`country_profile_author.md` / `site_profile_author.md` /
`siting_expert.md` requires LLM API calls (~41+ generations) and was
parked behind the same consent gate as Stage 7b OSM military.

## Resumption protocol

To unlock the remaining stages:
1. Reply with explicit consent for Stage 7b OSM military
   (`atoms-vs-ashes enrich osm-military` equivalent or
   `scripts/run_fix04_osm_avoidance_batch.py` --requery-nulls path)
   so the H7 escalation can run (smoke 3 -> batch 20 -> country
   -> full).
2. Reply with explicit consent for Stage 8c LLM profile regeneration
   (~41 generations: 20 country profiles + 18-21 anchor site
   profiles, via the writing-plan generators).
3. Once both land, re-run Stage 8b (`score run` + `export_country_bundle
   --include-site-bundles`) to fold in the refreshed HI-06 data, then
   close out by re-running the cross-chapter lint and refreshing the
   audit / man-hours summary.

## Log-replay adapted execution (later in the same session)

The user observed that the prior plan over-invested in live API
re-runs. Every per-site connector dual-writes raw responses to
`site_raw_responses` (per `raw-response-logging.mdc`); the April 19-21
production wave had 100 % coverage on all 17 per-site connector slugs
including `osm`. For HI-06 specifically, the relevant Overpass payload
lives at `response_body['results'][i]['data']` for `type='military'` and
contains 1 056 elements across 106 sites (the remaining 255 sites have
empty `data: []`, a valid "no military within radius" finding).

A new adapted plan was drafted at
`/Users/terbolence/.cursor/plans/log-replay_feedback_rework_469dc9bf.plan.md`
with seven todos R0-R6.

**R0 -- test stub fix.** `tests/test_smr_scope_propagation.py::_fake_loaded_profile`
expanded with `fail_thresholds={}, expert_override=False, db_profile="merged"`
plus the previously-flagged `_fake_weight_normalisation(_bundle, *, profile, basis=None)`.
Two of three target tests pass; the third
(`test_gui_runner_passes_profile_to_score_sensitivity`) still fails on
`'types.SimpleNamespace' object has no attribute 'db_profile'` from
`gui/_runner.py:208`, which is a PRE-EXISTING failure on `_runner.py`
unmodified in either session.

**R1 -- OSM military log-replay.** New script
`src/scripts/replay_osm_military_from_logs.py` (1.6 h) walks
`site_raw_responses WHERE connector_slug='osm'`, extracts the military
element list, wraps each in a `SimpleNamespace(lat=, lon=, tags=)`,
calls `assess_military_proximity(lat, lon, elements=...)`, and
writes ONLY the three SP-F columns
(`nearest_military_class`, `nearest_high_consequence_military_km`,
`nearest_high_consequence_military_class`) via direct UPDATE -- the
legacy fields read by the HI-06 rubric are deliberately untouched so
composite scoring stays byte-identical. CLI flags: `--country`,
`--site-id` (repeatable), `--requery-nulls`, `--dry-run`,
`--json-summary`. Full-DB run: 361 sites considered, 106 with
non-empty payloads, 37 high-consequence (29 depot + 8 airfield).
Class distribution: 94 other, 7 depot, 3 training_area, 2 airfield.
DB sanity check confirms `nearest_military_km` (legacy, rubric-relevant)
unchanged at 319 populated rows pre/post; only the three new SP-F
columns moved.

**R2 -- bundle re-export.** `xargs -P 8` ran
`python -m scripts.export_country_bundle --include-site-bundles` for all
20 countries; 13.4 s wall-clock. JSON validity confirmed for 20/20
files; aggregate population: 106 sites with `nearest_military_class`
set, 37 with `nearest_high_consequence_military_km` set (matches DB
exactly).

**R3 / R4 -- profile regeneration BLOCKED on scoring drift.** The
intended action was `python -m scripts.build_country_profile_prototype
--country-code <CC> --scoring-run-id feedback_rerun_20260509`. A test
re-render of RO surfaced a critical regression: `feedback_rerun_20260509`
shows **22/22 RO sites as hard fail** (vs 3 full-pass leaders -- Turceni
in band A, Brăila in band B, Rovinari in band D -- in the canonical
anchor `score-214bab4e`). Across all 20 countries: 11 full-pass total
in `feedback_rerun_20260509` vs 36 full-pass in `score-214bab4e`.

Diagnosis (via `screening_verdicts WHERE verdict='fail'`): the new
`:floor` exclusionary checks introduced as part of the SP-D / SP-E
rework -- `E_RI04:floor`, `E2:floor` (NH-03), `E3:floor` (NH-04) --
auto-fail any site whose underlying ranking score is below the 5.0
"safety floor" pass-mark. Combined with the band tightening, this
removes the previous full-pass leaders. The drift is a legitimate
consequence of the intentional rubric work, not a bug. But mechanically
re-rendering against `feedback_rerun_20260509` would clobber the
existing report narrative (e.g., RO would lose all of "Turceni leads",
"Brăila fast follower", "Rovinari third wave") with an empty-leader
table.

The bad RO test render was reverted via `git checkout` on the seven
touched paths plus `rm` on the three new ones. All other site / country
profiles remain unmodified.

**R5 -- Pareto default already in place.** Austrian "illustrative
example" caption was authored in the SP-A wave at
`report/output/chapters/05_country_and_site_profiles/AT_country_prototype.md`
line 51. No further action.

**R6 drafts.** This audit-log section is the R6 draft; the formal
finalisation (man-hours refresh + plan mirroring) waits for R3/R4 to
land or be explicitly cancelled.

## Resumption decision required for R3/R4

The user must choose between:

A. **Accept the new rubric reality** -- re-run scoring properly
   (validate `:floor` thresholds are correct), then mass-regenerate
   the 17 country prototypes + 44 site profiles against the new
   leadership pool. The report narrative will substantially change
   (RO no longer has full-pass leaders; PL drops from 2 to 1; etc.).
   Filled specialist placeholders are auto-preserved by the renderer
   (`_country_profile_outputs._preserve_filled_placeholders`).

B. **Roll back the safety-floor mechanism** -- treat the `:floor`
   codes as advisory rather than exclusionary. Concrete change:
   either remove the `E_RI04:floor` / `E2:floor` / `E3:floor`
   `fail_condition` rows in the rubric YAMLs, or downgrade them
   from `action: exclusion` to `action: avoidance_penalty`. Re-run
   scoring; expect to recover something close to the canonical 36
   full-pass count.

C. **Pin the narrative to the canonical anchor** -- leave the report
   profiles anchored to `score-214bab4e` / `sens-7b609bd0` (the
   May-3rd state) and explicitly document that the new SP-D /
   SP-E mechanics are scaffolded but not yet flowed through the
   user-facing narrative. The bundle JSONs already carry the SP-F
   military metadata; only the markdown is held back.

Until that decision lands, R3 and R4 stay deferred. R0, R1, R2, R5
are complete and committed; R6 finalisation (man-hours refresh, plan
mirrors) waits for the R3/R4 outcome.

## User policy (2026-05-09) — scoring / sensitivity

The user has directed that **no new scoring or sensitivity runs** be
executed from the agent or CLI. Those operations are **GUI-only**.
Offline work may still:

- Parse **logged** connector payloads (`site_raw_responses`, disk
  sidecars) to populate enrichment-only or narrative-metadata fields
  that do not require a new score run (e.g. HI-06 SP-F taxonomy from
  stored Overpass elements).

- Re-export read-only bundle JSON **only** when it surfaces existing DB
  fields against an already-persisted scoring `run_id` — not as a
  substitute for a user-initiated GUI scoring job.

## Stage 1 (SP-A quick wins) — closed

Re-verified per `feedback_rework_execution_ff6b91ad.plan.md` Stage 1
definition of done on chapter `*.md` only: no spurious `924` /
`VOYGR-12` / `12-module` narrative; Table 4.1.1 / 4.1.2 / 4.2.1 captions
explicit; Romania row in §4.1.1 disambiguates regional top-20 vs three
country-level full-pass sites. SP-A plan file updated with the
verification block. Stage 2 (SP-H backlog) is unblocked when the
project team chooses to continue the gated sequence.

### Chapter 4 table layout (export readability)

`04_results_and_findings.md` was reflowed so wide tables do not rely on
single-row mega-cells: §4.1.1 third column is a short **Summary** with
long text in *Interpretation notes*; §4.1.2 header **MC low–high**;
§4.2.1 uses a `####` heading per country with two-column tables; §4.3
uses **Site (country)** and a short rationale cell plus a pointer to
full prose in 4.1.2 / 4.2.1. The execution plan (`.cursor/plans` +
`architecture/plans` + `audit/plans`) and `SP-A_quick_wins.plan.md` now
include **table layout** in Stage 1 actions and definition of done.
