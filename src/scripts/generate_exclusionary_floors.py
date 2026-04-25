# man_hours: 1.5
"""Generate ``report/methodology/exclusionary_floors.md`` from the rubric YAMLs.

For every criterion that carries one or more ``action: exclude``
fail conditions, the doc records:

- Criterion ID + name + source YAML
- Hard fail expression (``condition_expr``) and its descriptor
- Declared ``pass_mark`` (0-10 ranking-score floor)
- The 0-10 band table that maps metric values to scores
- Minimum metric value required to clear the floor (the band 5-6 expr)

The doc is the source-of-truth cross-reference between the rubric, the
methodology narrative, and the IAEA expert-review pack. It is fully
generated; ``tests/scoring/test_exclusionary_floors_doc.py`` asserts the
on-disk file matches the generator output so YAML changes cannot drift
silently.

Run:
    .venv/bin/python -m scripts.generate_exclusionary_floors
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from atoms_vs_ashes.scoring.rubric import (
    Band,
    Criterion,
    FailCondition,
    SubScore,
    load_rubric_bundle,
)

DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")
DEFAULT_OUT_PATH = Path("report/methodology/exclusionary_floors.md")
SOURCE_FILE_FOR_CODE = {
    "E1": "nh_natural_hazards.yaml",
    "E2": "nh_natural_hazards.yaml",
    "E3": "nh_natural_hazards.yaml",
    "E4": "nh_natural_hazards.yaml",
    "E5": "nh_natural_hazards.yaml",
    "E6": "nh_natural_hazards.yaml",
    "project_wind_envelope": "nh_natural_hazards.yaml",
    "E7": "ns_non_safety.yaml",
    "E8": "ep_emergency_planning.yaml",
    "E9": "ns_non_safety.yaml",
}


@dataclass
class FlooredEntry:
    code: str
    criterion: Criterion
    fail: FailCondition

    @property
    def source_yaml(self) -> str:
        return SOURCE_FILE_FOR_CODE.get(self.code, "scoring_rubrics/*.yaml")


def _iter_floored(bundle: dict[str, Criterion]) -> Iterable[FlooredEntry]:
    for crit in bundle.values():
        for fc in crit.fail_conditions:
            if fc.action == "exclude" and fc.pass_mark is not None:
                yield FlooredEntry(code=fc.code, criterion=crit, fail=fc)


def _band_5_6_anchor(crit: Criterion) -> str:
    """Return the 5-6 band condition_expr (best proxy for 'min to clear floor')."""

    def _scan(bands: list[Band]) -> str | None:
        for band in bands:
            lo, hi = band.score_range
            if lo == 5 and hi == 6:
                return band.condition_expr
        return None

    if crit.bands:
        anchor = _scan(crit.bands)
        if anchor:
            return anchor
    if crit.sub_scores:
        for sub in crit.sub_scores:
            anchor = _scan(list(sub.bands))
            if anchor:
                return f"{sub.key}: {anchor}"
    return "(no 5-6 band declared)"


def _bands_table(crit: Criterion) -> str:
    rows: list[str] = []
    if crit.bands:
        rows.extend(_format_band_rows(crit.bands))
    elif crit.sub_scores:
        for sub in crit.sub_scores:
            rows.append(f"| _sub-score: {sub.key}_ |  |  |")
            rows.extend(_format_band_rows(list(sub.bands)))
    if not rows:
        return "_no band table declared_"
    header = "| Band | Condition | Descriptor |\n| --- | --- | --- |"
    return header + "\n" + "\n".join(rows)


def _format_band_rows(bands: list[Band]) -> list[str]:
    out: list[str] = []
    for band in sorted(bands, key=lambda b: -b.score_range[0]):
        lo, hi = band.score_range
        label = f"{int(lo)}-{int(hi)}" if lo != hi else f"{int(lo)}"
        out.append(
            f"| **{label}** | `{band.condition_expr}` | {band.descriptor.strip() or '—'} |"
        )
    return out


def _summary_table(entries: list[FlooredEntry]) -> str:
    header = (
        "| E-code | Criterion | Source YAML | Hard fail expression | pass_mark "
        "| Min metric to clear floor |\n"
        "| --- | --- | --- | --- | --- | --- |"
    )
    rows = []
    for e in entries:
        anchor = _band_5_6_anchor(e.criterion).replace("|", "\\|")
        expr = e.fail.condition_expr.replace("|", "\\|")
        rows.append(
            f"| `{e.code}` | {e.criterion.criterion_id} — {e.criterion.name} "
            f"| {e.source_yaml} | `{expr}` | {e.fail.pass_mark:.1f} | `{anchor}` |"
        )
    return header + "\n" + "\n".join(rows)


def _detail_section(e: FlooredEntry) -> str:
    crit = e.criterion
    fc = e.fail
    parts = [
        f"### {e.code} — {crit.criterion_id} {crit.name}",
        "",
        f"- **Source**: `config/scoring_rubrics/{e.source_yaml}`",
        f"- **Phases**: {', '.join(crit.phases)}",
        f"- **Hard fail expression**: `{fc.condition_expr}`",
        f"- **Hard fail descriptor**: {fc.descriptor}",
        f"- **Floor (pass_mark)**: {fc.pass_mark:.1f}",
        f"- **Min metric to clear floor (band 5-6)**: `{_band_5_6_anchor(crit)}`",
        "",
        _bands_table(crit),
        "",
    ]
    return "\n".join(parts)


def render_document(bundle: dict[str, Criterion]) -> str:
    entries = sorted(_iter_floored(bundle), key=lambda e: e.code)
    if not entries:
        return "# Exclusionary Floors\n\n_No exclusionary fail conditions declared._\n"

    blocks: list[str] = [
        "# Exclusionary Floors — Source-of-Truth Reference",
        "",
        "> Generated by `python -m scripts.generate_exclusionary_floors` from",
        "> `config/scoring_rubrics/*.yaml`. Do not hand-edit. The unit test",
        "> `tests/scoring/test_exclusionary_floors_doc.py` asserts the on-disk",
        "> file matches the generator output, so YAML edits cannot drift silently.",
        "",
        "## How the dual gate works",
        "",
        "Each exclusionary criterion can mark a (site, SMR) pair as failed via",
        "two independent gates. Both produce `passed_exclusionary = False` and",
        "`composite_score = NULL` in `composite_rankings`, which the banding /",
        "country / sensitivity layers all skip.",
        "",
        "1. **Hard E-code** — the rubric's `condition_expr` evaluates to true",
        "   (e.g. `nearest_fault_km < 5`). The verdict carries `prompt_key = E1`.",
        "2. **Safety floor** — the evaluated 0–10 ranking score is strictly",
        "   below `pass_mark` (e.g. score 4 on NH-04). The verdict carries",
        "   `prompt_key = E1:floor` so audits can distinguish the two paths.",
        "",
        "Underlying `ranking_scores` rows are written for **both** outcomes",
        "(transparency principle). Excluded sites therefore retain their raw",
        "0–10 evidence in the audit trail without polluting any ranking.",
        "",
        "## Summary",
        "",
        _summary_table(entries),
        "",
        "## Details",
        "",
    ]
    for e in entries:
        blocks.append(_detail_section(e))
    return "\n".join(blocks).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rubric-dir",
        type=Path,
        default=DEFAULT_RUBRIC_DIR,
        help="Directory holding the YAML rubric files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_PATH,
        help="Output Markdown path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated text against the on-disk file; exit 1 on drift.",
    )
    args = parser.parse_args(argv)

    bundle = load_rubric_bundle(args.rubric_dir)
    rendered = render_document(bundle)

    if args.check:
        existing = args.out.read_text() if args.out.exists() else ""
        if existing != rendered:
            raise SystemExit(
                f"DRIFT: {args.out} is out of sync with {args.rubric_dir}. "
                "Re-run scripts.generate_exclusionary_floors."
            )
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(f"Wrote {args.out} ({len(rendered)} chars, {len(list(_iter_floored(bundle)))} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
