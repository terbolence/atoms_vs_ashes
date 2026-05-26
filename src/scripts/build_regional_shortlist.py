# man_hours: 1.5
"""Emit regional top-5-per-country shortlist markdown with site maps.

Usage::

    PYTHONPATH=src python -m scripts.build_regional_shortlist \\
        --db-profile merged
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import CompositeRanking, RankingScore, Site
from atoms_vs_ashes.db.models_analytics import Run, SiteBand
from atoms_vs_ashes.db.runs import _git_sha  # type: ignore[attr-defined]
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_persist import _resolve_baseline_run_id
from scripts._country_profile_map import write_maps
from scripts._country_profile_query import load_bands, load_family_scores
from scripts._nuscale_top10_query import FAMILIES
from scripts._phase_1_6_report_writer import country_display_name
from scripts._shortlist_handpick_query import load_shortlist_grouped

log = get_logger(__name__)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

NUSCALE_LABEL = "NuScale VOYGR-6"
DEFAULT_OUT = Path("report/version 1.03/output/report")
FIG_SUBDIR = "figures/regional_shortlist"
# Published roster excludes Belarus; data is preserved in the DB but no
# build artefact is emitted for BY.
EXCLUDED_PUBLISHED_COUNTRIES = frozenset({"BY"})


def _resolve_national_sensitivity_run_id(session: Session, supplied: str | None) -> str:
    if supplied:
        return supplied
    rid = session.execute(
        select(Run.run_id)
        .where(Run.run_kind == "national_sensitivity")
        .where(Run.status == "completed")
        .order_by(Run.completed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if rid is None:
        raise SystemExit(
            "No completed national_sensitivity run — pass --sensitivity-run-id.",
        )
    return rid


def _resolve_scoring_run_id(
    session: Session,
    supplied: str | None,
    weight_profile: str,
    *,
    sensitivity_run_id: str | None = None,
) -> str:
    if supplied:
        return supplied
    if sensitivity_run_id:
        parent = session.execute(
            select(Run.parent_run_id).where(Run.run_id == sensitivity_run_id)
        ).scalar_one_or_none()
        if parent:
            return str(parent)
    rid = _resolve_baseline_run_id(session, weight_profile_base=weight_profile)
    if rid is None:
        raise SystemExit("No baseline scoring run — pass --scoring-run-id.")
    return rid


def _load_shortlist_from_composites(
    session: Session,
    *,
    scoring_run_id: str,
    sensitivity_run_id: str,
    smr_key: str,
    top_n: int,
    weight_profile: str = "baseline",
) -> dict[str, list[dict[str, Any]]]:
    """Top-N per country from baseline composites when ``country_site_rankings`` is empty."""
    rows = session.execute(
        select(
            Site.country_code,
            Site.site_id,
            Site.name.label("site_name"),
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.passed_exclusionary,
            CompositeRanking.passed_avoidance,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            CompositeRanking.run_id == scoring_run_id,
            CompositeRanking.weight_profile == weight_profile,
            CompositeRanking.smr_key == smr_key,
            CompositeRanking.composite_score.is_not(None),
        )
        .order_by(
            Site.country_code,
            CompositeRanking.composite_score.desc(),
            Site.name,
        )
    ).all()
    if not rows:
        return {}
    site_ids = [r.site_id for r in rows]
    bands: dict[tuple[Any, str], SiteBand] = {}
    for b in session.execute(
        select(SiteBand).where(
            SiteBand.run_id == sensitivity_run_id,
            SiteBand.smr_key.in_([smr_key, "_all_"]),
            SiteBand.site_id.in_(site_ids),
        )
    ).scalars().all():
        key = (b.site_id, str(b.scope_country_code))
        existing = bands.get(key)
        if existing is None or (
            str(existing.smr_key) == "_all_" and str(b.smr_key) != "_all_"
        ):
            bands[key] = b
    by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_country[str(r.country_code)].append(dict(r._mapping))
    regional_pool = sorted(
        [dict(r._mapping) for r in rows],
        key=lambda x: float(x["composite_score"]),
        reverse=True,
    )
    regional_rank_by_site = {
        r["site_id"]: idx for idx, r in enumerate(regional_pool, start=1)
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for cc in sorted(by_country):
        shortlist: list[dict[str, Any]] = []
        for nat_rank, r in enumerate(by_country[cc][:top_n], start=1):
            sid = r["site_id"]
            nat_band = bands.get((sid, cc))
            shortlist.append({
                "country_code": cc,
                "site_id": sid,
                "site_name": r["site_name"],
                "national_rank": nat_rank,
                "regional_rank": regional_rank_by_site.get(sid),
                "composite_score": r["composite_score"],
                "composite_score_low": r["composite_score_low"],
                "composite_score_high": r["composite_score_high"],
                "band": nat_band.band if nat_band else None,
                "acceptability_flag": bool(r["passed_exclusionary"]),
                "passed_exclusionary": r["passed_exclusionary"],
                "passed_avoidance": r["passed_avoidance"],
                "composite_ranking_score": r["composite_score"],
                "composite_ranking_low": r["composite_score_low"],
                "composite_ranking_high": r["composite_score_high"],
            })
        grouped[cc] = shortlist
    return grouped


def _fmt_float(v: Any, digits: int = 2) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{digits}f}"


def _fmt_pct(v: Any) -> str:
    if v is None:
        return "—"
    return f"{int(round(float(v) * 100))}%"


def _status_label(passed_exclusionary: bool | None, passed_avoidance: bool | None) -> str:
    if not passed_exclusionary:
        return "Hard-fail"
    if not passed_avoidance:
        return "Avoidance flag"
    return "Full pass"


def _map_row(r: dict[str, Any], site_meta: dict[uuid.UUID, Any]) -> dict[str, Any]:
    sid = uuid.UUID(str(r["site_id"]))
    meta = site_meta.get(sid)
    pe = r.get("passed_exclusionary")
    pa = r.get("passed_avoidance")
    status = (
        "pass" if pe and pa
        else "hard-fail" if not pe
        else "avoidance-flag"
    )
    composite = r.get("composite_ranking_score") or r.get("composite_score")
    return {
        "national_rank": r.get("national_rank"),
        "site_id": str(r["site_id"]),
        "name": r.get("site_name"),
        "status": status,
        "status_label": _status_label(pe, pa),
        "latitude": float(meta.latitude) if meta and meta.latitude is not None else None,
        "longitude": float(meta.longitude) if meta and meta.longitude is not None else None,
        "composite": composite,
        "composite_low": r.get("composite_score_low") or r.get("composite_ranking_low"),
        "composite_high": r.get("composite_score_high") or r.get("composite_ranking_high"),
        "national_band": r.get("band"),
        "national_top10_rate": None,
    }


def _enrich_rows(
    session: Session,
    *,
    grouped: dict[str, list[dict[str, Any]]],
    scoring_run_id: str,
    sensitivity_run_id: str,
    smr_key: str,
) -> tuple[
    dict[uuid.UUID, dict[str, float]],
    dict[tuple[uuid.UUID, str], dict[str, Any]],
    dict[uuid.UUID, list[tuple[str, float]]],
    dict[uuid.UUID, Any],
    dict[uuid.UUID, Any],
]:
    site_ids = [
        uuid.UUID(str(r["site_id"]))
        for rows in grouped.values()
        for r in rows
    ]
    family = load_family_scores(session, scoring_run_id, site_ids, smr_key)
    bands = load_bands(session, sensitivity_run_id, site_ids, smr_key)
    crit_rows = session.execute(
        select(
            RankingScore.site_id,
            RankingScore.criterion_id,
            RankingScore.score_0_10,
        ).where(
            RankingScore.run_id == scoring_run_id,
            RankingScore.smr_key == smr_key,
            RankingScore.site_id.in_(site_ids),
        ).order_by(RankingScore.site_id, RankingScore.criterion_id)
    ).all()
    crit_by_site: dict[uuid.UUID, list[tuple[str, float]]] = defaultdict(list)
    for sid, cid, score in crit_rows:
        if score is not None:
            crit_by_site[sid].append((str(cid), float(score)))

    site_meta = {
        row.site_id: row
        for row in session.execute(
            select(
                Site.site_id,
                Site.latitude,
                Site.longitude,
                Site.installed_capacity_mw,
            ).where(Site.site_id.in_(site_ids))
        ).all()
    }
    comp_extra = {
        row.site_id: row
        for row in session.execute(
            select(
                CompositeRanking.site_id,
                CompositeRanking.criteria_coverage,
                CompositeRanking.avg_confidence,
                CompositeRanking.rank_position,
            ).where(
                CompositeRanking.run_id == scoring_run_id,
                CompositeRanking.smr_key == smr_key,
                CompositeRanking.weight_profile == "baseline",
                CompositeRanking.site_id.in_(site_ids),
            )
        ).all()
    }
    return family, bands, crit_by_site, site_meta, comp_extra


def _render_markdown(
    *,
    scoring_run_id: str,
    sensitivity_run_id: str,
    smr_key: str,
    grouped: dict[str, list[dict[str, Any]]],
    family: dict[uuid.UUID, dict[str, float]],
    bands: dict[tuple[uuid.UUID, str], dict[str, Any]],
    crit_by_site: dict[uuid.UUID, list[tuple[str, float]]],
    site_meta: dict[uuid.UUID, Any],
    comp_extra: dict[uuid.UUID, Any],
    fig_rel_prefix: str,
    git_sha: str | None,
) -> str:
    lines = [
        "# Regional Atoms vs Ashes Shortlist",
        "",
        f"_Reference SMR: {NUSCALE_LABEL}. Analytical basis: the project's "
        "50,000-iteration national Monte Carlo sensitivity analysis over the "
        "current frozen scoring rubric._",
        "",
        "National ranks are ordered by baseline composite score within each "
        "country. Stability bands and top-tier hit rates come from the "
        "national sensitivity analysis. Composite scores, family means, "
        "criterion scores, and screening status come from the scoring stage.",
        "",
        "Each country section lists up to **five** sites by national rank "
        "(normal qualification: avoidance-flagged sites may appear). "
        "Per-country locator maps tag every shortlisted site with rank, "
        "status, and composite score.",
        "",
        "---",
        "",
    ]
    fam_header = " | ".join(FAMILIES)
    for cc in sorted(grouped):
        rows = grouped[cc]
        cname = country_display_name(cc)
        lines.append(f"## {cname} ({cc})")
        lines.append("")
        lines.append(
            f"![{cc} shortlist map]({fig_rel_prefix}/{cc}_shortlist_map.png)"
        )
        lines.append("")
        lines.append(
            "| # | Site | Status | Composite | MC low | MC high | Band | "
            f"Top-10% | {fam_header} | Coverage | Confidence | Cap (MW) | "
            "Reg. rank |"
        )
        lines.append(
            "| ---: | --- | --- | ---: | ---: | ---: | :---: | ---: | "
            + " | ".join("---:" for _ in FAMILIES)
            + " | ---: | :--- | ---: | ---: |"
        )
        for r in rows:
            sid = uuid.UUID(str(r["site_id"]))
            pe = r.get("passed_exclusionary")
            pa = r.get("passed_avoidance")
            comp = r.get("composite_ranking_score") or r.get("composite_score")
            lo = r.get("composite_score_low") or r.get("composite_ranking_low")
            hi = r.get("composite_score_high") or r.get("composite_ranking_high")
            fam = family.get(sid, {})
            nat_band = bands.get((sid, cc)) or {}
            band_label = r.get("band") or nat_band.get("band") or "—"
            top10 = nat_band.get("top10pct")
            extra = comp_extra.get(sid)
            meta = site_meta.get(sid)
            fam_cells = " | ".join(_fmt_float(fam.get(f), 1) for f in FAMILIES)
            cov = extra.criteria_coverage if extra else None
            lines.append(
                f"| {r.get('national_rank')} "
                f"| {r.get('site_name')} "
                f"| {_status_label(pe, pa)} "
                f"| {_fmt_float(comp)} "
                f"| {_fmt_float(lo)} "
                f"| {_fmt_float(hi)} "
                f"| {band_label} "
                f"| {_fmt_pct(top10)} "
                f"| {fam_cells} "
                f"| {_fmt_float(cov, 0) if cov is not None else '—'} "
                f"| {(extra.avg_confidence if extra else None) or '—'} "
                f"| {_fmt_float(meta.installed_capacity_mw, 0) if meta else '—'} "
                f"| {r.get('regional_rank') or '—'} |"
            )
        lines.append("")
        lines.append("### Criterion scores (0–10)")
        lines.append("")
        for r in rows:
            sid = uuid.UUID(str(r["site_id"]))
            scores = crit_by_site.get(sid, [])
            if not scores:
                continue
            lines.append(f"**{r.get('site_name')}** — national rank {r.get('national_rank')}")
            lines.append("")
            lines.append("| Criterion | Score |")
            lines.append("| :--- | ---: |")
            for cid, score in scores:
                lines.append(f"| {cid} | {_fmt_float(score, 1)} |")
            lines.append("")
        lines.append("---")
        lines.append("")
    lines.extend([
        "## Status legend",
        "",
        "- **Full pass** — clears exclusionary and avoidance screens.",
        "- **Avoidance flag** — clears exclusionary screen; at least one "
        "avoidance criterion is flagged.",
        "- **Hard-fail** — fails the exclusionary screen.",
        "",
        "## Family codes",
        "",
        "- **NH** — Natural hazards",
        "- **HI** — Human-induced hazards",
        "- **RI** — Radiological impact",
        "- **EP** — Emergency planning",
        "- **NS** — Non-safety / infrastructure",
        "",
    ])
    return "\n".join(lines)


def _write_country_maps(
    fig_dir: Path,
    grouped: dict[str, list[dict[str, Any]]],
    site_meta: dict[uuid.UUID, Any],
) -> None:
    for cc, rows in grouped.items():
        map_rows = [_map_row(r, site_meta) for r in rows]
        cname = country_display_name(cc)
        write_maps(
            fig_dir,
            map_rows,
            country_name=f"{cname} ({cc})",
            country_code=cc,
            smr_label=NUSCALE_LABEL,
        )
        src = fig_dir / f"{cc}_site_status_map.png"
        dst = fig_dir / f"{cc}_shortlist_map.png"
        if src.exists():
            src.replace(dst)
        html_src = fig_dir / f"{cc}_site_status_map.html"
        html_dst = fig_dir / f"{cc}_shortlist_map.html"
        if html_src.exists():
            html_src.replace(html_dst)


def _run(args: argparse.Namespace) -> Path:
    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    init_engine(Settings())
    out_root = Path(args.out_dir or DEFAULT_OUT)
    fig_dir = out_root / FIG_SUBDIR
    fig_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_root / "Regional Atoms vs Ashes Shortlist.md"

    with session_scope() as session:
        sens_id = _resolve_national_sensitivity_run_id(
            session, args.sensitivity_run_id,
        )
        score_id = _resolve_scoring_run_id(
            session,
            args.scoring_run_id,
            args.weight_profile,
            sensitivity_run_id=sens_id,
        )
        smr_key = args.smr_key
        grouped = load_shortlist_grouped(
            session,
            sensitivity_run_id=sens_id,
            scoring_run_id=score_id,
            smr_key=smr_key,
            top_n=args.top_n,
            weight_profile=args.weight_profile,
        )
        if not grouped:
            log.warning(
                "country_site_rankings_empty_using_composite_fallback",
                sensitivity_run_id=sens_id,
                scoring_run_id=score_id,
            )
            grouped = _load_shortlist_from_composites(
                session,
                scoring_run_id=score_id,
                sensitivity_run_id=sens_id,
                smr_key=smr_key,
                top_n=args.top_n,
                weight_profile=args.weight_profile,
            )
        grouped = {
            cc: rows
            for cc, rows in grouped.items()
            if cc not in EXCLUDED_PUBLISHED_COUNTRIES
        }
        family, bands, crit_by_site, site_meta, comp_extra = _enrich_rows(
            session,
            grouped=grouped,
            scoring_run_id=score_id,
            sensitivity_run_id=sens_id,
            smr_key=smr_key,
        )
        log.info(
            "regional_shortlist_resolved",
            scoring_run_id=score_id,
            sensitivity_run_id=sens_id,
            countries=len(grouped),
            sites=sum(len(v) for v in grouped.values()),
        )

    if not args.no_maps:
        _write_country_maps(fig_dir, grouped, site_meta)

    md = _render_markdown(
        scoring_run_id=score_id,
        sensitivity_run_id=sens_id,
        smr_key=smr_key,
        grouped=grouped,
        family=family,
        bands=bands,
        crit_by_site=crit_by_site,
        site_meta=site_meta,
        comp_extra=comp_extra,
        fig_rel_prefix=FIG_SUBDIR,
        git_sha=_git_sha(),
    )
    md_path.write_text(md, encoding="utf-8")
    log.info("regional_shortlist_written", path=str(md_path))
    return md_path


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Regional top-5 shortlist markdown + maps")
    p.add_argument("--db-profile", choices=sorted(DB_PROFILES), default="merged")
    p.add_argument("--scoring-run-id", default=None)
    p.add_argument("--sensitivity-run-id", default=None,
                   help="National sensitivity run (default: latest completed).")
    p.add_argument("--smr-key", default="nuscale_voygr6")
    p.add_argument("--top-n", type=int, default=5)
    p.add_argument("--weight-profile", default="baseline")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--no-maps", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    path = _run(args)
    print(str(path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
