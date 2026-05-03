# man_hours: 0.8
"""Build reusable country and site profile artefacts.

This is the canonical CLI for generating one country profile and one
selected site profile in ``report/output/chapters/05_country_and_site_profiles``.

Data flow:

1. ``build_country_bundle`` produces the country-level data dump
   (totals, sites, avoidance Pareto, family means, ranking score
   distribution).
2. ``build_site_bundle`` produces the site-level dump for the chosen
   site (raw measured values per criterion, ownership, units,
   verdicts, ranking scores, sensitivity bands).
3. The renderers in ``_country_profile_markdown`` and
   ``_site_profile_markdown`` turn those bundles into report-ready
   markdown.
4. ``write_artifacts`` writes the JSON dumps, the figures, and the
   markdown to disk.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import re
import sys
import unicodedata
import uuid

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_detail import site_detail
from atoms_vs_ashes.reporting import build_country_bundle, build_site_bundle
from scripts._country_profile_outputs import write_artifacts
from scripts._country_profile_query import resolve_runs


def _slug(raw: str) -> str:
    normal = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normal).strip("_").lower()
    return slug or "site"


def _select_site(sites, *, site_id: str | None, site_name: str | None):
    if not sites:
        raise SystemExit("No sites returned for this country/SMR/run selection")
    if site_id:
        wanted = str(uuid.UUID(site_id))
        matches = [row for row in sites if row["site_id"] == wanted]
        if not matches:
            raise SystemExit(f"No site found with site_id={site_id}")
        return matches[0]
    if site_name:
        q = site_name.casefold()
        exact = [row for row in sites if row["name"].casefold() == q]
        partial = [row for row in sites if q in row["name"].casefold()]
        if exact or partial:
            return (exact or partial)[0]
        raise SystemExit(f"No site name match for {site_name!r}")
    full_pass = [
        row for row in sites
        if row["passed_exclusionary"] and row["passed_avoidance"]
    ]
    return full_pass[0] if full_pass else sites[0]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("build_country_profile_prototype")
    parser.add_argument("--country-code", default="RO")
    parser.add_argument("--site-id")
    parser.add_argument("--site-name")
    parser.add_argument("--smr-key", default="nuscale_voygr6")
    parser.add_argument("--output-dir", type=Path, default=Path(
        "report/output/chapters/05_country_and_site_profiles",
    ))
    parser.add_argument("--scoring-run-id")
    parser.add_argument("--sensitivity-run-id")
    parser.add_argument(
        "--sensitivity-stamp", default="20260425b",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cc = args.country_code.upper()
    init_engine(Settings())
    with session_scope() as session:
        scoring, sensitivity = resolve_runs(
            session, args.scoring_run_id, args.sensitivity_run_id,
        )
        country_bundle = build_country_bundle(
            session, country_code=cc, smr_key=args.smr_key,
            run_id=scoring, sensitivity_run_id=sensitivity,
            sensitivity_stamp=args.sensitivity_stamp,
        )
        selected = _select_site(
            country_bundle["sites"],
            site_id=args.site_id, site_name=args.site_name,
        )
        site_bundle = build_site_bundle(
            session,
            site_id=uuid.UUID(selected["site_id"]),
            smr_key=args.smr_key, run_id=scoring,
            sensitivity_run_id=sensitivity,
            sensitivity_stamp=args.sensitivity_stamp,
        )
        detail = site_detail(
            scoring, uuid.UUID(selected["site_id"]), args.smr_key,
            weight_profile="baseline",
        )
    return _write(
        args, cc, country_bundle, site_bundle, detail, selected,
    )


def _write(args, country_code, country_bundle, site_bundle, detail, selected):
    cname = country_name(country_code)
    smr_label = country_bundle["metadata"].get("smr_label", args.smr_key)
    detail_payload = asdict(detail) if detail else {}
    write_artifacts(
        out=args.output_dir,
        country_bundle=country_bundle,
        site_bundle=site_bundle,
        detail=detail_payload,
        selected_row=selected,
        country_name=cname,
        country_code=country_code,
        smr_label=smr_label,
        site_slug=_slug(selected["name"]),
    )
    print(
        f"Wrote country profile for {cname} / {selected['name']} "
        f"(scoring={country_bundle['metadata']['analytics_run_id']}, "
        f"sensitivity={country_bundle['metadata'].get('sensitivity_run_id')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
