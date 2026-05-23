# Criterion correlation flag list

- Stamp: `20260425`
- Threshold: |ρ| ≥ 0.70
- Pairs observed: 2904
- Flagged pairs: 4
- Source CSV: `audit/post_processing/06_scoring/20260425_criterion_correlation.csv`
- Pearson heatmap: `report/output/sensitivity/20260425/figures/correlation/criterion_correlation_pearson.png`
- Spearman heatmap: `report/output/sensitivity/20260425/figures/correlation/criterion_correlation_spearman.png`

## Flagged criterion pairs

| Criterion A | Criterion B | Pearson | Spearman | n |
| --- | --- | ---: | ---: | ---: |
| HI-02 (Industrial explosions (Seveso / IED)) | HI-04 (External fires) | +1.000 | +1.000 | 2904 |
| BF-02 (Land / nuclear-island footprint) | NS-05 (Land availability / ownership / zoning) | +0.982 | +0.992 | 2904 |
| EP-01 (Emergency-plan feasibility (composite)) | RI-04 (Population density (EPZ rings)) | +0.722 | +0.747 | 2904 |
| NH-01 (Seismic ground motion (PGA)) | NH-02 (Seismic surface rupture (capable faults)) | +0.619 | +0.722 | 2904 |
