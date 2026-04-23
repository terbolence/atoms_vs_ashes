# man_hours: 4.0
"""Postgres-backed enrichment coverage: field fill rates, per-country summary, LLM verdicts.

Uses the same column mapping as LLM context (`RELEVANT_ENRICHMENT_FIELDS`). Read-only
SELECT queries only.

Usage:
    python scripts/report_enrichment_coverage.py
    python scripts/report_enrichment_coverage.py --db-profile llm --write-report
    python scripts/report_enrichment_coverage.py --db-profile api --compare-profile llm --write-report
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
REPORTS_DIR = PROJECT_ROOT / "reports"

_APP_DEPS: tuple[type, dict, object] | None = None


def _deps() -> tuple[type, dict, object]:
    """Load Settings + field map only after CLI parsing (``--help`` stays fast)."""
    global _APP_DEPS
    if _APP_DEPS is None:
        if str(SRC_ROOT) not in sys.path:
            sys.path.insert(0, str(SRC_ROOT))
        from atoms_vs_ashes.config import Settings
        from atoms_vs_ashes.llm.context import (
            RELEVANT_ENRICHMENT_FIELDS,
            validate_relevant_enrichment_fields,
        )

        _APP_DEPS = (Settings, RELEVANT_ENRICHMENT_FIELDS, validate_relevant_enrichment_fields)
    return _APP_DEPS

DOMAIN_SQL: dict[str, tuple[str, str]] = {
    "natural_hazards": ("site_natural_hazards", "nh"),
    "human_hazards": ("site_human_hazards", "hh"),
    "radiological": ("site_radiological", "rd"),
    "emergency_planning": ("site_emergency_planning", "ep"),
    "infrastructure": ("site_infrastructure_v2", "inf"),
}

_COL_OK = re.compile(r"^[a-z][a-z0-9_]*$", re.I)


def _validate_sql_identifier(name: str) -> str:
    if not _COL_OK.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def make_engine(database_url: str | None, profile: str | None) -> Engine:
    Settings, _, _validate = _deps()
    if database_url:
        return create_engine(database_url, echo=False, pool_pre_ping=True)
    if profile not in ("api", "llm"):
        raise ValueError("profile must be 'api' or 'llm' when database_url is omitted")
    prev = os.environ.get("POSTGRES_DB")
    try:
        if profile == "llm":
            os.environ["POSTGRES_DB"] = "atoms_vs_ashes_llm"
        elif profile == "api":
            os.environ["POSTGRES_DB"] = "atoms_vs_ashes"
        settings = Settings()
        return create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    finally:
        if prev is not None:
            os.environ["POSTGRES_DB"] = prev
        else:
            os.environ.pop("POSTGRES_DB", None)


def _count_pair(
    engine: Engine, table: str, alias: str, column: str, country: str | None = None
) -> tuple[int, int]:
    """Return (total_sites, sites_with_non_null_column) for optional country filter."""
    t = _validate_sql_identifier(table)
    a = _validate_sql_identifier(alias)
    c = _validate_sql_identifier(column)
    q = f"""
        SELECT COUNT(*)::bigint AS n_tot, COUNT({a}.{c})::bigint AS n_fill
        FROM sites s
        LEFT JOIN {t} {a} ON {a}.site_id = s.site_id
    """
    params: dict[str, str] = {}
    if country:
        q += " WHERE s.country_code = :cc"
        params["cc"] = country
    with engine.connect() as conn:
        row = conn.execute(text(q), params).one()
    return int(row.n_tot), int(row.n_fill)


def _count_by_country(engine: Engine, table: str, alias: str, column: str) -> list[tuple[str, int, int]]:
    t = _validate_sql_identifier(table)
    a = _validate_sql_identifier(alias)
    c = _validate_sql_identifier(column)
    q = f"""
        SELECT s.country_code AS cc,
               COUNT(*)::bigint AS n_tot,
               COUNT({a}.{c})::bigint AS n_fill
        FROM sites s
        LEFT JOIN {t} {a} ON {a}.site_id = s.site_id
        GROUP BY s.country_code
        ORDER BY s.country_code
    """
    with engine.connect() as conn:
        rows = conn.execute(text(q)).all()
    return [(str(r.cc), int(r.n_tot), int(r.n_fill)) for r in rows]


def collect_unique_columns() -> list[tuple[str, str]]:
    """(domain, column) unique pairs preserving stable order."""
    _, relevant, _ = _deps()
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for domains in relevant.values():
        for domain, cols in domains.items():
            for col in sorted(cols):
                key = (domain, col)
                if key not in seen:
                    seen.add(key)
                    out.append(key)
    return out


def fill_pct(filled: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * filled / total, 2)


def global_column_fills(
    engine: Engine,
) -> tuple[dict[tuple[str, str], float], list[tuple[str, str, str]]]:
    """Return ({(domain, col): fill_pct}, [(domain, col, error_summary), ...]).

    Second element is the list of (domain, column, error) pairs for columns the
    DB could not resolve — surfaced in the report so silent drops cannot hide
    schema/wiring drift.
    """
    fills: dict[tuple[str, str], float] = {}
    errors: list[tuple[str, str, str]] = []
    for domain, col in collect_unique_columns():
        table, alias = DOMAIN_SQL[domain]
        try:
            tot, fil = _count_pair(engine, table, alias, col)
        except ProgrammingError as e:
            summary = str(getattr(e, "orig", e)).splitlines()[0][:240]
            errors.append((domain, col, summary))
            continue
        fills[(domain, col)] = fill_pct(fil, tot)
    if errors:
        print("Warnings (DB column missing or errored):", file=sys.stderr)
        for domain, col, summary in errors[:20]:
            print(f"  {domain}.{col}: {summary}", file=sys.stderr)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more", file=sys.stderr)
    return fills, errors


def per_country_avg_fills(engine: Engine) -> list[tuple[str, int, float]]:
    """Per ISO country: site count and mean fill % across deduped mapped columns."""
    col_fills_by_country: dict[str, list[float]] = defaultdict(list)
    site_counts: dict[str, int] = {}

    for domain, col in collect_unique_columns():
        table, alias = DOMAIN_SQL[domain]
        try:
            rows = _count_by_country(engine, table, alias, col)
        except ProgrammingError:
            continue
        for cc, tot, fil in rows:
            site_counts[cc] = max(site_counts.get(cc, 0), tot)
            col_fills_by_country[cc].append(fill_pct(fil, tot))

    out: list[tuple[str, int, float]] = []
    for cc in sorted(col_fills_by_country.keys()):
        pcts = col_fills_by_country[cc]
        avg = round(sum(pcts) / len(pcts), 2) if pcts else 0.0
        out.append((cc, site_counts.get(cc, 0), avg))
    return out


def per_criterion_rows(
    global_fills: dict[tuple[str, str], float],
    missing_cols: set[tuple[str, str]] | None = None,
) -> list[tuple[str, float, int, int, str]]:
    """criterion_id, avg_fill_pct, n_resolved_cols, n_missing_cols, detail string.

    ``missing_cols`` is the set of (domain, column) pairs that failed at the DB
    layer; these are reported alongside the resolved columns so reviewers see
    when a criterion's "good" average hides half its fields.
    """
    _, relevant, _ = _deps()
    missing_cols = missing_cols or set()
    rows: list[tuple[str, float, int, int, str]] = []
    for crit, domains in sorted(relevant.items()):
        pcts: list[float] = []
        parts: list[str] = []
        missing_parts: list[str] = []
        for domain, cols in domains.items():
            for col in sorted(cols):
                p = global_fills.get((domain, col))
                if p is None:
                    if (domain, col) in missing_cols:
                        missing_parts.append(f"{col} [MISSING]")
                    continue
                pcts.append(p)
                parts.append(f"{col}:{p:.1f}%")
        avg = round(sum(pcts) / len(pcts), 2) if pcts else 0.0
        detail_parts = parts[:8]
        if missing_parts:
            detail_parts.append(f"MISSING: {', '.join(missing_parts[:6])}")
            if len(missing_parts) > 6:
                detail_parts[-1] += f", …(+{len(missing_parts) - 6})"
        detail = "; ".join(detail_parts)
        if len(parts) > 8:
            detail += f"; …(+{len(parts) - 8} cols)"
        rows.append((crit, avg, len(parts), len(missing_parts), detail))
    return rows


def row_counts(engine: Engine) -> dict[str, int]:
    tables = ["sites", "screening_verdicts", "site_observations"]
    out: dict[str, int] = {}
    with engine.connect() as conn:
        for t in tables:
            try:
                r = conn.execute(text(f"SELECT COUNT(*)::bigint AS c FROM {t}")).scalar_one()
                out[t] = int(r)
            except ProgrammingError:
                out[t] = -1
    return out


def verdict_confidence_distribution(engine: Engine) -> list[tuple[str, str, int]]:
    q = text(
        """
        SELECT criterion_id, confidence, COUNT(*)::bigint AS n
        FROM screening_verdicts
        GROUP BY criterion_id, confidence
        ORDER BY criterion_id, confidence
        """
    )
    with engine.connect() as conn:
        try:
            rows = conn.execute(q).all()
        except ProgrammingError:
            return []
    return [(str(r.criterion_id), str(r.confidence), int(r.n)) for r in rows]


def section_profile_header(label: str, url: str) -> list[str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        f"## {label}\n\n",
        f"**Generated (UTC):** {now}  \n",
        f"**Database URL:** `{url}`\n\n",
    ]


def build_markdown(
    primary_label: str,
    primary_url: str,
    primary_fills: dict[tuple[str, str], float],
    primary_counts: dict[str, int],
    primary_verdicts: list[tuple[str, str, int]],
    primary_countries: list[tuple[str, int, float]],
    phantom_cols: list[tuple[str, str, str]] | None = None,
    missing_db_cols: list[tuple[str, str, str]] | None = None,
    compare: tuple[str, str, dict[str, int], list[tuple[str, str, int]]] | None = None,
) -> str:
    phantom_cols = phantom_cols or []
    missing_db_cols = missing_db_cols or []
    lines: list[str] = [
        "<!-- Generated by scripts/report_enrichment_coverage.py -->\n",
        "# Enrichment coverage report\n\n",
    ]
    lines += section_profile_header(primary_label, primary_url)

    if phantom_cols or missing_db_cols:
        lines.append("### Wiring / schema drift\n\n")
        lines.append(
            "Columns listed in `RELEVANT_ENRICHMENT_FIELDS` that do not resolve. "
            "These are **not counted** in the fill-rate averages below and indicate "
            "either a wiring bug in `src/atoms_vs_ashes/llm/context.py` or an "
            "un-migrated DB schema.\n\n"
        )
        if phantom_cols:
            lines.append("#### Phantom columns (not present in ORM)\n\n")
            lines.append("| Criterion | Domain | Column | Details |\n| --- | --- | --- | --- |\n")
            for crit, domain_col, reason in phantom_cols:
                domain, col = domain_col.split(".", 1) if "." in domain_col else ("?", domain_col)
                lines.append(f"| {crit} | {domain} | `{col}` | {reason} |\n")
            lines.append("\n")
        if missing_db_cols:
            lines.append("#### Missing at the DB (SQL `column does not exist` etc.)\n\n")
            lines.append("| Domain | Column | Error |\n| --- | --- | --- |\n")
            for domain, col, err in missing_db_cols:
                lines.append(f"| {domain} | `{col}` | {err} |\n")
            lines.append("\n")
    lines.append("### Row counts\n\n")
    lines.append("| Table | Rows |\n| --- | ---: |\n")
    for t, c in sorted(primary_counts.items()):
        lines.append(f"| `{t}` | {c if c >= 0 else 'n/a'} |\n")
    lines.append("\n### Per-criterion mapped field fill (global)\n\n")
    lines.append(
        "Average of `% non-null` over columns listed for each criterion in "
        "`RELEVANT_ENRICHMENT_FIELDS` (see `src/atoms_vs_ashes/llm/context.py`).\n"
        "`Missing` counts columns that failed to resolve (phantom or un-migrated); "
        "they are excluded from the average.\n\n"
    )
    lines.append("| Criterion | Avg fill % | Resolved | Missing | Sample columns |\n")
    lines.append("| --- | ---: | ---: | ---: | --- |\n")
    missing_set: set[tuple[str, str]] = {(d, c) for d, c, _ in missing_db_cols}
    for crit, avg, n_res, n_miss, det in per_criterion_rows(primary_fills, missing_set):
        lines.append(f"| {crit} | {avg} | {n_res} | {n_miss} | {det} |\n")
    lines.append("\n### Per country (mean fill % across all mapped columns)\n\n")
    lines.append("| Country | Sites | Mean fill % |\n| --- | ---: | ---: |\n")
    for cc, n, avg in primary_countries:
        lines.append(f"| {cc} | {n} | {avg} |\n")

    if primary_verdicts:
        lines.append("\n### Screening verdict confidence (LLM DB)\n\n")
        lines.append("| Criterion | Confidence | Count |\n| --- | --- | ---: |\n")
        for cid, conf, n in primary_verdicts:
            lines.append(f"| {cid} | {conf} | {n} |\n")
    else:
        lines.append(
            "\n*No `screening_verdicts` rows or table missing — typical for API-only DB.*\n"
        )

    if compare:
        clabel, curl, ccnts, cver = compare
        lines.append(f"\n---\n\n## Compare: {clabel}\n\n**Database URL:** `{curl}`\n\n")
        lines.append("### Row counts\n\n| Table | Rows |\n| --- | ---: |\n")
        for t, c in sorted(ccnts.items()):
            lines.append(f"| `{t}` | {c if c >= 0 else 'n/a'} |\n")
        if cver:
            lines.append("\n### Screening verdict confidence\n\n")
            lines.append("| Criterion | Confidence | Count |\n| --- | --- | ---: |\n")
            for cid, conf, n in cver:
                lines.append(f"| {cid} | {conf} | {n} |\n")

    lines.append("\n---\n\n### Cumulative narrative\n\n")
    lines.append(
        "- **API profile (`atoms_vs_ashes`):** structured connector fills in domain tables; "
        "use per-criterion averages above to see where REST/GIS enrichment landed.\n"
        "- **LLM profile (`atoms_vs_ashes_llm`):** same schema plus `screening_verdicts` "
        "(verdict, confidence, justification) per site/SMR/criterion when assessments ran.\n"
        "- **Combined interpretability:** high field fill supports deterministic screening; "
        "verdicts document reasoning where data are thin or ambiguous.\n"
    )
    return "".join(lines)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Enrichment coverage from Postgres (read-only).")
    parser.add_argument(
        "--db-profile",
        choices=("api", "llm"),
        default="api",
        help="Which POSTGRES_DB default to use if URL not set (api=atoms_vs_ashes, llm=_llm).",
    )
    parser.add_argument(
        "--database-url",
        help="Full postgresql:// URL (overrides Settings / profile db name).",
    )
    parser.add_argument(
        "--compare-profile",
        choices=("api", "llm"),
        default=None,
        help="Optional second database (same host/user/password, other POSTGRES_DB).",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help=f"Write {REPORTS_DIR / 'coverage_latest.md'} and dated copy (skip stdout unless --print-report).",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print full markdown to stdout (default when --write-report is not set).",
    )
    parser.add_argument(
        "--allow-phantom-columns",
        action="store_true",
        help=(
            "Do not exit non-zero when RELEVANT_ENRICHMENT_FIELDS references "
            "columns absent from ORM or DB. They will still be reported."
        ),
    )
    args = parser.parse_args()

    if args.database_url and args.compare_profile:
        parser.error("--compare-profile cannot be used together with --database-url (no second URL).")

    Settings, _, validate = _deps()

    phantom_entries = validate()
    if phantom_entries:
        print(
            f"ORM validation: {len(phantom_entries)} phantom column(s) in "
            "RELEVANT_ENRICHMENT_FIELDS — see report + src/atoms_vs_ashes/llm/context.py.",
            file=sys.stderr,
        )
        for crit, field, reason in phantom_entries[:20]:
            print(f"  {crit}: {field} — {reason}", file=sys.stderr)
        if len(phantom_entries) > 20:
            print(f"  ... and {len(phantom_entries) - 20} more", file=sys.stderr)
    engine = make_engine(args.database_url, None if args.database_url else args.db_profile)
    prev_db = os.environ.get("POSTGRES_DB")
    try:
        if not args.database_url:
            os.environ["POSTGRES_DB"] = (
                "atoms_vs_ashes_llm" if args.db_profile == "llm" else "atoms_vs_ashes"
            )
        primary_url = args.database_url or Settings().database.url
    finally:
        if prev_db is not None:
            os.environ["POSTGRES_DB"] = prev_db
        else:
            os.environ.pop("POSTGRES_DB", None)

    primary_label = f"Primary profile: {args.db_profile}"

    print("Computing global column fills (may take a minute)…", file=sys.stderr)
    try:
        fills, missing_db = global_column_fills(engine)
        countries = per_country_avg_fills(engine)
        counts = row_counts(engine)
        verdicts = verdict_confidence_distribution(engine)
    except OperationalError as exc:
        print(f"Postgres not reachable ({exc}). Check `.env` / `POSTGRES_*`.", file=sys.stderr)
        sys.exit(1)

    compare_block: tuple[str, str, dict[str, int], list[tuple[str, str, int]]] | None = None
    if args.compare_profile and args.compare_profile != args.db_profile:
        eng2 = make_engine(None, args.compare_profile)
        prev2 = os.environ.get("POSTGRES_DB")
        try:
            os.environ["POSTGRES_DB"] = (
                "atoms_vs_ashes_llm" if args.compare_profile == "llm" else "atoms_vs_ashes"
            )
            url2 = Settings().database.url
        finally:
            if prev2 is not None:
                os.environ["POSTGRES_DB"] = prev2
            else:
                os.environ.pop("POSTGRES_DB", None)
        try:
            counts2 = row_counts(eng2)
            verdicts2 = verdict_confidence_distribution(eng2)
        except OperationalError as exc:
            print(f"Compare database not reachable ({exc}).", file=sys.stderr)
            sys.exit(1)
        compare_block = (f"profile: {args.compare_profile}", url2, counts2, verdicts2)

    phantom_for_md: list[tuple[str, str, str]] = []
    for prompt_key, domain, field in phantom_entries:
        if field.startswith("<unknown domain"):
            phantom_for_md.append((prompt_key, f"{domain}.?", field))
        else:
            phantom_for_md.append(
                (prompt_key, f"{domain}.{field}", "not a column on the target ORM model")
            )

    md = build_markdown(
        primary_label,
        primary_url,
        fills,
        counts,
        verdicts,
        countries,
        phantom_for_md,
        missing_db,
        compare_block,
    )
    if args.write_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        latest = REPORTS_DIR / "coverage_latest.md"
        dated = REPORTS_DIR / f"coverage_{date.today().isoformat().replace('-', '')}.md"
        latest.write_text(md, encoding="utf-8")
        dated.write_text(md, encoding="utf-8")
        print(f"Wrote {latest} and {dated}", file=sys.stderr)
    if not args.write_report or args.print_report:
        sys.stdout.write(md)

    if (phantom_entries or missing_db) and not args.allow_phantom_columns:
        print(
            f"FAIL: {len(phantom_entries)} phantom ORM column(s), "
            f"{len(missing_db)} missing DB column(s). "
            "Re-run with --allow-phantom-columns to bypass.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
