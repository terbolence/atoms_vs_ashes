# man_hours: 2.0
"""Database engine and session management."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings

_engine = None
_SessionFactory: sessionmaker[Session] | None = None

# #region agent log
_AGENT_DEBUG_LOG = Path(__file__).resolve().parents[3] / ".cursor" / "debug-3fece0.log"


def _agent_debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    import json
    import time

    line = {
        "sessionId": "3fece0",
        "timestamp": int(time.time() * 1000),
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
    }
    try:
        _AGENT_DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_AGENT_DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except OSError:
        pass


# #endregion


def init_engine(settings: Settings | None = None) -> None:
    global _engine, _SessionFactory
    _repo_root = Path(__file__).resolve().parents[3]
    # #region agent log
    _agent_debug_log(
        "H-B",
        "db/engine.py:init_engine",
        "os.environ before Settings() (GUI may not call load_dotenv)",
        {
            "env_file_exists": (_repo_root / ".env").is_file(),
            "POSTGRES_HOST": os.environ.get("POSTGRES_HOST"),
            "POSTGRES_PORT": os.environ.get("POSTGRES_PORT"),
            "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
            "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
            "POSTGRES_PASSWORD_set": bool(os.environ.get("POSTGRES_PASSWORD")),
        },
    )
    # #endregion
    if settings is None:
        settings = Settings()
    # #region agent log
    _pwd = settings.database.password or ""
    _agent_debug_log(
        "H1-H4",
        "db/engine.py:init_engine",
        "resolved DatabaseSettings + client executable",
        {
            "host": settings.database.host,
            "port": settings.database.port,
            "db": settings.database.db,
            "user": settings.database.user,
            "password_length": len(_pwd),
            "sys_executable": sys.executable,
            "url_masked": (
                f"postgresql://{settings.database.user}:***@"
                f"{settings.database.host}:{settings.database.port}/{settings.database.db}"
            ),
        },
    )
    # #endregion
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
    except Exception as exc:
        # #region agent log
        if isinstance(exc, OperationalError):
            orig = getattr(exc, "orig", None)
            _agent_debug_log(
                "H-A",
                "db/engine.py:session_scope",
                "OperationalError during DB use",
                {
                    "exc_type": type(exc).__name__,
                    "orig_type": type(orig).__name__ if orig else None,
                    "orig_prefix": (str(orig)[:400] if orig else str(exc)[:400]),
                    "mentions_postgresapp": (
                        "Postgres.app" in str(orig or exc)
                        or "postgresapp" in str(orig or exc).lower()
                    ),
                },
            )
        # #endregion
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
