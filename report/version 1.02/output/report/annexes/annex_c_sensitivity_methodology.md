# Annex C: Sensitivity Methodology

**What this annex adds.** Annex C carries the numerical parameter settings and banding cut-offs for the project's 10,000-iteration Monte Carlo sensitivity analysis. Chapter 3 §3.8 describes what the six sensitivity components do and why they are used; Annex C states how they are configured and what the stability bands mean in precise terms.

## Scope of the analysis

The sensitivity analysis operates on site–SMR pairs that cleared the exclusionary and safety-floor gates under the NuScale VOYGR-6 reference case. For the current pool this is 208 surviving site–SMR pairs out of a 2,904-pair universe. Pairs that fail either gate are never passed to any sensitivity scenario; the baseline filter enforces this before the perturbation code runs. The analysis therefore tests whether the ranking among survivors is robust, not whether additional sites should be recovered from the excluded population.

## Sensitivity components and parameter settings

### One-at-a-time (OAT) criterion importance

| Parameter | Value |
| --- | --- |
| Scope | Every ranking-phase criterion in the project rubric. |
| Perturbation | Set the target criterion weight to zero and renormalise the remaining weights to sum to one. |
| Metric | Mean absolute rank change versus baseline across surviving pairs. |
| Importance score | Mean absolute rank change divided by number of scored pairs, in the 0–1 interval. |
| Output | OAT importance CSV with one row per criterion; the top 15 populate the "influential set" narrative. |

### Category weight perturbation

| Parameter | Value |
| --- | --- |
| Families perturbed | NH, HI, RI, EP, NS (five criterion families). |
| Perturbation magnitude | ±20 per cent scaling on the target family. |
| Profiles | Ten per-family profiles (plus and minus for each of the five families). |
| Renormalisation | After scaling the target family, all 48 weights renormalise to sum to one. |
| Pass threshold | Jaccard at the top-10 per cent ≥ 0.85 for every per-category profile. |

### Swing-weight adjustment

| Parameter | Value |
| --- | --- |
| Rescale rule | Each criterion's declared weight is multiplied by the observed 0–10 score range across the survivor pool, then the whole weight vector renormalises to one. |
| Profile label | Single profile `w_swing`. |
| Purpose | Corrects the "declared weight on a criterion that does not discriminate" artefact; identifies criteria whose weight earns no ranking power. |

### Monte Carlo score-band sampling

| Parameter | Value |
| --- | --- |
| Iteration count | 10,000 per pair per run (single production run). |
| Sampling | Uniform draw on each criterion's `[score_low, score_high]` band. |
| Band widths | `score_low = score − 1`, `score_high = score + 1` for `quality = low`; width zero otherwise. |
| RNG seed | Deterministic per pair: `seed = f"{site_id}:{smr_key}:42"`. |
| Returned statistics | Mean, 5th percentile, 95th percentile, standard deviation, and a stability flag for `p95 − p05 ≤ 1.0`. |
| Reproducibility | Bit-for-bit reproducibility given the same inputs and seed. |

### Threshold perturbation

| Parameter | Value |
| --- | --- |
| Perturbation scope | Numeric measured context (distances, densities, areas, flows). |
| Perturbation magnitude | Multiplicative factors 0.75 and 1.25 on measured numeric inputs. |
| Interpretation | Analytically equivalent to shifting rubric band edges by ∓25 per cent, without mutating the rubric YAML. |
| Profiles | `threshold_minus_25` and `threshold_plus_25`. |

### Country-balance diagnostic

| Parameter | Value |
| --- | --- |
| Metric | Share of the top-20 ranked pairs held by the largest single country. |
| Monitoring threshold | 40 per cent (above this the country share is flagged in the audit narrative). |
| Profile | Baseline composites re-persisted under `country_balanced` to make the diagnostic visible to the banding stage. |

## Stability band definitions (A through H)

Each scored site is assigned a single stability band based on its hit-rate across the 15 non-baseline scenarios (10 per-category weight profiles, 1 swing-weight profile, 1 Monte Carlo profile, 2 threshold profiles, 1 country-balanced profile). The band is assigned on hit-rate at three percentile slices: top-5 per cent, top-10 per cent, and top-30 per cent of the local pool. "Hit-rate" is the fraction of scenarios in which the site lies inside the slice.

| Band | Rule | Interpretation |
| --- | --- | --- |
| A | top-5 % hit rate ≥ 0.80 | Robust short-list: the site sits in the head of the ranking across essentially every sensitivity scenario. |
| B | top-10 % hit rate ≥ 0.80 and not Band A | Defensible top-10: the site remains inside the top tier under every scenario even if it is not in the very head. |
| C | top-10 % hit rate 0.50–0.79 and not Band A or B | Bench: the site sits inside the top tier in most but not all scenarios. |
| D | top-30 % hit rate ≥ 0.64 and not Band A, B, or C | Frequently in the broader top tier. |
| E | top-30 % hit rate ≥ 0.50 | The site sits inside the broader top tier in roughly half or more of scenarios. |
| F | top-30 % hit rate ≥ 0.36 | Roughly a third of scenarios. |
| G | top-30 % hit rate ≥ 0.21 | Occasional appearance in the broader top tier. |
| H | below all of the above | Rarely or never in the top-30 per cent slice. |

### Scope of the banding

The same assignment rule runs at four scopes. The regional all-SMR pool enters one pair per site (best of the eight SMR designs). The regional NuScale-only pool restricts to the VOYGR-6 reference. The national all-SMR pool computes percentiles inside each country. The national NuScale-only pool combines both restrictions. Within-country percentiles are computed on the local pool, so national bands reflect local competitiveness rather than global rank.

## Robustness and interpretation thresholds

| Metric | Threshold | Interpretation |
| --- | --- | --- |
| Jaccard at top-10 % under weight perturbation | ≥ 0.85 | Ranking is robust to ±20 per cent weight perturbation. |
| Jaccard at top-10 % under Monte Carlo | ≥ 0.70 | Ranking is robust to declared data uncertainty. |
| Mean absolute Δscore | Lower is better | Magnitude of perturbation. |
| Country maximum share in top-20 | > 0.40 | Triggers a country-balance flag in the audit narrative. |

## Score provenance used in the sensitivity analysis

Sensitivity runs only on scores that carry a defensible provenance trail. The project operates a three-tier provenance hierarchy: Tier 1 first-party API or open-data fields, Tier 2 LLM-curated fields under deterministic prompts and schemas, and Tier 3 raw LLM responses that never enter the scored rubric. Exclusionary criteria use Tier 1 only; a missing Tier 1 value falls through to the pass-mark default and lets the safety floor enforce the cut. Ranking criteria may use Tier 2 fallbacks, and the provenance column on each ranking row lets the audit group survivors by evidence share.

## Known limitations

- OAT captures first-order effects only. Interactions between two simultaneously perturbed criteria are not explored at this stage.
- Threshold perturbation acts on numeric measured inputs; categorical quality tiers are insensitive to the 25 per cent operator by construction.
- Banding is population-relative; the percentile slices are recomputed against the local scored pool, so bands at small-pool countries have a wider implicit uncertainty than at large-pool countries. `scenarios_total` and `scenarios_scored` are carried alongside every band assignment so reviewers can judge coverage.
- The uniform plus-or-minus-one-band Monte Carlo distribution for `low`-quality fields is deliberately conservative. High-quality fields with `score_low = score_high` contribute no uncertainty to the Monte Carlo bracket.

## Primary sources for this annex

- `report/methodology/sensitivity_analysis.md` — the authoritative method description.
- `report/methodology/swing_weight_audit.md` — the swing-weight rescale rationale and diagnostic outcome.
- `report/methodology/criterion_correlation.md` — the correlation check ensuring no pair exceeds 0.7.
- Current sensitivity export pack under `report/output/sensitivity/`.
- Chapter 3 §3.8 and Chapter 4 §4.5 for the narrative framework.
