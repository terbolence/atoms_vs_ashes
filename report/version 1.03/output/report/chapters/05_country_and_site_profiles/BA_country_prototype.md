# Bosnia and Herzegovina Country Profile

Analytical basis: scoring `score-c2a90942` and sensitivity `nat-sens-b1a62885`.

Bosnia and Herzegovina has 11 thermal and coal-site records that have been tested against the NuScale VOYGR-6 reference deployment envelope. 0 sites pass both the exclusionary and avoidance screens, 6 pass the exclusionary screen but retain avoidance flags, and 5 fail one or more exclusionary checks. The country is therefore not a single-site case, but only a small subset of the national site population currently clears the full screening pathway without a remediation step.

The leading site is **Gacko Thermal Power Plant**, with a composite score of 6.951 and a Monte Carlo interval of 6.073-7.442. Its national stability band is `A` with a national top-10% hit rate of 100%. The leader is therefore not only the current point-estimate front-runner; it is also a stable national candidate under the sensitivity treatment used for the report.

<!-- specialist key=country_exec scope=country country_code=BA bundle=BA_country_bundle.json status=pending -->
> _Specialist interpretation pending: Country coal-to-nuclear executive read (full-pass leadership pool, avoidance unlock potential, greenfield lever, and credible programme cadence). Cursor agent fills via `python -m scripts.run_specialist_pass show --country BA --key country_exec` then `... patch --country BA --key country_exec --text-file <draft.md>`._
<!-- /specialist key=country_exec -->

<a id="country-status-map"></a>

![Bosnia and Herzegovina status map](figures/BA_site_status_map.png)

Interactive review map with marker tooltips: [BA_site_status_map.html](figures/BA_site_status_map.html).

## Bosnia and Herzegovina Site Ledger

| Rank | Site | Status | Composite | MC Low | MC High | Band | Top-10 Hit | Coverage |
|---:|---|---|---:|---:|---:|---|---:|---:|
| 1 | Gacko Thermal Power Plant | Exclusion pass with avoidance flag | 6.951 | 6.073 | 7.442 | A | 100% | 74% |
| 2 | Stanari Thermal Power Plant | Exclusion pass with avoidance flag | 6.747 | 6.028 | 7.237 | H | 0% | 76% |
| 3 | Miljevina power station | Exclusion pass with avoidance flag | 6.622 | 5.927 | 7.131 | H | 0% | 76% |
| 4 | Kamengrad Thermal Power Plant | Exclusion pass with avoidance flag | 6.572 | 5.886 | 7.131 | H | 0% | 76% |
| 5 | Ugljevik power station | Exclusion pass with avoidance flag | 6.458 | 5.707 | 6.929 | H | 0% | 74% |
| 6 | Banovici power station | Exclusion pass with avoidance flag | 5.934 | 5.325 | 6.425 | H | 0% | 76% |
| - | Bugojno Thermal Power Project | Hard fail | - | - | - | - | - | 0% |
| - | Glinica power station | Hard fail | - | - | - | - | - | 0% |
| - | Kakanj Thermal Power Plant | Hard fail | - | - | - | - | - | 0% |
| - | Kongora Thermal Power Plant | Hard fail | - | - | - | - | - | 0% |
| - | Tuzla Thermal Power Plant | Hard fail | - | - | - | - | - | 0% |

## Avoidance Flag Pareto

Of the 6 sites that pass the exclusionary screen, the avoidance-phase flags concentrate on a small set of criteria. Resolving them is what would move the country from a small leading group to a broader candidate pool.

![Avoidance flag Pareto](figures/BA_avoidance_pareto.png)

- **Grid Connection (NS-02)** - 6 of 6 exclusionary-pass sites (100%).
- **Aircraft Crash (HI-01)** - 1 of 6 exclusionary-pass sites (17%).

## Exclusionary Failure Pareto

The exclusionary failures across the country trace back to a small number of criteria. They identify which screening checks are responsible for removing sites from further consideration.

![Exclusionary failure Pareto](figures/BA_exclusionary_pareto.png)

- **Seismic: Surface Rupture (NH-02)** - 5 of 11 country sites (45%).

## Family Strength and Weakness

Across the country the strongest criterion family is **Human-Induced Hazards** at a mean normalised score of 7.87/10. The weakest family is **Emergency Planning** at 4.60/10. The bottom three individual criteria across the country are:

- **Military Installations (HI-06)** - mean 1.64/10 across 11 scored sites (min 0.0, max 5.0).
- **Evacuation Routes (EP-02)** - mean 2.41/10 across 11 scored sites (min 1.5, max 3.5).
- **Surface Water Dispersion (RI-02)** - mean 2.77/10 across 11 scored sites (min 1.5, max 7.5).

## Interpretation for Site Selection

The Bosnia and Herzegovina result shows a clear separation between sites that can support further Stage 3 consideration and sites that should remain in the evidence base only as comparators. The full-pass group is the relevant pool for progression. Avoidance-flag sites are not discarded, but they identify locations where a specific constraint must be resolved before the site can be treated as equivalent to the leading group.

![Avoidance flag Pareto - what unlocks more sites](figures/BA_avoidance_pareto.png)

The chart shows where focused remediation effort would broaden the candidate pool. The criteria at the top of the Pareto are the policy and engineering levers that, if resolved, move avoidance-flag sites into the leading group.

An IAEA-style reading of the table focuses less on the exact rank number and more on screening class, score stability, and the nature of remaining uncertainty. **Gacko Thermal Power Plant** is important because it leads nationally, sits inside the strongest stability band, and retains a full-pass status. That does not establish final site suitability. It is a defensible reason to spend Stage 3 effort on field confirmation, national data review, and stakeholder engagement before lower-ranked or avoidance-flag locations.

The Monte Carlo interval is a caution against false precision: several sites have overlapping score bands, so small score differences should not be overinterpreted. The decisive distinction is whether a site combines acceptable exclusionary performance with a stable ranking position and no unresolved avoidance flag.

The main Stage 3 questions are therefore targeted rather than generic: confirm local natural-hazard inputs, verify emergency-planning assumptions, test land and ownership constraints, assess cooling and grid interface conditions, and reconcile environmental constraints with national permitting requirements.

## Status Counts

- Full pass: 0
- Exclusion pass with avoidance flag: 6
- Hard fail: 5
