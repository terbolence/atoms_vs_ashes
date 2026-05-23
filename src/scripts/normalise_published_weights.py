"""Re-derive `normalised_weight_pct` from the runtime weight normaliser.

Phase 1A of the v1.03 feedback closure (reviewer #43): make the runtime
view in :func:`atoms_vs_ashes.scoring.rubric.weight_normalisation` the
single source of truth for every published per-criterion percentage.

This script:

1. Loads ``config/scoring_rubrics/`` and calls
   ``weight_normalisation(bundle, profile="baseline", basis=None)`` to
   get composite shares summing to 1.0 over the 41 composite-participating
   active criteria.
2. Rewrites the ``normalised_weight_pct`` field in every
   ``config/scoring_rubrics/*.yaml`` and ``config/scoring_specs/*.yaml``
   in-place. Composite participants get the new active-set percentage;
   non-composite criteria (basic-filter, exclusionary-only) get ``0.0``
   with an inline YAML comment so the field stays syntactically valid
   while reflecting that they no longer enter the composite normalisation.
3. Regenerates two canonical Markdown views:
   - ``report/version 1.03/sites_evaluation/02_master_weights.md`` master
     weight table + category roll-ups.
   - The five Stage 2 family tables in
     ``report/version 1.03/output/report/chapters/03_stage_2_site_selection.md``
     (delimited by HTML-comment markers inserted on first run for
     idempotency).

The script is idempotent: running it twice in a row produces a zero diff
on the second run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from atoms_vs_ashes.scoring.rubric import (  # noqa: E402
    Criterion,
    load_rubric_bundle,
    weight_normalisation,
)

RUBRIC_DIR = PROJECT_ROOT / "config" / "scoring_rubrics"
SPEC_DIR = PROJECT_ROOT / "config" / "scoring_specs"
REPORT_ROOT = PROJECT_ROOT / "report" / "version 1.03"
MASTER_WEIGHTS_MD = REPORT_ROOT / "sites_evaluation" / "02_master_weights.md"
STAGE2_CHAPTER_MD = (
    REPORT_ROOT / "output" / "report" / "chapters" / "03_stage_2_site_selection.md"
)

PHASE_LABELS_HEAD = {
    "basic_filter": "Basic filter",
    "exclusionary": "Exclusionary gate",
    "avoidance": "Avoidance signal",
    "ranking": "Ranking",
}
PHASE_LABELS_TAIL = {
    "basic_filter": "basic filter",
    "exclusionary": "exclusionary gate",
    "avoidance": "avoidance signal",
    "ranking": "ranking",
}

STAGE2_TABLE_GROUPS: list[tuple[str, str, list[str]]] = [
    ("nh", "3.2", ["NH-01", "NH-02", "NH-03", "NH-04", "NH-05", "NH-06", "NH-07",
                    "NH-08", "NH-09", "NH-10", "NH-11", "NH-12", "NH-13", "NH-14"]),
    ("hi", "3.3", ["HI-01", "HI-02", "HI-03", "HI-04", "HI-05", "HI-06", "HI-07", "HI-08"]),
    ("ri", "3.4", ["RI-01", "RI-02", "RI-03", "RI-04", "RI-05", "RI-06"]),
    ("ep", "3.5", ["EP-01", "EP-02", "EP-03", "EP-04", "EP-05"]),
    ("ns", "3.6", ["BF-02", "NS-01", "NS-02", "NS-03", "NS-04", "NS-05", "NS-06",
                    "NS-07", "NS-08", "NS-09", "NS-10", "NS-11", "NS-12", "NS-13"]),
]

MASTER_WEIGHTS_ORDER: list[str] = [
    "BF-01", "BF-02",
    *(f"NH-{i:02d}" for i in range(1, 15)),
    *(f"HI-{i:02d}" for i in range(1, 9)),
    *(f"RI-{i:02d}" for i in range(1, 7)),
    *(f"EP-{i:02d}" for i in range(1, 6)),
    *(f"NS-{i:02d}" for i in range(1, 14)),
]

FAMILY_NAMES = {
    "BF": "Basic filters (BF)",
    "NH": "Natural hazards (NH)",
    "HI": "Human-induced (HI)",
    "RI": "Radiological impact (RI)",
    "EP": "Emergency planning (EP)",
    "NS": "Non-safety (NS)",
}


def stage2_treatment(crit: Criterion) -> str:
    phases = list(crit.phases)
    if len(phases) == 1:
        return PHASE_LABELS_HEAD[phases[0]]
    head = PHASE_LABELS_HEAD[phases[0]]
    tails = [PHASE_LABELS_TAIL[p] for p in phases[1:]]
    return head + " and " + " and ".join(tails)


def compute_published_pcts(bundle: dict[str, Criterion]) -> dict[str, float]:
    """Map criterion_id -> published percentage (composite share or 0.0)."""
    composite = weight_normalisation(bundle, profile="baseline", basis=None)
    result: dict[str, float] = {}
    for cid in bundle:
        if cid in composite:
            result[cid] = composite[cid] * 100.0
        else:
            result[cid] = 0.0
    return result


# ---------------------------------------------------------------------------
# YAML rewriter — line-based, preserves comments, formatting, and ordering
# ---------------------------------------------------------------------------

_CRITERION_ID_RE = re.compile(r"^\s*-\s*criterion_id:\s*['\"]?([A-Z]{2}-\d{2})['\"]?\s*$")
_NORM_PCT_RE = re.compile(r"^(\s*normalised_weight_pct:\s*)([0-9]+(?:\.[0-9]+)?)(\s*(?:#.*)?)$")
_NORM_PCT_COMPOSITE_TAIL = ""
_NORM_PCT_NONCOMPOSITE_TAIL = "  # excluded from composite normalisation"


def _format_pct(value: float, composite_member: bool) -> str:
    """Round to 4 dp and trim trailing zeros so 1.7391304... -> 1.7391."""
    if not composite_member:
        return "0.0"
    s = f"{value:.4f}"
    s = s.rstrip("0").rstrip(".")
    return s or "0"


def rewrite_yaml(path: Path, pcts: dict[str, float], composite: set[str]) -> bool:
    """Rewrite ``normalised_weight_pct`` lines in ``path``. Returns True if changed."""
    original = path.read_text()
    lines = original.splitlines()
    current_cid: str | None = None
    changed = False
    out: list[str] = []
    for line in lines:
        cid_match = _CRITERION_ID_RE.match(line)
        if cid_match:
            current_cid = cid_match.group(1)
            out.append(line)
            continue
        pct_match = _NORM_PCT_RE.match(line)
        if pct_match and current_cid is not None and current_cid in pcts:
            prefix = pct_match.group(1)
            is_composite = current_cid in composite
            new_value = _format_pct(pcts[current_cid], is_composite)
            tail = (
                _NORM_PCT_COMPOSITE_TAIL if is_composite
                else _NORM_PCT_NONCOMPOSITE_TAIL
            )
            new_line = f"{prefix}{new_value}{tail}"
            if new_line != line:
                changed = True
            out.append(new_line)
            continue
        out.append(line)
    new_text = "\n".join(out)
    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    if new_text != original:
        path.write_text(new_text)
        return True
    return changed


# ---------------------------------------------------------------------------
# Master weights markdown rendering
# ---------------------------------------------------------------------------

MASTER_BEGIN = "<!-- begin: weights-master -->"
MASTER_END = "<!-- end: weights-master -->"


def _pct_4dp(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") + "%" if value > 0 else "0.0%"


def render_master_weights(
    bundle: dict[str, Criterion],
    pcts: dict[str, float],
) -> str:
    rows: list[str] = []
    rows.append("| ID    | Criterion                                       | Phase                          | Weight factor | Composite share |")
    rows.append("| ----- | ----------------------------------------------- | ------------------------------ | ------------: | --------------: |")
    total_wf = 0
    total_pct = 0.0
    for cid in MASTER_WEIGHTS_ORDER:
        if cid not in bundle:
            continue
        crit = bundle[cid]
        treatment = stage2_treatment(crit)
        share = pcts.get(cid, 0.0)
        rows.append(
            f"| {cid} | {crit.name:<47s} | {treatment:<30s} | {crit.weight_factor:>13d} | {_pct_4dp(share):>15s} |"
        )
        total_wf += crit.weight_factor
        total_pct += share
    rows.append(
        f"| **Σ** |                                                 |                                | **{total_wf}**       | **{_pct_4dp(total_pct)}**       |"
    )
    family_blocks: dict[str, tuple[int, float]] = {}
    for cid in MASTER_WEIGHTS_ORDER:
        if cid not in bundle:
            continue
        prefix = cid.split("-")[0]
        wf = bundle[cid].weight_factor
        share = pcts.get(cid, 0.0)
        cur = family_blocks.get(prefix, (0, 0.0))
        family_blocks[prefix] = (cur[0] + wf, cur[1] + share)
    rollup: list[str] = []
    rollup.append("")
    rollup.append("**Category roll-ups**")
    rollup.append("")
    rollup.append("| Category                  | Σ weight factor | Σ composite share |")
    rollup.append("| ------------------------- | --------------: | ----------------: |")
    for prefix, (wf, share) in family_blocks.items():
        rollup.append(
            f"| {FAMILY_NAMES[prefix]:<25s} | {wf:>15d} | {_pct_4dp(share):>17s} |"
        )
    rollup.append(
        f"| **Total**                 |        **{total_wf}** |       **{_pct_4dp(total_pct)}** |"
    )
    return "\n".join(rows + rollup)


def rewrite_master_weights(
    bundle: dict[str, Criterion], pcts: dict[str, float]
) -> bool:
    if not MASTER_WEIGHTS_MD.exists():
        raise FileNotFoundError(MASTER_WEIGHTS_MD)
    original = MASTER_WEIGHTS_MD.read_text()
    body = render_master_weights(bundle, pcts)
    block = f"{MASTER_BEGIN}\n{body}\n{MASTER_END}"
    if MASTER_BEGIN in original and MASTER_END in original:
        new_text = re.sub(
            rf"{re.escape(MASTER_BEGIN)}.*?{re.escape(MASTER_END)}",
            block,
            original,
            count=1,
            flags=re.DOTALL,
        )
    else:
        anchor = "## 3. Master weight table"
        if anchor not in original:
            raise RuntimeError(
                f"Cannot locate master-weights anchor {anchor!r} in {MASTER_WEIGHTS_MD}"
            )
        old_table_re = re.compile(
            r"(?ms)^\| ID\s+\|.*?(?=^\n## |\Z)"
        )
        match = old_table_re.search(original)
        if match is None:
            raise RuntimeError(
                "Could not find existing master-weights table to replace."
            )
        new_text = (
            original[: match.start()]
            + block
            + "\n\n"
            + original[match.end():].lstrip()
        )
    if new_text != original:
        MASTER_WEIGHTS_MD.write_text(new_text)
        return True
    return False


# ---------------------------------------------------------------------------
# Stage 2 chapter table rendering
# ---------------------------------------------------------------------------


def render_stage2_table(
    bundle: dict[str, Criterion],
    pcts: dict[str, float],
    cids: list[str],
) -> str:
    rows: list[str] = []
    rows.append("| Criterion | Public-facing name | Baseline weight (%) | Stage 2 treatment |")
    rows.append("| :---: | :--- | ---: | :--- |")
    for cid in cids:
        if cid not in bundle:
            continue
        crit = bundle[cid]
        share = pcts.get(cid, 0.0)
        share_str = f"{share:.4f}".rstrip("0").rstrip(".") or "0"
        rows.append(
            f"| {cid} | {crit.name} | {share_str} | {stage2_treatment(crit)} |"
        )
    return "\n".join(rows)


def rewrite_stage2_chapter(
    bundle: dict[str, Criterion], pcts: dict[str, float]
) -> bool:
    if not STAGE2_CHAPTER_MD.exists():
        raise FileNotFoundError(STAGE2_CHAPTER_MD)
    original = STAGE2_CHAPTER_MD.read_text()
    text = original
    for family, table_num, cids in STAGE2_TABLE_GROUPS:
        begin = f"<!-- begin: weights-{family} -->"
        end = f"<!-- end: weights-{family} -->"
        body = render_stage2_table(bundle, pcts, cids)
        block = f"{begin}\n{body}\n{end}"
        if begin in text and end in text:
            text = re.sub(
                rf"{re.escape(begin)}.*?{re.escape(end)}",
                block,
                text,
                count=1,
                flags=re.DOTALL,
            )
            continue
        caption_re = re.compile(
            rf"(?ms)^Table {re.escape(table_num)}\..*?\n\n"
            r"(\| Criterion \| Public-facing name.*?(?=\n\n))"
        )
        match = caption_re.search(text)
        if match is None:
            raise RuntimeError(
                f"Cannot find Stage 2 table {table_num} to wrap in {STAGE2_CHAPTER_MD}"
            )
        start, stop = match.span(1)
        text = text[:start] + block + text[stop:]
    if text != original:
        STAGE2_CHAPTER_MD.write_text(text)
        return True
    return False


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    bundle = load_rubric_bundle(str(RUBRIC_DIR))
    pcts = compute_published_pcts(bundle)
    composite_ids = {
        cid for cid, c in bundle.items() if c.participates_in_composite
    }
    total_published = sum(pcts.values())
    if not abs(total_published - 100.0) < 1e-6:
        raise RuntimeError(
            f"Composite published shares do not sum to 100%: {total_published!r}"
        )

    changes: list[str] = []
    for yaml_dir in (RUBRIC_DIR, SPEC_DIR):
        for path in sorted(yaml_dir.glob("*.yaml")):
            if path.name in {"threshold_metadata.yaml", "criterion_activation.yaml"}:
                continue
            if rewrite_yaml(path, pcts, composite_ids):
                changes.append(str(path.relative_to(PROJECT_ROOT)))
    if rewrite_master_weights(bundle, pcts):
        changes.append(str(MASTER_WEIGHTS_MD.relative_to(PROJECT_ROOT)))
    if rewrite_stage2_chapter(bundle, pcts):
        changes.append(str(STAGE2_CHAPTER_MD.relative_to(PROJECT_ROOT)))

    if changes:
        print(f"Updated {len(changes)} files:")
        for c in changes:
            print(f"  {c}")
    else:
        print("No changes (already normalised).")
    print(
        f"Composite participants: {len(composite_ids)}; "
        f"sum of published percentages: {total_published:.6f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
