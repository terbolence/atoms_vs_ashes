"""Database engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings

_engine = None
_SessionFactory: sessionmaker[Session] | None = None


def init_engine(settings: Settings | None = None) -> None:
    global _engine, _SessionFactory
    if settings is None:
        settings = Settings()
    _engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    _SessionFactory = sessionmaker(bind=_engine)


def get_engine():
    if _engine is None:
        init_engine()
    return _engine


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if _SessionFactory is None:
        init_engine()
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection(settings: Settings | None = None) -> bool:
    """Return True if the database is reachable."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
