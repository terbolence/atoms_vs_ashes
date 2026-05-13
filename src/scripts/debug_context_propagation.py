# man_hours: 0.8
"""Debug whether derived context values reach the band evaluator at score time.

Read-only diagnostic for the P2-2 audit step. For each anchor site (or any
site passed via ``--site``), the script loads the merged context that
:mod:`atoms_vs_ashes.scoring.merge_resolver` would build for every
criterion in the rubric bundle, then prints which keys in
``DERIVED_CONTEXT_NAMES`` and the SP-F sentinel keys are actually present.

The result is the smoking gun for the "favorable branch does not fire even
though the YAML is correct" symptom: if a derived key is absent at score
time, the rubric expression cannot use it and the band silently falls
through to the unscored default.

Output is a Markdown report listing per-site:

- One row per criterion in the bundle.
- One column per key in ``DERIVED_CONTEXT_NAMES`` plus ``country_code``.
- ``T`` if the key is present (including ``None``), ``-`` if absent.

Never writes to the DB.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.scoring.merge_context_derivations import DERIVED_CONTEXT_NAMES
from atoms_vs_ashes.scoring.merge_resolver import build_context_for_site
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"

ANCHOR_SITES: dict[str, uuid.UUID] = {
    "timelkam": uuid.UUID("2dcd2c6d-f375-4408-9492-7910662fac03"),
    "braila": uuid.UUID("29836b52-a882-4921-95a7-6417e636d9a2"),
    "riedersbach": uuid.UUID("660d9d71-6733-4294-951b-1c58614d58cf"),
}

KEY_GROUPS: dict[str, list[str]] = {
    "country / landlocked": [
        "country_code",
        "country_is_landlocked",
    ],
    "HI search sentinels": [
        "hi02_search_completed",
        "hi04_search_completed",
        "hi05_search_completed",
        "hi08_search_completed",
    ],
    "military": [
        "nearest_military_airfield_km",
        "nearest_military_class",
        "nearest_high_consequence_military_km",
        "hi06_quality",
    ],
    "aliases": [
        "nearest_volcano_km",
        "coast_distance_km",
        "river_distance_km",
        "flood_zone_class_500yr",
        "slope_angle_mean_deg",
    ],
}


def _present(values: dict[str, object], key: str) -> str:
    if key not in values:
        return "-"
    val = values[key]
    if val is None:
        return "Tn"
    return "T"


def _render_site_section(site_name: str, site: Site, ctx_by_criterion) -> str:
    lines = [f"## {site_name} (`{site.site_id}`)", ""]
    for group, keys in KEY_GROUPS.items():
        lines.append(f"### {group}")
        lines.append("")
        header = ["criterion", *keys]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for cid, ctx in ctx_by_criterion.items():
            row = [cid] + [_present(ctx.values, k) for k in keys]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


def _gap_summary(ctx_by_criterion_per_site: dict) -> str:
    """Cross-site summary of which keys are missing for any criterion."""
    lines = ["## Gap summary across sites", ""]
    lines.append("| Key | Sites where missing for ≥1 criterion |")
    lines.append("|---|---|")
    all_keys = [k for group in KEY_GROUPS.values() for k in group]
    for key in all_keys:
        missing_sites = []
        for site_name, ctx_by_criterion in ctx_by_criterion_per_site.items():
            if any(key not in ctx.values for ctx in ctx_by_criterion.values()):
                missing_sites.append(site_name)
        lines.append(f"| `{key}` | {', '.join(missing_sites) or '—'} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        default="20260513T030738_70d5bc2c",
        help="Used for the output header only; the diagnostic reads the "
        "current DB state, not a specific run snapshot.",
    )
    parser.add_argument(
        "--site",
        action="append",
        choices=sorted(ANCHOR_SITES),
        default=None,
        help="Restrict to one or more anchor sites (default: all three).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the markdown report. Default: stdout.",
    )
    args = parser.parse_args()

    bundle = load_rubric_bundle(RUBRIC_DIR)
    site_filter = set(args.site) if args.site else set(ANCHOR_SITES)

    pieces: list[str] = [
        "<!-- man_hours: 0.3 -->",
        f"# Context propagation diagnostic (run anchor: {args.run_id})",
        "",
        "`T` = key is present with a non-null value. `Tn` = key is present "
        "but the value is `None` (e.g. an explicit sentinel). `-` = key is "
        "absent from the per-criterion context (the rubric expression cannot "
        "reference it without raising `NameError`).",
        "",
    ]

    ctx_by_criterion_per_site: dict[str, dict] = {}
    with session_scope() as session:
        for site_name in sorted(site_filter):
            site_id = ANCHOR_SITES[site_name]
            site = session.query(Site).filter(Site.site_id == site_id).one_or_none()
            if site is None:
                pieces.append(f"## {site_name}\n\n*Site not in DB.*\n")
                continue
            ctx_by_criterion = {}
            for cid in sorted(bundle):
                ctx_by_criterion[cid] = build_context_for_site(
                    session, site, bundle[cid]
                )
            ctx_by_criterion_per_site[site_name] = ctx_by_criterion
            pieces.append(_render_site_section(site_name, site, ctx_by_criterion))
            pieces.append("")

    pieces.append(_gap_summary(ctx_by_criterion_per_site))
    pieces.append("")
    pieces.append(
        "DERIVED_CONTEXT_NAMES (declared in `merge_context_derivations.py`): "
        + ", ".join(f"`{k}`" for k in sorted(DERIVED_CONTEXT_NAMES))
    )

    text = "\n".join(pieces).rstrip() + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
