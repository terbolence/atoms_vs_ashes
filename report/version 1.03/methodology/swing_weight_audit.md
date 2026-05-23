# Swing-weight audit

- Stamp: `20260523`
- Pool: 362 (site, SMR) pairs from the latest baseline rescore
- Source CSV: `audit/post_processing/06_scoring/20260523_swing_weight_audit.csv`

## What this audit shows

The Phase 1.2 weights were elicited declaratively (rubric author judgement).
**Swing weights** rescale each criterion by its observed 0-10 score range
across the survivor pool, then renormalise. A criterion that scores 5-7 for
every site adds little discriminating power, so its swing weight drops.

Re-running the composite under the swing profile (``w_swing``, written by
``run_weight_sensitivity``) is part of the sensitivity suite; this file is
the human-readable companion to the ``audit_post_processing`` CSV that
documents the per-criterion delta.

## Per-criterion table (sorted by |Δ|)

| Criterion | Family | Declared | Observed range | Swing | Δ (swing − declared) |
| --- | --- | ---: | --- | ---: | ---: |
| RI-05 (Distance to large population centres (>50 k)) | RI | 0.0435 | [0.00, 9.50] | 0.0722 | +0.0287 |
| NH-01 (Seismic ground motion (PGA)) | NH | 0.0391 | [0.00, 9.50] | 0.0649 | +0.0258 |
| NS-02 (Grid connection (detailed)) | NS | 0.0348 | [0.00, 9.50] | 0.0577 | +0.0229 |
| NH-09 (River flooding) | NH | 0.0348 | [5.50, 7.50] | 0.0122 | -0.0226 |
| HI-05 (Transport hazards (hazmat road / rail / pipe)) | HI | 0.0261 | — | 0.0046 | -0.0215 |
| NS-11 (Coal-to-nuclear synergies) | NS | 0.0261 | — | 0.0046 | -0.0215 |
| NS-12 (Regulatory / political environment) | NS | 0.0261 | [5.00, 5.00] | 0.0046 | -0.0215 |
| RI-01 (Atmospheric dispersion (wind, stability, BLH)) | RI | 0.0261 | [5.00, 5.00] | 0.0046 | -0.0215 |
| HI-03 (Toxic / gas releases) | HI | 0.0304 | [0.00, 9.50] | 0.0505 | +0.0201 |
| NS-06 (Existing infrastructure reuse) | NS | 0.0217 | [5.00, 5.00] | 0.0038 | -0.0179 |
| NS-07 (Environmental impact (non-radiological)) | NS | 0.0217 | — | 0.0038 | -0.0179 |
| NS-09 (Socioeconomic impact) | NS | 0.0217 | — | 0.0038 | -0.0179 |
| NH-08 (Coastal flooding (storm surge, tsunami)) | NH | 0.0261 | [0.00, 9.50] | 0.0433 | +0.0172 |
| EP-05 (Concurrent-hazard impact on EP) | EP | 0.0174 | — | 0.0030 | -0.0144 |
| NS-10 (Workforce availability) | NS | 0.0174 | [5.00, 5.00] | 0.0030 | -0.0144 |
| NS-13 (Construction logistics) | NS | 0.0174 | [5.00, 5.00] | 0.0030 | -0.0144 |
| NS-05 (Land availability / ownership / zoning) | NS | 0.0217 | [0.00, 9.50] | 0.0361 | +0.0143 |
| RI-04 (Population density (EPZ rings)) | RI | 0.0348 | [1.50, 9.50] | 0.0486 | +0.0138 |
| HI-01 (Aircraft crash hazard) | HI | 0.0304 | [1.50, 9.50] | 0.0425 | +0.0121 |
| NH-05 (Subsidence / karst / mining / oil & gas) | NH | 0.0304 | [1.50, 9.50] | 0.0425 | +0.0121 |
| HI-08 (Other nuclear installations) | HI | 0.0130 | — | 0.0023 | -0.0108 |
| NH-13 (Forest / wildfire) | NH | 0.0130 | — | 0.0023 | -0.0108 |
| EP-04 (Special populations (hospitals, prisons, care homes)) | EP | 0.0261 | [1.50, 9.50] | 0.0365 | +0.0104 |
| NS-04 (Site topography / grading) | NS | 0.0261 | [1.50, 9.50] | 0.0365 | +0.0104 |
| HI-02 (Industrial explosions (Seveso / IED)) | HI | 0.0304 | [5.50, 9.50] | 0.0213 | -0.0092 |
| EP-03 (Physical-geography constraints) | EP | 0.0217 | [1.50, 9.50] | 0.0304 | +0.0086 |
| BF-02 (Land / nuclear-island footprint) | BF | 0.0217 | [1.50, 9.50] | 0.0304 | +0.0086 |
| RI-02 (Surface water dispersion) | RI | 0.0217 | [1.50, 9.50] | 0.0304 | +0.0086 |
| RI-06 (Population projections (60-yr design life)) | RI | 0.0217 | [1.50, 9.50] | 0.0304 | +0.0086 |
| NH-14 (Combined hazards) | NH | 0.0130 | [0.00, 9.50] | 0.0216 | +0.0086 |
| HI-04 (External fires) | HI | 0.0261 | [5.50, 9.50] | 0.0182 | -0.0079 |
| NS-01 (Cooling water / ultimate heat sink) | NS | 0.0348 | [3.00, 10.00] | 0.0425 | +0.0078 |
| NH-10 (Extreme winds) | NH | 0.0130 | [1.50, 9.50] | 0.0182 | +0.0052 |
| NH-11 (Extreme precipitation (rain, snow, drought)) | NH | 0.0130 | [2.00, 10.00] | 0.0182 | +0.0052 |
| NS-03 (Transport access (heavy haul road / rail / port)) | NS | 0.0348 | [5.00, 10.00] | 0.0304 | -0.0044 |
| HI-07 (Electromagnetic interference) | HI | 0.0087 | [1.50, 9.50] | 0.0122 | +0.0035 |
| HI-06 (Military installations) | HI | 0.0261 | [0.00, 5.00] | 0.0228 | -0.0033 |
| NH-12 (Extreme temperatures) | NH | 0.0174 | [3.50, 8.50] | 0.0152 | -0.0022 |
| EP-02 (Evacuation routes (road network)) | EP | 0.0261 | [1.50, 7.50] | 0.0273 | +0.0013 |
| RI-03 (Groundwater dispersion) | RI | 0.0217 | [1.50, 7.50] | 0.0228 | +0.0010 |
| NH-06 (Foundation conditions (bearing, bedrock, groundwater)) | NH | 0.0217 | [0.00, 5.50] | 0.0209 | -0.0009 |
| EP-01 (Emergency-plan feasibility (composite)) | EP | 0.0000 | [1.50, 7.50] | 0.0000 | +0.0000 |
| BF-01 (Grid export / connection adequacy (basic-filter note)) | BF | 0.0000 | [1.50, 9.50] | 0.0000 | +0.0000 |
| NH-02 (Seismic surface rupture (capable faults)) | NH | 0.0000 | [0.00, 9.50] | 0.0000 | +0.0000 |
| NH-03 (Geotechnical - settlement and liquefaction) | NH | 0.0000 | [3.50, 9.50] | 0.0000 | +0.0000 |
| NH-04 (Geotechnical - slope stability) | NH | 0.0000 | [3.50, 9.50] | 0.0000 | +0.0000 |
| NH-07 (Volcanism) | NH | 0.0000 | [5.50, 9.50] | 0.0000 | +0.0000 |
| NS-08 (Ecological sensitivity (Natura 2000 / WDPA)) | NS | 0.0000 | [1.50, 9.50] | 0.0000 | +0.0000 |

## Reading the deltas

- **Δ > 0**: the criterion is **up-weighted** by swing — its observed
  range across the pool is wider than the rubric's declared weight
  implies. Watch for hidden drivers of the ranking.
- **Δ < 0**: the criterion is **down-weighted** — it has narrow
  observed range, so its declared weight is partly being absorbed by
  renormalisation. The composite is robust to its weight.
- **Δ ≈ 0**: declared weight is roughly aligned with the swing.

## Provenance

- Generator: `python -m scripts.generate_swing_weight_audit`
- Module: `atoms_vs_ashes.scoring._swing_weights`
- Profile injected into the suite: `w_swing` (see `atoms_vs_ashes.scoring._weight_perturbation`).
