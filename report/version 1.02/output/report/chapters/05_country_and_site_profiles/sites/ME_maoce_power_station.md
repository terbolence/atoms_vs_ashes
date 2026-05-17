# Maoce Power Station Site Profile

_Montenegro | tested against the NuScale VOYGR-6 reference deployment envelope | **Hard-fail at the exclusionary screen**._

Maoce Power Station is a coal/thermal site in Montenegro that does not survive the exclusionary screen against the NuScale VOYGR-6 reference deployment envelope. This profile records the screening evidence that drives the failure and provides the siting expert's read on whether further characterization is justified. It is not a site-suitability determination, vendor recommendation, or licensing finding.

## Site Snapshot

| Field | Value |
| --- | --- |
| Site name | Maoce Power Station |
| Country | Montenegro |
| Coordinates | 43.3600, 19.3600 |
| Subnational unit | Pljevlja |
| Installed thermal capacity (source data) | 500 MW |
| Operating status | cancelled |
| Parent owner(s) | - |
| Generating units on record | 1 |
| Screening verdict | Hard-fail (exclusionary) |
| Failed exclusionary criteria | NH-02 |
| Composite score | — (not scored) |
| National stability band | — (not banded) |

_See the country status map in_ [Montenegro Country Profile](../ME_country_prototype.md#country-status-map).

## Why It Failed

The site fails 1 exclusionary criterion(a) below. Exclusionary failures act as gates: a single confirmed failure removes the site from the brownfield candidate pool until the underlying measurement is refuted by site-specific Stage 3 work or until a regulatory threshold change makes the failure moot.

| Criterion | Code | Measured value | Threshold | Confidence | Justification |
| --- | --- | --- | --- | --- | --- |
| Seismic: Surface Rupture | NH-02 | {"nearest_fault_km": 3.94} | Capable fault within 8 km. | medium | TRIGGERED: E1 — Capable fault within 8 km. |

## Unlock Analysis


<!-- specialist key=unlock_analysis scope=site site_id=a851b5f3-8392-4766-82b9-379c6c04fe5d bundle=ME_maoce_power_station_site_bundle.json status=filled by=cursor-agent filled_at=2026-05-03T16:47:07Z -->
**NH-02 Seismic: Surface Rupture** fails because the nearest mapped capable fault (MECF00A, an active right-lateral strike-slip structure with a slip rate of 0.17 mm/yr) is **3.94 km from the site**, deep inside the 8 km project A2 capable-fault screening exclusion radius and inside the 5 km regulatory floor that no Stage 3 PSHA can lift through measurement alone. The wider seismotectonic context is consistent with the screening read: the regional capable-fault catalogue records **8 capable faults within 50 km** of the site, reflecting the active Dinaric thrust belt of northern Montenegro where the Maoće site sits in the Pljevlja basin against the Durmitor-Sinjajevina massif. This is a **structural** failure analogous to the Ploče case on the Croatian Adriatic coast: a site-specific PSHA can refine the design-basis ground motion for the project, but it cannot move the fault, change its capability classification, or relax the SSR-1 capable-fault stand-off requirement. The site fails on the geometry of the fault network with respect to the brownfield envelope, and the buildable patch cannot be relocated within the existing thermal complex footprint to clear the 8 km buffer (the Pljevlja-basin local geomorphology constrains the alternative siting envelope to within the same fault corridor). No further site-level investment is justified at this stage. The site would only re-enter the brownfield candidate pool if a future revision of the capable-fault catalogue downgrades MECF00A (the catalogue is updated periodically as new geodetic and palaeoseismic evidence accrues), or if the regulatory framework for capable-fault stand-off were materially changed, neither of which can be assumed for programme-planning purposes. **Recommendation: Deprecate.**
<!-- /specialist key=unlock_analysis -->

## Evidence Limitations

- This profile is intentionally compact. Composite scoring, Monte-Carlo stability, family contributions, and the residual risk register are omitted because none of those views are informative for a site that is removed at the exclusionary screen.
- The exclusionary thresholds are screening thresholds; site-specific Stage 3 measurement can either confirm the failure or lift it. The unlock analysis above states whether that investment is justified.
