# Suitable Sites Scoring Audit

## Scope

This report audits every live exclusionary and avoidance rule from the scoring rubrics.
Each rule was checked for threshold metadata, band/evaluator wiring, DB-field availability,
and current run impact where a scoring run was available.

## Suitability Definition

- Run: `20260425T140231_ff84d75e` with weight profile `baseline`.
- Total site-SMR pairs: 2904 across 363 sites and 20 countries.
- Hard-exclusion pass: 208 pairs, 26 sites, 5 countries.
- UI survivor pass (`passed_exclusionary AND passed_avoidance`): 56 pairs, 7 sites, 3 countries.
- Hard-failed pairs: 2696; avoidance-flagged-but-rankable pairs: 152.

Audit decision: avoidance cautions should be displayed separately from hard unsuitability.
The current shortlist may still require both flags, but labels must not call avoidance flags safety-floor failures.

## E/A Catalogue Audit

- Exclusionary rules audited: 10.
- Avoidance rules audited: 16.
- Rules with DB/context wiring risks: 16.

Highest-priority wiring findings:
- `EP-01/E8`: missing model fields site_emergency.nearest_hospital_km, site_emergency.nearest_trauma_center_km.
- `NH-03/E2`: missing context has_remedy.
- `NH-07/E4`: missing context in_pyroclastic_zone.
- `NH-10/project_wind_envelope`: missing model fields site_natural_hazards.extreme_wind_ms.
- `NS-01/E9`: missing context dry_cooling_viable; missing model fields site_natural_hazards.spi12_min.
- `HI-01/A1`: missing model fields site_human_induced.nearest_military_airfield_km.
- `HI-01/A2`: missing model fields site_human_induced.nearest_military_airfield_km.
- `HI-01/A3`: missing model fields site_human_induced.nearest_military_airfield_km.
- `HI-01/A4`: missing model fields site_human_induced.nearest_military_airfield_km.
- `HI-02/A7`: missing model fields site_human_induced.nearest_ied_km.
- `HI-03/A8`: missing model fields site_human_induced.toxic_source_type.
- `HI-06/A5`: missing model fields site_human_induced.military_type.

## Full E/A Audit Checklist

- Hard exclusionary rules: 10; synthetic safety floors: 10.
- Avoidance rules: 16.
- Full per-item decisions are written to `audit_status.csv`.
- Exclusionary failures remain hard-unsuitable unless a data-application defect is listed.
- Avoidance cautions are risk flags/ranking pressure and are reported separately from hard unsuitability.

## EP-01/E8 Disjunct Audit

- `composite_score_lt_30`: 456 rows, 57 sites, 11 countries.
- `no_failure_or_missing_trauma_distance`: 2448 rows, 306 sites, 20 countries.

Audit decision: EP-01/E8 threshold intent is internally consistent at `ep01_composite_score < 30`; current stored verdicts also expose that trauma-centre distance is absent for many rows, so E8 disjunct reporting must use measured JSON rather than the scalar export threshold.

## Focused High-Impact Blockers

- `NH-05` rules: E5: context=ok; model=ok | E6: context=ok; model=ok; current impacts: E5/pass=2896 | E6/pass=2104 | E5:floor/fail=824 | E6/fail=800 | E6:floor/fail=32 | E5/fail=8.
- `NH-04` rules: E3: context=ok; model=ok; current impacts: E3/pass=2880 | E3:floor/fail=1288 | E3/fail=24.
- `NH-02` rules: E1: context=ok; model=ok; current impacts: E1/pass=2504 | E1/fail=400 | E1:floor/fail=304.
- `NS-08` rules: E7: context=ok; model=ok; current impacts: E7/inconclusive=2904 | E7:floor/fail=32.

Audit decision: NH-02, NH-04, and NH-05 have coherent thresholds and live DB fields; their large impact is not explained by field-name drift. NS-08 now has a derived strict-protected flag from zero-distance protected area hits, but source coverage still needs domain review.

## Current Run Impact

Top triggered verdict groups:
- `A11` avoidance/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `NH-09`.
- `A12` avoidance/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `RI-05`.
- `A3` avoidance/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `HI-01`.
- `A4` avoidance/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `HI-01`.
- `A9` avoidance/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `NH-08`.
- `E4` exclusionary/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `NH-07`.
- `E7` exclusionary/inconclusive: 2904 rows, 363 sites, 20 countries, criteria `NS-08`.
- `E9` exclusionary/pass: 2904 rows, 363 sites, 20 countries, criteria `NS-01`.
- `NH-10` exclusionary/pass: 2904 rows, 363 sites, 20 countries, criteria `NH-10`.
- `A14` avoidance/pass: 2896 rows, 362 sites, 20 countries, criteria `NS-03`.
- `E2` exclusionary/pass: 2896 rows, 362 sites, 19 countries, criteria `NH-03`.
- `E5` exclusionary/pass: 2896 rows, 362 sites, 20 countries, criteria `NH-05`.
- `E3` exclusionary/pass: 2880 rows, 360 sites, 20 countries, criteria `NH-04`.
- `A7` avoidance/inconclusive: 2840 rows, 355 sites, 20 countries, criteria `HI-02`.
- `A2` avoidance/pass: 2816 rows, 352 sites, 20 countries, criteria `HI-01`.

## Ranking Score Diagnostics

Criteria with unscored or insufficient rows: 31.
- `BF-01`: 0 unscored, 2904 insufficient out of 2904 rows.
- `BF-02`: 48 unscored, 2904 insufficient out of 2904 rows.
- `EP-03`: 2904 unscored, 0 insufficient out of 2904 rows.
- `EP-04`: 2904 unscored, 0 insufficient out of 2904 rows.
- `EP-05`: 2904 unscored, 2904 insufficient out of 2904 rows.
- `HI-02`: 2840 unscored, 0 insufficient out of 2904 rows.
- `HI-03`: 2240 unscored, 0 insufficient out of 2904 rows.
- `HI-04`: 2840 unscored, 0 insufficient out of 2904 rows.
- `HI-05`: 2904 unscored, 2904 insufficient out of 2904 rows.
- `HI-06`: 336 unscored, 0 insufficient out of 2904 rows.
- `HI-07`: 2904 unscored, 0 insufficient out of 2904 rows.
- `HI-08`: 2904 unscored, 2904 insufficient out of 2904 rows.

## Audit Status

- Every E-code and A-code has a catalogue row in `ea_catalogue.csv`.
- Codes with DB/context risks require either a resolver alias, a derived context value, or connector/schema enrichment.
- EP-01/E8 should be reviewed with the full measured JSON; scalar exports are not enough to distinguish the composite-score and trauma-centre disjuncts.
- Avoidance cautions are rankable risk flags unless the project explicitly chooses a shortlist definition that requires `passed_avoidance`.

