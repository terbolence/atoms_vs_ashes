## 8. Scoring Matrix Design

### 8.1 Scoring Methodology

Each ranking criterion shall be assessed using a five-level scoring scale:

| Score | Descriptor | Definition |
|---|---|---|
| 5 | Excellent | Significantly exceeds requirements; minimal or no mitigation needed |
| 4 | Good | Meets requirements with minor favourable conditions |
| 3 | Acceptable | Meets minimum requirements; standard mitigation may be needed |
| 2 | Marginal | Approaches minimum requirements; significant mitigation required |
| 1 | Poor | Does not meet requirements without major engineering intervention |

Binary exclusionary criteria (Section 7, Phase = "Screen (Excl.)") are scored Pass/Fail. A Fail on any exclusionary criterion eliminates the site regardless of other scores.

### 8.2 Weighting Framework

Criterion weights shall reflect the relative importance of each criterion category, informed by IAEA principles (safety primacy) and the project's coal-to-nuclear conversion objectives.

| Category | Weight Allocation | Rationale |
|---|---|---|
| Safety-Related: Natural Hazards (NH) | 25% | Primary safety concern per SF-1 Principle 8 |
| Safety-Related: Human Induced Hazards (HI) | 10% | Defence-in-depth from external threats |
| Safety-Related: Radiological Impact (RI) | 15% | Population protection per NS-R-3 §2.27 |
| Safety-Related: Emergency Planning (EP) | 10% | Emergency response feasibility per NS-R-3 §2.29 |
| Non-Safety: Infrastructure & Grid (NS-01–03) | 15% | Critical for coal-to-nuclear economic viability |
| Non-Safety: Site Characteristics (NS-04–08) | 10% | Physical and environmental suitability |
| Non-Safety: Socioeconomic & Synergies (NS-09–13) | 15% | Coal-to-nuclear business case and workforce transition |

**Total: 100%**

Within each category, individual criteria shall be assigned sub-weights summing to the category allocation. The detailed sub-weight table shall be developed during project execution and documented in the report Annex A.

### 8.3 Composite Score Calculation

For each candidate site *s*, the composite score *S(s)* is calculated as:

\[
S(s) = \sum_{i=1}^{n} w_i \cdot c_i(s)
\]

Where:
- \( w_i \) = normalised weight for criterion *i* (sum of all weights = 1.0)
- \( c_i(s) \) = score (1–5) for site *s* on criterion *i*
- \( n \) = total number of ranking criteria

### 8.4 Sensitivity Analysis

To ensure ranking robustness:

1. **Weight perturbation:** Each category weight shall be varied ±20% (with complementary adjustment of other weights to maintain sum = 100%). Rankings shall be re-computed for each perturbation.
2. **Score uncertainty:** Where data quality is low, criterion scores shall be assigned as ranges (e.g., 2–4). Monte Carlo simulation (1,000 iterations) using uniform distributions within score ranges shall produce a ranking stability index.
3. **Threshold sensitivity:** Discretionary screening thresholds (Section 6.3.2) shall be varied ±25% to assess the impact on the candidate site pool.

Results shall be reported as a ranking stability table showing whether each site's position in the top-15 is robust or sensitive to assumption changes.
