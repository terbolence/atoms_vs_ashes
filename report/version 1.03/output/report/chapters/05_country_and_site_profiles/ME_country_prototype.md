# Montenegro Country Profile

Montenegro has 4 thermal and coal-site records that have been tested against the NuScale VOYGR-6 reference deployment envelope. 0 sites pass both the exclusionary and avoidance screens, 2 pass the exclusionary screen but retain avoidance flags, and 2 fail one or more exclusionary checks. The country is therefore not a single-site case, but only a small subset of the national site population currently clears the full screening pathway without a remediation step.

No site clears both the exclusionary and avoidance screens, so there is no full-pass national leader. The leading exclusion-pass site at the point estimate is **Bar power station**, with a composite score of 6.023 and a Monte Carlo interval of 5.321-6.467; its national stability band is `F` with a top-10% hit rate of 42%, so the point-estimate lead is not robust under the sensitivity treatment. **Berane power station** is tied at composite 6.023 (interval 5.321-6.559) and sits in the more stable band `C` with a top-10% hit rate of 58%, making it the more stable avoidance-flag candidate under the same sensitivity treatment.

<!-- specialist key=country_exec scope=country country_code=ME bundle=ME_country_bundle.json status=pending -->

<!-- /specialist key=country_exec -->

<a id="country-status-map"></a>

![Montenegro status map](figures/ME_site_status_map.png)

Interactive review map with marker tooltips: [ME_site_status_map.html](figures/ME_site_status_map.html).

## Montenegro Site Ledger

| Rank | Site | Status | Composite | MC Low | MC High | Band | Top-10 Hit | Coverage |
|---:|---|---|---:|---:|---:|---|---:|---:|
| 1 | Bar power station | Exclusion pass with avoidance flag | 6.023 | 5.321 | 6.467 | F | 42% | 74% |
| 2 | Berane power station | Exclusion pass with avoidance flag | 6.023 | 5.321 | 6.559 | C | 58% | 74% |
| - | Maoce Power Station | Hard fail | - | - | - | - | - | 0% |
| - | Pljevlja power station | Hard fail | - | - | - | - | - | 0% |

## Avoidance Flag Pareto

Of the 2 sites that pass the exclusionary screen, the avoidance-phase flags concentrate on a small set of criteria. Resolving them is what would move the country from a small leading group to a broader candidate pool.

![Avoidance flag Pareto](figures/ME_avoidance_pareto.png)

- **Aircraft Crash (HI-01)** - 1 of 2 exclusionary-pass sites (50%).
- **Seismic: Ground Motion (NH-01)** - 1 of 2 exclusionary-pass sites (50%).
- **Coastal Flooding (NH-08)** - 1 of 2 exclusionary-pass sites (50%).
- **Grid Connection (NS-02)** - 1 of 2 exclusionary-pass sites (50%).

## Exclusionary Failure Pareto

The exclusionary failures across the country trace back to a small number of criteria. They identify which screening checks are responsible for removing sites from further consideration.

![Exclusionary failure Pareto](figures/ME_exclusionary_pareto.png)

- **Seismic: Surface Rupture (NH-02)** - 2 of 4 country sites (50%).
- **Ecological Sensitivity (NS-08)** - 1 of 4 country sites (25%).

## Family Strength and Weakness

Across the country the strongest criterion family is **Human-Induced Hazards** at a mean normalised score of 6.94/10. The weakest family is **Emergency Planning** at 4.44/10. The bottom three individual criteria across the country are:

- **Military Installations (HI-06)** - mean 0.38/10 across 4 scored sites (min 0.0, max 1.5).
- **Ecological Sensitivity (NS-08)** - mean 1.50/10 across 4 scored sites (min 1.5, max 1.5).
- **Evacuation Routes (EP-02)** - mean 1.50/10 across 4 scored sites (min 1.5, max 1.5).

## Interpretation for Site Selection

The Montenegro result shows a clear separation between sites that can support further Stage 3 consideration and sites that should remain in the evidence base only as comparators. No site clears both the exclusionary and avoidance screens, so there is no full-pass pool to draw from; the leading exclusion-pass sites with avoidance flags are the relevant pool for progression once those specific constraints are resolved.

![Avoidance flag Pareto - what unlocks more sites](figures/ME_avoidance_pareto.png)

The chart shows where focused remediation effort would broaden the candidate pool. The criteria at the top of the Pareto are the policy and engineering levers that, if resolved, move avoidance-flag sites into the leading group.

An IAEA-style reading of the table focuses less on the exact rank number and more on screening class, score stability, and the nature of remaining uncertainty. **Bar power station** holds the point-estimate national lead but sits in stability band `F`, so its position is sensitive to weighting choices; **Berane power station** is tied on point estimate and sits in the more stable band `C`. Both retain avoidance flags rather than full-pass status, so neither is currently a full-pass candidate. That does not establish final site suitability. It is a defensible reason to spend Stage 3 effort on field confirmation, national data review, and stakeholder engagement on the leading exclusion-pass sites and on resolving the avoidance-flag criteria that currently prevent a full-pass classification before lower-ranked or hard-fail locations.

The Monte Carlo interval is a caution against false precision: several sites have overlapping score bands, so small score differences should not be overinterpreted. The decisive distinction is whether a site combines acceptable exclusionary performance with a stable ranking position and no unresolved avoidance flag.

The main Stage 3 questions are therefore targeted rather than generic: confirm local natural-hazard inputs, verify emergency-planning assumptions, test land and ownership constraints, assess cooling and grid interface conditions, and reconcile environmental constraints with national permitting requirements.

## Status Counts

- Full pass: 0
- Exclusion pass with avoidance flag: 2
- Hard fail: 2
