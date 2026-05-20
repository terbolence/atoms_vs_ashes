<!-- man_hours: 1.8 -->
# Site Template Decision: Turceni Model

## Decision Requested

Approve or reject the Turceni site-profile template as the model for selected-site profiles in Chapter 5 version 1.2.

Exact approval prompt for the user:

> I approve `site_template_decision.md` as the selected-site template gate for version 1.2. Use the Turceni profile structure for later selected-site profiles, with the limitations and follow-up choices recorded here.

If the decision is not approved, the user should identify which site-profile element must change before any broad Chapter 5 site fan-out begins.

## Artefacts For Review

| Artefact | Path | Review purpose |
| --- | --- | --- |
| Turceni site profile draft | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/sites/RO_turceni_power_station.md` | Review the selected-site structure, evidence sections, specialist interpretations, residual-risk register, Stage 3 follow-up checklist, and limitations section. |
| Turceni site bundle | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/data/RO_turceni_power_station_site_bundle.json` | Verify the site metadata, ownership, units, screening verdicts, scoring rows, family evidence, composite score, and national sensitivity band. |
| Turceni criterion chart | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_turceni_power_station_criterion_scores.png` | Review the criterion-score scaffold for selected-site profiles. |
| Turceni family chart | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_turceni_power_station_family_contributions.png` | Review the family-contribution scaffold for selected-site profiles. |
| Parent Romania country profile | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/RO_country_prototype.md` | Check that the site profile agrees with the country lead, rank, national stability band, and Stage 3 sequencing. |

## Template Features To Approve

1. The selected-site profile begins with a site snapshot, ownership and coal-to-nuclear context, then separates the criterion families into Natural Hazards, Human-Induced and Security-Relevant Hazards, Radiological Impact and Emergency Planning, and Non-Safety and Implementation Considerations.
2. Each family section shows measured evidence first, then the specialist interpretation. The specialist interpretation is written in Stage 1-2 screening language and routes unresolved issues to Stage 3 characterization.
3. The six Turceni specialist placeholders have been filled: `family_natural_hazards`, `family_human_hazards`, `family_radiological_emergency`, `family_infrastructure`, `stability`, and `residual_risk`.
4. The profile escalates reviewer-sensitive criteria where relevant: NH-11, HI-01, HI-06, EP-01 and RI-04 are visible in the family interpretations, residual-risk register, or Stage 3 follow-up logic. RI-04 is treated as a population and dose-feasibility screening proxy, not as a licensing dose conclusion.
5. The residual-risk register separates concern, evidence, consequence, Stage 3 action, and owner discipline. It makes clear that the register is a Stage 3 work plan for a leading screening candidate, not a site-approval finding.
6. The Stage 3 follow-up checklist is derived from weak scores, low-confidence or unscored values, and criterion-family limitations. It is intended to become the consistent selected-site review surface for all later countries.

## Evidence And Significance In The Turceni Model

The refreshed Turceni bundle gives a baseline composite score of 7.816, a Monte Carlo bracket of 6.891-8.256, national stability band A, and 100% top-5, top-10 and top-30 hit rates across the national sensitivity scenarios recorded in the bundle. The profile uses that as a stability signal for Stage 3 sequencing, while keeping residual risk separate.

The highest-value evidence pattern for later site profiles is the combination of favourable brownfield attributes and explicit unresolved constraints:

- Strong brownfield evidence: Râul Jiu cooling source 1.28 km away, 24.24 m3/s mean flow, 0.25 Low-Medium water-stress score, rail 0.26 km away, 173.0 ha canonical site footprint, and 169.78 ha current buildable-area estimate.
- Major residual constraints: depot-class military feature 2.91 km away with eight depot-class features within 25 km, Coridorul Jiului 1.418 km away, EPZ road density 0.427 km/km2, nearest transmitter 2.97 km away, and liquid-pathway / precipitation inputs requiring Stage 3 confirmation.

## Applicability To Later Selected Sites

The template works across all in-scope countries because it asks the same selected-site questions regardless of country:

- What measured evidence supports the site's Stage 1-2 screening position?
- Which criterion families drive the score and which specific criteria limit confidence?
- Which issues are exclusionary, avoidance-flagged, weak-scoring, unscored, or simply Stage 3 evidence gaps?
- Which ownership, grid, water, land, transport, ecology and emergency-planning facts can be stated without inferring project control or licensing readiness?
- Which Stage 3 tasks should be assigned to geotech, seismic, hydrology, EIA, emergency planning, grid, security, ownership/legal, or socioeconomic workstreams?

This means Turceni can serve as the selected-site template even though later sites may be weaker, avoidance-flagged, or selected for strategic rather than rank-only reasons. The template keeps those cases comparable by preserving the same evidence, significance, limitations, residual-risk, and Stage 3 structure.

## Known Limitations And Choices

- The renderer still emits filled specialist HTML comments as internal traceability. They are not unresolved placeholders, but they must be stripped or moved to the audit copy before publication assembly.
- Some auto-rendered criterion bullets remain mechanical. The specialist paragraphs and residual-risk register provide the decision-quality reading, but a later batch-review pass should smooth the mechanical bullets across all selected sites.
- Ownership wording remains a human-review item. The profile reports share chains and immediate operator information from the bundle without asserting legal control, land rights, procurement commitment, or regulatory acceptance.
- The site profile is not the full Romania site set. Step 4 still needs user confirmation of the Romania selected-site set before the broader Romania batch proceeds.
- Approval of this decision would approve the site-profile shape, not accept Turceni as publication-ready and not mark any `tableOfContents.md` row complete.

## Recommended User Decision

Approve the site template if the user agrees that later selected-site profiles should preserve this sequence: evidence ledger by family, specialist significance by family, composite and national stability interpretation, residual-risk register, Stage 3 follow-up checklist, and evidence limitations.
