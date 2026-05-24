<!-- man_hours: 4.6 -->
# Annex E: Assumption Register and Data Limitations

**What this annex adds.** Annex E carries the report-facing assumption register and evidence limitation catalogue. Chapter 2 Section 2.3 describes the evidence base at family level; Chapter 4 Section 4.5 summarises uncertainty in the results; Chapter 5 site profiles carry site-specific residual-risk entries. Annex E gives the stable assumption IDs that tie those discussions together.

## Reading the register

Every numerical answer in the study rests on a subset of the assumptions below. Each entry carries:

- **ID:** a stable handle for audit and review.
- **Domain:** the pipeline stage or criterion family the assumption constrains.
- **Statement:** the load-bearing claim.
- **Impact if wrong:** how the headline interpretation would change if the assumption fails.
- **Mitigation:** how the project guards against the risk.

The register is versioned with the rubric. Any rubric change should update or add an assumption.

## Scope assumptions

### A-SCOPE-01: Pre-screening only, not detailed siting

- **Domain:** entire assessment.
- **Statement:** every result is fit for Stage 1 and Stage 2 pre-screening, long-listing, short-listing, and comparative ranking. Detailed siting requires site walks, geophysical campaigns, PSHA and PFDHA, and regulator-led environmental assessment.
- **Impact if wrong:** users could mistake a robust screening candidate for an approved site.
- **Mitigation:** every relevant report surface states the Stage 1 and Stage 2 scope; Annex A marks each SSR-1 Requirement with an explicit coverage label.

### A-SCOPE-02: Climate-change horizon out of scope

- **Domain:** climatological criteria, including river flooding, extreme winds, extreme precipitation, extreme temperatures, and atmospheric dispersion.
- **Statement:** hazards use historical climatology for the latest available reference period. Long-term climate scenarios are not applied at this stage.
- **Impact if wrong:** sites near flood, heat, precipitation, or dispersion band boundaries could move by one scoring band under a late-century horizon.
- **Mitigation:** threshold perturbation in Annex C acts as a first-order proxy, and site-specific climate studies remain a Stage 3 follow-up.

### A-SCOPE-03: Current country roster

- **Domain:** site universe.
- **Statement:** the candidate-site population is restricted to the countries defined in the published report roster (16 in-scope countries plus the three consolidated no-pass portfolios) and supporting methodology artefacts.
- **Impact if wrong:** results would not claim completeness for countries outside the roster.
- **Mitigation:** country scope is stated in the main report and country-profile chapter.

## Evidence-architecture assumptions

### A-DATA-01: Structured public evidence hierarchy

- **Domain:** every field used in scoring.
- **Statement:** structured public evidence and first-party national or institutional records are preferred when available; curated public-evidence collection is used only to fill gaps where structured evidence is absent or incomplete.
- **Impact if wrong:** a score could depend too strongly on weak public evidence.
- **Mitigation:** scored rows carry evidence-quality fields, and low-confidence rows receive wider uncertainty treatment in the national Monte Carlo analysis.

### A-DATA-02: Single scoring evidence base

- **Domain:** scoring engine.
- **Statement:** scoring reads from one reconciled evidence base rather than mixing unreconciled source layers at scoring time.
- **Impact if wrong:** silent divergence between evidence layers could change scores.
- **Mitigation:** scoring outputs retain provenance and quality flags for review.

### A-DATA-03: Site geometry is a single representative point

- **Domain:** distance-based criteria.
- **Statement:** each site is represented by one latitude-longitude point at Stage 1 and Stage 2 resolution.
- **Impact if wrong:** very large host sites could have emergency-planning or hazard buffers that differ from the point-based screen.
- **Mitigation:** Stage 3 recomputes against the actual containment, laydown, cooling, and access geometry.

## Rubric and scoring assumptions

### A-RUBRIC-01: 0-10 ranking scale with uncertainty for low-quality rows

- **Statement:** every criterion produces a continuous 0-10 score. Rows marked as lower quality receive a wider Monte Carlo uncertainty band than high-quality rows.
- **Impact if wrong:** stability could be overstated for candidates with weak evidence.
- **Mitigation:** declared evidence quality is stored and carried into the national sensitivity analysis.

### A-RUBRIC-02: Hard safety floor at 5.0 for exclusionary criteria

- **Domain:** NH-02, NH-03, NH-04, NH-05, NH-07, NH-10, EP-01, NS-01, and NS-08.
- **Statement:** any site whose ranking score falls strictly below 5.0 on an exclusionary criterion is removed from composite ranking.
- **Impact if wrong:** the ranking could admit sites with critical weaknesses.
- **Mitigation:** Annex B documents the floor rules, and Annex D shows the resulting failure modes.

### A-RUBRIC-03: Failed sites keep their 0-10 scores for transparency

- **Statement:** sites that fail a hard E-code or safety floor still carry per-criterion scores in the audit evidence, but their composite ranking score is not used for shortlisting.
- **Impact if wrong:** ranking would not change, but review transparency would be weaker.
- **Mitigation:** failure-mode outputs keep the mechanism and criterion evidence visible.

### A-RUBRIC-04: Per-criterion weights are interpreted as decision importance

- **Statement:** published weights represent relative decision importance after normalisation.
- **Impact if wrong:** a criterion with little observed score variation could appear more influential than it is.
- **Mitigation:** the swing-weight audit checks whether declared importance matches discriminating power.

## Sensitivity assumptions

### A-SENS-01: Plus-or-minus-20 per cent category-weight envelope

- **Statement:** each criterion family can be perturbed by plus or minus 20 per cent for robustness testing.
- **Impact if wrong:** wider envelopes would expose more borderline candidates as unstable.
- **Mitigation:** the sensitivity suite is parameterised so the envelope can be widened in a later review cycle.

### A-SENS-02: 50,000 national Monte Carlo iterations

- **Statement:** the national sensitivity analysis (run `nat-sens-b1a62885`, stamp `20260523`, parent scoring run `score-c2a90942`) uses 50,000 Monte Carlo iterations for national rank-probability outputs.
- **Impact if wrong:** top-rank and top-five probabilities could carry unnecessary sampling noise.
- **Mitigation:** the fixed seed and deterministic sampling scheme make the analysis reproducible.

### A-SENS-03: Pair-specific seed equals 42

- **Statement:** each Monte Carlo draw is seeded deterministically from the site and reference-case pair with seed 42.
- **Impact if wrong:** reproduction failures would be detected by rerun comparison.
- **Mitigation:** the seed is fixed and documented in Annex C.

### A-SENS-04: Criterion-pair correlation flag at absolute correlation of 0.70

- **Statement:** any pair of criteria with Pearson or Spearman correlation of 0.70 or above is flagged for review.
- **Impact if wrong:** the scoring framework could double-count an evidence axis.
- **Mitigation:** the criterion-correlation artefact documents flagged pairs and reviewer decisions.

## Reporting and scope-management assumptions

### A-REPORT-01: Country shortlist sizing

- **Statement:** each country ranks at least the top 10 sites where enough sites exist; smaller countries rank all available candidates.
- **Impact if wrong:** small countries may not support statistically meaningful long-list slices.
- **Mitigation:** Chapter 5 country profiles explain small-pool limits where relevant.

### A-REPORT-02: Aligned methodology artefacts

- **Statement:** methodology, sensitivity, failure-mode, and report outputs should be aligned to the same frozen scoring and national sensitivity basis.
- **Impact if wrong:** reviewers could read outputs that do not share the same analytical basis.
- **Mitigation:** Annex F lists the generated methodology artefacts and maintenance notes.

### A-REPORT-03: Out-of-scope items are recorded, not hidden

- **Statement:** any SSR-1 Requirement the project does not cover is listed in Annex A with an explicit out-of-scope label and rationale.
- **Impact if wrong:** the report could imply broader coverage than the Stage 1 and Stage 2 method supports.
- **Mitigation:** Annex A preserves the full Requirement-level traceability matrix.

## Evidence-source limitation catalogue

The evidence categories below are the sources that shape scoring confidence. The report describes them by data family rather than by source-platform name.

| Evidence category | Domain | Resolution or scope | Screening caveat |
| --- | --- | --- | --- |
| Seismic and capable-fault hazard layers | PGA, fault proximity, and geotechnical proxies | Continental or national grid and vector products | Stage 3 requires site-specific PSHA, PFDHA, and geotechnical ground-truthing. |
| Meteorological and climatological records | Wind, temperature, precipitation, and dispersion proxies | Gridded and national-station reference periods | Screening wind and precipitation values are relative indices for ranking. Implausibly low precipitation or wind values must be reconciled with national meteorological records before design-basis use. |
| Flood-hazard and hydrological records | River, coastal, surge, and cooling-water context | National and continental hazard layers | Dam-break, combined-event, and design-basis flood studies are Stage 3 tasks. |
| Land-cover and land-use inventories | Land availability, zoning, industrial context, and buildable-area proxies | Parcel, raster, or national land-use products where available | Industrial classification does not prove permitted, contiguous, or controlled land. |
| Protected-area and ecological inventories | Non-radiological environmental constraints | National and international protected-area records | Legal significance depends on national practice and project-specific assessment. |
| Population and settlement grids | EPZ population density, large-centre proximity, and projection proxies | Gridded population surfaces and national statistics where available | Stage 3 requires census, municipal planning, and evacuation-time evidence. |
| Open infrastructure and transport inventories | Roads, rail, ports, airports, military facilities, and industrial hazards | Public mapping and institutional records | Absence of a mapped feature does not prove absence in reality. |
| Thermal-plant and grid inventories | Candidate-site identification, plant status, grid context, and reuse potential | Public plant records and TSO disclosures | Retirement status, grid capacity, and ownership require national confirmation. |
| Conflict and territorial-status records | War-context and control-of-terrain caveats | Dated public evidence | Any site progression depends on updated legal, security, and infrastructure conditions at the time of review. |

## Country-specific data limitations

| Country | Caveat |
| --- | --- |
| Ukraine (UA) | War-context caveat. Any site progression depends on territorial stabilisation, updated infrastructure-condition evidence, and national authority review. |
| Moldova (MD) | Single-site evidence makes the national narrative sensitive to cross-border cooling-water, grid, and emergency-planning assumptions. |
| Kosovo (XK) | Political-status and data-availability caveats apply; the local failure artefact shows no surviving NuScale VOYGR-6 candidate. |
| Turkey (TR) | The site universe is large and geographically varied; national authority engagement is central to validating grid, emergency-planning, and infrastructure proxies. |

## Evidence basis

This annex is drawn from the project-wide assumption register and the evidence-base summaries used by Chapters 2, 4, and 5. The generated source artefact is listed in Annex F.
