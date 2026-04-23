# man_hours: 4.0
"""API ↔ LLM merge precedence for scoring inputs.

Implements the rules from ``report/sites_evaluation/09_llm_api_merge.md``:

  | Phase      | Priority order                                                         |
  | ---------- | ---------------------------------------------------------------------- |
  | Screen     | API(quality≥medium) → LLM(conf≥medium) → fail-closed default           |
  | Avoidance  | API(quality≥medium) → LLM(any conf)   → default score 4                |
  | Rank       | API(quality≥medium) → LLM(any conf)   → default score 5 (``unscored``) |

For scoring we only need to resolve scalar inputs: one value per
``db_fields.api`` entry (and any LLM overrides). This module builds a
flat ``dict[str, Any]`` the band evaluator can consume.

LLM inputs are **not** re-fetched here. We read the already-merged
``site_llm_verdicts`` and any LLM-promoted numeric fields written by
the dedicated merge pipeline (see
``audit/post_processing/02_data_verification/20260421_llm_field_promotion_proposal.md``).
The resolver therefore works identically on the merged DB and on a
plain API DB — it just gets fewer hits in the latter case.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    Site,
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteInfrastructureV2,
    SiteLlmVerdict,
    SiteNaturalHazards,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)


_DOMAIN_TABLES: dict[str, str] = {
    "sites": "site",
    "site_natural_hazards": "natural_hazards",
    "site_human_induced": "human_hazards",
    "site_human_hazards": "human_hazards",
    "site_radiological": "radiological",
    "site_emergency": "emergency_planning",
    "site_emergency_planning": "emergency_planning",
    "site_infrastructure_v2": "infrastructure",
    "site_socioeconomic": "infrastructure",  # socio-econ lives in infra in current schema
}


@dataclass
class MergedContext:
    """Flat context dict + quality/confidence metadata for a criterion."""

    site_id: uuid.UUID
    criterion_id: str
    values: dict[str, Any] = field(default_factory=dict)
    quality: str | None = None
    confidence: str | None = None
    data_sources: list[str] = field(default_factory=list)
    used_llm: bool = False
    raw_misses: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scalar resolution
# ---------------------------------------------------------------------------


def _strip_prefix(column: str) -> str | None:
    """Return column without a ``<family><digits>_`` prefix, if any."""
    if len(column) > 5 and column[0:2].isalpha() and column[2:4].isdigit() and column[4] == "_":
        return column[5:]
    if len(column) > 6 and column[0:2].isalpha() and column[2:5].isdigit() and column[5] == "_":
        return column[6:]
    if len(column) > 6 and column[0:3].isalpha() and column[3:5].isdigit() and column[5] == "_":
        return column[6:]
    return None


def _lookup_attr(instance: Any, column: str) -> Any:
    """Return the value of ``column`` on ``instance``, trying variants."""
    if instance is None:
        return None
    if hasattr(instance, column):
        val = getattr(instance, column)
        if val is not None:
            return val
    stripped = _strip_prefix(column)
    if stripped and hasattr(instance, stripped):
        return getattr(instance, stripped)
    return None


def resolve_scalar(site: Site, table: str, column: str) -> Any:
    """Resolve ``table.column`` from the ORM graph; ``None`` if missing."""
    attr = _DOMAIN_TABLES.get(table)
    if attr is None:
        return None
    if attr == "site":
        return _lookup_attr(site, column)
    instance = getattr(site, attr, None)
    return _lookup_attr(instance, column)


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------


def _quality_from_criterion(site: Site, criterion: Criterion) -> str | None:
    """Return the ``<family><digit>_quality`` flag used for band widening."""
    for table, _attr in _DOMAIN_TABLES.items():
        instance = _domain_instance(site, table)
        if instance is None:
            continue
        candidates = [
            f"{criterion.criterion_id.lower().replace('-', '')}_quality",
            f"{criterion.criterion_id.lower().split('-')[0]}"
            f"{criterion.criterion_id.split('-')[1].zfill(2)}_quality",
        ]
        for name in candidates:
            if hasattr(instance, name):
                return getattr(instance, name)
    return None


def _domain_instance(site: Site, table: str) -> Any:
    attr = _DOMAIN_TABLES.get(table)
    if attr is None:
        return None
    if attr == "site":
        return site
    return getattr(site, attr, None)


def _apply_llm_overrides(
    session: Session,
    site_id: uuid.UUID,
    criterion: Criterion,
    values: dict[str, Any],
) -> bool:
    """Fill any still-``None`` values from ``site_llm_verdicts``.

    Returns True if at least one LLM value was consumed. Only numeric
    or string LLM payloads are injected — nuanced merging (e.g. using
    the LLM justification text to derive a score) is out of scope for
    the engine and belongs to the merge pipeline itself.
    """
    used = False
    verdicts = (
        session.query(SiteLlmVerdict)
        .filter(
            SiteLlmVerdict.site_id == site_id,
            SiteLlmVerdict.criterion_id == criterion.criterion_id,
        )
        .all()
    )
    if not verdicts:
        return used

    for v in verdicts:
        key = f"llm_verdict_{v.prompt_key}"
        if key not in values:
            values[key] = v.llm_verdict
            used = True
    if any(
        v.llm_verdict in {"fail", "caution"} and v.llm_verdict_confidence in {"medium", "high"}
        for v in verdicts
    ):
        values.setdefault("llm_exclusion_signal", True)
    return used


def build_context_for_site(
    session: Session,
    site: Site,
    criterion: Criterion,
) -> MergedContext:
    """Build the evaluation context for one (site, criterion) pair.

    - Pulls each ``db_fields.api`` scalar from the ORM graph.
    - Exposes values under BOTH the fully qualified column name AND
      the bare expression name (e.g. ``pga_475yr_g`` even if the
      rubric spelt it ``nh01_pga_475yr_g``).
    - Fills gaps from ``site_llm_verdicts`` when available.
    - Collects the quality flag used for band widening.
    """
    ctx = MergedContext(site_id=site.site_id, criterion_id=criterion.criterion_id)

    for anchor in criterion.db_fields.api:
        table, _, column = anchor.partition(".")
        if not column:
            continue
        value = resolve_scalar(site, table, column)
        if value is None:
            ctx.raw_misses.append(anchor)
        ctx.values[column] = value
        stripped = _strip_prefix(column)
        if stripped and stripped not in ctx.values:
            ctx.values[stripped] = value
        ctx.data_sources.append(anchor)

    # The condition expressions reference bare site attributes too
    # (``site_area_ha``, ``elevation_m``). Expose them eagerly.
    for attr in ("site_area_ha", "elevation_m", "installed_capacity_mw", "country_code"):
        ctx.values.setdefault(attr, getattr(site, attr, None))

    ctx.used_llm = _apply_llm_overrides(session, site.site_id, criterion, ctx.values)
    ctx.quality = _quality_from_criterion(site, criterion)
    ctx.confidence = _confidence_from_quality(ctx.quality, ctx.used_llm)
    return ctx


def _confidence_from_quality(quality: str | None, used_llm: bool) -> str:
    """Derive the ``ranking_scores.confidence`` string."""
    if quality == "high":
        return "high"
    if quality == "medium":
        return "medium"
    if quality == "low":
        return "low" if not used_llm else "medium"
    if quality in {"no_data", "insufficient"} or quality is None:
        return "low" if used_llm else "insufficient"
    return "medium"
