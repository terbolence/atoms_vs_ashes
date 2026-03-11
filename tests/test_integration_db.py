"""Integration tests: verify DB state after ingestion (requires live DB)."""

import pytest
from sqlalchemy import func, select, text

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import (
    AuditLog,
    Country,
    Site,
    SiteOwnership,
    StagingUnmatchedOwnership,
)


@pytest.fixture(scope="module", autouse=True)
def _init_db():
    try:
        settings = Settings()
        init_engine(settings)
        with session_scope() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Database not available for integration tests")


def test_site_count():
    with session_scope() as session:
        count = session.scalar(select(func.count(Site.site_id)))
        assert count is not None and count >= 300


def test_no_missing_coordinates():
    with session_scope() as session:
        missing = session.scalar(
            select(func.count(Site.site_id)).where(
                (Site.latitude.is_(None)) | (Site.longitude.is_(None))
            )
        )
        assert missing == 0


def test_all_countries_have_sites():
    with session_scope() as session:
        countries = session.execute(select(Country.country_code)).scalars().all()
        for code in countries:
            count = session.scalar(
                select(func.count(Site.site_id)).where(Site.country_code == code)
            )
            assert count > 0, f"Country {code} has no sites"


def test_supplementary_sites_present():
    with session_scope() as session:
        braila = session.scalar(
            select(func.count(Site.site_id)).where(
                Site.name.ilike("%chi%cani%")
            )
        )
        feldioara = session.scalar(
            select(func.count(Site.site_id)).where(
                Site.name.ilike("%feldioara%")
            )
        )
        assert braila >= 1, "Brăila-Chișcani not found"
        assert feldioara >= 1, "FPCU Feldioara not found"


def test_ownership_linkage():
    with session_scope() as session:
        ownership_count = session.scalar(
            select(func.count(SiteOwnership.ownership_id))
        )
        assert ownership_count is not None and ownership_count >= 1000


def test_no_unmatched_ownership():
    with session_scope() as session:
        unmatched = session.scalar(
            select(func.count(StagingUnmatchedOwnership.row_id))
        )
        assert unmatched == 0


def test_audit_log_populated():
    with session_scope() as session:
        count = session.scalar(select(func.count(AuditLog.log_id)))
        assert count is not None and count >= 300


def test_postgis_functional():
    with session_scope() as session:
        result = session.scalar(text("SELECT PostGIS_version()"))
        assert result is not None and "USE_GEOS" in result
