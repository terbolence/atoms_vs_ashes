# man_hours: 2.0
"""Tests for SQLAlchemy model definitions (no DB required)."""

from atoms_vs_ashes.db.models import (
    AuditLog,
    Base,
    Country,
    Criterion,
    DataQualityFlag,
    DataSource,
    RankingResult,
    ScreeningResult,
    Site,
    SiteAttribute,
    SiteInfrastructure,
    SiteOwnership,
    SiteScore,
    StagingUnmatchedOwnership,
)


def test_all_tables_registered():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "sites",
        "site_ownership",
        "_staging_unmatched_ownership",
        "site_attributes",
        "site_infrastructure",
        "site_scores",
        "criteria",
        "screening_results",
        "ranking_results",
        "countries",
        "data_sources",
        "data_quality_flags",
        "audit_log",
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
