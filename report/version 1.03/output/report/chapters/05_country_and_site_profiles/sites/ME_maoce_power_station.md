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
| Available surface area | 43.5 ha |
| Available surface area for development | 43.5 ha |
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
| Seismic: Surface Rupture | NH-02 | {"nearest_fault_km": 3.94} | Capable fault within score-5 pivot distance. | medium | TRIGGERED: E1 — Capable fault within score-5 pivot distance. |

## Unlock Analysis


<!-- specialist key=unlock_analysis scope=site site_id=a851b5f3-8392-4766-82b9-379c6c04fe5d bundle=ME_maoce_power_station_site_bundle.json status=pending -->
> _Specialist interpretation pending: Unlock analysis (deprecate / characterize / escalate). Cursor agent fills via `python -m scripts.run_specialist_pass show --country <CC> --site-name <name> --key unlock_analysis` then `... patch --country <CC> --site-name <name> --key unlock_analysis --text-file <draft.md>`._
<!-- /specialist key=unlock_analysis -->

## Evidence Limitations

- This profile is intentionally compact. Composite scoring, Monte-Carlo stability, family contributions, and the residual risk register are omitted because none of those views are informative for a site that is removed at the exclusionary screen.
- The exclusionary thresholds are screening thresholds; site-specific Stage 3 measurement can either confirm the failure or lift it. The unlock analysis above states whether that investment is justified.
