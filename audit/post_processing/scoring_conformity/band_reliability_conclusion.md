<!-- man_hours: 0.6 -->
# Band reliability conclusion

## Question

The two questions the assessment was asked to answer:

1. Have Ovidiu Coman's scoring-related comments been implemented?
2. Are the current scoring bands reliable as applied to persisted scoring results?

## Final rating

**Conditionally reliable / partially implemented.**

- Scoring definitions are materially improved at the config and renderer level (see [`implementation_audit.md`](implementation_audit.md)).
- A current persisted scoring run **exists** (`20260513T030738_70d5bc2c`, May 13) and is the one this assessment evaluated. Despite that, the run still does not satisfy reviewer expectations at the anchor sites for the majority of the scoring-related comments.
- Three structural blockers prevent a higher rating: an unresolved rubric defect in HI-01 / HI-06, an engine / data-path issue that prevents favorable branches from firing for several criteria, and unaccepted full-pass drift in the cohort.

## Per-comment status (counts)

From [`ovidiu_comment_conformity.md`](ovidiu_comment_conformity.md):

| Status | Count | Share |
|---|---:|---:|
| implemented | 25 | 56 % |
| partially_implemented | 12 | 27 % |
| not_implemented | 3 | 7 % |
| needs_clarification | 2 | 4 % |
| not_applicable_ack | 2 | 4 % |
| deferred_by_reviewer_or_policy | 1 | 2 % |
| **total** | **45** | 100 % |

Of the 27 reviewer comments whose intent maps to a scoring or rubric change, fully **half** are partial or not implemented. Wording / cross-document / methodology fixes are nearly all closed; **the unresolved cluster is the scoring band intent at the anchor sites the reviewer used as exemplars**.

## What is reliable

- T4 / Stage 1 vs Stage 2 boundary documentation in chapter 3 (FB-LL-04).
- T4 / RI-04 dual-mode methodology and rubric notes (FB-LL-05).
- T6 / SP-A wording captions, illustrative-example labelling, table titles.
- T7 / VOYGR-6 capacity narrative + cross-chapter numeric lint (FB-LL-06).
- T3 / Renderer no longer asserts a numeric score with "no evidence" — at code + test level (FB-LL-02 partial; profile regeneration deferred).
- T2 / FB-LL-01 favorable-band rubric edits **as YAML**: NH-03, NH-04, NH-05, NH-07, NH-08, NH-09, NH-13, NH-14, HI-02, HI-04, HI-05, HI-08 all carry the correct favorable branch.
- T5 / FB-LL-03 connector enrichment: airport_class and military_class data populated for 100 % of sites; HI-06 fix04 replay verified.
- T1 / FB-LL-09 EPRI weight basis: config + engine wired; baseline-vs-EPRI artefact published.

## What is not yet reliable

1. **HI-01 high-band AND-clause (FB-LL-08).** Rubric `[9,10]` still reads `nearest_airport_km > 30 AND nearest_military_airfield_km > 60`. Missing military-airfield data drops favorable airport situations to pass-mark. 0 of 361 sites get the favorable branch. Reviewer comments #105, #106, #578 unresolved at scoring time. SP-D HI-01 v2 was explicitly deferred pending SP-F airport-class consumption; SP-F enrichment landed; SP-D HI-01 v2 was never authored.

2. **HI-06 rubric does not consume SP-F classification fields.** `nearest_military_class`, `nearest_high_consequence_military_km` populated for 361 sites (37 high-consequence). Rubric HI-06 still uses `nearest_military_km` + legacy `military_type`. Reviewer comments #120, #563, #582 unresolved at scoring time.

3. **Engine / data-path: favorable branches not firing.** For HI-02 / HI-04 / HI-05 / HI-08 / NH-07 / NH-08 / NH-13 the rubric carries the correct favorable branch but it fires for **0–9 sites of 361**. Either the underlying connector data is not produced, the quality / sentinel context is not derived at score time, or the country dimension (`country_is_landlocked`) is not joined into the score evaluator. At the three anchor sites this means reviewer-expected scores stay at 5.0 unscored despite the rubric being correct.

4. **NH-11 framing mismatch.** Reviewer's "low extreme daily precipitation = favorable" does not map to the rubric's "optimal annual precipitation 400–800 mm". `extreme_precip_mm` is declared but not consumed. NH-11 mean is **4.0** flat across all 361 sites in every run.

5. **EP-01 direction reversal.** Re-banded thresholds map Timelkam's 44/100 composite to `[3,4]` rather than the reviewer's hoped-for "higher than 5.5". Cohort EP-01 mean dropped from 5.19 (canonical) to 3.14 (latest).

6. **Full-pass drift (-69 %) not accepted.** Canonical 36 → latest 11; RO 3 → 0; HU 2 → 0; HR 1 → 0; SK 1 → 0. New `:floor` exclusion rules at `E2:floor`, `E3:floor`, `E4:floor`, `E_RI04:floor` produce 549 new exclusionary fail rows. The rework-execution audit log records three resumption options (A: accept and regenerate, B: roll back floor mechanism, C: pin to canonical anchor); none has been signed off.

7. **No sensitivity / Monte-Carlo run for the new rubric.** Latest scoring snapshot `scdef-85e7a461ec02b7d6` has no paired sensitivity run. Without that, A–H stability bands cannot be characterised against the new rubric, and reviewer #117 / #72 deferred-rebalancing readiness cannot be evaluated.

8. **EPRI weight-basis provenance is not visible per criterion in the rendered profile.** Reviewer #77 still cannot be answered from the report alone; out-of-band reference to `config/epri/weights.yaml` is required. SP-G renderer change to emit `(basis: epri | baseline)` per bullet was scoped but is not in the renderer code.

## Required actions before "Reliable" can be claimed

In rough order of effort, with explicit acceptance criteria.

1. **Author SP-D HI-01 v2 and SP-D HI-06 v2 bands** that consume the SP-F enrichment fields.
   Acceptance: rubric `[9,10]` for HI-01 reads `nearest_airport_km > 30 and (nearest_military_airfield_km > 60 or nearest_military_airfield_km is null) and nearest_airport_class != 'large_intl'`; rubric HI-06 references `nearest_military_class` / `nearest_high_consequence_military_km`. Score regression covers Timelkam, Brăila, Riedersbach producing favorable HI-01 and HI-06 where reviewer expected.

2. **Fix the favorable-branch firing gap** for HI-02, HI-04, HI-05, HI-08, NH-07, NH-08, NH-13. Root-cause whether the `*_search_completed` flag, `country_is_landlocked`, or the `is null` check are reaching the band evaluator. Probably one of: connector did not populate the quality column, `merge_context_derivations.apply_derived_context_values` is skipping the criterion, or `country_is_landlocked` is not in the per-site context. Acceptance: at three anchor sites, the favorable branches fire and produce scores in `[8,10]` consistent with FB-LL-01 acceptance.

3. **Address NH-11 framing.** Either consume `extreme_precip_mm` in a fourth sub-score (favorable when low) or document explicitly that NH-11 scores climate-typical precipitation and that reviewer comments #100 / #573 require a separate "tornado / extreme weather" criterion. Either way, NH-11 mean should not be 4.0 flat across all 361 sites.

4. **Decide on EP-01 direction.** Either accept the re-banded bands as authoritative and update the chapter narrative to show Timelkam at 3.5 (severe penalty), or re-band so 44/100 produces a score consistent with reviewer's "higher than 5.5" expectation.

5. **Take a decision on full-pass drift.** The rework-execution audit log already lays out options A / B / C. The longer this stays open the harder it is to make any cohort-level reliability claim because the canonical and post-rubric runs disagree on which sites pass.

6. **Surface EPRI weight basis per criterion bullet** in the rendered profile (FB-LL-09 acceptance).

7. **Run sensitivity / Monte-Carlo against the new rubric** (`sens-*` paired with `20260513T030738_70d5bc2c`) so A–H stability bands can be characterised. GUI-only per project policy.

8. **Regenerate site profiles** for the anchor sites (and ideally all 361) so the renderer fixes propagate to chapter 5. LLM-gated; needs user consent.

Once 1–5 are closed and a paired sensitivity run is taken, the assessment can be re-run and the rating revisited.

## Honest one-line answer to the user's question

> *"We have implemented more sensible scoring bands and Ovidiu's comments have now actually been implemented."*

Partial. The YAML and methodology say yes for most of the comments; the persisted scoring results say no for the comments that actually defined the original problem (HI-01, HI-06, and the family of sentinel-branch criteria that still default to 5.0 at the anchor sites). The new bands are more conservative and better designed, but at the moment they discriminate by **excluding** sites rather than by **scoring favorable sites higher**, which is the opposite of what the reviewer asked for.
