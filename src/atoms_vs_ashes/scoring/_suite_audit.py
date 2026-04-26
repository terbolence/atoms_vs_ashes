# man_hours: 1.5
"""Audit markdown writer for the sensitivity suite."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_config import (
    SensitivitySuiteConfig,
    SensitivitySuiteResult,
)
from atoms_vs_ashes.scoring.sensitivity import CountryBalanceReport

log = get_logger(__name__)


def write_audit_md(
    cfg: SensitivitySuiteConfig,
    result: SensitivitySuiteResult,
    country_report: CountryBalanceReport | None,
    *,
    provenance_block: str | None = None,
) -> Path:
    """Write ``<audit_dir>/<YYYYMMDD>_sensitivity.md`` (≤ 500 lines).

    ``provenance_block`` is the optional ``## Provenance`` markdown
    block emitted by
    :func:`atoms_vs_ashes.runprofile.render_provenance_md`; when
    supplied it is inserted directly after the run-header so audit
    MDs disclose run-profile/spec hashes alongside the existing
    sensitivity metadata.
    """
    cfg.audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = f"_{result.mc_label}" if cfg.include_mc else ""
    path = cfg.audit_dir / f"{stamp}_sensitivity{suffix}.md"

    lines: list[str] = []
    lines.append(f"# Sensitivity run — {stamp}")
    lines.append("")
    lines.append(f"- Run ID: `{result.run_id}`")
    lines.append(f"- Iterations: **{cfg.iterations}**")
    lines.append(f"- Preset: `{cfg.preset_label or 'custom'}`")
    lines.append(f"- Seed: `{cfg.seed}`")
    lines.append(f"- Weight profile base: `{cfg.weight_profile_base}`")
    lines.append(f"- Rubric dir: `{cfg.rubric_dir}`")
    lines.append("")
    if provenance_block:
        lines.append(provenance_block.rstrip())
        lines.append("")
    lines.append("## Config")
    lines.append("")
    lines.append("```json")
    lines.append(
        json.dumps(
            {
                "include_weights": cfg.include_weights,
                "include_mc": cfg.include_mc,
                "include_country": cfg.include_country,
                "include_threshold": cfg.include_threshold,
                "top_n_country": cfg.top_n_country,
                "progress_enabled": cfg.progress_enabled,
            },
            indent=2,
        )
    )
    lines.append("```")
    lines.append("")
    lines.append("## Rows persisted")
    lines.append("")
    lines.append(f"- Pairs processed: {result.pairs}")
    lines.append(f"- Weight-sensitivity rows: {result.weight_rows_persisted}")
    lines.append(f"- Monte Carlo rows (`{result.mc_label}`): {result.mc_rows_persisted}")
    lines.append(f"- Threshold (±25 %) rows: {result.threshold_rows_persisted}")
    lines.append(f"- Country-balanced rows: {result.country_balanced_rows_persisted}")
    lines.append("")
    lines.append("## Country balance")
    lines.append("")
    if country_report is None:
        lines.append("_Not run (include_country=False or no baseline composites)._")
    else:
        lines.append(f"- Total sites ranked: {country_report.total_sites}")
        lines.append(f"- Top-N: {country_report.top_n}")
        lines.append(f"- Max share: {country_report.max_share}")
        lines.append(f"- Flagged: **{country_report.flagged}**")
        lines.append("")
        lines.append("| Country | Count |")
        lines.append("| --- | ---: |")
        for code, cnt in sorted(
            country_report.country_counts.items(), key=lambda x: -x[1]
        ):
            lines.append(f"| {code} | {cnt} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for n in result.notes or ["(no additional notes)"]:
        lines.append(f"- {n}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("sensitivity_audit_written", path=str(path))
    return path
