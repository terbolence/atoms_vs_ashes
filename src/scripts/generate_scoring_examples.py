# man_hours: 1.5
"""Print two real scored sites per band for one criterion.

Reads the active merged DB (no live API), evaluates each picked site
with ``scoring.bands.evaluate_criterion_value`` so the table is the
real engine output, not an approximation.

Required by ``experts/scoring/scoring_criterion_review.md`` §E7: every
criterion change must include a scored-examples table proving the
bands and the verdicts match the data the engine sees.

Usage::

    PYTHONPATH=src python -m scripts.generate_scoring_examples \
        --criterion NH-04

Returns a markdown table on stdout.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.db import models
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value, safe_eval
from atoms_vs_ashes.scoring.merge_context_derivations import column_aliases
from atoms_vs_ashes.scoring.rubric import Criterion


SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


def _top_band_treats_null_as_best(
    criterion: Criterion, primary_metric: str
) -> bool:
    """Return True when the criterion's top band's expression matches NULL.

    Detects expressions like ``<metric> is null or <metric> >= X`` produced
    by ``BandRecipeSpec.null_policy='best'``. The compiled Criterion does
    not retain the recipe, so we inspect the band expression as the
    source of truth.
    """
    if not criterion.bands:
        return False
    top = max(criterion.bands, key=lambda b: b.score_range[1])
    expr = getattr(top, "condition_expr", "") or ""
    needle = f"{primary_metric} is null"
    return needle.lower() in expr.lower()


def _resolve_metric_columns(
    criterion: Criterion,
) -> list[tuple[str, str, str]]:
    """Return (table, db_column, context_key) tuples for the criterion.

    ``db_fields.api`` lists the *context keys* the rubric expressions use
    (e.g. ``site_natural_hazards.nearest_volcano_km``). The underlying
    DB column may differ (``nearest_holocene_volcano_km``) and is
    discovered via :func:`column_aliases` so the SQL query targets the
    real column while the scored context dict still carries the alias
    the rubric expects.
    """
    out: list[tuple[str, str, str]] = []
    for ref in criterion.db_fields.api:
        if "." not in ref:
            continue
        table, context_key = ref.split(".", 1)
        aliases = column_aliases(table, context_key)
        db_column = aliases[0] if aliases else context_key
        out.append((table, db_column, context_key))
    return out


_TABLE_MODELS = {
    "site_natural_hazards": models.SiteNaturalHazards,
    "site_human_hazards": models.SiteHumanHazards,
    "site_radiological": getattr(models, "SiteRadiological", None),
    "site_emergency": getattr(models, "SiteEmergencyPlanning", None),
    "site_non_safety": getattr(models, "SiteNonSafety", None),
    "sites": models.Site,
}


def _fetch_contexts(
    session: Session,
    criterion: Criterion,
    primary_metric: str,
) -> list[dict[str, Any]]:
    """Return one dict per site with every context key the criterion uses."""
    refs = _resolve_metric_columns(criterion)
    if not refs:
        return []

    primary_ref = next(
        (r for r in refs if r[2] == primary_metric), None
    )
    if primary_ref is None:
        raise SystemExit(
            f"Criterion {criterion.criterion_id!r}: primary_metric "
            f"{primary_metric!r} not referenced in db_fields.api "
            f"(known: {[(t, k) for (t, _, k) in refs]})"
        )
    primary_table, primary_db_column, _ = primary_ref
    domain = _TABLE_MODELS.get(primary_table)
    if domain is None:
        raise SystemExit(
            f"No SQLAlchemy model registered for table {primary_table!r}; "
            "extend _TABLE_MODELS in this script."
        )
    if not hasattr(domain, primary_db_column):
        raise SystemExit(
            f"Model {domain.__name__} has no column {primary_db_column!r} "
            f"(context key {primary_metric!r}); extend column_aliases or "
            "fix the criterion db_fields.api entry."
        )

    # When the top band's expression contains ``<metric> is null`` (set by
    # ``band_recipe.null_policy='best'`` on the template, e.g. NH-07), NULL
    # rows score 9-10 and must appear in the sample. The compiled
    # Criterion does not preserve the recipe, so we look at the band
    # expression directly.
    include_nulls = _top_band_treats_null_as_best(criterion, primary_metric)

    site_t = models.Site
    primary_col = getattr(domain, primary_db_column)
    base = select(domain, site_t.country_code).join(
        site_t, domain.site_id == site_t.site_id
    )
    if include_nulls:
        rows = session.execute(base.order_by(primary_col.is_(None), primary_col)).all()
    else:
        rows = session.execute(
            base.where(primary_col.is_not(None)).order_by(primary_col)
        ).all()

    out: list[dict[str, Any]] = []
    for domain_row, country in rows:
        ctx: dict[str, Any] = {"_site_id": str(domain_row.site_id), "_country": country}
        for table, db_column, context_key in refs:
            if table == primary_table:
                ctx[context_key] = getattr(domain_row, db_column, None)
            else:
                # cross-domain columns are rare; resolve via the Site
                # back-relationship if exposed, otherwise leave NULL so
                # the context dict still carries the key the rubric expects.
                ctx[context_key] = None
        out.append(ctx)
    return out


def _pick_band_samples(
    criterion: Criterion,
    contexts: Sequence[dict[str, Any]],
    n_per_band: int,
    primary_metric: str,
) -> list[tuple[tuple[float, float], list[dict[str, Any]]]]:
    """Group contexts by matched band, keeping ``n_per_band`` per band.

    When ``band_recipe.null_policy='best'`` is in effect, the top band
    sample is forced to include at least one NULL-metric row (if any
    exist) so the user can audit the NULL-as-best behaviour directly.
    """
    buckets: dict[tuple[float, float], list[dict[str, Any]]] = {}
    for ctx in contexts:
        scoring_ctx = {k: v for k, v in ctx.items() if not k.startswith("_")}
        result = evaluate_criterion_value(criterion, scoring_ctx, quality="medium")
        if result.matched_band is None:
            continue
        key = tuple(result.matched_band.score_range)
        buckets.setdefault(key, []).append({**ctx, "_score": result.score})

    ordered_bands = sorted(
        {tuple(b.score_range) for b in criterion.bands}, reverse=True
    )
    null_best = _top_band_treats_null_as_best(criterion, primary_metric)
    top_band = ordered_bands[0] if ordered_bands else None

    picked: list[tuple[tuple[float, float], list[dict[str, Any]]]] = []
    for band in ordered_bands:
        rows = buckets.get(band, [])
        if not rows:
            picked.append((band, []))
            continue
        rows_sorted = sorted(rows, key=lambda r: r["_score"])
        keep: list[dict[str, Any]] = [rows_sorted[0]]
        if len(rows_sorted) >= n_per_band:
            median_idx = len(rows_sorted) // 2
            if rows_sorted[median_idx] is not rows_sorted[0]:
                keep.append(rows_sorted[median_idx])
        if null_best and band == top_band:
            null_rows = [r for r in rows if r.get(primary_metric) is None]
            non_null = [r for r in keep if r.get(primary_metric) is not None]
            if null_rows and non_null:
                # Replace the lowest-score row with a NULL row so the top
                # band always shows at least one NULL example alongside a
                # non-null one. Picks first NULL row in DB order for
                # deterministic output.
                keep = [null_rows[0], non_null[0]]
        picked.append((band, keep[:n_per_band]))
    return picked


def _verdict_label(
    criterion: Criterion, ctx: dict[str, Any], score: float
) -> str:
    """Compose ``pass`` / ``E<N>`` / ``E<N>:floor`` for one row."""
    scoring_ctx = {k: v for k, v in ctx.items() if not k.startswith("_")}
    for fc in criterion.fail_conditions:
        if fc.action != "exclude":
            continue
        try:
            triggered = bool(safe_eval(fc.condition_expr, scoring_ctx))
        except Exception:
            triggered = False
        if triggered:
            return fc.code
        if fc.pass_mark is not None and score < float(fc.pass_mark):
            return f"{fc.code}:floor"
    return "pass"


def _format_table(
    criterion: Criterion,
    grouped: Sequence[tuple[tuple[float, float], list[dict[str, Any]]]],
    primary_metric: str,
    extra_columns: Sequence[str],
) -> str:
    headers = ["band", "site_id", "country", primary_metric]
    headers.extend(extra_columns)
    headers.extend(["score", "verdict"])
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for band, rows in grouped:
        if not rows:
            empty_row = [
                f"{band[0]:.0f}-{band[1]:.0f}",
                "(no sites in this band)",
                "—",
                "—",
            ] + ["—"] * len(extra_columns) + ["—", "—"]
            lines.append("| " + " | ".join(empty_row) + " |")
            continue
        for ctx in rows:
            primary_val = ctx.get(primary_metric)
            cells: list[str] = [
                f"{band[0]:.0f}-{band[1]:.0f}",
                ctx["_site_id"][:8],
                str(ctx.get("_country", "—")),
                f"{primary_val:.2f}"
                if isinstance(primary_val, (int, float))
                else "NULL"
                if primary_val is None
                else str(primary_val),
            ]
            for col in extra_columns:
                v = ctx.get(col)
                if isinstance(v, (int, float)):
                    cells.append(f"{v:.2f}")
                else:
                    cells.append(str(v) if v is not None else "—")
            cells.append(f"{ctx['_score']:.1f}")
            cells.append(_verdict_label(criterion, ctx, ctx["_score"]))
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--criterion", required=True, help="Criterion ID (e.g. NH-04)"
    )
    p.add_argument(
        "--n-per-band", type=int, default=2, help="Sites to show per band"
    )
    p.add_argument(
        "--extra-columns",
        nargs="*",
        default=None,
        help="Extra DB columns to show (defaults: every secondary metric in db_fields.api).",
    )
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    bundle = load_template_bundle(str(SPEC_DIR))
    compiled = compile_bundle(bundle)
    if args.criterion not in compiled.criteria:
        print(
            f"Unknown criterion {args.criterion!r}. Known: "
            f"{sorted(compiled.criteria)}",
            file=sys.stderr,
        )
        return 2

    criterion = compiled.criteria[args.criterion]
    primary = criterion.primary_metric or ""
    if not primary:
        print(
            f"{args.criterion}: criterion has no primary_metric — cannot "
            "build a scored-examples table.",
            file=sys.stderr,
        )
        return 2

    if args.extra_columns is None:
        extras = [
            context_key
            for (_t, _db, context_key) in _resolve_metric_columns(criterion)
            if context_key != primary
        ]
    else:
        extras = list(args.extra_columns)

    with session_scope() as session:
        contexts = _fetch_contexts(session, criterion, primary)

    if not contexts:
        print(
            f"{args.criterion}: no sites in DB have {primary!r} populated; "
            "cannot generate examples.",
            file=sys.stderr,
        )
        return 1

    grouped = _pick_band_samples(criterion, contexts, args.n_per_band, primary)
    table = _format_table(criterion, grouped, primary, extras)

    print(f"## Scored examples — {args.criterion} (merged DB)\n")
    print(
        f"Two sites per band, picked by lowest + median {primary} within the band.\n"
    )
    print(table)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
