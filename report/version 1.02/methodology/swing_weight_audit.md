# Swing-weight audit

- Stamp: `20260425`
- Pool: 2904 (site, SMR) pairs from the latest baseline rescore
- Source CSV: `audit/post_processing/06_scoring/20260425_swing_weight_audit.csv`

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
| NH-01 (Seismic ground motion (PGA)) | NH | 0.0318 | [0.00, 9.50] | 0.0774 | +0.0456 |
| RI-04 (Population density (EPZ rings)) | RI | 0.0283 | [1.50, 9.50] | 0.0579 | +0.0297 |
| NH-02 (Seismic surface rupture (capable faults)) | NH | 0.0318 | [0.00, 7.50] | 0.0611 | +0.0293 |
| NH-07 (Volcanism) | NH | 0.0353 | [5.00, 5.00] | 0.0091 | -0.0263 |
| RI-05 (Distance to large population centres (>50 k)) | RI | 0.0353 | [5.00, 5.00] | 0.0091 | -0.0263 |
| EP-01 (Emergency-plan feasibility (composite)) | EP | 0.0283 | [0.00, 7.50] | 0.0543 | +0.0261 |
| NH-05 (Subsidence / karst / mining / oil & gas) | NH | 0.0247 | [1.50, 9.50] | 0.0507 | +0.0260 |
| NH-04 (Geotechnical - slope stability) | NH | 0.0177 | [0.00, 9.50] | 0.0430 | +0.0253 |
| NS-04 (Site topography / grading) | NS | 0.0212 | [1.50, 9.50] | 0.0435 | +0.0223 |
| NH-09 (River flooding) | NH | 0.0283 | [5.00, 5.00] | 0.0072 | -0.0210 |
| BF-02 (Land / nuclear-island footprint) | BF | 0.0177 | [1.50, 9.50] | 0.0362 | +0.0185 |
| NS-05 (Land availability / ownership / zoning) | NS | 0.0177 | [1.50, 9.50] | 0.0362 | +0.0185 |
| RI-02 (Surface water dispersion) | RI | 0.0177 | [1.50, 9.50] | 0.0362 | +0.0185 |
| RI-06 (Population projections (60-yr design life)) | RI | 0.0177 | [1.50, 9.50] | 0.0362 | +0.0185 |
| EP-04 (Special populations (hospitals, prisons, care homes)) | EP | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| HI-05 (Transport hazards (hazmat road / rail / pipe)) | HI | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| NH-08 (Coastal flooding (storm surge, tsunami)) | NH | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| NS-11 (Coal-to-nuclear synergies) | NS | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| NS-12 (Regulatory / political environment) | NS | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| RI-01 (Atmospheric dispersion (wind, stability, BLH)) | RI | 0.0212 | [5.00, 5.00] | 0.0054 | -0.0158 |
| NS-02 (Grid connection (detailed)) | NS | 0.0283 | [3.50, 9.50] | 0.0435 | +0.0152 |
| NS-01 (Cooling water / ultimate heat sink) | NS | 0.0283 | [5.00, 7.00] | 0.0145 | -0.0138 |
| HI-03 (Toxic / gas releases) | HI | 0.0247 | [1.50, 7.50] | 0.0380 | +0.0133 |
| EP-03 (Physical-geography constraints) | EP | 0.0177 | [5.00, 5.00] | 0.0045 | -0.0131 |
| NS-06 (Existing infrastructure reuse) | NS | 0.0177 | [5.00, 5.00] | 0.0045 | -0.0131 |
| NS-07 (Environmental impact (non-radiological)) | NS | 0.0177 | [5.00, 5.00] | 0.0045 | -0.0131 |
| NS-09 (Socioeconomic impact) | NS | 0.0177 | [5.00, 5.00] | 0.0045 | -0.0131 |
| RI-03 (Groundwater dispersion) | RI | 0.0177 | [5.00, 5.00] | 0.0045 | -0.0131 |
| HI-01 (Aircraft crash hazard) | HI | 0.0247 | [3.50, 5.50] | 0.0127 | -0.0121 |
| EP-02 (Evacuation routes (road network)) | EP | 0.0212 | [1.50, 7.50] | 0.0326 | +0.0114 |
| EP-05 (Concurrent-hazard impact on EP) | EP | 0.0141 | [5.00, 5.00] | 0.0036 | -0.0105 |
| NS-10 (Workforce availability) | NS | 0.0141 | [5.00, 5.00] | 0.0036 | -0.0105 |
| NS-13 (Construction logistics) | NS | 0.0141 | [5.00, 5.00] | 0.0036 | -0.0105 |
| NS-03 (Transport access (heavy haul road / rail / port)) | NS | 0.0283 | [5.00, 10.00] | 0.0362 | +0.0079 |
| HI-08 (Other nuclear installations) | HI | 0.0106 | [5.00, 5.00] | 0.0027 | -0.0079 |
| NH-10 (Extreme winds) | NH | 0.0106 | [9.50, 9.50] | 0.0027 | -0.0079 |
| NH-11 (Extreme precipitation (rain, snow, drought)) | NH | 0.0106 | [4.00, 4.00] | 0.0027 | -0.0079 |
| NH-13 (Forest / wildfire) | NH | 0.0106 | [5.00, 5.00] | 0.0027 | -0.0079 |
| NH-14 (Combined hazards) | NH | 0.0106 | [5.00, 5.00] | 0.0027 | -0.0079 |
| NH-06 (Foundation conditions (bearing, bedrock, groundwater)) | NH | 0.0177 | [0.00, 5.50] | 0.0249 | +0.0072 |
| NH-12 (Extreme temperatures) | NH | 0.0141 | [7.50, 9.50] | 0.0072 | -0.0069 |
| HI-07 (Electromagnetic interference) | HI | 0.0071 | [5.00, 5.00] | 0.0018 | -0.0053 |
| HI-02 (Industrial explosions (Seveso / IED)) | HI | 0.0247 | [5.00, 9.50] | 0.0285 | +0.0038 |
| HI-04 (External fires) | HI | 0.0212 | [5.00, 9.50] | 0.0244 | +0.0032 |
| BF-01 (Grid export / connection adequacy) | BF | 0.0283 | [5.50, 9.50] | 0.0290 | +0.0007 |
| NH-03 (Geotechnical - settlement and liquefaction) | NH | 0.0247 | [1.50, 5.50] | 0.0254 | +0.0006 |
| HI-06 (Military installations) | HI | 0.0212 | [1.50, 5.50] | 0.0217 | +0.0005 |
| NS-08 (Ecological sensitivity (Natura 2000 / WDPA)) | NS | 0.0212 | [3.50, 7.50] | 0.0217 | +0.0005 |

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
