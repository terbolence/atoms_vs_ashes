<!-- Part of Sites evaluation — see [00_index.md](00_index.md). -->

## 1. Purpose and scope

### 1.1 What this document is

A **prescriptive** scoring specification. For every siting criterion in scope it states:

1. **Why the criterion matters** for an NPP (nuclear power plant) and which engineering /
   safety / business question it answers.
2. The **pass / fail rule** (default mark **5.0** on a 0–10 scale; **0** for confirmed
   exclusionary failures with no engineering remedy).
3. The **0–10 marking scale** with concrete numeric thresholds.
4. The **weight factor** (engineering-team scale 1–10) and the corresponding **normalised
   composite weight** (% of total) that feeds the weighted-mean composite score.
5. The **primary data anchor** (DB column or LLM prompt) so the merge step knows where the
   value lives.

### 1.2 What this document is not

- Not a regulatory submission. National regulators may impose stricter thresholds.
- Not a replacement for vendor-specific design envelopes (e.g. NuScale VOYGR-6 PGA limits).
- Not a substitute for site-specific engineering studies — Phase 1 and 2 outputs guide the
  shortlist; Phase 3 ranking is comparative, not licensing-grade.

### 1.3 How it is consumed downstream

| Consumer                               | Use                                                                                                              |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Final report (narrative)               | Per-criterion section text and per-site score justification tables                                               |
| Phase 2 screening engine               | Pass/fail evaluator per site × criterion × SMR design (writes `screening_verdicts`)                              |
| Phase 3 ranking engine                 | 0–10 score per site × criterion (writes `ranking_scores`); composite written to `composite_rankings`             |
| LLM ↔ API DB merge                     | Per-criterion priority order: API value → LLM value → expert default. See §7 for the rule table.                 |
| Sensitivity analysis                   | Provides weight ±20% perturbation envelope and per-criterion score uncertainty bands for the Monte Carlo runs    |

---

## 2. Scoring framework

### 2.1 Marking scale (0–10)

Every ranking criterion receives an integer or one-decimal score on a **0–10** scale where
**higher = more favourable**. The five descriptors below align with the legacy 1–5 scale used
in `requirements/06_scoring_matrix.md` (mapping: 1→2, 2→4, 3→6, 4→8, 5→10).

| Score band | Descriptor    | Interpretation                                                                                              |
| :--------: | ------------- | ----------------------------------------------------------------------------------------------------------- |
| 9 – 10     | Outstanding   | Significantly exceeds requirements; baseline cost / risk; strong margin in every sub-metric.                |
| 7 – 8      | Excellent     | Comfortably meets requirements; minor favourable conditions; routine engineering provisions.                |
| 5 – 6      | Acceptable    | Meets the **pass mark**; standard mitigation may be needed; typical European industrial fit.                |
| 3 – 4      | Marginal      | Approaches the discretionary gate; **fails Phase 2** unless waived; significant mitigation required.        |
| 1 – 2      | Poor          | Does not meet requirements without major intervention; usually associated with an active E-condition.       |
| 0          | **Exclude**   | Confirmed E1–E9 trigger with no practicable engineering remedy → site removed from candidate set.           |

### 2.2 Pass / fail cut

- **Default pass mark = 5.0.** A criterion score below 5.0 fails the discretionary gate
  (Phase 2) for that family unless the project explicitly waives.
- **Exclusion = 0.** When an E-condition (see §A.1 below) is met and **no documented,
  practicable remedy** exists, the criterion scores **0** and the site is removed. If a
  remedy is plausible but not yet demonstrated, the score is **capped at 4.0** pending
  expert review.
- **Fail / Pass / Good / Excellent / Outstanding bands** map onto the table in §2.1 — this
  is the same vocabulary the engineering team uses in the project draft scoring framework.

### 2.3 Weight system

#### 2.3.1 Two-layer representation

Each criterion carries two numbers:

| Layer                  | Range  | Source                                                                                  |
| ---------------------- | ------ | --------------------------------------------------------------------------------------- |
| **Weight factor**      | 1 – 10 | Engineering-team intent (relative importance). Provided in §3 below.                    |
| **Normalised weight** | 0 – 100 % | Computed from the weight factor: `wᵢ = factorᵢ / Σ factor`. Sums to 100% across criteria. |

The **normalised weight** is what enters the composite formula. The **weight factor** is
preserved so the team can adjust priorities without re-deriving percentages.

#### 2.3.2 Sensitivity envelope

Per `requirements/06_scoring_matrix.md §8.4`, each weight factor is varied **±20%**
(relative) for the Monte Carlo ranking-stability runs. Score uncertainty is propagated as a
**±1 band range** when the underlying data quality is `low`, and as a **fixed value** when
quality is `medium` or `high`.

### 2.4 Composite score formula

Let `wᵢ` be the normalised decimal weight (Σwᵢ = 1.0) and `cᵢ ∈ [0, 10]` the criterion
score. The composite site score is:

\[
S(\text{site}) \;=\; \sum_{i=1}^{N} w_i \cdot c_i
\]

`S` is reported on a 0–10 scale (a weighted mean of the per-criterion scores). For
communication with the legacy 1–5 audience, divide by 2 and round to one decimal.

When at least one criterion is excluded (`cᵢ = 0` due to an E-condition), the composite is
**not** computed; the site is reported as **Excluded** with the triggering E-code.

### 2.5 Phase mapping

Every criterion is tagged with a phase in §3 and §4:

| Phase tag         | Meaning                                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| **BF**            | Basic filter — applied at Phase 1 / Phase 2 boundary; pass = baseline plant-physics viability.           |
| **Screen (Excl.)**| Exclusionary screening — fail = remove from candidate set unless remediable.                             |
| **Screen + Rank** | Both screened (pass/fail at the discretionary threshold) and used in the ranking composite.              |
| **Rank**          | Ranking only — contributes to composite score; no hard exclusion (unless an E-tie exists).               |

### 2.6 Quality and confidence handling

| `quality` flag    | Score handling                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| `high`            | Use the computed score; no uncertainty range.                                                           |
| `medium`          | Use the computed score; no uncertainty range.                                                           |
| `low`             | Replace the score by a **range** of ±1 band (e.g. `2–4`); propagate via Monte Carlo.                    |
| `no_data` / `insufficient` | Trigger LLM fallback (§7); if LLM also missing, record as `unscored`, penalise per §7.4.       |

---
