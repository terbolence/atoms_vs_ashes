<!-- man_hours: 4.5 -->
# Annex C: National Sensitivity Methodology

**What this annex adds.** Annex C defines the parameters and interpretation rules for the project's 50,000-iteration national Monte Carlo sensitivity analysis. Chapter 3 Section 3.8 explains why national rank robustness matters for site selection; this annex states how the national analysis is configured and how the A-H stability bands are read.

## Scope of the analysis

The national sensitivity analysis operates only on sites that clear the exclusionary and safety-floor gates for the NuScale VOYGR-6 reference case. Failed sites remain in the evidence base and in the failure-mode analysis, but they do not enter national ranking, national shortlist probabilities, or stability bands.

The estimand is national rank. Each candidate is compared with other candidates in the same country for the same reference deployment envelope. A stable candidate is therefore stable inside its national decision pool, not simply high-scoring in a larger cross-country comparison.

## Sensitivity components and parameter settings

### One-at-a-time criterion importance

| Parameter | Value |
| --- | --- |
| Scope | Every ranking-phase criterion in the project rubric. |
| Perturbation | Set the target criterion weight to zero and renormalise the remaining weights to sum to one. |
| Metric | Mean absolute national-rank change versus the baseline within each country. |
| Interpretation | Identifies which criteria most influence the ordering of candidates in a national shortlist. |

### Category weight perturbation

| Parameter | Value |
| --- | --- |
| Families perturbed | NH, HI, RI, EP, and NS. |
| Perturbation magnitude | Plus or minus 20 per cent scaling on the target family. |
| Profiles | Ten per-family profiles, plus and minus for each of the five families. |
| Renormalisation | After scaling the target family, all ranking weights renormalise to sum to one. |
| Interpretation | Tests whether the national shortlist remains similar when a criterion family is weighted more or less strongly. |

### Swing-weight adjustment

| Parameter | Value |
| --- | --- |
| Rescale rule | Each criterion's declared weight is multiplied by the observed 0-10 score range across the survivor pool, then the whole weight vector renormalises to one. |
| Purpose | Identifies criteria whose declared weight carries limited ranking power because the observed scores vary little across candidates. |

### National Monte Carlo rank simulation

| Parameter | Value |
| --- | --- |
| Iteration count | 50,000 per national site pool. |
| Reference case | NuScale VOYGR-6 only. |
| Seed | 42, applied deterministically to the site and reference-case pair. |
| Sampling | Uniform draw inside each criterion's declared score band. |
| Reported metrics | Probability of ranking first, probability of ranking in the national top three, probability of ranking in the national top five, median rank, and rank uncertainty bounds. |
| Interpretation | Separates point-estimate leadership from robust national shortlist membership. |

### Threshold perturbation

| Parameter | Value |
| --- | --- |
| Perturbation scope | Numeric measured context such as distances, densities, land areas, slopes, and flows. |
| Perturbation magnitude | Multiplicative factors of 0.75 and 1.25 on measured numeric inputs. |
| Interpretation | Tests whether national ordering depends on candidates sitting close to rubric band edges. |

### Small-pool rule

| Parameter | Value |
| --- | --- |
| Applicability | National pools with too few surviving candidates for a stable rank distribution. |
| Treatment | Results are labelled indicative and used as decision support, not as proof of a stable shortlist. |
| Interpretation | Small national pools can still identify the best available candidate, but probability statements carry wider uncertainty. |

## Stability band definitions

Each scored site is assigned a stability band using hit rates across non-baseline sensitivity scenarios. Hit rate means the fraction of scenarios in which a site lies inside the relevant national percentile slice.

| Band | Rule | Interpretation |
| --- | --- | --- |
| A | Top-5 per cent hit rate at least 0.80 | Robust national shortlist candidate. |
| B | Top-10 per cent hit rate at least 0.80 and not Band A | Defensible national top-tier candidate. |
| C | Top-10 per cent hit rate from 0.50 to 0.79 and not Band A or B | Candidate often remains in the national top tier. |
| D | Top-30 per cent hit rate at least 0.64 and not Band A, B, or C | Candidate frequently appears in the broader national tier. |
| E | Top-30 per cent hit rate at least 0.50 | Candidate appears in the broader tier in roughly half or more of scenarios. |
| F | Top-30 per cent hit rate at least 0.36 | Candidate appears in roughly one third of scenarios. |
| G | Top-30 per cent hit rate at least 0.21 | Candidate appears occasionally in the broader tier. |
| H | Below all rules above | Candidate rarely enters the broader national tier. |

## Reading the national outputs

The national sensitivity tables should be read together with the exclusionary verdict, avoidance flags, and the Chapter 5 site profile. A Band A or Band B result supports progression toward Stage 3 investigation when the site also has a credible residual-risk register. It does not establish licensing readiness, public acceptance, land control, grid availability, or procurement feasibility.

Point-estimate rank is less important than the joint pattern. A site that ranks first but has low top-three probability is a fragile leader. A site with a slightly lower baseline rank but high top-three or top-five probability may be a stronger practical shortlist candidate.

## Known limitations

- One-at-a-time analysis captures first-order effects only. It does not estimate every interaction between criteria.
- Threshold perturbation acts on numeric measured inputs. Qualitative bands are not shifted by the numeric operator.
- Stability bands are population-relative. Small national pools have wider implicit uncertainty than large national pools.
- The Monte Carlo distribution is conservative for low-quality evidence rows and does not replace Stage 3 field confirmation.

## Evidence basis

This annex is drawn from the generated sensitivity method artefact, the swing-weight audit, the criterion-correlation check, and the national sensitivity export pack listed in Annex F. The reader-facing interpretation follows Chapter 3 Section 3.8 and Chapter 4 Sections 4.5-4.6.
