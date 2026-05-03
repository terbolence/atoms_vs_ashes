# man_hours: 2.0
"""In-Cursor specialist interpretation helper.

The Atoms vs Ashes report fills its specialist interpretation
placeholders inside Cursor (no external LLM API call). One single
prompt, ``report/output/writing plan/prompts/specialists/siting_expert.md``,
covers every interpretation block. The output shape is selected by
the placeholder key.

This CLI is the helper the Cursor agent uses to do that work:

1. ``list`` - print the pending placeholders for a country, a site,
   or the whole country folder.
2. ``show`` - print the system prompt and the bundle slice for one
   placeholder. Use it to load context before drafting.
3. ``patch`` - replace the body of one placeholder with the agent's
   drafted paragraph. Idempotent (refuses to overwrite ``status=filled``
   without ``--force``); rewrites the open tag to record
   ``status=filled by=cursor-agent filled_at=<UTC>``.

Live-API safety rule: this script does not call any external API.
The audit trail is the git diff plus the ``filled_at`` / ``filled_by``
attributes the patch step writes into the placeholder open tag.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = REPO_ROOT / "report" / "output" / "chapters" / "05_country_and_site_profiles"
SPECIALISTS_DIR = REPO_ROOT / "report" / "output" / "writing plan" / "prompts" / "specialists"
SITING_EXPERT_FILE = SPECIALISTS_DIR / "siting_expert.md"

FAMILY_KEYS = {
    "family_natural_hazards": {
        "bundle_key": "natural_hazards",
        "label": "Natural Hazards (NH)",
        "criteria_prefixes": ("NH", "BF-02"),
    },
    "family_human_hazards": {
        "bundle_key": "human_hazards",
        "label": "Human-Induced and Security-Relevant Hazards (HI)",
        "criteria_prefixes": ("HI",),
    },
    "family_radiological_emergency": {
        "bundle_key": ("radiological", "emergency_planning"),
        "label": "Radiological Impact and Emergency Planning (RI / EP)",
        "criteria_prefixes": ("RI", "EP"),
    },
    "family_infrastructure": {
        "bundle_key": "infrastructure",
        "label": "Non-Safety / Implementation (NS)",
        "criteria_prefixes": ("NS", "BF-01"),
    },
}
SYNTHESIS_KEYS = ("residual_risk", "stability", "country_exec")

PLACEHOLDER_RE = re.compile(
    r"<!-- specialist key=(?P<key>\S+) "
    r"(?P<attrs>[^>]*?)"
    r"-->\n(?P<body>.*?)\n<!-- /specialist key=(?P=key) -->",
    re.DOTALL,
)
ATTR_RE = re.compile(r"(\w+)=([^\s>]+)")


# ---- placeholder model -----------------------------------------------------


@dataclass
class Placeholder:
    key: str
    attrs: dict[str, str]
    span: tuple[int, int]
    body: str
    md_path: Path

    @property
    def status(self) -> str:
        return self.attrs.get("status", "pending")

    @property
    def scope(self) -> str:
        return self.attrs.get("scope", "site")

    @property
    def site_id(self) -> str | None:
        return self.attrs.get("site_id")

    @property
    def country_code(self) -> str | None:
        return self.attrs.get("country_code")

    @property
    def bundle_filename(self) -> str | None:
        return self.attrs.get("bundle")


def discover_placeholders(md_path: Path) -> list[Placeholder]:
    text = md_path.read_text(encoding="utf-8")
    out: list[Placeholder] = []
    for match in PLACEHOLDER_RE.finditer(text):
        attrs = dict(ATTR_RE.findall(match.group("attrs")))
        out.append(
            Placeholder(
                key=match.group("key"),
                attrs=attrs,
                span=match.span(),
                body=match.group("body"),
                md_path=md_path,
            )
        )
    return out


# ---- prompt resolution -----------------------------------------------------


def load_specialist_prompt(key: str) -> str:
    """Single source of truth for every interpretation block."""
    if key not in FAMILY_KEYS and key not in SYNTHESIS_KEYS:
        raise SystemExit(
            f"Unknown specialist key: {key}. Valid keys: "
            + ", ".join(sorted(list(FAMILY_KEYS) + list(SYNTHESIS_KEYS)))
        )
    if not SITING_EXPERT_FILE.exists():
        raise SystemExit(f"Missing specialist prompt: {SITING_EXPERT_FILE}")
    return SITING_EXPERT_FILE.read_text(encoding="utf-8")


# ---- bundle slicing --------------------------------------------------------


def slice_for_key(key: str, site_bundle: dict[str, Any] | None,
                  country_bundle: dict[str, Any] | None) -> dict[str, Any]:
    if key == "country_exec":
        if country_bundle is None:
            raise SystemExit("country_exec requires the country bundle")
        return _country_exec_slice(country_bundle)
    if site_bundle is None:
        raise SystemExit(f"{key} requires the site bundle")
    if key == "stability":
        return _stability_slice(site_bundle)
    if key == "residual_risk":
        return _residual_slice(site_bundle)
    if key in FAMILY_KEYS:
        return _family_slice(key, site_bundle)
    raise SystemExit(f"Unknown specialist key: {key}")


def _family_slice(key: str, site_bundle: dict[str, Any]) -> dict[str, Any]:
    """Slice for one family-level interpretation paragraph.

    Returns the family measurement row, every ranking and verdict for
    the family's criteria, and a small criteria-meta lookup so the
    siting expert can write one paragraph per family.
    """
    cfg = FAMILY_KEYS[key]
    bundle_key = cfg["bundle_key"]
    if isinstance(bundle_key, str):
        bundle_keys = (bundle_key,)
    else:
        bundle_keys = bundle_key
    site = site_bundle.get("site") or {}
    smr_label = (site_bundle.get("metadata") or {}).get(
        "smr_label", "NuScale VOYGR-6",
    )
    families = site_bundle.get("criterion_families") or {}
    verdicts = (site_bundle.get("screening") or {}).get("verdicts") or []
    rankings = (site_bundle.get("scoring") or {}).get("ranking_scores") or []
    components = (site_bundle.get("scoring") or {}).get(
        "criterion_components",
    ) or []
    family_row: dict[str, Any] = {}
    for bk in bundle_keys:
        row = families.get(bk) or {}
        if isinstance(row, dict):
            family_row.update(row)
    prefixes = tuple(cfg["criteria_prefixes"])
    in_family = lambda cid: bool(cid) and cid.startswith(prefixes)
    family_rankings = [
        r for r in rankings if in_family(r.get("criterion_id"))
    ]
    family_verdicts = [
        v for v in verdicts if in_family(v.get("criterion_id"))
    ]
    family_components = [
        c for c in components
        if in_family(c.get("criterion_id"))
        and c.get("weight_profile") == "baseline"
    ]
    return {
        "site": _site_summary(site),
        "smr_label": smr_label,
        "family_key": key,
        "family_label": cfg["label"],
        "family_row": family_row,
        "rankings": sorted(
            family_rankings, key=lambda r: r.get("criterion_id") or "",
        ),
        "verdicts": sorted(
            family_verdicts, key=lambda v: v.get("criterion_id") or "",
        ),
        "components": sorted(
            family_components, key=lambda c: c.get("criterion_id") or "",
        ),
        "criteria_lookup": {
            cid: site_bundle.get("criteria_lookup", {}).get(cid, {})
            for cid in {
                r.get("criterion_id") for r in family_rankings
            } | {
                v.get("criterion_id") for v in family_verdicts
            } if cid
        },
    }


def _stability_slice(site_bundle: dict[str, Any]) -> dict[str, Any]:
    site = site_bundle.get("site") or {}
    smr_label = (site_bundle.get("metadata") or {}).get(
        "smr_label", "NuScale VOYGR-6",
    )
    composites = (site_bundle.get("scoring") or {}).get(
        "composite_rankings",
    ) or []
    components = (site_bundle.get("scoring") or {}).get(
        "criterion_components",
    ) or []
    bands = (site_bundle.get("sensitivity") or {}).get("bands") or []
    baseline = next(
        (c for c in composites if c.get("weight_profile") == "baseline"),
        composites[0] if composites else {},
    )
    top_components = sorted(
        [
            c for c in components
            if c.get("weight_profile") == "baseline"
            and c.get("weighted_contribution") is not None
        ],
        key=lambda c: float(c.get("weighted_contribution") or 0),
        reverse=True,
    )[:6]
    return {
        "site": _site_summary(site),
        "smr_label": smr_label,
        "composite_baseline": baseline,
        "top_contributors": top_components,
        "bands": [
            b for b in bands
            if b.get("country_code") == site.get("country_code")
        ] or bands[:1],
    }


def _residual_slice(site_bundle: dict[str, Any]) -> dict[str, Any]:
    site = site_bundle.get("site") or {}
    smr_label = (site_bundle.get("metadata") or {}).get(
        "smr_label", "NuScale VOYGR-6",
    )
    families = site_bundle.get("criterion_families") or {}
    verdicts = (site_bundle.get("screening") or {}).get("verdicts") or []
    rankings = (site_bundle.get("scoring") or {}).get("ranking_scores") or []
    bands = (site_bundle.get("sensitivity") or {}).get("bands") or []
    flagged = [
        v for v in verdicts
        if str(v.get("phase")) == "avoidance"
        and str(v.get("verdict")) in ("fail", "caution")
    ]
    weakest = sorted(
        [r for r in rankings if r.get("score_0_10") is not None],
        key=lambda r: float(r.get("score_0_10") or 0),
    )[:8]
    keep_criteria = {v.get("criterion_id") for v in flagged}
    keep_criteria.update(r.get("criterion_id") for r in weakest)
    family_slim: dict[str, Any] = {}
    for fam_key, fam_row in families.items():
        if not isinstance(fam_row, dict):
            continue
        row_subset = {
            k: v for k, v in fam_row.items()
            if k.endswith("_quality") or any(
                cid.lower().replace("-", "") in k.lower()
                for cid in keep_criteria if cid
            )
        }
        if row_subset:
            family_slim[fam_key] = row_subset
    return {
        "site": _site_summary(site),
        "smr_label": smr_label,
        "criterion_families_slim": family_slim,
        "flagged_verdicts": flagged,
        "weakest_ranking_scores": weakest,
        "bands": [
            b for b in bands
            if b.get("country_code") == site.get("country_code")
        ] or bands[:1],
        "criteria_lookup": {
            cid: site_bundle.get("criteria_lookup", {}).get(cid, {})
            for cid in keep_criteria if cid
        },
    }


def _country_exec_slice(country_bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": country_bundle.get("metadata", {}),
        "totals": country_bundle.get("totals", {}),
        "sites": [
            _country_site_summary(row)
            for row in country_bundle.get("sites", [])
        ],
        "avoidance_pareto": country_bundle.get("avoidance_pareto", []),
        "exclusionary_failure_pareto": country_bundle.get(
            "exclusionary_failure_pareto", [],
        ),
        "family_normalised_score_means": country_bundle.get(
            "family_normalised_score_means", {},
        ),
    }


def _site_summary(site: dict[str, Any]) -> dict[str, Any]:
    return {
        k: site.get(k)
        for k in (
            "site_id", "name", "country_code", "subnational_unit",
            "latitude", "longitude", "installed_capacity_mw",
        )
    }


def _country_site_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        k: row.get(k)
        for k in (
            "site_id", "name", "national_rank",
            "passed_exclusionary", "passed_avoidance",
            "composite_score", "composite_score_low", "composite_score_high",
            "national_band", "national_top10pct_hit_rate",
            "installed_capacity_mw",
        )
    }


# ---- bundle / md path resolution ------------------------------------------


def country_bundle_path(country_code: str) -> Path:
    return PROFILES_DIR / "data" / f"{country_code}_country_bundle.json"


def country_md_path(country_code: str) -> Path:
    return PROFILES_DIR / f"{country_code}_country_prototype.md"


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()


def site_md_path(country_code: str, site_name: str) -> Path:
    return PROFILES_DIR / "sites" / f"{country_code}_{_slug(site_name)}.md"


def site_bundle_path(country_code: str, site_name: str) -> Path:
    return (
        PROFILES_DIR / "data"
        / f"{country_code}_{_slug(site_name)}_site_bundle.json"
    )


def load_country_bundle(country_code: str) -> dict[str, Any]:
    path = country_bundle_path(country_code)
    if not path.exists():
        raise SystemExit(
            f"Country bundle not found: {path}. Build it with "
            "`python -m scripts.build_country_profile_prototype "
            f"--country-code {country_code} --site-name <site>`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def find_site_bundle_for_md(md_path: Path) -> Path | None:
    """Convert ``RO_turceni_power_station.md`` to its bundle path."""
    stem = md_path.stem
    return md_path.parent.parent / "data" / f"{stem}_site_bundle.json"


def site_name_from_md_path(md_path: Path) -> str:
    """Reverse-engineer the site display name from the md filename."""
    stem = md_path.stem
    parts = stem.split("_", 1)
    if len(parts) == 2:
        return parts[1].replace("_", " ")
    return stem


# ---- placeholder discovery walks ------------------------------------------


def country_placeholders(country_code: str) -> list[Placeholder]:
    md = country_md_path(country_code)
    if not md.exists():
        return []
    return discover_placeholders(md)


def site_placeholders_for_country(country_code: str) -> dict[Path, list[Placeholder]]:
    """Map of site md path -> its placeholders."""
    out: dict[Path, list[Placeholder]] = {}
    site_dir = PROFILES_DIR / "sites"
    if not site_dir.exists():
        return out
    for md in sorted(site_dir.glob(f"{country_code}_*.md")):
        out[md] = discover_placeholders(md)
    return out


# ---- subcommand: list ------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    cc = args.country.upper()
    only_pending = not args.include_filled
    rows: list[tuple[str, str, str, str]] = []
    if not args.sites_only:
        for ph in country_placeholders(cc):
            if only_pending and ph.status != "pending":
                continue
            rows.append((cc, "country", ph.key, ph.status))
    for md_path, placeholders in site_placeholders_for_country(cc).items():
        site_label = site_name_from_md_path(md_path)
        if args.site_name and args.site_name.casefold() not in site_label.casefold():
            continue
        if args.site_id:
            site_id_match = any(
                ph.site_id == args.site_id for ph in placeholders
            )
            if not site_id_match:
                continue
        for ph in placeholders:
            if only_pending and ph.status != "pending":
                continue
            rows.append((cc, site_label, ph.key, ph.status))
    if not rows:
        print(f"No matching placeholders for {cc}.")
        return 0
    width_country = max(2, max(len(r[0]) for r in rows))
    width_site = max(4, max(len(r[1]) for r in rows))
    width_key = max(3, max(len(r[2]) for r in rows))
    print(
        f"{'CC':<{width_country}}  {'Site':<{width_site}}  "
        f"{'Key':<{width_key}}  Status"
    )
    print(
        f"{'-' * width_country}  {'-' * width_site}  "
        f"{'-' * width_key}  ------"
    )
    for cc_, site, key, status in rows:
        print(f"{cc_:<{width_country}}  {site:<{width_site}}  {key:<{width_key}}  {status}")
    pending_count = sum(1 for r in rows if r[3] == "pending")
    filled_count = sum(1 for r in rows if r[3] == "filled")
    print()
    print(f"Totals: {pending_count} pending, {filled_count} filled.")
    return 0


# ---- subcommand: show ------------------------------------------------------


def _resolve_placeholder(
    *, country_code: str, site_id: str | None, site_name: str | None,
    key: str,
) -> tuple[Placeholder, dict[str, Any] | None, dict[str, Any] | None]:
    if key == "country_exec":
        cb = load_country_bundle(country_code)
        for ph in country_placeholders(country_code):
            if ph.key == key:
                return ph, None, cb
        raise SystemExit(f"country_exec placeholder not found in {country_code}")
    md_paths_searched: list[Path] = []
    for md_path, placeholders in site_placeholders_for_country(country_code).items():
        site_label = site_name_from_md_path(md_path)
        if site_name and site_name.casefold() not in site_label.casefold():
            continue
        for ph in placeholders:
            if site_id and ph.site_id != site_id:
                continue
            if ph.key == key:
                bundle_path = find_site_bundle_for_md(md_path)
                if bundle_path is None or not bundle_path.exists():
                    raise SystemExit(
                        f"Site bundle missing for {md_path.name}: expected "
                        f"{bundle_path}"
                    )
                site_bundle = json.loads(
                    bundle_path.read_text(encoding="utf-8"),
                )
                return ph, site_bundle, None
        md_paths_searched.append(md_path)
    raise SystemExit(
        f"Placeholder key={key} not found in {country_code} sites "
        f"matching site_id={site_id}, site_name={site_name}. Searched: "
        f"{[p.name for p in md_paths_searched]}"
    )


def cmd_show(args: argparse.Namespace) -> int:
    cc = args.country.upper()
    ph, site_bundle, country_bundle = _resolve_placeholder(
        country_code=cc, site_id=args.site_id, site_name=args.site_name,
        key=args.key,
    )
    prompt = load_specialist_prompt(args.key)
    slice_payload = slice_for_key(args.key, site_bundle, country_bundle)
    site_name_display = (
        site_name_from_md_path(ph.md_path)
        if ph.scope == "site" else cc
    )
    _print_show(
        scope=ph.scope,
        scope_id=ph.site_id or ph.country_code or cc,
        site_name=site_name_display,
        md_path=ph.md_path,
        key=args.key,
        prompt=prompt,
        slice_payload=slice_payload,
        current_body=ph.body,
        country_code=cc,
    )
    return 0


# ---- subcommand: patch -----------------------------------------------------


def _resolve_site_md(country_code: str, site_name: str | None,
                     site_id: str | None) -> Path:
    candidates = list(
        (PROFILES_DIR / "sites").glob(f"{country_code}_*.md"),
    )
    if site_name:
        q = site_name.casefold()
        for md in candidates:
            if q in site_name_from_md_path(md).casefold():
                return md
        raise SystemExit(
            f"No {country_code} site md matches name {site_name!r}"
        )
    if site_id:
        for md in candidates:
            for ph in discover_placeholders(md):
                if ph.site_id == site_id:
                    return md
        raise SystemExit(
            f"No {country_code} site md carries placeholders for "
            f"site_id={site_id}"
        )
    raise SystemExit("Provide --site-name or --site-id to identify the site.")


def cmd_patch(args: argparse.Namespace) -> int:
    text = _read_text_input(args)
    if not text.strip():
        raise SystemExit("--text / --text-file produced empty content")
    cc = args.country.upper()
    if args.key == "country_exec":
        md_path = country_md_path(cc)
        if not md_path.exists():
            raise SystemExit(f"Country md missing: {md_path}")
    else:
        md_path = _resolve_site_md(cc, args.site_name, args.site_id)
    placeholders = discover_placeholders(md_path)
    target = next((ph for ph in placeholders if ph.key == args.key), None)
    if target is None:
        raise SystemExit(
            f"Placeholder key={args.key} not found in {md_path.name}. "
            "Available keys: "
            + ", ".join(ph.key for ph in placeholders)
        )
    if target.status == "filled" and not args.force:
        raise SystemExit(
            f"Placeholder key={args.key} already status=filled. Use "
            "--force to overwrite."
        )
    new_attrs = {
        "key": target.key,
        **target.attrs,
        "status": "filled",
        "by": "cursor-agent",
        "filled_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ",
        ),
    }
    open_tag = "<!-- specialist " + " ".join(
        f"{k}={v}" for k, v in new_attrs.items()
    ) + " -->"
    close_tag = f"<!-- /specialist key={args.key} -->"
    new_block = f"{open_tag}\n{text.rstrip()}\n{close_tag}"
    full = md_path.read_text(encoding="utf-8")
    start, end = target.span
    md_path.write_text(
        full[:start] + new_block + full[end:], encoding="utf-8",
    )
    print(f"Patched {md_path.name} key={args.key} -> status=filled")
    return 0


def _read_text_input(args: argparse.Namespace) -> str:
    if args.text and args.text_file:
        raise SystemExit("Pass either --text or --text-file, not both.")
    if args.text:
        return args.text
    if args.text_file:
        if args.text_file == "-":
            return sys.stdin.read()
        return Path(args.text_file).read_text(encoding="utf-8")
    raise SystemExit("Provide --text or --text-file (use - for stdin).")


# ---- shared printing helpers ----------------------------------------------


def _print_show(
    *,
    scope: str,
    scope_id: str,
    site_name: str,
    md_path: Path,
    key: str,
    prompt: str,
    slice_payload: dict[str, Any],
    current_body: str | None,
    country_code: str,
) -> None:
    print("=" * 78)
    print("=== specialist task ===")
    print("=" * 78)
    print(f"scope:        {scope}")
    print(f"scope_id:     {scope_id}")
    if scope == "site":
        print(f"site_name:    {site_name}")
        print(f"country:      {country_code}")
    print(f"md_file:      {md_path.relative_to(REPO_ROOT)}")
    print(f"key:          {key}")
    print()
    print("=" * 78)
    print("=== system prompt (siting expert) ===")
    print("=" * 78)
    print(prompt.strip())
    print()
    print("=" * 78)
    print("=== bundle slice ===")
    print("=" * 78)
    print(json.dumps(slice_payload, indent=2, ensure_ascii=False, default=str))
    print()
    if current_body is not None:
        print("=" * 78)
        print("=== current placeholder body (will be replaced) ===")
        print("=" * 78)
        print(current_body)
        print()
    print("=" * 78)
    print("=== how to patch ===")
    print("=" * 78)
    if scope == "site":
        scope_arg = f'--site-name "{site_name}"'
    else:
        scope_arg = "  # country scope, no --site-* flag"
    print(textwrap.dedent("""\
    Once the paragraph is drafted, patch the placeholder:

      python -m scripts.run_specialist_pass patch \\
        --country {cc} {scope_arg} --key {key} \\
        --text-file <draft.md>

    Or feed via stdin:

      cat draft.md | python -m scripts.run_specialist_pass patch \\
        --country {cc} {scope_arg} --key {key} --text-file -
    """).format(cc=country_code, key=key, scope_arg=scope_arg))


# ---- argparse wiring ------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_specialist_pass",
        description=(
            "Helper for the in-Cursor specialist interpretation pass. "
            "No external API calls; the Cursor agent reads the single "
            "siting_expert.md prompt and the bundle slice with show "
            "and patches the result back with patch."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser(
        "list", help="Print pending placeholders for a country / site.",
    )
    p_list.add_argument("--country", required=True)
    p_list.add_argument("--site-name")
    p_list.add_argument("--site-id")
    p_list.add_argument(
        "--sites-only", action="store_true",
        help="Skip the country-scope placeholders.",
    )
    p_list.add_argument(
        "--include-filled", action="store_true",
        help="Also list placeholders that are already filled.",
    )
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser(
        "show", help="Print the prompt + bundle slice for one placeholder.",
    )
    p_show.add_argument("--country", required=True)
    p_show.add_argument("--site-name")
    p_show.add_argument("--site-id")
    p_show.add_argument(
        "--key", required=True,
        help=(
            "One of: family_natural_hazards, family_human_hazards, "
            "family_radiological_emergency, family_infrastructure, "
            "residual_risk, stability, country_exec."
        ),
    )
    p_show.set_defaults(func=cmd_show)

    p_patch = sub.add_parser(
        "patch",
        help="Replace a placeholder body with the agent-drafted text.",
    )
    p_patch.add_argument("--country", required=True)
    p_patch.add_argument("--site-name")
    p_patch.add_argument("--site-id")
    p_patch.add_argument("--key", required=True)
    p_patch.add_argument(
        "--text", help="Inline paragraph text (mutually exclusive with --text-file).",
    )
    p_patch.add_argument(
        "--text-file",
        help="Path to a markdown file holding the paragraph; - reads stdin.",
    )
    p_patch.add_argument(
        "--force", action="store_true",
        help="Allow overwriting placeholders that are already filled.",
    )
    p_patch.set_defaults(func=cmd_patch)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
