# Berane power station Site Profile

_Montenegro | tested against the NuScale VOYGR-6 reference deployment envelope | **Hard-fail at the exclusionary screen**._

Berane power station is a coal/thermal site in Montenegro that does not survive the exclusionary screen against the NuScale VOYGR-6 reference deployment envelope. This profile records the screening evidence that drives the failure and provides the siting expert's read on whether further characterization is justified. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Berane power station |
| Country | Montenegro |
| Coordinates | 42.8400, 19.8600 |
| Subnational unit | Berane |
| Installed thermal capacity (source data) | 110 MW |
| Operating status | cancelled |
| Parent owner(s) | Balkan Energy |
| Generating units on record | 1 |
| Screening verdict | Hard-fail (exclusionary) |
| Failed exclusionary criteria | EP-01 |
| Composite score | — (not scored) |
| National stability band | — (not banded) |

_See the country status map in_ [Montenegro Country Profile](../ME_country_prototype.md#country-status-map).

## Why It Failed

The site fails 1 exclusionary criterion(a) below. Exclusionary failures act as gates: a single confirmed failure removes the site from the brownfield candidate pool until the underlying measurement is refuted by site-specific Stage 3 work or until a regulatory threshold change makes the failure moot.

| Criterion | Code | Measured value | Threshold | Confidence | Justification |
| --- | --- | --- | --- | --- | --- |
| Emergency Planning Feasibility | EP-01 | {"composite_score": 25.0, "ep01_composite_score": 25.0} | DRV-02 composite < 30 OR nearest Level-2+ trauma centre > 60 km. | high | TRIGGERED: E8 — DRV-02 composite < 30 OR nearest Level-2+ trauma centre > 60 km. |

## Unlock Analysis


<!-- specialist key=unlock_analysis scope=site site_id=e77a7e7f-11ba-4e61-98da-f44471bc52ab bundle=ME_berane_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:47:07Z -->
**EP-01 Emergency Planning Feasibility** fails because the DRV-02 emergency-planning composite reads **25/100 — well below the 30/100 exclusionary threshold and registering NOT FEASIBLE** for an evacuation under the 16 km EPZ at the Berane site. The composite is dragged below the threshold by four binding sub-scores: the road-network sub-score is **0/100** (the road density and connectivity inside the Berane EPZ in the upper Lim valley are inadequate to support a credible evacuation under any reasonable summer or winter loading), the terrain sub-score is **10/100** (the site is hemmed in by the Bjelasica and Komovi ranges, with steep alpine valleys constraining every potential evacuation corridor), the geography sub-score is **10/100** (the same alpine context reads against IAEA SSG-35 evacuation feasibility on the geographic-constraints axis), and the special-population sub-score is **10/100** (the special-population estate inside the EPZ exceeds the screening tolerance against the constrained road and terrain envelope). Only the population sub-score (60/100) is in the middle band, but the four binding sub-scores leave the composite at 25/100 with `ep01_evacuation_feasible: false` on `high` data quality. This is a **structural** failure: the screening reads against a deeply-rooted geographic constraint (the upper Lim alpine valley) that no Stage 3 site-specific re-measurement can lift through engineering investment alone. A new road network, a relocated trauma centre and a re-zoning of the alpine special-population estate would all be programme-level public-investment decisions that exceed the scope of any plausible nuclear-deployment business case for a 110 MW thermal-replacement site. No further site-level investment is justified at this stage. The site would only re-enter the brownfield candidate pool if the wider Berane regional infrastructure were independently upgraded under unrelated public-investment programmes that materially change the road-network, terrain-corridor and trauma-centre envelopes. **Recommendation: Deprecate.**
<!-- /specialist key=unlock_analysis -->

## Evidence Limitations

- This profile is intentionally compact. Composite scoring, Monte-Carlo stability, family contributions, and the residual risk register are omitted because none of those views are informative for a site that is removed at the exclusionary screen.
- The exclusionary thresholds are screening thresholds; site-specific Stage 3 measurement can either confirm the failure or lift it. The unlock analysis above states whether that investment is justified.
