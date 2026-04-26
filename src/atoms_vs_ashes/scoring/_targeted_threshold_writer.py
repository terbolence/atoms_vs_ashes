# man_hours: 0.75
"""CSV + JSON writers for the targeted-threshold sensitivity sweep.

Drops two artefacts next to the sensitivity audit MD so the GUI's
four-panel sensitivity view (plan §8) and the future
``GET /metrics/{run_id}`` endpoint both have a stable on-disk source of
truth before the dedicated ``threshold_sensitivity_targeted`` analytics
table is added.

- ``<stamp>_threshold_targeted.csv`` — long-format rows, suitable for
  pandas / spreadsheet drill-down.
- ``<stamp>_threshold_targeted.json`` — same payload + metadata, ready
  for direct embedding in :class:`MetricsBundle.sensitivity`.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_threshold_targeted_helpers import (
    TargetedThresholdSuiteResult,
)

log = get_logger(__name__)

_CSV_FIELDS = (
    "criterion_id",
    "code",
    "metric",
    "op",
    "units",
    "base_value",
    "perturbed_value",
    "perturbation_pct",
    "direction",
    "n_pairs_added",
    "n_pairs_removed",
    "n_pairs_evaluated",
    "mean_margin_delta",
    "median_margin_delta",
    "p95_margin_delta",
)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def write_targeted_threshold_artefacts(
    result: TargetedThresholdSuiteResult,
    *,
    audit_dir: Path,
    run_id: str,
    stamp: str | None = None,
) -> dict[str, Path]:
    """Write CSV + JSON artefacts; return ``{"csv": ..., "json": ...}``.

    ``stamp`` defaults to today's UTC ``YYYYMMDD`` so callers can
    deterministically pin filenames in tests.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or _stamp()
    csv_path = audit_dir / f"{stamp}_threshold_targeted.csv"
    json_path = audit_dir / f"{stamp}_threshold_targeted.json"

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({k: getattr(row, k) for k in _CSV_FIELDS})

    payload = {
        "run_id": run_id,
        "stamp": stamp,
        **result.to_dict(),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    log.info(
        "targeted_threshold_artefacts_written",
        run_id=run_id,
        rows=len(result.rows),
        csv=str(csv_path),
        json=str(json_path),
    )
    return {"csv": csv_path, "json": json_path}


def render_targeted_threshold_md(
    result: TargetedThresholdSuiteResult, *, top_n: int = 20
) -> str:
    """Return a sortable markdown table; appended by the audit writer."""
    if not result.rows:
        return "_No targeted-threshold rows produced._"
    sorted_rows = sorted(
        result.rows,
        key=lambda r: (r.n_pairs_added + r.n_pairs_removed),
        reverse=True,
    )
    header = (
        "| Criterion | Code | Direction | Pct | Base | Perturbed | "
        "Added | Removed | Mean Δ |"
    )
    sep = "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    lines = [
        f"_Targets: {len(result.targets)} · pct_steps: {list(result.pct_steps)} "
        f"· total rows: {len(result.rows)} (top {top_n} by membership churn)_",
        "",
        header,
        sep,
    ]
    for r in sorted_rows[:top_n]:
        mean_delta = (
            f"{r.mean_margin_delta:+.3f}" if r.mean_margin_delta is not None else "—"
        )
        lines.append(
            f"| {r.criterion_id} | {r.code} | {r.direction} | "
            f"{r.perturbation_pct:.1f} | {r.base_value:g} | "
            f"{r.perturbed_value:g} | {r.n_pairs_added} | "
            f"{r.n_pairs_removed} | {mean_delta} |"
        )
    return "\n".join(lines)


__all__ = [
    "render_targeted_threshold_md",
    "write_targeted_threshold_artefacts",
]
