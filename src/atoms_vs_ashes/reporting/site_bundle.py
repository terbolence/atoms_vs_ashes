# man_hours: 1.7
"""Build read-only site bundles for report narrative drafting."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    CompositeRanking,
    RankingScore,
    ScreeningVerdict,
    Site,
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteInfrastructureV2,
    SiteLlmObservation,
    SiteLlmVerdict,
    SiteNaturalHazards,
    SiteObservation,
    SiteOwnership,
    SiteRadiological,
    SiteUnit,
)
from atoms_vs_ashes.db.models_analytics import SiteBand
from atoms_vs_ashes.db.queries import (
    failure_explanation,
    site_criterion_scores,
    top_n_per_country,
)
from atoms_vs_ashes.reporting.run_profile_provenance import run_profile_provenance

FAMILY_MODELS = {
    "natural_hazards": SiteNaturalHazards,
    "human_hazards": SiteHumanHazards,
    "radiological": SiteRadiological,
    "emergency_planning": SiteEmergencyPlanning,
    "infrastructure": SiteInfrastructureV2,
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Geometry/WKB and other DB-specific values should not break JSON export.
    return str(value)


def _model_dict(obj: Any | None) -> dict[str, Any] | None:
    if obj is None:
        return None
    return {
        col.name: _jsonable(getattr(obj, col.name))
        for col in obj.__table__.columns
    }


def _rows(session: Session, model: Any, site_id: uuid.UUID) -> list[dict[str, Any]]:
    stmt = select(model).where(model.site_id == site_id)
    return [_model_dict(row) or {} for row in session.execute(stmt).scalars().all()]


def _run_rows(
    session: Session,
    model: Any,
    *,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    order_by: Any,
) -> list[dict[str, Any]]:
    stmt = (
        select(model)
        .where(
            model.site_id == site_id,
            model.smr_key == smr_key,
            model.run_id == run_id,
        )
        .order_by(order_by)
    )
    return [_model_dict(row) or {} for row in session.execute(stmt).scalars().all()]


def _observations(
    session: Session, *, site_id: uuid.UUID, smr_key: str, run_id: str
) -> dict[str, Any]:
    obs_stmt = (
        select(SiteObservation)
        .where(
            SiteObservation.site_id == site_id,
            (SiteObservation.smr_key.is_(None) | (SiteObservation.smr_key == smr_key)),
        )
        .order_by(SiteObservation.criterion_id, SiteObservation.created_at)
    )
    llm_obs_stmt = (
        select(SiteLlmObservation)
        .where(SiteLlmObservation.site_id == site_id)
        .order_by(SiteLlmObservation.criterion_id, SiteLlmObservation.created_at)
    )
    llm_verdict_stmt = (
        select(SiteLlmVerdict)
        .where(
            SiteLlmVerdict.site_id == site_id,
            (
                SiteLlmVerdict.llm_verdict_smr_key.is_(None)
                | (SiteLlmVerdict.llm_verdict_smr_key == smr_key)
            ),
        )
        .order_by(SiteLlmVerdict.criterion_id, SiteLlmVerdict.created_at)
    )
    return {
        "site_observations": [
            _model_dict(row) or {} for row in session.execute(obs_stmt).scalars().all()
        ],
        "llm_observations": [
            _model_dict(row) or {} for row in session.execute(llm_obs_stmt).scalars().all()
        ],
        "llm_verdicts": [
            _model_dict(row) or {}
            for row in session.execute(llm_verdict_stmt).scalars().all()
        ],
        "filter_note": (
            "Site observations include site-wide rows and rows for the requested SMR. "
            f"Run-specific scoring sections use run_id={run_id!r}."
        ),
    }


def _criterion_families(session: Session, site_id: uuid.UUID) -> dict[str, Any]:
    return {
        name: _model_dict(session.get(model, site_id))
        for name, model in FAMILY_MODELS.items()
    }


def _land_area_summary(site: Site) -> dict[str, Any]:
    infra = site.infrastructure
    return {
        "site_area_ha": _jsonable(site.site_area_ha),
        "site_area_source": _jsonable(site.site_area_source),
        "site_area_confidence": _jsonable(site.site_area_confidence),
        "favourable_area_ha": _jsonable(
            getattr(infra, "favourable_area_ha", None)
        ),
        "favourable_area_method": _jsonable(
            getattr(infra, "favourable_area_method", None)
        ),
        "reporting_note": (
            "Use site_area_ha as the NS-05/A15 surface-area indicator. "
            "Use favourable_area_ha, when populated, as the wider expansion "
            "envelope for laydown or future site expansion."
        ),
    }


def _scoring(
    session: Session, *, site_id: uuid.UUID, smr_key: str, run_id: str
) -> dict[str, Any]:
    composites = _run_rows(
        session,
        CompositeRanking,
        site_id=site_id,
        smr_key=smr_key,
        run_id=run_id,
        order_by=CompositeRanking.weight_profile,
    )
    ranking_scores = _run_rows(
        session,
        RankingScore,
        site_id=site_id,
        smr_key=smr_key,
        run_id=run_id,
        order_by=RankingScore.criterion_id,
    )
    return {
        "composite_rankings": composites,
        "ranking_scores": ranking_scores,
        "criterion_components": site_criterion_scores(
            session, run_id=run_id, site_id=site_id, smr_key=smr_key,
        ),
    }


def _screening(
    session: Session, *, site_id: uuid.UUID, smr_key: str, run_id: str
) -> dict[str, Any]:
    verdicts = _run_rows(
        session,
        ScreeningVerdict,
        site_id=site_id,
        smr_key=smr_key,
        run_id=run_id,
        order_by=ScreeningVerdict.criterion_id,
    )
    return {
        "verdicts": verdicts,
        "failure_explanation": failure_explanation(
            session, run_id=run_id, site_id=site_id, smr_key=smr_key,
        ),
    }


def _sensitivity(
    session: Session,
    *,
    site: Site,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    sensitivity_run_id: str,
    sensitivity_stamp: str,
) -> dict[str, Any]:
    bands_stmt = (
        select(SiteBand)
        .where(
            SiteBand.run_id == sensitivity_run_id,
            SiteBand.site_id == site_id,
            SiteBand.smr_key.in_([smr_key, "_all_"]),
        )
        .order_by(SiteBand.scope_country_code)
    )
    top_country = top_n_per_country(
        session, run_id=run_id, smr_key=smr_key, n=10,
        country_code=site.country_code,
    )
    rel_base = Path("report/output/sensitivity") / sensitivity_stamp
    return {
        "bands": [
            _model_dict(row) or {} for row in session.execute(bands_stmt).scalars().all()
        ],
        "country_top_10": top_country,
        "stamp": sensitivity_stamp,
        "files": {
            "regional_summary": (rel_base / "00_regional_summary.md").as_posix(),
            "national_dir": (rel_base / "national").as_posix(),
            "country_note": (
                rel_base / "national" / f"{site.country_code}_*.md"
            ).as_posix(),
        },
    }


def _asset_links(site: Site, sensitivity_stamp: str) -> dict[str, Any]:
    rel_base = Path("report/output/sensitivity") / sensitivity_stamp
    return {
        "sensitivity_summary": (rel_base / "00_regional_summary.md").as_posix(),
        "national_sensitivity_dir": (rel_base / "national").as_posix(),
        "country_top_sites_figure": (
            rel_base / "national" / "figures" / f"{site.country_code}_top_sites.png"
        ).as_posix(),
    }


def build_site_bundle(
    session: Session,
    *,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    sensitivity_run_id: str | None = None,
    sensitivity_stamp: str = "20260425b",
) -> dict[str, Any]:
    """Return one machine-readable bundle for report narrative drafting.

    ``run_id`` is the scoring (parent) run used for composite, screening,
    and ranking rows. ``sensitivity_run_id`` selects the sensitivity run
    that owns ``SiteBand`` rows; when ``None`` it defaults to ``run_id``.
    """
    site = session.get(Site, site_id)
    if site is None:
        raise ValueError(f"site_id not found: {site_id}")
    sens_run = sensitivity_run_id or run_id

    return {
        "metadata": {
            "bundle_schema": "site_bundle.v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "site_id": str(site_id),
            "smr_key": smr_key,
            "analytics_run_id": run_id,
            "sensitivity_run_id": sens_run,
            "sensitivity_stamp": sensitivity_stamp,
            "claim_boundary": "Screening-grade Stage 1-2 support only.",
        },
        "provenance": run_profile_provenance(session, run_id=run_id),
        "site": _model_dict(site),
        "land_area": _land_area_summary(site),
        "ownership": _rows(session, SiteOwnership, site_id),
        "units": _rows(session, SiteUnit, site_id),
        "criterion_families": _criterion_families(session, site_id),
        "observations": _observations(
            session, site_id=site_id, smr_key=smr_key, run_id=run_id,
        ),
        "screening": _screening(
            session, site_id=site_id, smr_key=smr_key, run_id=run_id,
        ),
        "scoring": _scoring(
            session, site_id=site_id, smr_key=smr_key, run_id=run_id,
        ),
        "sensitivity": _sensitivity(
            session, site=site, site_id=site_id, smr_key=smr_key,
            run_id=run_id, sensitivity_run_id=sens_run,
            sensitivity_stamp=sensitivity_stamp,
        ),
        "asset_links": _asset_links(site, sensitivity_stamp),
        "limitations_for_llm": [
            "Use ownership data conservatively; do not infer legal control.",
            "Treat rankings as frozen-run screening outputs, not licensing findings.",
            "Flag missing or low-quality criterion fields instead of filling gaps.",
            "Do not claim U.S. NRC, national regulator, or vendor approval.",
        ],
    }
