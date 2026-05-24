"""Regenerate the six Chapter 4 tables from the v1.03 ledgers + DB-derived
audit CSVs and reinject them under idempotent markers.

This script is the canonical generator for:

- Table 4.1.1 — Regional Stage 1-2 screening distribution.
- Table 4.2.1 — Per-country leading candidates (top 3 scored per country).
- Table 4.3.1 — First-wave Stage 3 characterisation candidates (full pass).
- Table 4.3.2 — Conditional unlock candidates (exclusionary-pass + avoidance flag).
- Table 4.4.1 — Main suitability and exclusion drivers.
- Table 4.6.1 — National sensitivity summary by country.

Data sources (master plan rule 3 — single data source per table):

- ``report/version 1.03/output/report/chapters/05_country_and_site_profiles/data/<CC>_site_ledger.csv``
  (17 in-scope countries) — primary aggregation surface.
- ``<CC>_country_bundle.json`` and ``<CC>_<slug>_site_bundle.json`` from
  the same directory — Pareto + per-site verdict feeds.
- ``report/version 1.03/output/report/bundles/feedback_rerun_20260509/<CC>_country_bundle.json``
  (AL, SI, XK only) — consolidated no-pass country row of Table 4.1.1.
- ``audit/post_processing/06_scoring/20260523_failure_per_criterion.csv``
  (or any other stamp via ``--failure-criterion-csv``) — Table 4.4.1
  exclusionary half.

Idempotent markers (``<!-- begin: table-X.Y.Z -->`` /
``<!-- end: table-X.Y.Z -->``) are inserted on first run; subsequent runs
only rewrite the content between markers. Hand-authored prose around
each table is preserved.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_DEFAULT_CHAPTER4 = Path(
    "report/version 1.03/output/report/chapters/04_results_and_findings.md"
)
_DEFAULT_DATA_DIR = Path(
    "report/version 1.03/output/report/chapters/05_country_and_site_profiles/data"
)
_DEFAULT_NOPASS_DIR = Path(
    "report/version 1.03/output/report/bundles/feedback_rerun_20260509"
)
_DEFAULT_FAILURE_CSV = Path(
    "audit/post_processing/06_scoring/20260523_failure_per_criterion.csv"
)

_IN_SCOPE_COUNTRIES = (
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)
_NOPASS_COUNTRIES = ("AL", "SI", "XK")

_COUNTRY_DISPLAY = {
    "AL": "Albania", "AT": "Austria", "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria", "BY": "Belarus", "CZ": "Czechia", "HR": "Croatia",
    "HU": "Hungary", "LV": "Latvia", "MD": "Moldova", "ME": "Montenegro",
    "MK": "North Macedonia", "PL": "Poland", "RO": "Romania",
    "RS": "Serbia", "SI": "Slovenia", "SK": "Slovakia", "TR": "Türkiye",
    "UA": "Ukraine", "XK": "Kosovo",
}

_CRITERION_DISPLAY = {
    "NS-02": ("Grid Connection (NS-02)", "Avoidance",
              "Principal unlock issue for many exclusionary-pass brownfield sites."),
    "HI-01": ("Aircraft Crash (HI-01)", "Avoidance",
              "Requires airport-class, flight-path and local aviation-context confirmation."),
    "RI-05": ("Distance to Population Centres (RI-05)", "Avoidance",
              "Requires settlement-distance and emergency-planning-zone review."),
    "NH-01": ("Seismic: Ground Motion (NH-01)", "Avoidance",
              "Requires national seismic evidence and site-specific hazard characterisation."),
    "NS-05": ("Site Footprint Adequacy (NS-05)", "Avoidance",
              "Requires parcel, contiguous-area and development-envelope confirmation."),
    "RI-04": ("Population Density EPZ (RI-04)", "Avoidance",
              "Requires EPZ-density and population modelling review."),
    "HI-06": ("Military Installations (HI-06)", "Avoidance",
              "Requires military-corridor and operational-context confirmation."),
    "HI-03": ("Toxic / gas releases (HI-03)", "Avoidance",
              "Requires hazardous-facility plume and chemical-release review."),
    "NS-01": ("Cooling water / heat sink (NS-01)", "Avoidance",
              "Requires water-availability and ultimate-heat-sink confirmation."),
    "NH-08": ("Coastal flooding / storm surge (NH-08)", "Avoidance",
              "Requires coastal-flood and storm-surge characterisation."),
    "NS-08": ("Ecological sensitivity (NS-08)", "Exclusionary",
              "Localised hard constraint requiring environmental and legal review."),
    "NH-02": ("Seismic: Surface Rupture (NH-02)", "Exclusionary",
              "Structural natural-hazard exclusion unless later evidence refutes the measurement."),
    "EP-01": ("Emergency Planning Feasibility (EP-01)", "Exclusionary",
              "Hard-fail driver where access, terrain or response-context proxies do not support the screen."),
    "NH-04": ("Geotechnical: Slope Stability (NH-04)", "Exclusionary",
              "Site-specific geotechnical issue that cannot be offset by implementation strengths."),
    "NH-03": ("Geotechnical: Settlement / Liquefaction (NH-03)", "Exclusionary",
              "Site-specific geotechnical issue cleared only by site-specific investigation."),
    "NH-07": ("Volcanic Hazards (NH-07)", "Exclusionary",
              "Localised hard constraint requiring volcanic-hazard expert review."),
}

_MARKER_RE = re.compile(
    r"<!--\s*begin:\s*table-(\d+\.\d+\.\d+)\s*-->(.*?)<!--\s*end:\s*table-\1\s*-->",
    re.DOTALL,
)


@dataclass
class LedgerRow:
    country_code: str
    national_rank: int | None
    name: str
    passed_exclusionary: bool
    passed_avoidance: bool
    composite_score: float | None
    composite_score_low: float | None
    composite_score_high: float | None
    national_band: str | None
    national_top10pct_hit_rate: float | None
    criteria_coverage: float | None

    @property
    def status(self) -> str:
        if not self.passed_exclusionary:
            return "hard-fail"
        if not self.passed_avoidance:
            return "avoidance flag"
        return "full pass"


def _load_ledger(path: Path) -> list[LedgerRow]:
    rows: list[LedgerRow] = []
    cc = path.name.split("_")[0]
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(LedgerRow(
                country_code=cc,
                national_rank=int(r["national_rank"]) if r["national_rank"] else None,
                name=r["name"],
                passed_exclusionary=(r["passed_exclusionary"] == "True"),
                passed_avoidance=(r["passed_avoidance"] == "True"),
                composite_score=_f(r["composite_score"]),
                composite_score_low=_f(r["composite_score_low"]),
                composite_score_high=_f(r["composite_score_high"]),
                national_band=(r.get("national_band") or None),
                national_top10pct_hit_rate=_f(r.get("national_top10pct_hit_rate")),
                criteria_coverage=_f(r.get("criteria_coverage")),
            ))
    return rows


def _f(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _fmt(value: float | None, places: int = 3) -> str:
    return f"{value:.{places}f}" if value is not None else "—"


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{round(100.0 * value)}%"


def _load_country_bundles(data_dir: Path, countries: list[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cc in countries:
        path = data_dir / f"{cc}_country_bundle.json"
        if path.exists():
            out[cc] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _load_nopass_bundles(nopass_dir: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cc in _NOPASS_COUNTRIES:
        path = nopass_dir / f"{cc}_country_bundle.json"
        if path.exists():
            out[cc] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _load_failure_csv(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cid = r["criterion_id"]
            out[cid] = int(r["union_pairs"])
    return out


def _avoidance_counts_by_criterion(
    bundles: dict[str, dict[str, Any]],
) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for bundle in bundles.values():
        for entry in bundle.get("avoidance_pareto") or []:
            cid = entry.get("criterion_id")
            n = entry.get("n_sites")
            if cid and isinstance(n, int):
                out[cid] += n
    return dict(out)


def _site_avoidance_drivers(
    data_dir: Path, country: str, site_name: str,
) -> list[str]:
    """Return the avoidance-tier criterion IDs that triggered for one site.

    Reads the per-site bundle JSON (matched by ``site_name``) and
    extracts caution-phase verdicts where ``phase == 'avoidance'``.
    Returns ``[]`` if no bundle is available — caller decides how to
    interpret an empty list.
    """
    matches = [
        p for p in data_dir.glob(f"{country}_*_site_bundle.json")
        if site_name.lower().replace(" ", "_") in p.stem.lower()
    ]
    if not matches:
        slug = _slug(site_name)
        candidate = data_dir / f"{country}_{slug}_site_bundle.json"
        if candidate.exists():
            matches = [candidate]
    if not matches:
        return []
    bundle = json.loads(matches[0].read_text(encoding="utf-8"))
    drivers: list[str] = []
    for v in (bundle.get("screening") or {}).get("verdicts") or []:
        if v.get("verdict") == "caution" and v.get("phase") == "avoidance":
            cid = v.get("criterion_id")
            if cid and cid not in drivers:
                drivers.append(cid)
    return drivers


def _slug(name: str) -> str:
    import re
    import unicodedata
    normal = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normal).strip("_").lower()
    return slug or "site"


def _bundle_site_id_lookup(data_dir: Path) -> set[str]:
    return {
        path.stem.replace("_site_bundle", "")
        for path in data_dir.glob("*_site_bundle.json")
    }


def _render_table_4_1_1(
    in_scope: list[LedgerRow],
    nopass: dict[str, dict[str, Any]],
) -> str:
    countries_in = len({r.country_code for r in in_scope})
    sites_in = len(in_scope)
    scored_in = sum(1 for r in in_scope if r.composite_score is not None)
    fp_in = sum(1 for r in in_scope if r.passed_exclusionary and r.passed_avoidance)
    avf_in = sum(1 for r in in_scope if r.passed_exclusionary and not r.passed_avoidance)
    hf_in = sum(1 for r in in_scope if not r.passed_exclusionary)

    countries_np = len(nopass)
    sites_np = sum((b.get("totals") or {}).get("n_sites", 0) for b in nopass.values())
    scored_np = sum((b.get("totals") or {}).get("n_with_score", 0) for b in nopass.values())
    fp_np = sum((b.get("totals") or {}).get("n_full_pass", 0) for b in nopass.values())
    avf_np = sum((b.get("totals") or {}).get("n_avoidance_flag", 0) for b in nopass.values())
    hf_np = sum((b.get("totals") or {}).get("n_hard_fail", 0) for b in nopass.values())

    lines = [
        "| Set | Countries | Site records | Scored / ranked records | Full pass | Avoidance flag | Hard fail |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Published country ledgers | {countries_in} | {sites_in} | {scored_in} | {fp_in} | {avf_in} | {hf_in} |",
        f"| Consolidated no-pass country section | {countries_np} | {sites_np} | {scored_np} | {fp_np} | {avf_np} | {hf_np} |",
        f"| Published Chapter 4 evidence base | {countries_in + countries_np} | {sites_in + sites_np} | {scored_in + scored_np} | {fp_in + fp_np} | {avf_in + avf_np} | {hf_in + hf_np} |",
    ]
    return "\n".join(lines)


def _render_table_4_2_1(
    in_scope: list[LedgerRow],
) -> str:
    by_country: dict[str, list[LedgerRow]] = defaultdict(list)
    for r in in_scope:
        by_country[r.country_code].append(r)

    lines = [
        "| Country | Full pass / avoidance flag / hard fail | Leading scored candidates |",
        "| :--- | :---: | :--- |",
    ]
    for cc in sorted(by_country, key=lambda c: _COUNTRY_DISPLAY.get(c, c)):
        rows = by_country[cc]
        fp = sum(1 for r in rows if r.passed_exclusionary and r.passed_avoidance)
        avf = sum(1 for r in rows if r.passed_exclusionary and not r.passed_avoidance)
        hf = sum(1 for r in rows if not r.passed_exclusionary)
        scored = [r for r in rows if r.composite_score is not None]
        scored.sort(key=lambda r: (-(r.composite_score or 0), r.name))
        top3 = scored[:3]
        if not top3:
            leaders = "—"
        else:
            leaders = "; ".join(
                f"{r.name} ({_fmt(r.composite_score)}, band {r.national_band or '—'}, "
                f"{r.status})"
                for r in top3
            )
        lines.append(
            f"| {_COUNTRY_DISPLAY.get(cc, cc)} | {fp} / {avf} / {hf} | {leaders} |"
        )
    return "\n".join(lines)


def _stage3_rationale(row: LedgerRow, all_rows: list[LedgerRow]) -> str:
    cc = row.country_code
    siblings_fp = [
        r for r in all_rows
        if r.country_code == cc and r.passed_exclusionary and r.passed_avoidance
    ]
    siblings_fp.sort(key=lambda r: -(r.composite_score or 0))
    leader = siblings_fp[0] if siblings_fp else None
    country = _COUNTRY_DISPLAY.get(cc, cc)
    is_leader = leader is not None and leader.name == row.name
    band = row.national_band or "?"
    top10 = row.national_top10pct_hit_rate or 0.0
    if band in ("A",) and top10 >= 0.95 and is_leader:
        return f"{country} full-pass leader; strongest national stability."
    if band in ("A", "B") and top10 >= 0.9 and is_leader:
        return f"{country} full-pass leader with strong national persistence."
    if band in ("A", "B") and top10 >= 0.9:
        return f"{country} full-pass fast follower with strong national persistence."
    if band in ("A", "B"):
        return f"{country} full-pass candidate with defensible stability."
    if band == "D" and top10 > 0:
        return f"{country} full-pass site with moderate stability; sequence after stronger national leaders."
    if band in ("D", "E", "F", "G", "H"):
        return f"{country} full-pass comparator whose rank stability needs caution."
    return f"{country} full-pass candidate; sequence per country profile."


def _render_table_4_3_1(in_scope: list[LedgerRow]) -> str:
    full_pass = [
        r for r in in_scope
        if r.passed_exclusionary and r.passed_avoidance and r.composite_score is not None
    ]
    full_pass.sort(key=lambda r: (-(r.composite_score or 0), r.name))
    lines = [
        "| Priority | Site | Country | Composite | MC interval | Band | Top-tier probability | Sequencing rationale |",
        "| ---: | :--- | :--- | ---: | :---: | :---: | ---: | :--- |",
    ]
    for i, r in enumerate(full_pass, start=1):
        mc = f"{_fmt(r.composite_score_low)}-{_fmt(r.composite_score_high)}"
        lines.append(
            f"| {i} | {r.name} | {_COUNTRY_DISPLAY.get(r.country_code, r.country_code)} | "
            f"{_fmt(r.composite_score)} | {mc} | {r.national_band or '—'} | "
            f"{_pct(r.national_top10pct_hit_rate)} | {_stage3_rationale(r, in_scope)} |"
        )
    return "\n".join(lines)


def _avoidance_flag_progression_text(drivers: list[str], country: str) -> str:
    if not drivers:
        return (
            f"Resolve the controlling avoidance finding before treating the site as "
            f"equivalent to full-pass {country} candidates."
        )
    pretty = ", ".join(drivers)
    if len(drivers) == 1:
        return (
            f"Resolve the {pretty} avoidance finding before treating the site as "
            f"equivalent to full-pass {country} candidates."
        )
    return (
        f"Resolve the {pretty} avoidance findings before treating the site as "
        f"equivalent to full-pass {country} candidates."
    )


def _render_table_4_3_2(
    in_scope: list[LedgerRow],
    data_dir: Path,
) -> str:
    bundle_stems = _bundle_site_id_lookup(data_dir)
    candidates: list[tuple[LedgerRow, list[str]]] = []
    for r in in_scope:
        if not (r.passed_exclusionary and not r.passed_avoidance and r.composite_score is not None):
            continue
        slug = f"{r.country_code}_{_slug(r.name)}"
        if slug not in bundle_stems:
            continue
        drivers = _site_avoidance_drivers(data_dir, r.country_code, r.name)
        candidates.append((r, drivers))
    candidates.sort(key=lambda pair: (-(pair[0].composite_score or 0), pair[0].name))

    lines = [
        "| Site | Country | Composite | Band | Top-tier probability | Avoidance drivers | Progression condition |",
        "| :--- | :--- | ---: | :---: | ---: | :--- | :--- |",
    ]
    for r, drivers in candidates:
        country = _COUNTRY_DISPLAY.get(r.country_code, r.country_code)
        driver_text = ", ".join(drivers) if drivers else "—"
        lines.append(
            f"| {r.name} | {country} | {_fmt(r.composite_score)} | "
            f"{r.national_band or '—'} | {_pct(r.national_top10pct_hit_rate)} | "
            f"{driver_text} | {_avoidance_flag_progression_text(drivers, country)} |"
        )
    return "\n".join(lines)


def _render_table_4_4_1(
    failure_counts: dict[str, int],
    avoidance_counts: dict[str, int],
) -> str:
    rows: list[tuple[str, str, int, str]] = []
    seen: set[str] = set()
    for cid, n in sorted(avoidance_counts.items(), key=lambda kv: -kv[1]):
        if n <= 0:
            continue
        name, dtype, interp = _CRITERION_DISPLAY.get(
            cid, (cid, "Avoidance", "—"),
        )
        rows.append((name, "Avoidance", n, interp))
        seen.add(cid)
    for cid, n in sorted(failure_counts.items(), key=lambda kv: -kv[1]):
        if n <= 0:
            continue
        name, dtype, interp = _CRITERION_DISPLAY.get(
            cid, (cid, "Exclusionary", "—"),
        )
        rows.append((name, "Exclusionary", n, interp))
        seen.add(cid)
    lines = [
        "| Driver | Driver type | Count | Interpretation |",
        "| :--- | :--- | ---: | :--- |",
    ]
    for name, dtype, n, interp in rows:
        lines.append(f"| {name} | {dtype} | {n} | {interp} |")
    return "\n".join(lines)


def _stability_reading(
    leader_row: LedgerRow, pool_scored: int, country_code: str,
) -> str:
    band = leader_row.national_band or "?"
    top10 = leader_row.national_top10pct_hit_rate or 0.0
    is_full_pass = leader_row.passed_exclusionary and leader_row.passed_avoidance
    sensitive = country_code in ("UA", "MD", "BY")
    if is_full_pass and band == "A" and top10 >= 0.95:
        if sensitive:
            return "Defensible leader with country-specific caveats."
        return "Stable national leader."
    if is_full_pass and band in ("A", "B") and top10 >= 0.9:
        return "Stable national leader with strong persistence."
    if is_full_pass:
        return "Full-pass leader; stability moderate."
    if band == "A" and pool_scored == 1:
        return "Stable but single-site and unlock-led."
    if band == "A" and pool_scored <= 3:
        return "Stable but small-pool and unlock-led."
    if band == "A":
        return "Stable, but unlock-led."
    return "Avoidance-led leader; treat with caution."


def _render_table_4_6_1(
    in_scope: list[LedgerRow],
) -> str:
    by_country: dict[str, list[LedgerRow]] = defaultdict(list)
    for r in in_scope:
        by_country[r.country_code].append(r)
    lines = [
        "| Country | Leading scored site | Status | Composite | MC interval | Band | Top-tier probability | Stability reading |",
        "| :--- | :--- | :--- | ---: | :---: | :---: | ---: | :--- |",
    ]
    for cc in sorted(by_country, key=lambda c: _COUNTRY_DISPLAY.get(c, c)):
        rows = by_country[cc]
        scored = [r for r in rows if r.composite_score is not None]
        if not scored:
            continue
        scored.sort(key=lambda r: -(r.composite_score or 0))
        leader = scored[0]
        mc = f"{_fmt(leader.composite_score_low)}-{_fmt(leader.composite_score_high)}"
        status = leader.status.capitalize()
        if leader.status == "full pass":
            status = "Full pass"
        elif leader.status == "avoidance flag":
            status = "Avoidance flag"
        lines.append(
            f"| {_COUNTRY_DISPLAY.get(cc, cc)} | {leader.name} | {status} | "
            f"{_fmt(leader.composite_score)} | {mc} | {leader.national_band or '—'} | "
            f"{_pct(leader.national_top10pct_hit_rate)} | "
            f"{_stability_reading(leader, len(scored), cc)} |"
        )
    return "\n".join(lines)


def _wrap_block(table_id: str, body: str) -> str:
    return (
        f"<!-- begin: table-{table_id} -->\n"
        f"{body}\n"
        f"<!-- end: table-{table_id} -->"
    )


def _replace_existing_block(text: str, table_id: str, body: str) -> str:
    """Replace ``<!-- begin/end: table-X.Y.Z -->`` block content, or
    insert markers around the existing markdown table on first run.

    On first run we locate the existing ``**Table X.Y.Z. ...**`` heading
    line, follow it past the blank line(s), and wrap the table body
    (consecutive ``| ... |`` lines) plus the heading line in markers.
    """
    block = _wrap_block(table_id, body)

    marker_pattern = re.compile(
        rf"<!--\s*begin:\s*table-{re.escape(table_id)}\s*-->.*?<!--\s*end:\s*table-{re.escape(table_id)}\s*-->",
        re.DOTALL,
    )
    if marker_pattern.search(text):
        return marker_pattern.sub(block, text)

    heading_re = re.compile(
        rf"(\*\*Table\s+{re.escape(table_id)}\.\s[^\n]*\*\*)\n+",
    )
    match = heading_re.search(text)
    if not match:
        raise SystemExit(
            f"Could not find heading or existing markers for table {table_id} "
            f"in chapter 4 file."
        )
    heading_end = match.end()
    table_block_re = re.compile(r"((?:^\|[^\n]*\n)+)", re.MULTILINE)
    table_match = table_block_re.match(text, heading_end)
    if not table_match:
        raise SystemExit(
            f"Heading for table {table_id} found but no markdown table follows."
        )
    inner = text[match.start():table_match.end()].rstrip("\n")

    pre_heading = text[:match.start()]
    rest = text[table_match.end():]
    heading_line = text[match.start():match.end()].rstrip("\n")
    new_block = (
        f"{heading_line}\n\n"
        f"{_wrap_block(table_id, body)}\n"
    )
    return pre_heading + new_block + rest


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("build_chapter_4_tables")
    p.add_argument("--chapter4", type=Path, default=_DEFAULT_CHAPTER4)
    p.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR)
    p.add_argument("--nopass-dir", type=Path, default=_DEFAULT_NOPASS_DIR)
    p.add_argument(
        "--failure-criterion-csv", type=Path, default=_DEFAULT_FAILURE_CSV,
    )
    p.add_argument(
        "--countries", nargs="+", default=list(_IN_SCOPE_COUNTRIES),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    in_scope: list[LedgerRow] = []
    for cc in args.countries:
        ledger_path = args.data_dir / f"{cc}_site_ledger.csv"
        if not ledger_path.exists():
            print(f"  ! missing ledger for {cc}: {ledger_path}", file=sys.stderr)
            continue
        in_scope.extend(_load_ledger(ledger_path))

    bundles = _load_country_bundles(args.data_dir, args.countries)
    nopass_bundles = _load_nopass_bundles(args.nopass_dir)
    failure_counts = _load_failure_csv(args.failure_criterion_csv)
    avoidance_counts = _avoidance_counts_by_criterion(bundles)

    if not args.chapter4.exists():
        raise SystemExit(f"Chapter 4 file not found: {args.chapter4}")
    text = args.chapter4.read_text(encoding="utf-8")

    blocks = {
        "4.1.1": _render_table_4_1_1(in_scope, nopass_bundles),
        "4.2.1": _render_table_4_2_1(in_scope),
        "4.3.1": _render_table_4_3_1(in_scope),
        "4.3.2": _render_table_4_3_2(in_scope, args.data_dir),
        "4.4.1": _render_table_4_4_1(failure_counts, avoidance_counts),
        "4.6.1": _render_table_4_6_1(in_scope),
    }

    new_text = text
    for table_id in ("4.1.1", "4.2.1", "4.3.1", "4.3.2", "4.4.1", "4.6.1"):
        new_text = _replace_existing_block(new_text, table_id, blocks[table_id])

    if new_text == text:
        print(f"Chapter 4 tables already up to date at {args.chapter4}")
    else:
        args.chapter4.write_text(new_text, encoding="utf-8")
        print(f"Wrote {args.chapter4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
