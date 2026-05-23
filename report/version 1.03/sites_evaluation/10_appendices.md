<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## Appendix A — Exclusionary (E1–E9) and Avoidance (A1–A15) cross-reference

### A.1 E1–E9 → criterion anchor

| Code | Anchor criterion(ia)         | Project threshold (this doc)                                |
| ---- | ---------------------------- | ----------------------------------------------------------- |
| E1   | NH-02                        | < 5 km capable fault (project) / < 8 km (SSG-35).           |
| E2   | NH-03                        | Unacceptable liquefaction with no remedy.                   |
| E3   | NH-04                        | Catastrophic landslide / slope > 25°.                       |
| E4   | NH-07                        | < 50 km Holocene volcano or in mapped hazard zone.          |
| E5   | NH-05 (karst)                | Review-only in current scoring; hard exclusion requires site-specific no-remedy collapse evidence. |
| E6   | NH-05 (mining / O&G)         | Review-only in current scoring; EGDI mine-feature proximity is ranking-only. |
| E7   | NS-08                        | Site within strict-category Natura 2000 / WDPA.             |
| E8   | EP-01                        | DRV-02 composite < 30 / fundamentally infeasible EP.        |
| E9   | NS-01                        | No viable cooling source AND dry cooling not viable.        |

### A.2 A1–A15 → criterion anchor

| Code  | Anchor criterion(ia)        | Project threshold |
| ----- | --------------------------- | ----------------- |
| A2-A4 | HI-01                       | Large / medium civilian airport < 15 km / military < 30 km → fail; SSG-35 sub-thresholds embedded in §4. **A1 (small / GA / heliport < 10 km) retired in Phase 1C of v1.03 feedback closure (reviewer #183):** small classes are persisted as informational only. |
| A5–A6 | HI-06                       | ≥ 30 km from ranges; ≥ 8 km from ammunition storage. |
| A7    | HI-02                       | ≥ 5 km from major hazard storage. |
| A8    | HI-03                       | ≥ 8 km from hazardous-cloud sources. |
| A9    | NH-08                       | ≥ 10 km from sea / ≥ 1 km from lake or ≥ 50 m AMSL. |
| A10   | NH-01                       | `PGA(2475 yr) <= 0.5 g`; use as the score-5 design-envelope boundary. |
| A11   | NH-09                       | River distance ≥ 4 km OR vertical separation ≥ 30.5 m. |
| A12   | RI-04                       | Population thresholds per §4 RI-04 / RI-05 tables. |
| A13   | NS-02 (also BF-01)          | Transmission ≥ reference SMR net MWe within feasible distance. |
| A14   | NS-03                       | Heavy-haul access ≥ 700 t segment capacity. |
| A15   | NS-05 (also BF-02)          | ≥ 14 ha contiguous industrial land. |

---

## Appendix B — Weight reconciliation (project vs IAEA/EPRI matrix)

| Category | IAEA/EPRI matrix (`docs/expert_…_matrix.md`) | This document (engineer-team factors) | Δ                |
| -------- | -------------------------------------------- | ------------------------------------- | ---------------- |
| BF       | 4.0 %                                        | 4.6 %                                 | + 0.6 pp         |
| NH       | 23.0 %                                       | 29.0 %                                | + 6.0 pp         |
| HI       | 10.0 %                                       | 15.5 %                                | + 5.5 pp         |
| RI       | 15.0 %                                       | 13.8 %                                | − 1.2 pp         |
| EP       | 10.0 %                                       | 10.2 %                                | + 0.2 pp         |
| NS       | 38.0 %                                       | 26.9 %                                | − 11.1 pp        |
| **Σ**    | **100 %**                                    | **100 %**                             | —                |

**Drivers of the divergence**

- The team weighted **NH-07 volcanism** at 10 (highest possible) and **NH-01 / NH-02
  seismic** at 9; this lifts the NH bucket.
- **HI-01 aircraft** and **HI-02 / HI-03 industrial-explosion / toxic** weights of 7
  raise the HI bucket above the matrix default.
- The team weighted **NS-01 / NS-02 / NS-03 infrastructure** at 8 (significant) but did
  **not** uplift the larger NS-09 / NS-10 / NS-11 / NS-12 / NS-13 set; the matrix gives
  them more relative share, hence the NS reduction.
- **RI-05 (large population centres distance)** carries the team's highest weight (10),
  partially compensating for the lower RI-04 weight.

Sensitivity runs in §6 vary each category back to the matrix baseline (±20 %) so the
final shortlist is reported under both weight schemes.

---

## Revision history

| Date       | Change                                                                                                                                                                                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-21 | Initial issue. Aggregates the IAEA/EPRI matrix (`docs/expert_siting_criteria_evaluation_matrix.md`), the 1–5 scoring matrix (`requirements/06_scoring_matrix.md`), the audit prioritisation (`audit/post_processing/.../20260418_2_5_7_scoring_method.md`) and engineer-team draft thresholds. Codifies the 0–10 scoring scale, weight factors (1–10), normalised weights, pass / fail rules, and LLM ↔ API merge precedence. |
