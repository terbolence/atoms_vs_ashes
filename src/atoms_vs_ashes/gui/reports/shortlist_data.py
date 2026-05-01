# man_hours: 1.5
"""Collect hand-pick shortlist data for compact Results-page PDF export."""

from __future__ import annotations

from sqlalchemy import select

from atoms_vs_ashes.db.analytics_writers import ALL_SMR_SENTINEL
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.gui.reports.models import (
    AvoidanceSitePdfSection,
    AvoidanceVerdictPdfRow,
    ShortlistExecutiveRow,
    ShortlistPackReport,
)
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.runtime.scope import RunScope
from scripts._shortlist_handpick_query import (
    load_avoidance_flagged_pairs,
    load_avoidance_verdicts_for_pairs,
    load_full_pass_pairs,
    load_shortlist_grouped,
)


def _scope_summary(scope: RunScope) -> str:
    cc = scope.country_codes
    sk = scope.smr_keys
    parts = []
    if cc is not None:
        parts.append(f"countries={len(cc)}")
    if sk is not None:
        parts.append(f"smrs={len(sk)}")
    return ", ".join(parts) if parts else "full DB scope"


def resolve_sensitivity_run_for_shortlist(
    baseline_run_id: str,
    hinted_sensitivity_run_id: str | None,
) -> str | None:
    """Return sensitivity ``run_id`` for ``country_site_rankings``, or None."""
    if hinted_sensitivity_run_id:
        return hinted_sensitivity_run_id
    with session_scope() as session:
        rid = session.execute(
            select(Run.run_id)
            .where(Run.run_kind == "sensitivity")
            .where(Run.status == "completed")
            .where(Run.parent_run_id == baseline_run_id)
            .order_by(Run.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return str(rid) if rid else None


def _infer_smr_key(session, sensitivity_run_id: str, scope: RunScope) -> str:
    if scope.smr_keys:
        return sorted(scope.smr_keys)[0]
    from atoms_vs_ashes.db.models_analytics import CountrySiteRanking

    concrete = session.execute(
        select(CountrySiteRanking.smr_key)
        .where(CountrySiteRanking.run_id == sensitivity_run_id)
        .where(CountrySiteRanking.smr_key != ALL_SMR_SENTINEL)
        .distinct()
        .limit(2)
    ).all()
    if not concrete:
        raise ValueError(
            f"No country_site_rankings for sensitivity run {sensitivity_run_id!r}.",
        )
    keys = [row[0] for row in concrete]
    if len(keys) > 1:
        raise ValueError(
            f"Multiple SMR keys in rankings {keys!r}; narrow SMR scope in run profile.",
        )
    return str(keys[0])


def _fmt_num(x: object | None) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(x)


def _trunc(s: str | None, max_len: int) -> str:
    if not s:
        return ""
    t = " ".join(s.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def build_shortlist_pack_report(
    *,
    baseline_run_id: str,
    sensitivity_run_id: str | None,
    weight_profile: str,
    profile: RunProfile,
    scope: RunScope,
    top_n: int,
    include_full_pass_annex: bool,
    max_avoidance_site_sections: int,
    justification_max_len: int = 96,
) -> ShortlistPackReport:
    """Load shortlist + optional annexes; cap avoidance detail for compact PDFs."""
    sens_id = resolve_sensitivity_run_for_shortlist(
        baseline_run_id, sensitivity_run_id,
    )
    if sens_id is None:
        raise ValueError(
            "No sensitivity run is linked to this baseline and none was found "
            "with matching parent_run_id — open a sensitivity run on Results or "
            "run sensitivity after scoring.",
        )
    with session_scope() as session:
        smr_key = _infer_smr_key(session, sens_id, scope)
        grouped = load_shortlist_grouped(
            session,
            sensitivity_run_id=sens_id,
            scoring_run_id=baseline_run_id,
            smr_key=smr_key,
            top_n=top_n,
            weight_profile=weight_profile,
        )
        full_pass: list[dict] = []
        if include_full_pass_annex:
            full_pass = load_full_pass_pairs(
                session,
                scoring_run_id=baseline_run_id,
                smr_key=smr_key,
                weight_profile=weight_profile,
            )
        avoidance_pairs = load_avoidance_flagged_pairs(
            session,
            scoring_run_id=baseline_run_id,
            smr_key=smr_key,
            weight_profile=weight_profile,
        )
        limited_pairs = avoidance_pairs[: max(0, int(max_avoidance_site_sections))]
        pair_keys = [(r["site_id"], str(r["smr_key"])) for r in limited_pairs]
        verdicts_by_pair = load_avoidance_verdicts_for_pairs(
            session, scoring_run_id=baseline_run_id, pairs=pair_keys,
        )

    index_rows = tuple(
        (
            str(p.get("country_code")),
            str(p.get("site_name") or "")[:44],
            _fmt_num(p.get("composite_score")),
        )
        for p in avoidance_pairs[:40]
    )
    exec_rows: list[ShortlistExecutiveRow] = []
    for cc in sorted(grouped):
        for r in grouped[cc]:
            exec_rows.append(
                ShortlistExecutiveRow(
                    country_code=cc,
                    national_rank=r.get("national_rank"),
                    band=r.get("band"),
                    site_name=str(r.get("site_name") or ""),
                    site_id=str(r.get("site_id")),
                    csr_composite=_fmt_num(r.get("composite_score")),
                    cr_composite=_fmt_num(r.get("composite_ranking_score")),
                    passed_exclusionary=_bool_label(r.get("passed_exclusionary")),
                    passed_avoidance=_bool_label(r.get("passed_avoidance")),
                    acceptability=_bool_label(r.get("acceptability_flag")),
                ),
            )

    avoid_sections: list[AvoidanceSitePdfSection] = []
    for r in limited_pairs:
        sid, sk = r["site_id"], str(r["smr_key"])
        vrows = verdicts_by_pair.get((sid, sk), [])
        pdf_verdicts = tuple(
            AvoidanceVerdictPdfRow(
                criterion_id=str(v.get("criterion_id") or ""),
                verdict=str(v.get("verdict") or ""),
                measured=str(v.get("measured_value") or "")[:48],
                threshold=str(v.get("threshold") or "")[:48],
                justification_short=_trunc(
                    str(v.get("justification") or ""), justification_max_len,
                ),
            )
            for v in vrows
        )
        avoid_sections.append(
            AvoidanceSitePdfSection(
                country_code=str(r.get("country_code") or ""),
                site_name=str(r.get("site_name") or ""),
                site_id=str(sid),
                smr_key=sk,
                composite=_fmt_num(r.get("composite_score")),
                verdict_rows=pdf_verdicts,
            ),
        )

    return ShortlistPackReport(
        scoring_run_id=baseline_run_id,
        sensitivity_run_id=sens_id,
        smr_key=smr_key,
        weight_profile=weight_profile,
        top_n=top_n,
        scope_summary=_scope_summary(scope),
        executive_rows=tuple(exec_rows),
        full_pass_included=include_full_pass_annex,
        full_pass_rows=tuple(
            (
                str(x.get("country_code")),
                str(x.get("site_name")),
                str(x.get("site_id")),
                _fmt_num(x.get("composite_score")),
            )
            for x in full_pass
        ),
        avoidance_sites_total=len(avoidance_pairs),
        avoidance_index_rows=index_rows,
        avoidance_sections=tuple(avoid_sections),
    )


def _bool_label(v: object | None) -> str:
    if v is True:
        return "Y"
    if v is False:
        return "N"
    return "—"


__all__ = [
    "build_shortlist_pack_report",
    "resolve_sensitivity_run_for_shortlist",
]
