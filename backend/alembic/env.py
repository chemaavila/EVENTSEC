from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base
from app import models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

MIGRATION_LOCK_KEY = 915701234


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        connection.exec_driver_sql(
            f"SELECT pg_advisory_lock({MIGRATION_LOCK_KEY})"
        )
        print(f"Acquired PG advisory lock {MIGRATION_LOCK_KEY}")
        try:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
        finally:
            connection.exec_driver_sql(
                f"SELECT pg_advisory_unlock({MIGRATION_LOCK_KEY})"
            )
            print(f"Released PG advisory lock {MIGRATION_LOCK_KEY}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
