# man_hours: 4.0
"""Export all Postgres columns for one country's sites to Markdown (read-only).

Uses ``information_schema.columns`` so the export tracks the live database (new
migrations add columns automatically). PostGIS geometries are emitted as WKT;
JSONB and arrays as text. One Markdown table per logical table.

Usage:
    python scripts/export_country_power_plants_md.py
    python scripts/export_country_power_plants_md.py --country RO --output reports/country_snapshots/RO/power_plants_data.md
"""

from __future__ import annotations

import argparse
import html
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PG_SCHEMA = "public"

SITE_COLUMN_HELP: dict[str, str] = {
    "site_id": "Primary key (UUID) for the site row in `sites`.",
    "name": "Plant or station name (typically aligned with GEM wiki).",
    "country_code": "ISO 3166-1 alpha-2 country code.",
    "country_name": "Full country name.",
    "latitude": "WGS-84 latitude (decimal degrees).",
    "longitude": "WGS-84 longitude (decimal degrees).",
    "subnational_unit": "First-level admin area (e.g. county / judet) from ingest.",
    "local_area": "Finer locality label when available.",
    "plant_type": "Fuel / technology class enum (`coal`, `lignite`, `gas`, `thermal`, `other`).",
    "status": "Lifecycle status enum (`operating`, `retired`, `mothballed`, …).",
    "installed_capacity_mw": "Nameplate / installed capacity aggregated at site level (MW).",
    "operating_capacity_mw": "Currently operating capacity at site level when tracked (MW).",
    "unit_count": "Number of generating units linked in `site_units`.",
    "start_year": "Earliest commercial operation year (site-level).",
    "retired_year": "Retirement year when the site is no longer operating.",
    "coal_phaseout_year": "National or asset-level coal phase-out reference year when set.",
    "grid_voltage_kv": "Nominal grid connection voltage (kV) when captured from GEM.",
    "grid_capacity_mw": "Grid connection capacity (MW) when captured from GEM.",
    "site_area_ha": "Site footprint in hectares when enriched (OSM / FIX-03 pipeline).",
    "elevation_m": "Ground elevation (m) from Copernicus DEM or similar enrichment.",
    "cooling_water_source": "Text description of cooling source from GEM.",
    "owner_operator": "Owner / operator string from GEM ownership ingest.",
    "parent_company": "Ultimate parent / corporate grouping from GEM.",
    "combustion_technology": "Boiler / turbine technology class (e.g. `subcritical`, `supercritical`).",
    "gem_location_id": "Global Energy Monitor location identifier.",
    "gem_unit_phase_id": "GEM unit-phase identifier when a single primary unit is linked.",
    "wiki_url": "GEM wiki URL for the location.",
    "extended_data": "JSONB payload from GEM / connectors (full dump as text in this export).",
    "geom": "Site point geometry (WKT, SRID 4326).",
}

UNITS_COLUMN_HELP: dict[str, str] = {
    "site_id": "Parent site UUID (`sites.site_id`).",
    "unit_id": "Primary key for the unit row.",
    "unit_name": "GEM unit label within the location.",
    "capacity_mw": "Unit nameplate capacity (MW).",
    "status": "Unit lifecycle status enum.",
    "start_year": "Unit commercial operation start year.",
    "retired_year": "Unit retirement year when applicable.",
    "combustion_technology": "Unit technology class.",
    "gem_unit_phase_id": "GEM unit-phase identifier for this row.",
    "extended_data": "JSONB per-unit extras from ingest.",
}

GENERIC_COLUMN_HELP = (
    "Column from live Postgres; see `src/atoms_vs_ashes/db/models.py` and "
    "`architecture/specs/02_data_model_postgres.md` for field semantics."
)


def md_cell(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    s = str(value).replace("\n", " ").replace("\r", "").replace("|", "¦")
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return html.escape(s)


def table(headers: list[str], rows: list[list[object]], max_cell_len: int = 12000) -> str:
    lines = [
        "| " + " | ".join(md_cell(h, max_cell_len) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_cell(c, max_cell_len) for c in row) + " |")
    return "\n".join(lines) + "\n"


def legend_block(headers: list[str], help_map: dict[str, str]) -> str:
    lines = [
        "### Column legend\n\n",
        "| Column | Meaning |\n",
        "| --- | --- |\n",
    ]
    for h in headers:
        desc = help_map.get(h) or GENERIC_COLUMN_HELP
        lines.append(f"| `{md_cell(h, 500)}` | {md_cell(desc, 2000)} |\n")
    return "".join(lines) + "\n"


def fetch_columns(conn, table_name: str) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        text(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :tname
            ORDER BY ordinal_position
            """
        ),
        {"schema": PG_SCHEMA, "tname": table_name},
    ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def col_expr(alias: str, col: str, data_type: str, udt_name: str) -> str:
    ref = f"{alias}.{col}"
    if udt_name in ("geometry", "geography"):
        return f"ST_AsText({ref}) AS {col}"
    if udt_name == "jsonb":
        return f"{ref}::text AS {col}"
    if data_type == "ARRAY":
        return f"{ref}::text AS {col}"
    if udt_name == "uuid":
        return f"{ref}::text AS {col}"
    if data_type == "USER-DEFINED" and udt_name not in ("geometry", "geography"):
        return f"{ref}::text AS {col}"
    return f"{ref} AS {col}"


def build_select(
    conn,
    *,
    table: str,
    alias: str,
    from_clause: str,
    where_clause: str,
    order_clause: str,
) -> str | None:
    cols = fetch_columns(conn, table)
    if not cols:
        return None
    parts = [col_expr(alias, c, dt, udt) for c, dt, udt in cols]
    sql = f"SELECT {', '.join(parts)} FROM {from_clause}"
    if where_clause.strip():
        sql += f" {where_clause}"
    if order_clause.strip():
        sql += f" {order_clause}"
    return sql


def emit_section(
    lines: list[str],
    title: str,
    blurb: str,
    headers: list[str],
    rows: list[Mapping[str, object]],
    help_map: dict[str, str],
) -> None:
    lines.append(f"\n---\n\n{title}\n\n{blurb}\n\n")
    if not rows:
        lines.append("*No rows.*\n")
        return
    lines.append(legend_block(headers, help_map))
    data = [[r[h] for h in headers] for r in rows]
    lines.append(table(headers, data))


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from atoms_vs_ashes.config import Settings

    parser = argparse.ArgumentParser(description="Export country site data to Markdown.")
    parser.add_argument("--country", default="RO", help="ISO 3166-1 alpha-2 country code")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .md path (default: reports/country_snapshots/<CC>/power_plants_data.md)",
    )
    args = parser.parse_args()
    cc = args.country.upper()
    out = args.output or (PROJECT_ROOT / "reports" / "country_snapshots" / cc / "power_plants_data.md")
    out.parent.mkdir(parents=True, exist_ok=True)

    settings = Settings()
    engine = create_engine(
        settings.database.url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 15},
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db_host = settings.database.host
    db_name = settings.database.db

    lines: list[str] = [
        f"# Power plant sites — {cc} (full Postgres snapshot)\n\n",
        f"**Generated (UTC):** {now}  \n",
        f"**Source database:** `{db_host}` / `{db_name}` (read-only export)  \n",
        "**Scope:** Every column currently present in `information_schema` for the listed tables, "
        "filtered to this country’s sites where applicable. PostGIS columns use `ST_AsText`. "
        "JSONB and arrays are cast to text (may be long). Reference tables `criteria`, "
        "`smr_designs`, `data_sources`, and the matching `countries` row are included. "
        "`audit_log` is restricted to `site_id` values that belong to sites in this country.\n\n",
    ]

    with engine.connect() as conn:
        def run_select(
            table: str,
            alias: str,
            from_clause: str,
            where_clause: str,
            order_clause: str,
            params: dict[str, object] | None = None,
        ) -> list[Mapping[str, object]]:
            sql = build_select(
                conn,
                table=table,
                alias=alias,
                from_clause=from_clause,
                where_clause=where_clause,
                order_clause=order_clause,
            )
            if not sql:
                return []
            return conn.execute(text(sql), params or {}).mappings().all()

        site_sql = build_select(
            conn,
            table="sites",
            alias="s",
            from_clause="sites s",
            where_clause="WHERE s.country_code = :cc",
            order_clause="ORDER BY s.name",
        )
        if not site_sql:
            lines.append("*Could not introspect `sites` (table missing?).*\n")
            out.write_text("".join(lines), encoding="utf-8")
            print(f"Wrote {out} (introspection failed)")
            return

        sites = conn.execute(text(site_sql), {"cc": cc}).mappings().all()
        site_ids_subq = "(SELECT site_id FROM sites WHERE country_code = :cc)"

        if not sites:
            lines.append(f"*No sites found for country code `{cc}`.*\n\n")
            lines.append("---\n\n*Produced by `scripts/export_country_power_plants_md.py`*\n")
            out.write_text("".join(lines), encoding="utf-8")
            print(f"Wrote {out} (empty)")
            return

        def count_where(table: str, where_sql: str) -> int:
            r = conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE {where_sql}"),
                {"cc": cc},
            ).scalar()
            return int(r or 0)

        site_count = len(sites)
        units_n = count_where("site_units", f"site_id IN {site_ids_subq}")
        own_n = count_where("site_ownership", f"site_id IN {site_ids_subq}")
        nh_n = count_where("site_natural_hazards", f"site_id IN {site_ids_subq}")
        hh_n = count_where("site_human_hazards", f"site_id IN {site_ids_subq}")
        rd_n = count_where("site_radiological", f"site_id IN {site_ids_subq}")
        inf_n = count_where("site_infrastructure_v2", f"site_id IN {site_ids_subq}")
        ep_n = count_where("site_emergency_planning", f"site_id IN {site_ids_subq}")
        sv_n = count_where("screening_verdicts", f"site_id IN {site_ids_subq}")
        rk_n = count_where("ranking_scores", f"site_id IN {site_ids_subq}")
        cr_n = count_where("composite_rankings", f"site_id IN {site_ids_subq}")
        ob_n = count_where("site_observations", f"site_id IN {site_ids_subq}")
        al_n = count_where("audit_log", f"site_id IN {site_ids_subq}")

        lines.append(
            f"**Row counts:** {site_count} sites; "
            f"{units_n} `site_units`; {own_n} `site_ownership`; "
            f"{nh_n} `site_natural_hazards`; {hh_n} `site_human_hazards`; "
            f"{rd_n} `site_radiological`; {inf_n} `site_infrastructure_v2`; {ep_n} `site_emergency_planning`; "
            f"{sv_n} `screening_verdicts`; {rk_n} `ranking_scores`; {cr_n} `composite_rankings`; "
            f"{ob_n} `site_observations`; {al_n} `audit_log`.\n"
        )

        country_rows = run_select(
            "countries",
            "c",
            "countries c",
            "WHERE c.country_code = :cc",
            "ORDER BY c.country_code",
            {"cc": cc},
        )
        emit_section(
            lines,
            "## `countries` (this country)",
            "Reference row for `sites.country_code`.",
            list(country_rows[0].keys()) if country_rows else [],
            country_rows,
            {},
        )

        site_headers = list(sites[0].keys())
        emit_section(
            lines,
            "## `sites`",
            "All columns for plants in this country (introspected).",
            site_headers,
            list(sites),
            SITE_COLUMN_HELP,
        )

        ownership = run_select(
            "site_ownership",
            "o",
            "site_ownership o JOIN sites s ON s.site_id = o.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, o.share_pct DESC NULLS LAST, o.parent_name NULLS LAST",
            {"cc": cc},
        )
        emit_section(
            lines,
            "## `site_ownership`",
            "GEM ownership stakes linked to these sites.",
            list(ownership[0].keys()) if ownership else [],
            ownership,
            {},
        )

        units = run_select(
            "site_units",
            "u",
            "site_units u JOIN sites s ON s.site_id = u.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, u.unit_name NULLS LAST",
            {"cc": cc},
        )
        emit_section(
            lines,
            "## `site_units`",
            "Per-unit GEM records for sites in this country.",
            list(units[0].keys()) if units else [],
            units,
            UNITS_COLUMN_HELP,
        )

        nh = run_select(
            "site_natural_hazards",
            "nh",
            "site_natural_hazards nh JOIN sites s ON s.site_id = nh.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name",
            {"cc": cc},
        )
        emit_section(lines, "## `site_natural_hazards`", "NH-01 … NH-14 (+ metadata).", list(nh[0].keys()) if nh else [], nh, {})

        hh = run_select(
            "site_human_hazards",
            "hh",
            "site_human_hazards hh JOIN sites s ON s.site_id = hh.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name",
            {"cc": cc},
        )
        emit_section(lines, "## `site_human_hazards`", "HI-01 … HI-08 (+ metadata).", list(hh[0].keys()) if hh else [], hh, {})

        rd = run_select(
            "site_radiological",
            "rd",
            "site_radiological rd JOIN sites s ON s.site_id = rd.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name",
            {"cc": cc},
        )
        emit_section(lines, "## `site_radiological`", "RI-01 … RI-06 (+ metadata).", list(rd[0].keys()) if rd else [], rd, {})

        inf = run_select(
            "site_infrastructure_v2",
            "inf",
            "site_infrastructure_v2 inf JOIN sites s ON s.site_id = inf.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name",
            {"cc": cc},
        )
        emit_section(lines, "## `site_infrastructure_v2`", "NS-01 … NS-13 (+ metadata).", list(inf[0].keys()) if inf else [], inf, {})

        ep = run_select(
            "site_emergency_planning",
            "ep",
            "site_emergency_planning ep JOIN sites s ON s.site_id = ep.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name",
            {"cc": cc},
        )
        emit_section(lines, "## `site_emergency_planning`", "EP-01 … EP-05 (+ metadata).", list(ep[0].keys()) if ep else [], ep, {})

        sv = run_select(
            "screening_verdicts",
            "v",
            "screening_verdicts v JOIN sites s ON s.site_id = v.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, v.smr_key, v.criterion_id, v.phase, v.prompt_key NULLS LAST",
            {"cc": cc},
        )
        emit_section(lines, "## `screening_verdicts`", "Per site × SMR × criterion (and phase / prompt when set).", list(sv[0].keys()) if sv else [], sv, {})

        rk = run_select(
            "ranking_scores",
            "r",
            "ranking_scores r JOIN sites s ON s.site_id = r.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, r.smr_key, r.criterion_id",
            {"cc": cc},
        )
        emit_section(lines, "## `ranking_scores`", "Per site × SMR × criterion ranking.", list(rk[0].keys()) if rk else [], rk, {})

        cr = run_select(
            "composite_rankings",
            "cr",
            "composite_rankings cr JOIN sites s ON s.site_id = cr.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, cr.smr_key",
            {"cc": cc},
        )
        emit_section(lines, "## `composite_rankings`", "Weighted composite per site × SMR.", list(cr[0].keys()) if cr else [], cr, {})

        obs = run_select(
            "site_observations",
            "o",
            "site_observations o JOIN sites s ON s.site_id = o.site_id",
            "WHERE s.country_code = :cc",
            "ORDER BY s.name, o.criterion_id, o.created_at",
            {"cc": cc},
        )
        emit_section(lines, "## `site_observations`", "Structured notes per site × criterion.", list(obs[0].keys()) if obs else [], obs, {})

        audit = run_select(
            "audit_log",
            "a",
            "audit_log a",
            f"WHERE a.site_id IN {site_ids_subq}",
            "ORDER BY a.timestamp DESC",
            {"cc": cc},
        )
        emit_section(
            lines,
            "## `audit_log` (rows for these sites only)",
            "Change history where `site_id` matches this export’s sites.",
            list(audit[0].keys()) if audit else [],
            audit,
            {},
        )

        crit = run_select("criteria", "cr", "criteria cr", "", "ORDER BY cr.criterion_id")
        emit_section(lines, "## `criteria` (full table)", "Criterion definitions (reference).", list(crit[0].keys()) if crit else [], crit, {})

        smr = run_select("smr_designs", "d", "smr_designs d", "", "ORDER BY d.smr_key")
        emit_section(lines, "## `smr_designs` (full table)", "SMR design parameters (reference).", list(smr[0].keys()) if smr else [], smr, {})

        ds = run_select("data_sources", "ds", "data_sources ds", "", "ORDER BY ds.name")
        emit_section(lines, "## `data_sources` (full table)", "Provenance registry (reference).", list(ds[0].keys()) if ds else [], ds, {})

    lines.append("\n---\n\n*Produced by `scripts/export_country_power_plants_md.py`.*\n")
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({site_count} sites, {units_n} units)")


if __name__ == "__main__":
    main()
