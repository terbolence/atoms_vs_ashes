# man_hours: 3.0
"""Materialize siting-expert audit folders: SAMPLES.json + skeleton FINDINGS.md per connector.

Read-only SELECT against API-profile Postgres (`atoms_vs_ashes`). Writes
`SAMPLES.json` + machine-assisted `FINDINGS.md` (tables + executive summary).
A human should still complete §D–§H where domain judgement is required; the
`zhu_liquefaction` pilot folder contains a full hand-written §H example.

Stratified site picks use per-slug SQL; if 5–19 sites match, the list is
**padded** with random additional sites (no duplicates) to reach 20 rows.

Usage:
    python scripts/generate_siting_expert_audits.py
    python scripts/generate_siting_expert_audits.py --slug corine
    python scripts/generate_siting_expert_audits.py --date 20260417
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
AUDIT_ROOT = PROJECT_ROOT / "docs" / "siting_expert_audits"

# Same order as src/atoms_vs_ashes/connectors/__init__.py __all__ (OverpassClient -> osm).
CONNECTOR_SLUGS: tuple[str, ...] = (
    "copernicus_dem",
    "copernicus_ems",
    "copernicus_era5",
    "corine",
    "eea_industrial",
    "efsm20_faults",
    "egdi_geology",
    "entso_e",
    "eu_flood_risk",
    "eurostat_gisco",
    "eurostat_projections",
    "geonames_dump",
    "gfms",
    "ghsl_pop",
    "glofas_discharge",
    "hydrorivers",
    "natura2000",
    "noaa_ncei",
    "onegeology",
    "ourairports",
    "osm",
    "population",
    "seismic_hazard",
    "seveso",
    "smithsonian_gvp",
    "wdpa",
    "wokam_karst",
    "worldcover",
    "wri_aqueduct",
    "zhu_liquefaction",
)

# SQL WHERE fragments (nh/hh/rd/ep/inf aliases) to bias site pick toward connector writes.
# When nothing matches, caller falls back to random sites.
_SLUG_SITE_FILTER_SQL: dict[str, str] = {
    "copernicus_dem": "(nh.nh04_quality = 'copernicus_dem_30m' OR inf.ns04_quality = 'copernicus_dem_30m')",
    "copernicus_ems": "(nh.nh09_comment ILIKE '%CEMS%' OR nh.nh08_comment ILIKE '%CEMS%')",
    "copernicus_era5": (
        "(nh.nh10_comment ILIKE '%ERA5%' OR nh.nh11_comment ILIKE '%ERA5%' "
        "OR nh.nh12_comment ILIKE '%ERA5%' OR rd.ri01_comment ILIKE '%ERA5%' "
        "OR inf.ns01_comment ILIKE '%copernicus_era5%')"
    ),
    "corine": "(inf.dominant_land_class IS NOT NULL AND inf.ns04_quality IS NOT NULL)",
    "eea_industrial": "(hh.hi02_comment ILIKE '%eea_industrial%' OR hh.hi02_comment ILIKE '%eea.europa%')",
    "efsm20_faults": "(nh.nh02_source ILIKE '%efsm20%')",
    # No nh06_source column — EGDI provenance lives in nh06_comment / nh06_quality.
    "egdi_geology": "(nh.nh06_comment ILIKE '%EGDI%' OR nh.nh06_comment ILIKE '%egdi%')",
    # No ns02_source — ENTSO-E batch stamps ns02_comment (see entso_e/batch.py SOURCE_NAME).
    "entso_e": (
        "(inf.ns02_comment ILIKE '%entsoe%' OR inf.ns02_comment ILIKE '%ENTSO%' "
        "OR inf.ns02_comment ILIKE '%Transparency%')"
    ),
    "eu_flood_risk": "(nh.nh09_comment ILIKE '%GLOFAS%' OR nh.nh09_comment ILIKE '%APSFR%' OR nh.nh09_comment ILIKE '%eu_flood%')",
    "eurostat_gisco": "(rd.ri05_quality = 'gisco_urau_2021')",
    "eurostat_projections": "(rd.ri06_comment ILIKE '%eurostat%' OR rd.ri06_comment ILIKE '%Europop%')",
    "geonames_dump": "(rd.ri05_comment ILIKE '%GeoNames%')",
    "gfms": "(nh.nh09_comment ILIKE '%gfms%' OR nh.nh08_comment ILIKE '%gfms%')",
    "ghsl_pop": "(rd.ri04_quality::text ILIKE '%ghsl%' OR rd.ri04_comment ILIKE '%GHSL%')",
    "glofas_discharge": "(inf.ns01_source = 'glofas_discharge')",
    "hydrorivers": "(inf.ns01_source = 'hydrorivers')",
    "natura2000": "(inf.n2k_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%natura%')",
    "noaa_ncei": "(nh.nh10_comment ILIKE '%noaa%' OR nh.nh11_comment ILIKE '%noaa%' OR nh.nh12_comment ILIKE '%noaa%')",
    "onegeology": "(nh.nh06_comment ILIKE '%OneGeology%' OR nh.nh06_comment ILIKE '%onegeology%')",
    # No hi01_source — provenance in hi01_comment.
    "ourairports": "(hh.hi01_comment ILIKE '%OurAirports%' OR hh.hi01_comment ILIKE '%ourairports%')",
    "osm": "(inf.ns03_comment ILIKE '%Source: OSM Overpass API%')",
    "population": "(rd.ri04_comment ILIKE '%Overpass%' OR rd.ri04_comment ILIKE '%OSM%' OR rd.pop_density_5km IS NOT NULL)",
    "seismic_hazard": "(nh.nh01_source ILIKE '%efehr%' OR nh.nh01_source ILIKE '%ESHM%')",
    # No hi02_source — Seveso writes HI-02 (nearest_seveso_km, hi02_comment).
    "seveso": "(hh.hi02_comment ILIKE '%seveso%' OR hh.hi02_comment ILIKE '%SEVESO%' OR hh.nearest_seveso_km IS NOT NULL)",
    "smithsonian_gvp": "(nh.nh07_comment ILIKE '%gvp%' OR nh.nh07_comment ILIKE '%Smithsonian%')",
    "wdpa": "(inf.wdpa_nearest_distance_km IS NOT NULL OR inf.ns08_comment ILIKE '%wdpa%')",
    # No nh05_source — WOKAM provenance in nh05_comment / nh05_quality.
    "wokam_karst": "(nh.nh05_comment ILIKE '%wokam%' OR nh.nh05_comment ILIKE '%WOKAM%')",
    "worldcover": "(inf.ns04_comment ILIKE '%WorldCover%' OR inf.ns04_quality::text ILIKE '%worldcover%')",
    "wri_aqueduct": "(inf.ns01_comment ILIKE '%wri_aqueduct%' OR inf.water_stress_label IS NOT NULL)",
    # NH-03: no nh03_source column — connector sets nh03_quality='zhu_global_1km' (see zhu_liquefaction/batch.py).
    "zhu_liquefaction": (
        "(nh.nh03_quality = 'zhu_global_1km' OR nh.nh03_comment ILIKE '%zhu%' "
        "OR nh.liquefaction_suscept IS NOT NULL)"
    ),
}

# One-line screening hint per slug (for auto-generated FINDINGS.md §1).
_SLUG_SCREENING_HINT: dict[str, str] = {
    "copernicus_dem": "Terrain / elevation proxies (NH-04, NS-04) via Copernicus DEM.",
    "copernicus_ems": "CEMS-based hazard layers (NH-08/09/10 family).",
    "copernicus_era5": "Climate means and extremes (NH-10–12, NS-01, RI-01).",
    "corine": "Land cover / fragmentation (NS-04, NS-08).",
    "eea_industrial": "Industrial hazardous facilities proximity (HI-02).",
    "efsm20_faults": "Fault proximity and seismic line sources (NH-02).",
    "egdi_geology": "OneGeology / EGDI geology context (NH-06).",
    "entso_e": "Grid capacity and substation context (NS-02).",
    "eu_flood_risk": "EU flood / GLOFAS-related screening (NH-09).",
    "eurostat_gisco": "Large-city proximity and GISCO urban boundaries (RI-05).",
    "eurostat_projections": "Population projection context (RI-06).",
    "geonames_dump": "GeoNames city / population context (RI-05).",
    "gfms": "Global flood monitoring (NH-08/09).",
    "ghsl_pop": "GHSL population density (RI-04, EP-01).",
    "glofas_discharge": "River discharge context (NS-01).",
    "hydrorivers": "HydroRIVERS / river network (NS-01).",
    "natura2000": "Natura 2000 proximity (NS-08).",
    "noaa_ncei": "NOAA climate extremes (NH-10–12).",
    "onegeology": "OneGeology map context (NH-06).",
    "ourairports": "Airport proximity (HI-01).",
    "osm": "OSM transport / infrastructure (NS-03).",
    "population": "OSM ring population (RI-04).",
    "seismic_hazard": "Seismic hazard (NH-01).",
    "seveso": "Seveso establishment proximity (HI-02).",
    "smithsonian_gvp": "Volcanic feature proximity (NH-07).",
    "wdpa": "WDPA protected-area proximity (NS-08).",
    "wokam_karst": "Karst susceptibility (NH-05).",
    "worldcover": "ESA WorldCover land cover (NS-04).",
    "wri_aqueduct": "Water stress (NS-01).",
    "zhu_liquefaction": "Global liquefaction susceptibility (NH-03).",
}

_BASE_JOIN = """
FROM sites s
LEFT JOIN site_natural_hazards nh ON nh.site_id = s.site_id
LEFT JOIN site_human_hazards hh ON hh.site_id = s.site_id
LEFT JOIN site_radiological rd ON rd.site_id = s.site_id
LEFT JOIN site_emergency_planning ep ON ep.site_id = s.site_id
LEFT JOIN site_infrastructure_v2 inf ON inf.site_id = s.site_id
"""


def _make_engine() -> Engine:
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))
    load_dotenv(PROJECT_ROOT / ".env")
    from atoms_vs_ashes.config import Settings

    settings = Settings()
    return create_engine(settings.database.url, echo=False, pool_pre_ping=True)


def _pick_site_ids(engine: Engine, slug: str, limit: int = 20) -> tuple[list[str], str | None]:
    filt = _SLUG_SITE_FILTER_SQL.get(slug)
    if filt:
        q = f"""
            SELECT s.site_id::text AS site_id
            {_BASE_JOIN}
            WHERE {filt}
            GROUP BY s.site_id
            ORDER BY random()
            LIMIT :lim
        """
        with engine.connect() as conn:
            rows = conn.execute(text(q), {"lim": limit}).fetchall()
        ids = [r.site_id for r in rows]
        if len(ids) >= min(5, limit):
            if len(ids) < limit:
                need = limit - len(ids)
                pad_stmt = (
                    text(
                        f"""
                        SELECT s.site_id::text AS site_id
                        {_BASE_JOIN}
                        WHERE s.site_id NOT IN :ids
                        GROUP BY s.site_id
                        ORDER BY random()
                        LIMIT :need
                        """
                    )
                    .bindparams(bindparam("ids", expanding=True))
                )
                with engine.connect() as conn:
                    extra = conn.execute(pad_stmt, {"ids": ids, "need": need}).fetchall()
                ids.extend(r.site_id for r in extra)
            return ids, filt
    q2 = f"""
        SELECT s.site_id::text AS site_id
        {_BASE_JOIN}
        GROUP BY s.site_id
        ORDER BY random()
        LIMIT :lim
    """
    with engine.connect() as conn:
        rows = conn.execute(text(q2), {"lim": limit}).fetchall()
    return [r.site_id for r in rows], None


def _fetch_observations(engine: Engine, site_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not site_ids:
        return {}
    stmt = (
        text(
            """
            SELECT site_id::text AS site_id, criterion_id, observation, confidence
            FROM site_observations
            WHERE site_id IN :ids
            ORDER BY created_at DESC
            """
        )
        .bindparams(bindparam("ids", expanding=True))
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt, {"ids": site_ids}).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        obs = {
            "criterion_id": r.criterion_id,
            "observation": (r.observation or "")[:800],
            "confidence": r.confidence,
        }
        out.setdefault(r.site_id, []).append(obs)
    return out


def _fetch_errors(engine: Engine, slug: str, site_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not site_ids:
        return {}
    stmt = (
        text(
            """
            SELECT site_id::text AS site_id, error_type, message
            FROM connector_errors
            WHERE connector_slug = :slug AND site_id IN :ids
            """
        )
        .bindparams(bindparam("ids", expanding=True))
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt, {"slug": slug, "ids": site_ids}).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r.site_id, []).append(
            {"error_type": r.error_type, "message": (r.message or "")[:800]}
        )
    return out


def _row_dict(row: Any, keys: list[str]) -> dict[str, Any]:
    d: dict[str, Any] = {}
    mapping = row._mapping if hasattr(row, "_mapping") else row
    for k in keys:
        if k in mapping:
            v = mapping[k]
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat() if v else None
            else:
                d[k] = v
    return d


_DOMAIN_TABLES = frozenset(
    {
        "sites",
        "site_natural_hazards",
        "site_human_hazards",
        "site_radiological",
        "site_emergency_planning",
        "site_infrastructure_v2",
    }
)


def _select_star_by_site_ids(engine: Engine, table: str, site_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not site_ids or table not in _DOMAIN_TABLES:
        return {}
    stmt = (
        text(f"SELECT * FROM {table} WHERE site_id IN :ids")
        .bindparams(bindparam("ids", expanding=True))
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt, {"ids": site_ids}).mappings().all()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        sid = str(r["site_id"])
        row = dict(r)
        for k, v in list(row.items()):
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat() if v is not None else None
        out[sid] = row
    return out


def _batch_build_samples(engine: Engine, site_ids: list[str]) -> dict[str, dict[str, Any]]:
    """site_id -> sample dict (without observations/errors)."""
    sites = _select_star_by_site_ids(engine, "sites", site_ids)
    nh = _select_star_by_site_ids(engine, "site_natural_hazards", site_ids)
    hh = _select_star_by_site_ids(engine, "site_human_hazards", site_ids)
    rd = _select_star_by_site_ids(engine, "site_radiological", site_ids)
    ep = _select_star_by_site_ids(engine, "site_emergency_planning", site_ids)
    inf = _select_star_by_site_ids(engine, "site_infrastructure_v2", site_ids)
    out: dict[str, dict[str, Any]] = {}
    for sid in site_ids:
        srow = sites.get(sid)
        if not srow:
            continue
        out[sid] = {
            "site_id": sid,
            "site_name": srow.get("name"),
            "country_code": srow.get("country_code"),
            "latitude": float(srow["latitude"]) if srow.get("latitude") is not None else None,
            "longitude": float(srow["longitude"]) if srow.get("longitude") is not None else None,
            "domain": {
                "site_natural_hazards": nh.get(sid),
                "site_human_hazards": hh.get(sid),
                "site_radiological": rd.get(sid),
                "site_emergency_planning": ep.get(sid),
                "site_infrastructure_v2": inf.get(sid),
            },
        }
    return out


def _prune_domain(domain: dict[str, Any | None]) -> dict[str, Any]:
    """Drop null-only tables; trim huge JSON to keys containing quality/source/value hints."""
    out: dict[str, Any] = {}
    for tbl, row in domain.items():
        if not row:
            continue
        slim = {k: v for k, v in row.items() if v is not None}
        if not slim:
            continue
        # keep priority keys first
        priority = sorted(
            [k for k in slim if "quality" in k or "source" in k or "comment" in k],
            key=lambda x: x,
        )
        other = [k for k in slim if k not in priority and k not in ("run_id", "fetched_at")]
        keep = set(priority + ["run_id", "fetched_at"])
        # cap other numeric / value columns
        for k in other[:40]:
            keep.add(k)
        out[tbl] = {k: slim[k] for k in slim if k in keep}
    return out


def _flatten_domain_paths(domain: dict[str, Any]) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for table, row in domain.items():
        if not isinstance(row, dict):
            continue
        for k, v in row.items():
            out.append((f"{table}.{k}", v))
    return out


def _field_weight(path: str) -> float:
    key = path.split(".")[-1]
    if "quality" in key:
        return 10.0
    if any(s in key for s in ("_km", "distance")) and "comment" not in key:
        return 8.0
    if any(s in key for s in ("suscept", "label", "score", "pct", "overlap")):
        return 6.0
    if "comment" in key:
        return 3.0
    return 1.0


def _pick_display_columns(samples: list[dict[str, Any]], max_cols: int = 7) -> list[str]:
    freq: Counter[str] = Counter()
    for s in samples:
        dom = s.get("domain") or {}
        if not isinstance(dom, dict):
            continue
        for path, v in _flatten_domain_paths(dom):
            if v is None or v == "":
                continue
            freq[path] += 1
    if not freq:
        return []
    scored = {p: _field_weight(p) * freq[p] for p in freq}
    ordered = sorted(scored.keys(), key=lambda p: scored[p], reverse=True)
    return ordered[:max_cols]


def _get_domain_path(sample: dict[str, Any], path: str) -> Any:
    dom = sample.get("domain") or {}
    if "." not in path:
        return None
    table, key = path.split(".", 1)
    row = dom.get(table)
    if not isinstance(row, dict):
        return None
    return row.get(key)


def _md_cell(val: Any, max_len: int = 120) -> str:
    if val is None:
        return ""
    if isinstance(val, bool):
        return "yes" if val else "no"
    if isinstance(val, float):
        s = f"{val:.4g}".rstrip("0").rstrip(".")
        return s
    s = str(val).replace("\n", " ").replace("|", "/")
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def _connector_report_exists(slug: str) -> bool:
    p = PROJECT_ROOT / "docs" / "connector_reports" / f"{slug}_sample_report.md"
    return p.is_file()


def _render_findings_md(
    slug: str,
    yyyymmdd: str,
    disposition: str,
    samples_payload: dict[str, Any],
) -> str:
    samples = samples_payload.get("samples") or []
    extraction_note = samples_payload.get("extraction_note") or ""
    extraction_sql = samples_payload.get("extraction_sql")
    ts = samples_payload.get("extraction_timestamp_utc") or ""
    run_id = samples_payload.get("run_id")
    hint = _SLUG_SCREENING_HINT.get(
        slug,
        f"Connector `{slug}` — see `src/atoms_vs_ashes/connectors/{slug}/`.",
    )
    report_ok = _connector_report_exists(slug)
    folder = f"{slug}__{yyyymmdd}__{disposition}"

    cols = _pick_display_columns(samples, 7)
    countries = sorted({(s.get("country_code") or "") for s in samples})
    countries = [c for c in countries if c]
    n_err = sum(len(s.get("connector_errors") or []) for s in samples)
    n_obs = sum(len(s.get("site_observations") or []) for s in samples)

    lines: list[str] = []
    lines.append(f"# Siting expert audit — {slug}")
    lines.append("")
    lines.append("## 1. Review scope")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Connector slug** | `{slug}` |")
    lines.append(f"| **Screening hint** | {hint} |")
    lines.append(f"| **Disposition folder** | `{folder}` |")
    lines.append(
        f"| **Connector sample report** | "
        f"`docs/connector_reports/{slug}_sample_report.md` — **{'present' if report_ok else 'missing'}** |"
    )
    lines.append("")
    lines.append("## 2. Sample intake")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append("| **Database profile** | `api` → `atoms_vs_ashes` |")
    lines.append("| **Generator** | `scripts/generate_siting_expert_audits.py` |")
    lines.append(f"| **Stratification SQL** | `{extraction_sql or '(random fallback)'}` |")
    lines.append(f"| **Sample count** | **{len(samples)}** |")
    lines.append(f"| **Run ID (payload)** | `{run_id}` |")
    lines.append(f"| **Extraction timestamp (UTC)** | `{ts}` |")
    lines.append(f"| **Generator note** | {extraction_note} |")
    lines.append("")
    lines.append("## 3. Executive summary (machine-assisted)")
    lines.append("")
    if len(samples) == 0:
        lines.append(
            "**No samples** were returned — enrichment may be missing, the stratification filter may be too "
            "strict, or the database was empty/unreachable. **Disposition:** `ACTION_REQUIRED` until a "
            "successful 20-site pull is possible."
        )
    else:
        shortfall = ""
        if len(samples) < 20:
            shortfall = " **SHORTFALL** — fewer than 20 sites; see `extraction_note`."
        if n_err:
            err_msg = (
                f"**{n_err}** connector error record(s) in this pull — inspect `connector_errors` in "
                "`SAMPLES.json`."
            )
        else:
            err_msg = "No connector error rows in these samples (still review observation text)."
        lines.append(
            f"**Samples:** {len(samples)} site(s).{shortfall} **Countries:** "
            f"{', '.join(countries) or '—'}."
        )
        lines.append(
            f"{err_msg} **Site observation rows (capped in JSON):** {n_obs} total."
        )
        lines.append(
            "Treat this as **screening-grade** evidence until a human completes domain plausibility (§D–§H)."
        )
        if not report_ok:
            lines.append(
                f"**Documentation:** `docs/connector_reports/{slug}_sample_report.md` is **missing** — "
                "add per workspace connector-report rule before calling implementation complete."
            )
        lines.append("")
        lines.append(
            f"**Suggested disposition:** `{disposition}` — confirm after human review per `prompts/sitingExpert.md`."
        )
    lines.append("")
    lines.append("## 4. Per-sample table")
    lines.append("")
    if not samples or not cols:
        lines.append(
            "(No domain columns auto-selected — open `SAMPLES.json` for full pruned domain rows.)"
        )
    else:
        headers = ["#", "Site", "CC", "Lat", "Lon"] + [c.split(".")[-1] for c in cols]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for i, s in enumerate(samples, start=1):
            row_cells = [
                str(i),
                _md_cell(s.get("site_name"), 40),
                _md_cell(s.get("country_code"), 4),
                _md_cell(s.get("latitude")),
                _md_cell(s.get("longitude")),
            ]
            for c in cols:
                row_cells.append(_md_cell(_get_domain_path(s, c)))
            lines.append("| " + " | ".join(row_cells) + " |")
    lines.append("")
    lines.append("## 5. Aggregate diagnostics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Unique countries | {len(countries)} |")
    lines.append(f"| Connector error rows (sum over sites) | {n_err} |")
    lines.append(f"| Auto table columns | {', '.join(cols) or '—'} |")
    lines.append("")
    lines.append("## 6. Human follow-up (prompts/sitingExpert.md §D–§H)")
    lines.append("")
    lines.append(
        "- Validate domain plausibility for each criterion touched by this connector.\n"
        "- If the stratification SQL used random fallback, tighten filters once provenance columns are stable.\n"
        "- Close gaps: connector sample report, automated tests, and schema notes."
    )
    lines.append("")
    lines.append("## 7. Machine generation note")
    lines.append("")
    lines.append(
        "This file was produced or refreshed by `scripts/generate_siting_expert_audits.py`. "
        "Expert judgement and final acceptance remain human."
    )
    return "\n".join(lines) + "\n"


def _write_audit(
    slug: str,
    yyyymmdd: str,
    samples_payload: dict[str, Any],
    disposition: str,
) -> Path:
    folder = AUDIT_ROOT / f"{slug}__{yyyymmdd}__{disposition}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SAMPLES.json").write_text(
        json.dumps(samples_payload, indent=2, default=str), encoding="utf-8"
    )
    (folder / "FINDINGS.md").write_text(
        _render_findings_md(slug, yyyymmdd, disposition, samples_payload),
        encoding="utf-8",
    )
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate siting expert audit sample packs.")
    parser.add_argument("--slug", help="Single connector slug; default: all 30.")
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y%m%d"),
        help="YYYYMMDD folder token (default: UTC today).",
    )
    args = parser.parse_args()
    slugs = (args.slug,) if args.slug else CONNECTOR_SLUGS
    for s in slugs:
        if s not in CONNECTOR_SLUGS:
            print(f"Unknown slug {s!r}; known: {CONNECTOR_SLUGS}", file=sys.stderr)
            return 2

    engine: Engine | None = None
    connect_error: str | None = None
    try:
        engine = _make_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        connect_error = str(exc)
        print(f"Database unreachable: {exc}", file=sys.stderr)
        engine = None

    if engine is None:
        for slug in slugs:
            payload = {
                "connector_slug": slug,
                "database_profile": "api",
                "run_id": None,
                "extraction_sql": None,
                "extraction_note": f"DB unreachable during probe: {connect_error}",
                "extraction_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "reviewed_columns": [],
                "samples": [],
            }
            _write_audit(slug, args.date, payload, "ACTION_REQUIRED")
        return 1

    for slug in slugs:
        site_ids, used_filter = _pick_site_ids(engine, slug, 20)
        obs_map = _fetch_observations(engine, site_ids)
        err_map = _fetch_errors(engine, slug, site_ids)
        bundle_map = _batch_build_samples(engine, site_ids)
        samples: list[dict[str, Any]] = []
        run_ids: set[str] = set()
        for sid in site_ids:
            b = bundle_map.get(sid)
            if not b:
                continue
            b["site_observations"] = obs_map.get(sid, [])[:5]
            b["connector_errors"] = err_map.get(sid, [])[:5]
            dom = b.pop("domain", {})
            b["domain"] = _prune_domain(dom)
            for tbl in b["domain"].values():
                if isinstance(tbl, dict) and tbl.get("run_id"):
                    run_ids.add(str(tbl["run_id"]))
            samples.append(b)

        run_id = next(iter(run_ids)) if len(run_ids) == 1 else (list(run_ids)[0] if run_ids else None)
        extraction_note = (
            f"pick_site_ids filter={used_filter!r} matched {len(site_ids)} sites; "
            f"domain rows batched per table; pruned to quality/source/value columns."
        )
        disposition = "ACTION_OPTIONAL"
        if len(samples) == 0:
            disposition = "ACTION_REQUIRED"
            extraction_note += " ZERO samples — enrichment missing or filter too strict."
        elif len(samples) < 20:
            extraction_note += f" SHORTFALL: only {len(samples)} sites returned (see prompts/sitingExpert.md Incomplete)."

        payload = {
            "connector_slug": slug,
            "database_profile": "api",
            "run_id": run_id,
            "extraction_note": extraction_note,
            "extraction_sql": _SLUG_SITE_FILTER_SQL.get(slug),
            "extraction_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "reviewed_columns": ["see domain keys per sample; full list in DB schema"],
            "samples": samples,
        }
        path = _write_audit(slug, args.date, payload, disposition)
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())