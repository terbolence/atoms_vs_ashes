<!-- man_hours: 1.4 -->
# Implementation audit — current repo state vs FB-LL acceptance

This audit verifies the implementation status of each scoring-related theme against the **current** files in the repository, separately from what the plans claim to have landed. It is the substrate for the per-comment status assignments in [`ovidiu_comment_conformity.md`](ovidiu_comment_conformity.md).

Sources verified:

- [`config/scoring_rubrics/`](../../../config/scoring_rubrics/) — `nh_natural_hazards.yaml`, `hi_human_induced.yaml`, `ri_radiological.yaml`, `ep_emergency_planning.yaml`, `ns_non_safety.yaml`.
- [`config/scoring_specs/`](../../../config/scoring_specs/) — paired spec bundles.
- [`config/epri/weights.yaml`](../../../config/epri/weights.yaml).
- [`src/scripts/_site_profile_markdown.py`](../../../src/scripts/_site_profile_markdown.py) — `_family_section`.
- [`tests/scripts/test_site_profile_unscored_rendering.py`](../../../tests/scripts/test_site_profile_unscored_rendering.py).
- `audit/post_processing/{hi01_preview,hi06_fix04_preview,sp_f_log_replay}/`.
- [`audit/conversations/2026-05-09_feedback-rework-execution.md`](../../conversations/2026-05-09_feedback-rework-execution.md).
- [`audit/conversations/2026-05-10_hi01-hi06-preview-apply.md`](../../conversations/2026-05-10_hi01-hi06-preview-apply.md).
- [`audit/post_processing/scoring_rerun_runbook/anchor_delta.md`](../scoring_rerun_runbook/anchor_delta.md).

## T2 / FB-LL-01 — Favorable-by-default high-band branches

FB-LL-01 acceptance: a clearly favorable hazard absence must produce a score in `[8, 10]`, not the `[5, 6]` project pass-mark.

| Criterion | High-band `[9,10]` condition | Reviewer acceptance | Verdict |
|---|---|---|---|
| NH-03 (liquefaction) | `liquefaction_suscept in ['very_low','none']` (and `[7,8]` matches `'low'`) | "low susceptibility = high score" | met |
| NH-04 (slope) | `slope_angle_deg < 1` | "on-site slope only; 10 deg must not exclude" | met (boundary check via E3 at 25 deg only) |
| NH-05 (subsidence) | `karst_severity == 'none' and subsidence_risk_class in [null,'none'] and (mining_void_distance_km >= 10 or null)` | "absent evidence = favorable" | met (NULL handled as favorable) |
| NH-07 (volcanism, reviewer called it NH-06) | `nearest_volcano_km > 1000 or nearest_volcano_km is null` | "no volcano = score 10" | met |
| NH-08 (coastal, reviewer called it NH-07) | `coast_distance_km > 50 or elevation_m >= 50 or country_is_landlocked == true` | "no coast in Austria = 10" | met (landlocked branch present) |
| NH-09 (river flood) | `flood_zone_class_500yr in ['none','negligible']` OR distance | "negligible flood zone = high" | met (rubric comment cites SP-F Ovidiu) |
| NH-11 (extreme precipitation) | `mean_annual_precip_mm in [400,800]` (sub-score); `extreme_precip_mm` declared but unused | "low extreme precipitation = favorable" | **not met**: low annual precipitation still scores `[1,2]`, and `extreme_precip_mm` is declared as a `db_field` but not used in any sub-score band |
| NH-13 (wildfire) | `combustible_veg_pct < 5` | "no nearby vegetation = high" | met |
| NH-14 (combined hazards) | engine emits unscored when `<5` underlying criteria resolved | "do not default to 5 without data" | met (engine `_inject_nh14_derived_metrics` + rubric supports unscored) |
| HI-01 (aircraft) | `nearest_airport_km > 30 AND nearest_military_airfield_km > 60` | "no major airport in 30 km = favorable" | **not met**: still an AND-clause; FB-LL-08 boundary-example failure mode unfixed; v2 bands explicitly deferred pending SP-F airport-class consumption |
| HI-02 (industrial) | `nearest_seveso_km > 20 or (null and hi02_search_completed)` | "favorable when search completed and nothing found" | met (sentinel-favorable branch) |
| HI-04 (external fires) | `nearest_flammable_storage_km > 15 or (null and hi04_search_completed)` | same | met |
| HI-05 (transport) | `nearest_hazmat_corridor_km > 10 or (null and hi05_search_completed)` | same | met |
| HI-06 (military) | `nearest_military_km > 60` only | "depends on classification; depot/firing polygon matters" | **not met at rubric level**: SP-F class fields populated in DB but not referenced by the band; HI-06 v2 not authored |
| HI-08 (other nuclear) | `nearest_nuclear_km > 100 or (null and hi08_search_completed)` | "favorable when no installation found" | met |
| EP-01 (emergency planning) | `ep01_composite_score >= 85` | "Timelkam 44/100 too low at 5.5" | partial (re-banded but Timelkam's composite still falls in `[3,4]`, lower than reviewer's expectation) |

**Net:** 12 of 16 reviewer-targeted criteria meet FB-LL-01 acceptance at the rubric level. HI-01 and HI-06 are blocked on rubric work consuming SP-F enrichment. NH-11 is a substantive miss: the reviewer's framing of "low precipitation = favorable" does not match the rubric's "optimal 400–800 mm" structure, and the dedicated `extreme_precip_mm` field is unused.

## T3 / FB-LL-02 — Renderer no longer asserts numeric score with "no evidence"

`src/scripts/_site_profile_markdown.py::_family_section` produces three distinct branches:

1. `is_unscored or score is None` ⇒ `"no native score (unscored — no band matched), … Evidence: not measured at this site (criterion remains unscored)"`.
2. `4.5 <= score <= 6.5` ⇒ `"<score>/10 — pass-mark band: <descriptor>"`.
3. `score >= 8.0` ⇒ `"<score>/10 — favorable: <descriptor>"`.

Acceptance tests in [`tests/scripts/test_site_profile_unscored_rendering.py`](../../../tests/scripts/test_site_profile_unscored_rendering.py) cover all three branches plus the unchanged scored case. **Verdict: met at code + test level.**

Caveat: the regression matrix that proves the rendered profiles inherit this fix end-to-end requires Stage 8c (LLM-driven profile regeneration), which is gated behind reviewer/LLM-consent and currently deferred. Source-level renderer behaviour is correct; the **rendered chapter 5 markdown files have not all been re-generated** against the new run.

## T5 / FB-LL-03 — Connector sub-classification (HI-01 airports, HI-06 military)

Data layer (populated via SP-F):

- HI-01: `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`, `flight_path_distance_km` — populated for all 361 sites (100 % class coverage; 30 % runway length, which matches OurAirports reality for the dominant small-airfield / heliport neighbours).
- HI-06: `nearest_military_class`, `nearest_high_consequence_military_km`, `nearest_high_consequence_military_class` — populated via `replay_osm_military_from_logs.py` for 361 sites (106 with non-empty payloads; 37 high-consequence).
- HI-06 preview/apply landed via JSONL replay verified by three-way verifier (`audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md`): 1 121 expected flips = 1 121 landed flips, 0 failures.

Rubric layer (consumes the new fields):

- HI-01 rubric still uses `nearest_airport_km` + `nearest_military_airfield_km`. **Does not consume `nearest_airport_class`.**
- HI-06 rubric still uses `nearest_military_km` + legacy `military_type` enum. **Does not consume `nearest_military_class` or `nearest_high_consequence_military_km`.**
- Confirmed by `rg "nearest_military_class|nearest_high_consequence_military"` returning zero hits under `config/scoring_rubrics/`.

**Verdict:** data-layer FB-LL-03 acceptance met (≥95 % coverage thresholds satisfied); rubric-layer FB-LL-03 acceptance **not met**. The reviewer's substantive complaint that HI-06 scores 0.20–1.5 because the rubric treats every military installation alike is **still active** at scoring time, even though the underlying distinction now exists in the database.

## T1 / FB-LL-09 — EPRI weight basis provenance

- [`config/epri/weights.yaml`](../../../config/epri/weights.yaml) exists with EPRI integer factors + percent breakdown for every criterion in the rubric set, citing EPRI 3002023910 (2022) and IAEA SSG-35 maps.
- Every criterion in `config/scoring_rubrics/*.yaml` carries `weight_factors: {baseline: N, epri: M}` and `weight_basis_source: {baseline: ..., epri: ...}` — provenance present in config.
- `score run --weight-basis {baseline|epri}` flag is wired in `_cli.py` / `_cli_run.py` (per the execution audit log) and `_assert_basis_populated` guards composite calculations.
- Audit comparison artefact: `audit/post_processing/epri_weights/baseline_vs_epri.{md,csv}`.

Gap relative to FB-LL-09 acceptance test ("every criterion bullet in regenerated site profiles reads `weight 0.0308 (basis: EPRI Site Selection Report 2022 Table 4-2)`"): the renderer in `_site_profile_markdown.py` emits `f"weight {_num(weight, 4)}"` with no `basis` annotation. The weight basis is loaded but not surfaced per bullet in the rendered profile.

**Verdict:** config + engine implementation met; renderer transparency requirement **not met**. To close fully, the rendered site profile bullets need a `(basis: <epri|baseline>)` suffix and the canonical methodology section needs to name the source document. The weight-basis swap is mechanically supported, but the reviewer's "Did you use EPRI?" question still cannot be answered from the report alone without out-of-band reference to `weights.yaml`.

## T4 / FB-LL-04 / FB-LL-05 — Stage 1 vs Stage 2 boundary and RI-04 dual mode

- Stage 4 of the rework execution rewrote chapter 3 §3.2 ("safety as controlling constraint"), §3.3 ("Stage 1 screening vs Stage 2 selection") and §3.5 ("RI-04 dual mode"). The chapter file references `config/ssr1_clause_map.yaml` per FB-LL-04 acceptance.
- `config/scoring_rubrics/ri_radiological.yaml` RI-04 carries the structured `notes:` block citing FB-LL-05, reviewer comments #33 and #564, and chapter 3 §3.5; defines both the `A12` avoidance penalty and the `E_RI04` exclusion (`pop_density_5km > 1500 or (pop_density_5km > 800 and pop_density_16km > 1200)`).
- The `notes` field is now first-class on `Criterion` and `CriterionTemplate` (`scoring/rubric.py`, `criterion_spec/schema.py`) per the audit log, so the dual-mode metadata survives the rubric→spec compile path.

**Verdict:** met at config and methodology level. The `E_RI04` exclusion uses density bands as a stand-in until the dose-feasibility calculation is wired in Stage 3 — the rubric notes that explicitly. Downstream effect on screening: in `feedback_rerun_20260509` the `E_RI04:floor` rule contributed to substantial full-pass-count drift (see [`audit/conversations/2026-05-09_feedback-rework-execution.md`](../../conversations/2026-05-09_feedback-rework-execution.md) §R3/R4), which is a legitimate consequence of the rubric work but **has not been formally accepted** as the new narrative baseline.

## T6 / SP-A wording fixes and FB-LL-06 cross-document consistency

- §4.1 caption disambiguating "Sites in regional top 20" added; §4.2 "Per-Country Top Candidate Sites" caption added.
- Austria Pareto labelled illustrative example in `AT_country_prototype.md` line 51.
- All "924 MWe" / "VOYGR-12" / "12-module" narrative removed from chapter 5 site profiles. `rg "924 MW|VOYGR-12|12-module" report/output/chapters/*.md` returned 0 matches at the time of the rework execution.
- `src/scripts/cross_chapter_numeric_lint.py` plus `tests/scripts/test_cross_chapter_numeric_lint.py` (slow marker) guard the VOYGR-6 capacity and Romania full-pass reconciliation; lint runs clean today against the committed report.

**Verdict:** met. This is the cleanest theme.

## T7 / VOYGR-6 capacity (#119) and T8 / deferred (#72)

- #119 closed via SP-A; #72 explicitly deferred by reviewer and parked in `SP-H_backlog.plan.md`.

## Audit-trail tensions to highlight

Two contradictions and one policy gate from the audit log should be visible in any final conclusion:

1. **HI-01 / HI-06 rubric gap is structural, not incidental.** SP-D Phase 0.6 sign-off for these criteria was conditional on SP-F enrichment landing. SP-F data landed (HI-01 via no-op preview because earlier work was already in sync; HI-06 via three-way verified replay). SP-D HI-01 v2 / HI-06 v2 were **never authored**. Reviewer comments #76, #105, #106, #120, #563, #578, #582 cannot be closed until the rubric consumes the new fields.

2. **`feedback_rerun_20260509` caused full-pass drift that has not been accepted.** Across the 20 countries: 11 full-pass total vs 36 in the canonical anchor `score-214bab4e`. RO loses Turceni / Brăila / Rovinari as leaders. The audit log offers three resumption decisions (A/B/C) and the test render was reverted; no decision is recorded as taken. Any "is the scoring reliable?" answer hinges on this.

3. **No new scoring or sensitivity runs from CLI / agent (user policy).** New runs are GUI-only. Until a fresh GUI run is taken **after** the rubric edits AND the SP-D HI-01/HI-06 v2 bands AND the EPRI weight values are agreed, there is no current persisted scoring run that proves the changes propagate to reviewer-anchored sites.

## Tests confirming source-level acceptance

The audit log records (and the test files match):

- `tests/scoring/` → 89/89 passed (last full run captured in audit log).
- `tests/scripts/test_site_profile_unscored_rendering.py` → 5/5 passed (favorable + pass-mark + unscored branches).
- `tests/scripts/test_cross_chapter_numeric_lint.py -m slow` → 1/1 passed.
- `tests/test_connectors_ourairports.py tests/test_smoke_ourairports.py` → 49/49 passed.

These tests are necessary but not sufficient for "scoring bands are reliable" because they test pure functions and renderer logic, not the cohort behaviour against persisted scoring runs.
