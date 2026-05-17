<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## 5. Composite calculation worked example

For an illustrative site `S`:

1. Each connector populates the API DB; the LLM pipeline populates the LLM DB; the merge
   step (§7) selects the best value per criterion.
2. The scoring engine reads §4 bands and writes one row per `site × criterion × SMR design`
   into `ranking_scores` (with `score_low` / `score_high` for low-quality bands).
3. The composite is computed as `S = Σ wᵢ · cᵢ` with `wᵢ` from §3 normalised weights.
4. Excluded criteria short-circuit the composite — site is reported as **Excluded** with
   the triggering E-code.
5. Sites with all `cᵢ ≥ 5.0` enter the Phase-3 ranking; ties broken by (a) fewer
   avoidance flags, (b) higher installed capacity, (c) alphabetical site name.

**Worked example (abbreviated)**

| Criterion | cᵢ (0–10) | wᵢ      | wᵢ·cᵢ |
| --------- | --------- | ------- | ----- |
| NH-01     | 7         | 0.030   | 0.210 |
| NH-02     | 9         | 0.030   | 0.270 |
| NH-09     | 6         | 0.027   | 0.162 |
| RI-04     | 8         | 0.027   | 0.216 |
| RI-05     | 7         | 0.034   | 0.238 |
| NS-01     | 8         | 0.027   | 0.216 |
| NS-02     | 9         | 0.027   | 0.243 |
| (… 41 more)|          |         |       |
| **Σ**     |           | **1.00**| **6.7** |

Composite `S = 6.7 / 10`. Site passes Phase 2 (no exclusion, all ≥ 5.0) and ranks at the
70th percentile of the 0–10 scale.

---

## 6. Sensitivity and uncertainty handling

| Parameter                          | Default            | Notes                                                                  |
| ---------------------------------- | ------------------ | ---------------------------------------------------------------------- |
| Weight perturbation (per category) | ± 20 %             | Re-rank under each perturbation; report ranking-stability index.       |
| Per-criterion sub-weight perturbation | ± 30 % (top-5 by influence) | Cover RI-05, NH-07, NH-01 / 02, NS-01 / 02 / 03.            |
| Score uncertainty (low quality)    | ± 1 band uniform   | Monte Carlo, 1 000 iterations (10 000 if budget allows).               |
| Threshold sensitivity              | ± 25 % on numeric thresholds | E.g. 5 km fault → 4–6 km; 30 km airport → 22–38 km.           |
| LLM-vs-API divergence              | API-only / LLM-only / fused | Compare top-20 stability under each.                          |
| Country balance                    | Verify top-20 not artefactually concentrated by data-coverage country | LL-022 risk flag.       |

---
