# man_hours: 1.5
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from atoms_vs_ashes.config import DatabaseSettings
from atoms_vs_ashes.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    """Resolve the database URL from env vars (POSTGRES_*), falling back
    to the ``sqlalchemy.url`` key in ``alembic.ini``."""
    try:
        return DatabaseSettings().url
    except Exception:
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
