<!-- man_hours: 6.0 -->

# Sites Evaluation — Scoring Process & Criteria Reference

> Authoritative scoring playbook for the Phase 2 (screening) and Phase 3 (ranking) evaluation of the
> ~363 candidate coal-to-nuclear / SMR sites in the project. This document is the **single source of
> truth** that drives:
>
> 1. The narrative of the final report (per-criterion descriptions, importance, thresholds).
> 2. The deterministic scoring engine (score band tables + weight factors).
> 3. The merge of the **LLM evidence database** into the **API quantitative database** —
>    LLM values fill exclusionary / avoidance gaps and back-stop ranking criteria where the
>    API connectors cannot reach the field.
>
> **Inputs aggregated here**
>
> - `docs/expert_siting_criteria_evaluation_matrix.md` (IAEA/EPRI matrix, 0–10 bands, weights).
> - `requirements/04_siting_methodology.md` (E1–E9 exclusions, A1–A15 avoidance).
> - `requirements/05_siting_criteria.md` and `05_1`…`05_5` (criterion master tables).
> - `requirements/06_scoring_matrix.md` (1–5 bands for the 6 criteria already implemented).
> - `audit/post_processing/02_data_verification/2_5_targeted_checks/20260418_2_5_7_scoring_method.md`
>   (P1–P4 priorities, sub-weight proposals).
> - Project draft thresholds supplied by the engineering team (PGA 2475-yr, fault buffers,
>   karst/mining buffers, airport buffers, population rings, slope cap, etc.).
>
> Last updated: 2026-04-21.

**Status:** Split across multiple files (each ≤ 500 lines) per `file-size-markdown.mdc`. Content is unchanged from the former monolith.

## Table of contents

| Part | File | Contents |
| ---- | ---- | -------- |
| 1 | [01_framework.md](01_framework.md) | §1–2 — Purpose and scope; scoring framework (0–10 scale, pass/fail, weights, composite formula, phase mapping, quality). |
| 2 | [02_master_weights.md](02_master_weights.md) | §3 — Master weight table and category roll-ups. |
| 3 | [03_criteria_natural_hazards.md](03_criteria_natural_hazards.md) | §4 — Basic filters (BF-01…BF-02); natural hazards NH-01…NH-14. |
| 4 | [04_criteria_human_induced.md](04_criteria_human_induced.md) | §4 — Human-induced hazards HI-01…HI-08. |
| 5 | [05_criteria_radiological.md](05_criteria_radiological.md) | §4 — Radiological impact RI-01…RI-06. |
| 6 | [06_criteria_emergency_planning.md](06_criteria_emergency_planning.md) | §4 — Emergency planning EP-01…EP-05. |
| 7 | [07_criteria_non_safety.md](07_criteria_non_safety.md) | §4 — Non-safety criteria NS-01…NS-13. |
| 8 | [08_composite_and_sensitivity.md](08_composite_and_sensitivity.md) | §5–6 — Composite worked example; sensitivity and uncertainty. |
| 9 | [09_llm_api_merge.md](09_llm_api_merge.md) | §7 — LLM ↔ API DB merge guidance. |
| 10 | [10_appendices.md](10_appendices.md) | Appendices A–B; revision history. |

**Entry point:** start with §1 in [01_framework.md](01_framework.md), or jump to a criterion file above.
