# man_hours: 2.0
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


# ---------------------------------------------------------------------------
# LLM database support
# ---------------------------------------------------------------------------

_llm_engine = None
_LlmSessionFactory: sessionmaker[Session] | None = None


def init_llm_engine(settings: Settings | None = None) -> None:
    """Initialise the engine for the LLM-populated database (atoms_vs_ashes_llm)."""
    global _llm_engine, _LlmSessionFactory
    if settings is None:
        settings = Settings()
    url = settings.database.url.replace(
        f"/{settings.database.db}",
        f"/{settings.database.db}_llm",
    )
    _llm_engine = create_engine(url, echo=False, pool_pre_ping=True)
    _LlmSessionFactory = sessionmaker(bind=_llm_engine)


def get_llm_engine():
    if _llm_engine is None:
        init_llm_engine()
    return _llm_engine


@contextmanager
def llm_session_scope() -> Generator[Session, None, None]:
    """Session scope for the LLM database."""
    if _LlmSessionFactory is None:
        init_llm_engine()
    session = _LlmSessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
