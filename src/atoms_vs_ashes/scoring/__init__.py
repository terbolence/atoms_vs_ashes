# man_hours: 0.5
"""Scoring engine — 0–10 native site × SMR × criterion evaluation.

This package replaces the legacy 1–5 scoring path. The public entry
point is ``engine.ScoringEngine`` / ``engine.run_scoring`` which
iterates every site × SMR × criterion and writes ``ranking_scores`` +
``composite_rankings`` rows plus ``screening_verdicts`` rows for the
E-code / A-code fail conditions embedded in each rubric.

Submodules (each ≤ 300 lines per ``file-size-python.mdc``):

- :mod:`rubric` — pydantic schema + YAML loader for ``config/scoring_rubrics/``.
- :mod:`bands` — band / sub-score evaluator (numeric + categorical).
- :mod:`merge_resolver` — API vs LLM precedence (see §7 of ``09_llm_api_merge.md``).
- :mod:`exclusionary` — E1–E9 evaluator, writes ``screening_verdicts`` phase = ``exclusionary``.
- :mod:`avoidance` — A1–A15 evaluator, writes ``screening_verdicts`` phase = ``avoidance``.
- :mod:`composite` — Σ wᵢ·cᵢ per (site, SMR) with ``unscored`` penalty.
- :mod:`sensitivity` — weight ±20 %, MC 1 000, threshold ±25 %, country balance.
- :mod:`engine` — orchestrator wiring the pieces together.
"""

from atoms_vs_ashes.scoring.bands import (
    BandResult,
    evaluate_bands,
    evaluate_criterion_value,
    evaluate_sub_scores,
)
from atoms_vs_ashes.scoring.composite import (
    CompositeResult,
    compute_composite_for_site_smr,
)
from atoms_vs_ashes.scoring.merge_resolver import (
    MergedContext,
    build_context_for_site,
    resolve_scalar,
)
from atoms_vs_ashes.scoring.rubric import (
    Band,
    Criterion,
    FailCondition,
    Rubric,
    SubScore,
    load_rubric_bundle,
)

__all__ = [
    "Band",
    "BandResult",
    "CompositeResult",
    "Criterion",
    "FailCondition",
    "MergedContext",
    "Rubric",
    "SubScore",
    "build_context_for_site",
    "compute_composite_for_site_smr",
    "evaluate_bands",
    "evaluate_criterion_value",
    "evaluate_sub_scores",
    "load_rubric_bundle",
    "resolve_scalar",
]
