NH-03 — Geotechnical: settlement and liquefaction — §O Pre-edit Analysis
Phase: [exclusionary, ranking] · Primary metric: liquefaction_suscept · E-code: E2 · pass_mark: 5.0 · EPRI step 1 / IAEA NS-R-3 §3.38-3.40 + NS-G-3.6 + SSG-35

1. Decision matrix — was / now
   Two candidate fixes are surfaced (Option A and Option C). Option B is "no change" for comparison. No edit will be made before you pick.

Element WAS (current spec) Option A — conservative no-remedy (SP-D-aligned) Option B — leave as-is Option C — add review_flag, keep E2 narrow
Band [9,10]
liquefaction_suscept in ['very_low', 'none']
(unchanged)
(unchanged)
(unchanged)
Band [7,8]
liquefaction_suscept == 'low'
(unchanged)
(unchanged)
(unchanged)
Band [5,6]
moderate or (high and (has_remedy == true or has_remedy is null)) or (very_high and has_remedy == true)
moderate or (high and has_remedy == true) or (very_high and has_remedy == true) — drop NULL→favorable
(unchanged)
(unchanged)
Band [3,4]
very_high and has_remedy is null
high and (has_remedy == false or has_remedy is null) — high w/o remedy lands here, caught by E2:floor
(unchanged)
(unchanged)
Band [1,2]
liquefaction_suscept in ['high', 'very_high'] and has_remedy == false (never fires in prod)
very_high and (has_remedy == false or has_remedy is null) — caught by hard E2
(unchanged)
(unchanged)
E2 condition_expr
liquefaction_suscept in ['high', 'very_high'] and has_remedy == false
(liquefaction_suscept == 'very_high' and (has_remedy == false or has_remedy is null)) or (liquefaction_suscept == 'high' and has_remedy == false)
(unchanged)
(unchanged)
New R2 review_flag
(none)
(none)
(none)
NEW: liquefaction_suscept in ['high', 'very_high'] and has_remedy is null — analyst-surfaced, no score effect
pass_mark
5.0
5.0 (unchanged)
(unchanged)
(unchanged)
Phases / weight / EPRI step
[exclusionary, ranking] / 7 / step 1
(unchanged)
(unchanged)
(unchanged) 2. Scoring bands (post-change boundary table)
For each option, after the change (or current spec for B). All rows below assume the canonical Zhu-global-1km susceptibility classes (very_low | low | moderate | high | very_high) and the production reality that has_remedy is always None in the scoring context (see §5).

Option A (proposed conservative reviewer-aligned)
Score Matching input (post-change) Effective production routing (has_remedy = NULL)
9-10
very_low, none
unchanged — 137 sites
7-8
low
unchanged — 4 sites
5-6
moderate or `(high
very_high)ANDhas_remedy == true`
3-4
high AND remedy absent/unknown
NEW: 61 high sites → score 3.5 → caught by E2:floor (fail)
1-2
very_high AND remedy absent/unknown
1 very_high site → score 1.5 → caught by hard E2 (fail)
Option B (current, unchanged)
Score Matching input Effective production routing
9-10
very_low, none
137 sites
7-8
low
4 sites
5-6
moderate, or high AND has_remedy is null (charitable)
149 + 61 = 210 sites
3-4
very_high AND has_remedy is null
1 site → caught by E2:floor (fail)
1-2
`(high
very_high)ANDhas_remedy == false`
Option C (add R2 review flag; bands unchanged)
Same as Option B for scoring; additionally R2 analyst flag fires on all 62 high+very_high sites with NULL has_remedy.

3. Transition note
   What changed (Option A): has_remedy is null no longer satisfies the favorable branch; it is now treated as "no remedy" on the unfavorable side. Aligns with LL-029 + FB-LL-08 asymmetric NULL handling and the pre-existing SP-D NH-03 reviewer proposal in report/output/feedback/plans/SP-D_band_proposals/NH-03.md.
   Citation anchor: IAEA NS-R-3 §3.38-3.40 + NS-G-3.6 (mitigation must be demonstrated before a high-susceptibility site is retained) + SSG-35 §3 prohibition framing for liquefaction without remedy. The E2 code remains anchored to those sources.
   System-side honesty mechanism: drift guard runs in criterion_spec.compiler but does not apply here (NH-03 is hand-written, no band_recipe). Honesty is enforced by tests/scoring/test_safety_floor_pipeline.py (E2 and E2:floor cases) plus the new targeted enumeration test (see §5 pending decisions).
   What is NOT changing: primary metric (liquefaction_suscept), weight (7), phases ([exclusionary, ranking]), EPRI step (1), pass_mark (5.0), composite participation (False).
   DB impact (per §K, Option A): 62 sites move from pass to fail across the merged DB (61 hard via E2-on-high-NULL → would actually land at E2:floor for high; 1 already failing for very_high). That is ~17% of the 361-site merged scope — above the §K 5% threshold, so this option requires explicit user approval before any edit. Option C has 0 score impact and only adds an analyst flag. Option B is no-op.
4. Scored examples from the merged DB
   Real engine output from the latest production run (score-d51c7c6b, nuscale_voygr6, 361 sites). The §E7 generator (generate_scoring_examples.py --criterion NH-03) silently omits the very_high row because the script does not invoke merge_context_derivations.apply_derived_context_values before band evaluation, so has_remedy is undefined and no band matches. That is a script-side defect, not a rubric defect; flagged below as a pending follow-up. The table below uses the actual DB-persisted ranking_scores + screening_verdicts rows.

band site_id country name liquefaction_suscept bear_kpa gw_m bedrock_m pga_475 score verdict (WAS) verdict (Option A)
9-10
0ada7b2a
TR
(very_low sample)
very_low
87.30
—
12.60
0.5642
9.5
pass
pass
9-10
992a4bf0
TR
(very_low sample)
very_low
86.00
—
29.81
0.5423
9.5
pass
pass
7-8
fac3d0b5
BY
(low sample)
low
116.00
—
23.39
0.0043
7.5
pass
pass
7-8
55cfe45b
TR
(low sample)
low
88.70
—
21.18
0.2425
7.5
pass
pass
5-6
43e5b2b4
CZ
(moderate sample)
moderate
60.00
—
23.12
0.0487
5.5
pass
pass
5-6
ca423571
TR
(moderate sample)
moderate
83.30
—
16.42
0.1677
5.5
pass
pass
5-6
6e7fc4d8
AT
Duernrohr power station
high
84.70
—
31.75
0.0867
5.5
pass
fail (E2:floor @ 3.5)
5-6
344e0e9a
BA
Kamengrad Thermal Power Plant
high
85.30
—
23.13
0.1249
5.5
pass
fail (E2:floor @ 3.5)
3-4
e6ecead0
AL
Porto Romano Power Station
very_high
68.50
—
21.55
0.3930
3.5
fail (E2:floor)
fail (hard E2 @ 1.5)
1-2
(none)
—
—
—
—
—
—
—
—
—
— 5. Pending decisions (require user sign-off before any edit)
PD-NH03-A — Charitable vs. conservative has_remedy is null. Production has no has_remedy data field; the column is hard-defaulted to None in merge_context_derivations.\_derive_site_screening_flags. The current rubric therefore treats unknown-remedy as effectively present, and 61 high susceptibility coal sites pass at exactly 5.5. The hard E2 (... and has_remedy == false) has fired 0 times in the latest run; only the E2:floor has caught the lone very_high site (AL, Porto Romano). Pick one:

Option A — conservative (SP-D NH-03 proposal, LL-029 asymmetric NULL): high+NULL → 3.5 (E2:floor), very_high+NULL → hard E2. 17 % reclassification.
Option B — keep as-is. The 61 high sites remain unscreened; the criterion ships an E2 that cannot fire in production.
Option C — add R2 review_flag for (high|very_high) and has_remedy is null. Zero score impact; preserves the current charitable bands but surfaces the gap to analysts.
PD-NH03-B — Acceptance of the §K dry-run impact under Option A. Newly hard-failed > 0 and > 5 % of sites reclassified; per §K this requires explicit prior approval. Affected countries: TR (12 high), PL (11), RO (8), CZ (6), BG (6), HU (5), SK (4), RS (3), AT (2), HR (1), BA (1), UA (1), XK (1), AL (1 very_high).

PD-NH03-C — Treat has_remedy as a future evaluable field? Today no connector populates remedy evidence; the LLM block nh03_liquefaction_text is the only narrative carrier. If the project wants has_remedy to ever resolve to a positive value, a connector or LLM-derived enrichment must populate it — that is out of scope for this criterion sweep but pertinent to PD-NH03-A: if remedy evidence will likely remain absent across the DB indefinitely, Option A is materially equivalent to "exclude all high+ susceptibility coal sites" for the foreseeable future.

PD-NH03-D — Generator quirk (out-of-scope follow-up). src/scripts/generate_scoring_examples.py does not apply merge_context_derivations.apply_derived_context_values before scoring, so it silently drops the only very_high site for NH-03 (the band-[3,4] row). Pre-existing defect; flagged here so it doesn't poison future §E7 outputs. Fix is a one-call insertion in \_pick_band_samples / \_fetch_contexts. Not bundled into the NH-03 rubric change.

PD-NH03-E — Threshold metadata. NH-03 is not in config/scoring_specs/threshold_metadata.yaml (categorical pivot, no numeric knob). No change needed under any option. Confirmed.

Status: Analysis complete; awaiting your decision on PD-NH03-A (+ PD-NH03-B if you pick Option A) before any YAML edit, test, doc regeneration, or audit-log step.

NH-03 §O pre-edit analysis is complete and posted above. Key findings:

Critical false-negative: has_remedy is hard-defaulted to None in src/atoms_vs_ashes/scoring/merge_context_derivations.py:339. The E2 hard expression (... and has_remedy == false) has therefore fired 0 times in the latest production run; only the E2:floor has caught the lone very_high site (Porto Romano, AL).
61 high susceptibility coal sites currently pass at exactly 5.5 with no documented mitigation evidence (AT 2, BA 1, BG 6, CZ 6, HR 1, HU 5, PL 11, RO 8, RS 3, SK 4, TR 12, UA 1, XK 1).
A prior SP-D NH-03 reviewer-aligned proposal (report/output/feedback/plans/SP-D_band_proposals/NH-03.md) and LL-029 already document the asymmetric NULL fix but it was never landed.
Three options surfaced (conservative no-remedy / no change / add review_flag); Option A requires explicit user approval because it reclassifies ~17 % of the merged DB.
No YAML edits performed — awaiting your sign-off on PD-NH03-A (and PD-NH03-B if Option A).
