# man_hours: 2.0
"""Explicit catalog of E1-E9 and A1-A15 screening codes.

The scoring engine walks the YAML ``fail_conditions`` directly (each
condition carries its own ``code`` and ``condition_expr``), but Phase 1.4
of the siting-report plan demands a *named evaluator per code* so we can:

1. Emit one verdict per (site, SMR, code) pair — the catalog gives us the
   authoritative list of codes to report against, so we can detect missing
   rubric coverage at engine start-up.
2. Keep appendix cross-reference metadata (anchor criterion + threshold
   synopsis from ``report/sites_evaluation/10_appendices.md``) in code,
   so maintainers can jump between the rubric, the engine, and the
   report without re-deriving the mapping.
3. Give tests and downstream audits a stable enumeration to assert
   against (see the ``CODE_CATALOG`` export).

This module is deliberately data-only — no DB / IO. Evaluation still
happens in :mod:`exclusionary` and :mod:`avoidance`, which use this
catalog to stamp ``prompt_key = code`` on every verdict so the
``uq_verdict_site_smr_criterion_prompt_run`` unique constraint stays
fully specified (no NULL prompt_key ambiguity for screening codes).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CodeAction = Literal["exclude", "avoidance_penalty"]


@dataclass(frozen=True)
class ScreeningCode:
    """Metadata describing one E- or A-code and its rubric anchor."""

    code: str
    action: CodeAction
    anchor_criterion_id: str
    anchor_aliases: tuple[str, ...]
    synopsis: str


# Source: report/sites_evaluation/10_appendices.md Tables A.1 / A.2 plus
# the E/A entries in config/scoring_rubrics/*.yaml. Keep this list and the
# YAML fail_conditions in sync; CI reads the catalog to assert coverage.
EXCLUSIONARY_CODES: tuple[ScreeningCode, ...] = (
    ScreeningCode(
        code="E1",
        action="exclude",
        anchor_criterion_id="NH-02",
        anchor_aliases=("NH-02",),
        synopsis="< 5 km capable fault (project) / < 8 km (SSG-35).",
    ),
    ScreeningCode(
        code="E2",
        action="exclude",
        anchor_criterion_id="NH-03",
        anchor_aliases=("NH-03",),
        synopsis="Unacceptable liquefaction with no engineering remedy.",
    ),
    ScreeningCode(
        code="E3",
        action="exclude",
        anchor_criterion_id="NH-04",
        anchor_aliases=("NH-04",),
        synopsis="Catastrophic landslide / slope > 25°.",
    ),
    ScreeningCode(
        code="E4",
        action="exclude",
        anchor_criterion_id="NH-07",
        anchor_aliases=("NH-07",),
        synopsis="< 50 km Holocene volcano or in mapped hazard zone.",
    ),
    ScreeningCode(
        code="E7",
        action="exclude",
        anchor_criterion_id="NS-08",
        anchor_aliases=("NS-08",),
        synopsis="Site within strict-category Natura 2000 / WDPA.",
    ),
    ScreeningCode(
        code="E8",
        action="exclude",
        anchor_criterion_id="EP-01",
        anchor_aliases=("EP-01",),
        synopsis="DRV-02 composite < 30 or fundamentally infeasible EP.",
    ),
    ScreeningCode(
        code="E9",
        action="exclude",
        anchor_criterion_id="NS-01",
        anchor_aliases=("NS-01",),
        synopsis="No viable cooling source AND dry cooling not viable.",
    ),
)


AVOIDANCE_CODES: tuple[ScreeningCode, ...] = (
    ScreeningCode(
        code="A1",
        action="avoidance_penalty",
        anchor_criterion_id="HI-01",
        anchor_aliases=("HI-01",),
        synopsis="SSG-35: general-aviation / small airport < 10 km.",
    ),
    ScreeningCode(
        code="A2",
        action="avoidance_penalty",
        anchor_criterion_id="HI-01",
        anchor_aliases=("HI-01",),
        synopsis="Project: commercial / large-international airport < 15 km.",
    ),
    ScreeningCode(
        code="A3",
        action="avoidance_penalty",
        anchor_criterion_id="HI-01",
        anchor_aliases=("HI-01",),
        synopsis="Project: military airport < 30 km (SSG-35 ≥ 16 km).",
    ),
    ScreeningCode(
        code="A4",
        action="avoidance_penalty",
        anchor_criterion_id="HI-01",
        anchor_aliases=("HI-01",),
        synopsis="SSG-35: flight-path overhead / < 4 km from airway.",
    ),
    ScreeningCode(
        code="A5",
        action="avoidance_penalty",
        anchor_criterion_id="HI-06",
        anchor_aliases=("HI-06",),
        synopsis="≥ 30 km from practice / bombing / firing ranges.",
    ),
    ScreeningCode(
        code="A6",
        action="avoidance_penalty",
        anchor_criterion_id="HI-06",
        anchor_aliases=("HI-06",),
        synopsis="≥ 8 km from ammunition storage.",
    ),
    ScreeningCode(
        code="A7",
        action="avoidance_penalty",
        anchor_criterion_id="HI-02",
        anchor_aliases=("HI-02",),
        synopsis="≥ 5 km from major-hazard storage (Seveso / IED).",
    ),
    ScreeningCode(
        code="A8",
        action="avoidance_penalty",
        anchor_criterion_id="HI-03",
        anchor_aliases=("HI-03",),
        synopsis="≥ 8 km from hazardous-cloud sources.",
    ),
    ScreeningCode(
        code="A9",
        action="avoidance_penalty",
        anchor_criterion_id="NH-08",
        anchor_aliases=("NH-08",),
        synopsis="≥ 10 km from sea / ≥ 1 km from lake or ≥ 50 m AMSL.",
    ),
    ScreeningCode(
        code="A10",
        action="avoidance_penalty",
        anchor_criterion_id="NH-01",
        anchor_aliases=("NH-01",),
        synopsis="PGA within SMR design envelope (2475 yr ≤ 0.5 g).",
    ),
    ScreeningCode(
        code="A11",
        action="avoidance_penalty",
        anchor_criterion_id="NH-09",
        anchor_aliases=("NH-09",),
        synopsis="River distance ≥ 4 km OR vertical separation ≥ 30.5 m.",
    ),
    ScreeningCode(
        code="A12",
        action="avoidance_penalty",
        anchor_criterion_id="RI-05",
        anchor_aliases=("RI-05",),
        synopsis="Population-centre distance thresholds per RI-05 table.",
    ),
    ScreeningCode(
        code="A13",
        action="avoidance_penalty",
        anchor_criterion_id="NS-02",
        anchor_aliases=("NS-02", "BF-01"),
        synopsis="Transmission ≥ reference SMR net MWe within feasible distance.",
    ),
    ScreeningCode(
        code="A14",
        action="avoidance_penalty",
        anchor_criterion_id="NS-03",
        anchor_aliases=("NS-03",),
        synopsis="Heavy-haul access ≥ 700 t segment capacity.",
    ),
    ScreeningCode(
        code="A15",
        action="avoidance_penalty",
        anchor_criterion_id="NS-05",
        anchor_aliases=("NS-05", "BF-02"),
        synopsis="≥ 14 ha contiguous industrial land.",
    ),
)


CODE_CATALOG: tuple[ScreeningCode, ...] = EXCLUSIONARY_CODES + AVOIDANCE_CODES
EXCLUSIONARY_CODE_NAMES: frozenset[str] = frozenset(c.code for c in EXCLUSIONARY_CODES)
AVOIDANCE_CODE_NAMES: frozenset[str] = frozenset(c.code for c in AVOIDANCE_CODES)


def codes_for_criterion(
    criterion_id: str, *, action: CodeAction
) -> tuple[ScreeningCode, ...]:
    """Return every catalog entry whose anchor aliases include ``criterion_id``."""
    return tuple(
        c
        for c in CODE_CATALOG
        if c.action == action and criterion_id in c.anchor_aliases
    )


def check_rubric_coverage(rubric_codes: set[str]) -> tuple[set[str], set[str]]:
    """Return (missing_from_rubric, extra_in_rubric) relative to the catalog.

    - ``missing_from_rubric`` — catalog codes with no matching
      ``fail_condition`` in any loaded rubric. Rendered as a warning by the
      engine so operators notice rubric drift (e.g. an A-code was deleted
      during a refactor).
    - ``extra_in_rubric`` — rubric codes that aren't in the catalog. Also
      a warning; typically signals a new code that needs to be added here.
    """
    catalog_names = {c.code for c in CODE_CATALOG}
    return catalog_names - rubric_codes, rubric_codes - catalog_names
