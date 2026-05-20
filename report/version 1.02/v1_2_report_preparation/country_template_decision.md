<!-- man_hours: 1.6 -->
# Country Template Decision: Romania Model

## Decision Requested

Approve or reject the Romania country-profile template as the model for Chapter 5 country profiles in version 1.2.

Exact approval prompt for the user:

> I approve `country_template_decision.md` as the country-profile template gate for version 1.2. Use the Romania profile structure for later country batches, with the limitations and follow-up choices recorded here.

If the decision is not approved, the user should identify which element to change before any broad Chapter 5 country fan-out begins.

## Artefacts For Review

| Artefact | Path | Review purpose |
| --- | --- | --- |
| Romania country profile draft | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/RO_country_prototype.md` | Review the country-profile structure, national opening, site ledger, Pareto sections, family read, and country-executive interpretation. |
| Romania country bundle | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/data/RO_country_bundle.json` | Verify the frozen scoring and national sensitivity basis, country totals, site rows, family means, and Pareto inputs. |
| Romania site ledger | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/data/RO_site_ledger.csv` | Verify the ranked country table consumed by the profile and map scaffold. |
| Static Romania status map | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_site_status_map.png` | Review the publication-intended map scaffold. It was refreshed through the renderer with the local Natural Earth fallback forced, avoiding external tile calls. |
| Interactive review map | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_site_status_map.html` | Internal review aid only unless later separated into the audit copy. It contains external tile references and is not publication-ready. |
| Avoidance and failure Pareto charts | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_avoidance_pareto.png`; `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/RO_exclusionary_pareto.png` | Review whether the country template explains unlock constraints and hard-fail drivers with explicit denominators. |

## Template Features To Approve

1. The country profile opens on the full national distribution before naming the leading site. For Romania, the refreshed bundle reports 23 ranked thermal and coal-site records, three full-pass sites, 19 avoidance-flagged exclusionary-pass sites, and one hard-fail site.
2. The ranked ledger remains the centre of the profile. It shows national rank, site name, screening class, composite score, Monte Carlo bracket, national stability band, top-10 hit rate, and evidence coverage.
3. The country-executive block interprets the full pool, not only Turceni. It separates the leadership pool, the avoidance unlock pool, and the credible Stage 3 cadence.
4. The Pareto sections use the correct denominator. Avoidance flags are measured against the 22 exclusionary-pass sites; hard-fail drivers are measured against all 23 country records.
5. The template is suitable for all in-scope countries because it can express four cases: multi-site leadership pools, single-leader countries, countries with large avoidance unlock pools, and countries that collapse into the consolidated failure section when no viable candidate remains.
6. The template supports the all-country programme because each country can be regenerated from the same frozen scoring run and national sensitivity basis, while preserving country-specific denominators, hard-fail criteria, avoidance criteria, national stability bands, and Stage 3 sequencing logic.

## Cross-Country Applicability

The template is not Romania-specific. It requires every later country author to answer the same questions from the country bundle:

- How many records are in the national ranked pool?
- How many sites are full-pass, avoidance-flagged, and hard-failed?
- Which sites are the leadership pool under national sensitivity?
- Which avoidance criteria unlock the next tier, and how many exclusionary-pass sites do they affect?
- Which hard-fail criteria remove sites from consideration, and are those failures structural, remediable, or data-limited?
- Does the country justify a full profile, or should it move to the consolidated failure section?

This structure accounts for all in-scope countries by using the country bundle as the authority for each national denominator. Belarus remains excluded from the published country analysis unless restored by the user.

## Known Limitations And Choices

- The regenerated Romania distribution is 23 / 3 / 19 / 1. Earlier plan language referenced 22 sites; the decision should accept the refreshed bundle count unless the user identifies a data-scope error.
- The country profile still carries filled specialist HTML comments as internal traceability. They are filled, not pending, but they must be stripped or moved to the audit copy before publication assembly.
- The interactive HTML map remains an internal review artefact because it contains external basemap references. The static PNG was regenerated offline and is the publication-oriented map scaffold.
- The profile cites the analytical basis in prose-safe language, but the JSON bundle retains run IDs for audit reproducibility.
- The template does not yet mark any `tableOfContents.md` section complete. Approval of this decision would approve the country-profile shape, not accept Chapter 5 as publication-ready.

## Recommended User Decision

Approve the country template if the user agrees that every later country profile should begin with the national distribution, use the ranked ledger as the core evidence surface, treat avoidance criteria as national unlock work, and route no-viable-candidate countries into the consolidated failure section.
