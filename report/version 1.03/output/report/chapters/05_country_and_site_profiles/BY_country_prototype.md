# Belarus Country Profile

> **Unpublished — held for audit only.** Belarus is **not** part of the published roster (16 country profiles: Austria through Ukraine, excluding Belarus). This file is retained on disk as an audit artefact alongside the BY ledger CSV and BY country/site bundles, but it is not linked from the Chapter 5 index and is not referenced from any other published surface. Do not cite the numbers below as part of the published deliverable.

Belarus has 2 thermal and coal-site records that have been tested against the NuScale VOYGR-6 reference deployment envelope. 1 sites pass both the exclusionary and avoidance screens, 1 pass the exclusionary screen but retain avoidance flags, and 0 fail one or more exclusionary checks. The country is therefore not a single-site case, but only a small subset of the national site population currently clears the full screening pathway without a remediation step.

The leading site is **Zelwa power station**, with a composite score of 7.378 and a Monte Carlo interval of 6.538-7.944. Its national stability band is `A` with a national top-10% hit rate of 100%. The leader is therefore not only the current point-estimate front-runner; it is also a stable national candidate under the sensitivity treatment used for the report.

<!-- specialist key=country_exec scope=country country_code=BY bundle=BY_country_bundle.json status=pending -->

<!-- /specialist key=country_exec -->

<a id="country-status-map"></a>

![Belarus status map](figures/BY_site_status_map.png)

Interactive review map with marker tooltips: [BY_site_status_map.html](figures/BY_site_status_map.html).

## Belarus Site Ledger

| Rank | Site                    | Status                             | Composite | MC Low | MC High | Band | Top-10 Hit | Coverage |
| ---: | ----------------------- | ---------------------------------- | --------: | -----: | ------: | ---- | ---------: | -------: |
|    1 | Zelwa power station     | Full pass                          |     7.378 |  6.538 |   7.944 | A    |       100% |      76% |
|    2 | Lelchitsy power station | Exclusion pass with avoidance flag |     6.991 |  6.225 |   7.487 | H    |         0% |      76% |

## Avoidance Flag Pareto

Of the 2 sites that pass the exclusionary screen, the avoidance-phase flags concentrate on a small set of criteria. Resolving them is what would move the country from a small leading group to a broader candidate pool.

![Avoidance flag Pareto](figures/BY_avoidance_pareto.png)

- **Grid Connection (NS-02)** - 1 of 2 exclusionary-pass sites (50%).
- **Site Footprint Adequacy (NS-05)** - 1 of 2 exclusionary-pass sites (50%).

## Family Strength and Weakness

Across the country the strongest criterion family is **Radiological Impact** at a mean normalised score of 7.92/10. The weakest family is **Emergency Planning** at 6.32/10. The bottom three individual criteria across the country are:

- **Military Installations (HI-06)** - mean 0.00/10 across 2 scored sites (min 0.0, max 0.0).
- **Land Area Basic Filter (BF-02)** - mean 1.50/10 across 2 scored sites (min 1.5, max 1.5).
- **Electromagnetic Interference (HI-07)** - mean 1.50/10 across 2 scored sites (min 1.5, max 1.5).

## Interpretation for Site Selection

The Belarus result shows a clear separation between sites that can support further Stage 3 consideration and sites that should remain in the evidence base only as comparators. The full-pass group is the relevant pool for progression. Avoidance-flag sites are not discarded, but they identify locations where a specific constraint must be resolved before the site can be treated as equivalent to the leading group.

![Avoidance flag Pareto - what unlocks more sites](figures/BY_avoidance_pareto.png)

The chart shows where focused remediation effort would broaden the candidate pool. The criteria at the top of the Pareto are the policy and engineering levers that, if resolved, move avoidance-flag sites into the leading group.

An IAEA-style reading of the table focuses less on the exact rank number and more on screening class, score stability, and the nature of remaining uncertainty. **Zelwa power station** is important because it leads nationally, sits inside the strongest stability band, and retains a full-pass status. That does not establish final site suitability. It is a defensible reason to spend Stage 3 effort on field confirmation, national data review, and stakeholder engagement before lower-ranked or avoidance-flag locations.

The Monte Carlo interval is a caution against false precision: several sites have overlapping score bands, so small score differences should not be overinterpreted. The decisive distinction is whether a site combines acceptable exclusionary performance with a stable ranking position and no unresolved avoidance flag.

The main Stage 3 questions are therefore targeted rather than generic: confirm local natural-hazard inputs, verify emergency-planning assumptions, test land and ownership constraints, assess cooling and grid interface conditions, and reconcile environmental constraints with national permitting requirements.

## Status Counts

- Full pass: 1
- Exclusion pass with avoidance flag: 1
- Hard fail: 0
