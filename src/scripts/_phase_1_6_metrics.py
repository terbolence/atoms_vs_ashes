# man_hours: 0.5
"""Glue between the failure-analysis orchestrator and the
:class:`MetricsBundle` writer.

Lives next to ``_phase_1_6_failure_pack.py`` so the orchestrator stays
under the 300-line cap; the helpers here are import-only — no side
effects unless you call them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec import load_template_bundle
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.metrics import (
    build_metrics_bundle_from_session,
    write_metrics_csvs,
    write_metrics_json,
)


def maybe_load_template_bundle(spec_dir: Path) -> TemplateBundle | None:
    """Return the CriterionSpec bundle, or ``None`` if unavailable."""
    try:
        return load_template_bundle(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(
            f"[warn] failed to load CriterionSpec templates from "
            f"{spec_dir}: {exc}; metrics bundle will skip per-pair "
            f"failure margins."
        )
        return None


def emit_metrics_bundle(  # noqa: PLR0913 - GUI-facing API
    session: Session,
    *,
    breakdown,
    country_by_site,
    composites_run_id,
    run_id: str,
    audit_dir: Path,
    stamp: str,
    smr_key: str | None,
    verdicts_by_pair=None,
    template_bundle: TemplateBundle | None = None,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    near_miss_gap_pct: float = 10.0,
    qualification_mode: str = "normal",
    top_n_per_country: int = 10,
) -> Path:
    """Materialise + persist the run-level :class:`MetricsBundle`.

    Per-SMR packs reuse the same builder with ``smr_keys=(smr_key,)`` so
    the GUI can fetch a slimmer payload when the user is filtering on
    one technology. Returns the metrics directory.
    """
    bundle = build_metrics_bundle_from_session(
        session,
        run_id=run_id,
        breakdown=breakdown,
        country_by_site=country_by_site,
        composites_run_id=composites_run_id,
        smr_keys=(smr_key,) if smr_key else None,
        verdicts_by_pair=verdicts_by_pair,
        template_bundle=template_bundle,
        fail_thresholds=fail_thresholds or {},
        near_miss_gap_pct=near_miss_gap_pct,
        qualification_mode=qualification_mode,
        top_n_per_country=top_n_per_country,
    )
    suffix = f"_{smr_key}" if smr_key else ""
    metrics_dir = audit_dir / "metrics" / f"{stamp}{suffix}"
    write_metrics_json(bundle, metrics_dir / "metrics.json")
    write_metrics_csvs(bundle, metrics_dir)
    return metrics_dir


__all__ = ["emit_metrics_bundle", "maybe_load_template_bundle"]
