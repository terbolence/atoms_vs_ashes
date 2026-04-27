Proposal — Results page (5 scoring tools + 3 sensitivity tools)

> **Implementation note (post-fix correction).** The earlier draft of
> this spec listed `failure_outcomes` as a primary data source for tools
> 2 and 3. That table is **post-processing-only** — it is written by
> `src/scripts/_phase_1_6_failure_db.py`, never by the live engine, so
> a fresh GUI run produces zero rows there. In the implementation we
> instead derive pass / hard-fail / floor-fail status live from
> `composite_rankings.passed_exclusionary` / `.passed_avoidance`
> (engine-written), joined with `screening_verdicts` (`verdict='fail'`)
> and the rubric flags (`Criterion.is_exclusionary` /
> `is_avoidance`). This keeps the tools usable immediately after a
> scoring run with no separate post-processing step. The
> `failure_outcomes` table remains a valid offline enrichment when the
> post-processing pipeline is run.

Page-level orchestration:

One sticky control row on top: run picker · country picker (defaults All) · "include eliminated sites" toggle. The country picker is shared by all scoring tools below, so picking Romania once cascades everywhere.
Single SMR auto-collapse: when the run has one smr_key, hide that column / colour everywhere.
Scoring — 5 tools
Run KPI strip — "is this run useful?"

Sites in scope · survivors (excl + avoid) · hard-failed · avoidance-failed · countries-with-≥1-survivor / total countries · median composite (survivors).
Data: dataset_snapshot + composite_rankings.
Widget: 6 × st.metric.
Country coverage matrix — the master view: where do I have/lack viable sites?

One row per country: # sites · # survivors · # near-miss (gap ≤ 25 % on ≤ 2 floor criteria) · # deep-fail · max composite among survivors · min gap among non-survivors.
Survivor cell coloured green / amber (only near-misses) / red (zero coverage). Click a row → sets the page-level country picker.
Data: composite_rankings + screening_verdicts + failure_outcomes.
Widget: st.dataframe with column_config (ProgressColumn for survivors, color-coded text for status).
Country site ledger — for the chosen country, every site listed.

Columns: rank · site name · status badge (✅ pass / 🟧 floor-fail / 🟥 hard-fail) · composite (ProgressColumn 0–10) · MC band (low–high) · # failed criteria · top-blocking criterion · worst gap %.
st.dataframe with selection enabled — selecting a row drives tool #4.
Data: composite_rankings + failure_outcomes + screening_verdicts (gap = measured_value_numeric − threshold_numeric).
Site detail drawer (drill-down — answers "why and by how much")

Header: name · lat/lon · country · status · capacity · composite + MC band.
Failed-criteria cards (red strip = exclusionary, amber = avoidance): criterion · measured + units · threshold · gap (raw + %) · justification. Tiny inline gauge showing measured-vs-threshold position.
Strengths cards (green strip): criteria scored ≥ 8 with one-line justification.
Per-criterion bar (all ranking_scores for the site, coloured by family, pass-mark line at 5.0).
Per-family contribution stack (one row from composite_score_components) — shows whether the site wins broadly or is propped up by one family.
Data: screening_verdicts, ranking_scores, composite_score_components.
Regional shortlist + geo map — cross-country comparison & geographic context.

Horizontal bar of top-N sites by composite, error bars from MC bands, coloured by country. Filterable by only-passed, limit slider.
Side-by-side st.pydeck_chart: marker colour = composite quartile (or A-H band when sensitivity exists), marker size = composite, greyed-out for excluded; tooltip shows country, composite, top-3 weakest criteria. Filters mirror the bar chart.
Data: composite_rankings + Site.latitude/longitude.
Sensitivity — 3 tools
Site stability ledger (band A–H)

One row per site: country · band · composite (mean from MC) · MC low–high · top-5% / top-10% / top-30% hit rate · # profiles in which it stayed in top-N. Filter by band.
"Robust shortlist" = bands A/B; "cliff-edge" = D-H.
Data: site*bands + composite_rankings (mc* / weight-perturbation profiles).
Widget: st.dataframe + bar of band counts.
Rank stability heatmap — site × weight_profile

Y: top-25 sites under baseline (or country*balanced). X: each weight_profile (baseline, country_balanced, w*<crit>_<dir>, threshold_<dir>\_25). Cell = rank_position or rank-delta vs baseline (diverging palette).
Flat horizontal rows = robust; rainbow rows = fragile. The single best "is the ranking trustworthy?" diagnostic.
Data: composite_rankings joined across profiles.
Threshold sweep (site impact)

Per-criterion expander, ±25 %: list the named sites that enter (survivors*added) and exit (survivors_removed) the survivor set. Companion bar of # sites added / removed per criterion sorted by absolute impact.
Tells you exactly which threshold change unlocks specific sites — directly actionable for the next iteration.
Data: threshold_sensitivity + composite_rankings filtered to weight_profile = threshold*<dir>_25.
Cross-cutting (one extra worth keeping)
Run-vs-run diff — pick a second baseline run, see entered / left top-20 + per-country survivor delta. Catches "did last week's threshold change help or hurt coverage?". Optional, single st.expander.
Implementation order if you want a phased rollout
Phase 1 (the workshop-ready set): tools 1, 2, 3, 4 — lets you "pick country → see fails → see why" end-to-end.
Phase 2: tools 5 (regional context) + 6 (site stability) — adds region-wide and robustness views.
Phase 3: tools 7, 8, 9 — deeper diagnostics.
Each tool maps to one \_results_\*.py module with one DB-data helper + one renderer, keeping files under the 300-line cap.

Switch to Agent mode and I'll fix the SMR-scope bug first, then build Phase 1 (tools 1–4).
