# Annex E: Assumption Register and Data Limitations

**What this annex adds.** Annex E carries the line-item assumption register and the per-dataset limitation catalogue that the main report summarises but does not reproduce. Chapter 2 §2.3 describes the evidence base at family level; Chapter 4 §4.5 summarises the uncertainty areas in a five-row table; the Chapter 5 site profiles carry site-specific residual-risk entries. Annex E lists every load-bearing assumption by ID and every authoritative dataset by name.

## Reading the register

Every numerical answer in the study rests on a subset of the assumptions below. Each entry carries:

- **ID** — a stable handle cited from code, audit reports, and reviewer responses.
- **Domain** — the pipeline stage or criterion family the assumption constrains.
- **Statement** — the load-bearing claim.
- **Impact if wrong** — a qualitative statement of how the headline rankings would shift if the assumption fails.
- **Mitigation** — how the project guards against the risk.

The register is versioned with the rubric. Any rubric change must update or add an assumption; the audit pack does not pass review with a silent change.

## Scope assumptions

### A-SCOPE-01 — Pre-screening only, not detailed siting

- **Domain:** entire pipeline.
- **Statement:** every result is fit for pre-screening (long-list or short-list) and not for permit-quality detailed siting. Detailed siting requires site-walk surveys, geophysical campaigns, deterministic probabilistic seismic hazard assessment (PSHA) and probabilistic fault displacement hazard assessment (PFDHA), and a regulator-led environmental impact assessment.
- **Impact if wrong:** users mistake a Band A site for an approved site.
- **Mitigation:** screening-only language in every per-country profile; the SSR-1 traceability matrix in Annex A marks every Requirement with an explicit coverage label.

### A-SCOPE-02 — Climate-change horizon out of scope

- **Domain:** ranking criteria with climatological inputs (NH-09 river flooding, NH-10 extreme winds, NH-11 extreme precipitation, NH-12 extreme temperatures, RI-01 atmospheric dispersion).
- **Statement:** hazards use historical climatology for the last available reference period. Projected emissions scenarios are not applied at this stage.
- **Impact if wrong:** sites near flood or heat hazard band boundaries could move plus or minus one band under a late-century horizon.
- **Mitigation:** flagged as a Stage 3 follow-up; the threshold-perturbation sensitivity component in Annex C acts as a first-order proxy for shifted climatology.

### A-SCOPE-03 — Region: 17-country pan-European study area

- **Domain:** site universe.
- **Statement:** the candidate-site population is restricted to AT, BA, BG, BY, CZ, HR, HU, LV, MD, ME, MK, PL, RO, RS, SK, TR, UA.
- **Impact if wrong:** none for in-scope ranking; the study does not claim regional completeness for any other country.
- **Mitigation:** every regional narrative states the country scope explicitly.

## Data-architecture assumptions

### A-DATA-01 — API-primary and LLM-fallback hierarchy

- **Domain:** every column in the merged evidence base.
- **Statement:** where a first-party API or open-data source provides a field value, the API value is authoritative. LLM-curated values are used only when the API has no value. Raw LLM responses never enter the merged base.
- **Impact if wrong:** scores depend on model knowledge cut-off; risk is bounded by the curation gate before promotion.
- **Mitigation:** every scored row carries a `provenance_source` column; the provenance hierarchy is described in Annex C.

### A-DATA-02 — Merged DB is the single source of truth for scoring

- **Domain:** scoring engine.
- **Statement:** the scoring engine reads only from the merged evidence base. API-only and LLM-only layers are never queried directly for scoring.
- **Impact if wrong:** silent score divergence between runs.
- **Mitigation:** every score row stores a run identifier; the rescore CLI refuses to write into the wrong database.

### A-DATA-03 — Site geometry is a single representative point

- **Domain:** distance-based criteria.
- **Statement:** each site is represented by a single (latitude, longitude) point; distance-based criteria measure to that point.
- **Impact if wrong:** for very-large host sites the emergency-planning buffer might intersect more constraints than the point measurement suggests.
- **Mitigation:** Stage 3 recomputes against the actual containment and cooling-tower footprint.

## Rubric and scoring assumptions

### A-RUBRIC-01 — 0–10 ranking scale with plus-or-minus-one uncertainty for low-quality rows

- **Statement:** every criterion produces a continuous 0–10 score; for rows whose source is flagged `quality = low`, the Monte Carlo uncertainty band is `score ± 1` (uniform). High-quality rows have zero-width uncertainty.
- **Impact if wrong:** Monte Carlo stability is over-estimated for high-quality rows; this is the conservative direction for a screening study.
- **Mitigation:** declared quality is itself a stored column; reviewers can re-run with a different dispersion model.

### A-RUBRIC-02 — Hard safety floor at 5.0 for exclusionary criteria

- **Domain:** NH-02, NH-03, NH-04, NH-05, NH-07, NH-10, EP-01, NS-01, NS-08.
- **Statement:** any site whose ranking score falls strictly below 5.0 on an exclusionary criterion is excluded from composite ranking by a synthetic `E*:floor` verdict.
- **Impact if wrong:** before the floor, about 7 per cent more pairs survived to ranking; the floor tightens but does not contradict the underlying hard E-code condition.
- **Mitigation:** documented in Annex B and unit-tested in the scoring pipeline.

### A-RUBRIC-03 — Failed sites keep their 0–10 scores for transparency

- **Statement:** sites that fail a hard E-code or safety floor still carry all per-criterion ranking scores in the audit; their composite is null and they never enter banding or national shortlists.
- **Impact if wrong:** none for ranking; reduces auditability if reverted.

### A-RUBRIC-04 — Per-criterion weights are swing weights once normalised

- **Statement:** published weights are interpreted as importance to the decision; the swing-weight audit rescales by observed score range to verify declared importance matches discriminating power.
- **Impact if wrong:** the headline ranking is robust to weight perturbation (Jaccard at top-10 per cent ≥ 0.85 on every plus-or-minus-20 per cent profile).

## Sensitivity-suite assumptions

### A-SENS-01 — Plus-or-minus-20 per cent per-category weight envelope

- **Statement:** the regulatory band for category weight perturbation is plus-or-minus-20 per cent.
- **Impact if wrong:** wider envelopes would expose more borderline pairs as unstable; the suite is parameterised so the band can be widened at low cost.

### A-SENS-02 — 10,000 Monte Carlo iterations is sufficient

- **Statement:** convergence of mean, fifth percentile, and ninety-fifth percentile is verified at 10,000 iterations against 1,000 and 3,000 iteration presets; differences are below 0.5 per cent on all reported metrics.
- **Mitigation:** smaller presets ship with the driver so reviewers can retest convergence.

### A-SENS-03 — Pair-specific RNG seeding

- **Statement:** every Monte Carlo draw is seeded from the pair's site identifier, SMR key, and a fixed integer so the suite is bit-reproducible.
- **Impact if wrong:** reproduction failures would be detected at rerun; the seed is fixed in code.

### A-SENS-04 — Country-balance flag at 40 per cent share

- **Statement:** if any single country's share of the regional top-20 exceeds 40 per cent, the suite emits a country-balance flag.
- **Impact if wrong:** soft signal of data-coverage bias rather than a hard rule; reviewers decide whether to redistribute scoring effort.

### A-SENS-05 — Criterion-pair correlation flagged at |ρ| ≥ 0.70

- **Statement:** any pair with Pearson or Spearman magnitude 0.70 or above is flagged as potentially double-counting an axis.
- **Mitigation:** the correlation flag list documents the latest flagged pairs and the decision on each one.

## Reporting and scope-management assumptions

### A-REPORT-01 — Country shortlist sizing

- **Statement:** each country's list ranks at least the top 10 sites (fewer only if the country has fewer scored sites). Larger countries carry `K = min(n, max(10, ceil(0.30·n)))`.
- **Impact if wrong:** small countries cannot offer a statistically meaningful 30 per cent slice; the floor of 10 forces a comparable narrative everywhere.

### A-REPORT-02 — Stamp-aligned artefacts

- **Statement:** every audit and report artefact within a single suite run shares the same provenance stamp; orphan stamps trigger a follow-up rerun rather than partial regeneration.

### A-REPORT-03 — Out-of-scope items are recorded, not hidden

- **Statement:** any IAEA SSR-1 Requirement the project does not cover is listed in the traceability matrix with an explicit `out_of_scope` label and rationale, rather than being silently omitted.

## Per-dataset limitation catalogue

The datasets below are the authoritative evidence sources the project uses for scoring. Each entry lists the data domain, spatial or temporal resolution, reference period, and the screening caveat that bounds how confidently the data can be used.

| Dataset or source | Domain | Resolution or scope | Reference period | Screening caveat |
| --- | --- | --- | --- | --- |
| European Seismic Hazard Model (EFEHR) | Seismic PGA and capable-fault proxy | European grid | Current EFEHR release | Stage 3 requires site-specific PSHA and PFDHA; screening Vs30 is a regional reference value. |
| ERA5 reanalysis (ECMWF, Copernicus) | Wind, temperature, precipitation, dispersion | Roughly 0.25° grid | 1991–2020 climatology window | Coarse grid produces artefacts in mountainous regions; meteorological tower data is required at Stage 3. |
| European Flood Awareness System and national flood-hazard cadastres | Flood hazard class | National and European grid | Current release | Coastal surge and dam-break contributions are not captured; design-basis flood analysis is a Stage 3 deliverable. |
| CORINE Land Cover (EEA) | Land-use class, buildable area | 100 m European grid | CORINE 2018 and later | Urban or industrial classes can include non-buildable parcels; Stage 3 requires site-specific zoning. |
| Natura 2000 network (EEA) | Protected area proximity | European vector | End of 2023 release | Article 6(3) appropriate assessment is a Stage 3 deliverable, not a screening verdict. |
| WDPA (World Database on Protected Areas) | Non-Natura 2000 protected-area proxy | Global vector | Latest release | Not all IUCN categories impose the same restrictions; use with national-practice qualifier. |
| WorldPop | Population density at screening radii | 100 m constrained | Latest release | Population projection is a linear projection for screening; Stage 3 requires national census plus municipal planning. |
| OpenStreetMap (OSM contributors) | Roads, rail, airports, industrial and military features | Crowd-sourced vector | Rolling | Completeness is country-dependent; absence of a feature does not imply absence in reality. |
| Global Energy Monitor and Beyond Fossil Fuels | Coal and thermal plant inventory | Global structured | Access window at drafting | Coal-retirement status may lag national sources; verify against national energy source at Stage 3. |
| JRC ENSPRESO | Power plant database | European structured | Access window at drafting | Source reconciliation required against GEM and national inventories. |
| ENTSO-E Transparency Platform | Grid topology and capacity | European platform | Access window at drafting | Public grid data supports screening only; firm-capacity headroom requires a transmission system operator study. |
| Institute for the Study of War control-of-terrain map | Ukraine control-of-terrain | National | Dated at publication | Temporal snapshot; attribute with the exact map date when cited in the Ukraine sections. |

## Country-specific data limitations

The table below lists the country-specific caveats that affect how the ranking should be read for each country. These supplement the per-dataset caveats above; they do not invalidate any specific ranking but they do identify where the ranking is most likely to be tightened by Stage 3 evidence.

| Country | Caveat |
| --- | --- |
| Ukraine (UA) | War-context caveat. Occupied-territory status for any site should be attributed to a dated control-of-terrain map at publication. Detailed site progression depends on post-war territorial stabilisation and infrastructure-condition evidence. |
| Belarus (BY) | National data access is restricted; the site count is small and ownership tracing is weaker than elsewhere. |
| Moldova (MD) | Single site in the in-scope universe; the country narrative depends on cross-border cooling-water, grid, and emergency-planning coordination with neighbouring states. |
| Russia-occupied regions (historical entries) | The ranking does not recompute political-control status. Any change in control would require a re-run with updated boundary data. |
| Kosovo (XK) | Political-status caveat attaches to data availability; the country carries no survivors in the current pool. |
| Turkey (TR) | Large universe with the strongest survivor pool but also the highest variability in data quality between provinces; national authority engagement is the priority for validating grid and emergency-planning proxies. |

## Primary sources for this annex

- `report/methodology/assumption_register.md` — the authoritative assumption source.
- `docs/large_assets.md` — the dataset index.
- Connector reports under `docs/connector_reports/`.
- Chapter 2 §2.3 and Chapter 4 §4.5 for the family-level summaries.
