<!-- man_hours: 10.0 -->
# 5. Screening and Scoring Engine

## 5.1 Purpose

This document specifies the screening, scoring, ranking, and sensitivity analysis components of the evaluation system.

**Traceability:** Requirements S10.6.

**Upstream references:**

- Siting criteria definitions: `requirements/05_siting_criteria.md`
- Scoring matrix and weighting: `requirements/06_scoring_matrix.md`

---

## 5.2 Exclusionary Screening

### 5.2.1 Objective

For each site, evaluate all exclusionary criteria (E1–E9). Any site failing one or more exclusionary criteria is flagged as **"Excluded"** and removed from further scoring.

### 5.2.2 Process

1. Load enriched site attributes from PostgreSQL.
2. For each exclusionary criterion, evaluate the site against the defined threshold.
3. Record pass/fail per criterion in `screening_results`, including:
   - Criterion ID
   - Result (pass / fail)
   - Justification text (e.g. "PGA 0.35g exceeds 0.3g threshold at site coordinates")
   - Data source reference
4. Sites with **any** fail result are flagged as excluded.

### 5.2.3 Configuration

All exclusionary thresholds shall be defined in YAML configuration, not hard-coded. This enables threshold adjustment without code changes.

---

## 5.3 Avoidance Screening

### 5.3.1 Objective

For sites that pass exclusionary screening, evaluate avoidance criteria (A1–A15). Avoidance results do not exclude sites but are recorded as risk flags and may influence scoring.

### 5.3.2 Process

1. For each non-excluded site, evaluate all avoidance criteria against configurable thresholds.
2. Record results in `screening_results` with the same structure as exclusionary results.
3. Avoidance flags are carried forward into the scoring stage as input context.

---

## 5.4 Score Assignment

### 5.4.1 Objective

For each candidate site (passed exclusionary screen), compute a score of 1–5 for every ranking criterion based on retrieved data and predefined scoring rubrics.

### 5.4.2 Scoring Rubrics

Each criterion shall have a mapping from data values to scores defined in YAML:

```yaml
# Example rubric structure
criterion_id: R1_seismic
score_bands:
  5: { max_pga: 0.05 }
  4: { max_pga: 0.10 }
  3: { max_pga: 0.15 }
  2: { max_pga: 0.20 }
  1: { max_pga: 0.30 }
```

Rubrics shall be versioned alongside the configuration to support audit and reproducibility.

### 5.4.3 Missing Data

When data for a criterion is unavailable:

- Assign a configurable default score (e.g. 3) or mark as "unscored."
- Flag the site-criterion pair in `data_quality_flags`.
- Include the missing-data count in the run summary.

---

## 5.5 Composite Scoring and Ranking

### 5.5.1 Formula

Composite score per site:

```
S_composite = Σ (w_i × s_i) / Σ w_i
```

Where `w_i` is the weight for criterion `i` and `s_i` is the assigned score.

Weights are defined in YAML configuration per the scoring matrix in `requirements/06_scoring_matrix.md`.

### 5.5.2 Ranking

Sites are sorted by descending composite score. Ties are broken by:

1. Fewer avoidance flags.
2. Higher installed capacity.
3. Alphabetical by site name (deterministic fallback).

### 5.5.3 Output

Store results in `ranking_results`:

- site_id
- composite_score
- rank
- per-criterion scores
- run_id, timestamp

---

## 5.6 Sensitivity Analysis

### 5.6.1 Weight Perturbation

Systematically vary criterion weights within a defined range (e.g. ±20%) and re-rank to identify:

- Sites whose rank is stable across weight variations.
- Criteria that most influence the ranking order.

### 5.6.2 Monte Carlo Score Uncertainty

For each site-criterion pair, model score uncertainty as a distribution (e.g. ±0.5 around assigned score). Run N iterations (configurable, default 1000), recompute composite scores, and report:

- Mean and standard deviation of rank per site.
- Probability of each site appearing in top-N.

### 5.6.3 Configuration

Sensitivity analysis parameters (perturbation range, number of iterations, score uncertainty model) shall be defined in YAML.

---

## 5.7 Acceptance Criteria

- All exclusionary criteria produce deterministic pass/fail results for a given dataset.
- Score assignment is fully reproducible given the same data, rubrics, and weights.
- Changing weights in YAML produces updated rankings without code changes.
- Sensitivity analysis results are included in the output artifacts.
- Every screening and scoring decision is traceable to source data and configuration version.
