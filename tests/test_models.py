# man_hours: 2.0
"""Tests for SQLAlchemy model definitions (no DB required)."""

from atoms_vs_ashes.db.models import (
    AuditLog,
    Base,
    CompositeRanking,
    Country,
    Criterion,
    DataSource,
    RankingScore,
    ScreeningVerdict,
    Site,
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteObservation,
    SiteOwnership,
    SiteRadiological,
    SmrDesign,
    StagingUnmatchedOwnership,
)


def test_all_tables_registered():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "sites",
        "site_ownership",
        "_staging_unmatched_ownership",
        "site_natural_hazards",
        "site_human_hazards",
        "site_radiological",
        "site_emergency_planning",
        "site_infrastructure_v2",
        "smr_designs",
        "screening_verdicts",
        "ranking_scores",
        "composite_rankings",
        "site_observations",
        "criteria",
        "countries",
        "data_sources",
        "audit_log",
        "threshold_overrides",
    }
    assert expected.issubset(table_names), f"Missing: {expected - table_names}"


def test_site_columns_match_spec():
    cols = {c.name for c in Site.__table__.columns}
    required = {
        "site_id", "name", "country_code", "latitude", "longitude",
        "gem_location_id", "gem_unit_phase_id", "status", "plant_type",
        "installed_capacity_mw", "extended_data", "last_verified",
    }
    assert required.issubset(cols), f"Missing: {required - cols}"


def test_ownership_fk():
    fks = {fk.target_fullname for fk in SiteOwnership.__table__.foreign_keys}
    assert "sites.site_id" in fks


def test_domain_tables_have_site_fk():
    for cls in (
        SiteNaturalHazards,
        SiteHumanHazards,
        SiteRadiological,
        SiteEmergencyPlanning,
        SiteInfrastructureV2,
    ):
        fks = {fk.target_fullname for fk in cls.__table__.foreign_keys}
        assert "sites.site_id" in fks, f"{cls.__tablename__} missing sites FK"


def test_screening_verdict_has_smr_fk():
    fks = {fk.target_fullname for fk in ScreeningVerdict.__table__.foreign_keys}
    assert "smr_designs.smr_key" in fks
    assert "sites.site_id" in fks
