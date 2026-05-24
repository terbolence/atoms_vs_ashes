# Bulgaria Country Profile

Analytical basis: scoring `score-c2a90942` and sensitivity `nat-sens-b1a62885`.

Bulgaria has 15 thermal and coal-site records that have been tested against the NuScale VOYGR-6 reference deployment envelope. 1 sites pass both the exclusionary and avoidance screens, 7 pass the exclusionary screen but retain avoidance flags, and 7 fail one or more exclusionary checks. The country is therefore not a single-site case, but only a small subset of the national site population currently clears the full screening pathway without a remediation step.

The leading site is **Maritsa Iztok-2 power station**, with a composite score of 7.709 and a Monte Carlo interval of 6.806-8.169. Its national stability band is `A` with a national top-10% hit rate of 100%. The leader is therefore not only the current point-estimate front-runner; it is also a stable national candidate under the sensitivity treatment used for the report.

<!-- specialist key=country_exec scope=country country_code=BG bundle=BG_country_bundle.json status=pending -->
> _Specialist interpretation pending: Country coal-to-nuclear executive read (full-pass leadership pool, avoidance unlock potential, greenfield lever, and credible programme cadence). Cursor agent fills via `python -m scripts.run_specialist_pass show --country BG --key country_exec` then `... patch --country BG --key country_exec --text-file <draft.md>`._
<!-- /specialist key=country_exec -->

<a id="country-status-map"></a>

![Bulgaria status map](figures/BG_site_status_map.png)

Interactive review map with marker tooltips: [BG_site_status_map.html](figures/BG_site_status_map.html).

## Bulgaria Site Ledger

| Rank | Site | Status | Composite | MC Low | MC High | Band | Top-10 Hit | Coverage |
|---:|---|---|---:|---:|---:|---|---:|---:|
| 1 | Maritsa Iztok-2 power station | Full pass | 7.709 | 6.806 | 8.169 | A | 100% | 76% |
| 2 | Lom Power Station | Exclusion pass with avoidance flag | 7.428 | 6.578 | 7.850 | D | 0% | 76% |
| 3 | Vidin Works power station | Exclusion pass with avoidance flag | 7.091 | 6.306 | 7.631 | H | 0% | 76% |
| 4 | Maritsa 3 power station | Exclusion pass with avoidance flag | 7.009 | 6.240 | 7.569 | H | 0% | 76% |
| 5 | Bobov Dol power station | Exclusion pass with avoidance flag | 6.984 | 6.220 | 7.525 | H | 0% | 76% |
| 6 | Svilosa power station | Exclusion pass with avoidance flag | 6.578 | 5.891 | 7.119 | H | 0% | 76% |
| 7 | Ruse Iztok power station | Exclusion pass with avoidance flag | 5.878 | 5.326 | 6.419 | H | 0% | 76% |
| 8 | Republika power station | Exclusion pass with avoidance flag | 5.875 | 5.323 | 6.325 | H | 0% | 76% |
| - | Brikel power station | Hard fail | - | - | - | - | - | 0% |
| - | Deven power station | Hard fail | - | - | - | - | - | 0% |
| - | Maritsa Iztok-1 power station | Hard fail | - | - | - | - | - | 0% |
| - | Maritsa Iztok-3 power station | Hard fail | - | - | - | - | - | 0% |
| - | Maritsa Iztok-4 power station | Hard fail | - | - | - | - | - | 0% |
| - | Sliven power station | Hard fail | - | - | - | - | - | 0% |
| - | Varna power station | Hard fail | - | - | - | - | - | 0% |

## Avoidance Flag Pareto

Of the 8 sites that pass the exclusionary screen, the avoidance-phase flags concentrate on a small set of criteria. Resolving them is what would move the country from a small leading group to a broader candidate pool.

![Avoidance flag Pareto](figures/BG_avoidance_pareto.png)

- **Grid Connection (NS-02)** - 6 of 8 exclusionary-pass sites (75%).
- **Aircraft Crash (HI-01)** - 2 of 8 exclusionary-pass sites (25%).
- **Distance to Population Centres (RI-05)** - 2 of 8 exclusionary-pass sites (25%).
- **Toxic/Gas Releases (HI-03)** - 1 of 8 exclusionary-pass sites (12%).

## Exclusionary Failure Pareto

The exclusionary failures across the country trace back to a small number of criteria. They identify which screening checks are responsible for removing sites from further consideration.

![Exclusionary failure Pareto](figures/BG_exclusionary_pareto.png)

- **Seismic: Surface Rupture (NH-02)** - 7 of 15 country sites (47%).
- **Ecological Sensitivity (NS-08)** - 1 of 15 country sites (7%).

## Family Strength and Weakness

Across the country the strongest criterion family is **Natural Hazards** at a mean normalised score of 7.48/10. The weakest family is **Emergency Planning** at 5.70/10. The bottom three individual criteria across the country are:

- **Military Installations (HI-06)** - mean 1.77/10 across 15 scored sites (min 0.0, max 5.0).
- **Ecological Sensitivity (NS-08)** - mean 2.03/10 across 15 scored sites (min 1.5, max 5.5).
- **Electromagnetic Interference (HI-07)** - mean 2.17/10 across 15 scored sites (min 1.5, max 3.5).

## Interpretation for Site Selection

The Bulgaria result shows a clear separation between sites that can support further Stage 3 consideration and sites that should remain in the evidence base only as comparators. The full-pass group is the relevant pool for progression. Avoidance-flag sites are not discarded, but they identify locations where a specific constraint must be resolved before the site can be treated as equivalent to the leading group.

![Avoidance flag Pareto - what unlocks more sites](figures/BG_avoidance_pareto.png)

The chart shows where focused remediation effort would broaden the candidate pool. The criteria at the top of the Pareto are the policy and engineering levers that, if resolved, move avoidance-flag sites into the leading group.

An IAEA-style reading of the table focuses less on the exact rank number and more on screening class, score stability, and the nature of remaining uncertainty. **Maritsa Iztok-2 power station** is important because it leads nationally, sits inside the strongest stability band, and retains a full-pass status. That does not establish final site suitability. It is a defensible reason to spend Stage 3 effort on field confirmation, national data review, and stakeholder engagement before lower-ranked or avoidance-flag locations.

The Monte Carlo interval is a caution against false precision: several sites have overlapping score bands, so small score differences should not be overinterpreted. The decisive distinction is whether a site combines acceptable exclusionary performance with a stable ranking position and no unresolved avoidance flag.

The main Stage 3 questions are therefore targeted rather than generic: confirm local natural-hazard inputs, verify emergency-planning assumptions, test land and ownership constraints, assess cooling and grid interface conditions, and reconcile environmental constraints with national permitting requirements.

## Status Counts

- Full pass: 1
- Exclusion pass with avoidance flag: 7
- Hard fail: 7
