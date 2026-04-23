<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## 3. Master weight table

The 48 criteria below cover BF (basic filters), NH (natural hazards), HI (human-induced
hazards), RI (radiological impact), EP (emergency planning) and NS (non-safety). The
**weight factor (1–10)** column captures engineering-team intent (project draft data where
provided; otherwise reasoned estimate aligned with the IAEA/EPRI matrix). Normalised
weights below sum to 100.0%.

| ID    | Criterion                                       | Phase            | Weight factor (1–10) | Normalised weight |
| ----- | ----------------------------------------------- | ---------------- | :------------------: | ----------------: |
| BF-01 | Grid export / connection adequacy               | Basic filter     | 8                    | 2.8%              |
| BF-02 | Land / nuclear-island footprint                 | Basic filter     | 5                    | 1.8%              |
| NH-01 | Seismic — ground motion (PGA)                   | Screen + Rank    | 9                    | 3.2%              |
| NH-02 | Seismic — capable fault distance                | Screen (Excl.)   | 9                    | 3.2%              |
| NH-03 | Geotechnical — liquefaction                     | Screen + Rank    | 7                    | 2.5%              |
| NH-04 | Geotechnical — slope stability                  | Screen + Rank    | 5                    | 1.8%              |
| NH-05 | Geotechnical — subsidence / karst / mining      | Screen + Rank    | 7                    | 2.5%              |
| NH-06 | Geotechnical — foundation conditions            | Rank             | 5                    | 1.8%              |
| NH-07 | Volcanism                                        | Screen (Excl.)   | 10                   | 3.5%              |
| NH-08 | Coastal flooding (surge / tsunami)              | Screen + Rank    | 6                    | 2.1%              |
| NH-09 | River flooding                                   | Screen + Rank    | 8                    | 2.8%              |
| NH-10 | Extreme winds                                    | Rank             | 3                    | 1.1%              |
| NH-11 | Extreme precipitation (rain / snow / drought)   | Rank             | 3                    | 1.1%              |
| NH-12 | Extreme temperatures                             | Rank             | 4                    | 1.4%              |
| NH-13 | Forest / wildfire                                | Rank             | 3                    | 1.1%              |
| NH-14 | Combined hazards                                 | Rank             | 3                    | 1.1%              |
| HI-01 | Aircraft crash hazard                            | Screen + Rank    | 7                    | 2.5%              |
| HI-02 | Industrial explosions (Seveso / IED)             | Screen + Rank    | 7                    | 2.5%              |
| HI-03 | Toxic / gas releases                             | Screen + Rank    | 7                    | 2.5%              |
| HI-04 | External fires (storage, pipelines)              | Screen + Rank    | 6                    | 2.1%              |
| HI-05 | Transport hazards (hazmat road / rail / pipe)    | Rank             | 6                    | 2.1%              |
| HI-06 | Military installations                           | Screen + Rank    | 6                    | 2.1%              |
| HI-07 | Electromagnetic interference                     | Rank             | 2                    | 0.7%              |
| HI-08 | Other nuclear installations                      | Rank             | 3                    | 1.1%              |
| RI-01 | Atmospheric dispersion (wind, stability, BLH)    | Rank             | 6                    | 2.1%              |
| RI-02 | Surface water dispersion                         | Rank             | 5                    | 1.8%              |
| RI-03 | Groundwater dispersion                           | Rank             | 5                    | 1.8%              |
| RI-04 | Population density (5/16/25/80 km rings)         | Screen + Rank    | 8                    | 2.8%              |
| RI-05 | Distance to large population centres (>50 k)     | Rank             | 10                   | 3.5%              |
| RI-06 | Population projections (60-yr design life)       | Rank             | 5                    | 1.8%              |
| EP-01 | Emergency-plan feasibility (composite)           | Screen + Rank    | 8                    | 2.8%              |
| EP-02 | Evacuation routes (road network)                 | Rank             | 6                    | 2.1%              |
| EP-03 | Physical-geography constraints                   | Rank             | 5                    | 1.8%              |
| EP-04 | Special populations (hospitals, prisons, …)      | Rank             | 6                    | 2.1%              |
| EP-05 | Concurrent-hazard impact on EP                   | Rank             | 4                    | 1.4%              |
| NS-01 | Cooling water / ultimate heat sink               | Screen + Rank    | 8                    | 2.8%              |
| NS-02 | Grid connection (detailed: voltage, capacity)    | Screen + Rank    | 8                    | 2.8%              |
| NS-03 | Transport access (heavy haul road / rail / port) | Screen + Rank    | 8                    | 2.8%              |
| NS-04 | Site topography / grading                        | Rank             | 6                    | 2.1%              |
| NS-05 | Land availability / ownership / zoning           | Screen + Rank    | 5                    | 1.8%              |
| NS-06 | Existing infrastructure reuse                    | Rank             | 5                    | 1.8%              |
| NS-07 | Environmental impact (non-radiological)          | Screen + Rank    | 5                    | 1.8%              |
| NS-08 | Ecological sensitivity (Natura 2000 / WDPA)      | Screen + Rank    | 6                    | 2.1%              |
| NS-09 | Socioeconomic impact                             | Rank             | 5                    | 1.8%              |
| NS-10 | Workforce availability                           | Rank             | 4                    | 1.4%              |
| NS-11 | Coal-to-nuclear synergies                        | Rank             | 6                    | 2.1%              |
| NS-12 | Regulatory / political environment               | Rank             | 6                    | 2.1%              |
| NS-13 | Construction logistics                           | Rank             | 4                    | 1.4%              |
| **Σ** |                                                  |                  | **283**              | **100.0%**        |

**Category roll-ups**

| Category                  | Σ factor | Σ normalised |
| ------------------------- | -------: | -----------: |
| Basic filters (BF)        |       13 |        4.6 % |
| Natural hazards (NH)      |       82 |       29.0 % |
| Human-induced (HI)        |       44 |       15.5 % |
| Radiological impact (RI)  |       39 |       13.8 % |
| Emergency planning (EP)   |       29 |       10.2 % |
| Non-safety (NS)           |       76 |       26.9 % |
| **Total**                 |  **283** |   **100.0 %**|

Compared with the IAEA/EPRI baseline in `docs/expert_siting_criteria_evaluation_matrix.md`
(NH 23 %, HI 10 %, RI 15 %, EP 10 %, NS 38 %, BF 4 %), the project weights uplift NH and HI
(driven by team weight factors of 9–10 on volcanism, faulting, flood and aircraft) and
modestly relax NS. See **Appendix B** for a side-by-side reconciliation.

---
