from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine.url import make_url

from app.config import settings
from app.database import Base
from app import models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

MIGRATION_LOCK_KEY = 7342573498572345


def _debug_log(message: str) -> None:
    print(message, file=sys.stderr)


def _debug_db_target(label: str, connection=None) -> None:
    if not os.environ.get("EVENTSEC_DB_DEBUG"):
        return
    url = config.get_main_option("sqlalchemy.url")
    try:
        parsed = make_url(url)
        host = parsed.host or "unknown"
        database = parsed.database or "unknown"
    except Exception:  # noqa: BLE001
        host = "unknown"
        database = "unknown"
    _debug_log(f"[db-debug] {label} url_host={host} db={database}")
    if connection is None:
        return
    row = (
        connection.execute(
            text(
                "SELECT current_database() AS db, current_user AS user, "
                "inet_server_addr() AS server_addr, "
                "inet_server_port() AS server_port, "
                "current_setting('search_path') AS search_path"
            )
        )
        .mappings()
        .first()
    )
    if row:
        _debug_log(
            "[db-debug] "
            f"{label} server_addr={row['server_addr']} "
            f"server_port={row['server_port']} "
            f"db={row['db']} user={row['user']} "
            f"search_path={row['search_path']}"
        )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    _debug_db_target("alembic-offline")
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
        _debug_db_target("alembic-online-start", connection)
        print(f"Acquiring PG advisory lock {MIGRATION_LOCK_KEY}")
        connection.exec_driver_sql(
            f"SELECT pg_advisory_lock({MIGRATION_LOCK_KEY})"
        )
        print(f"Acquired PG advisory lock {MIGRATION_LOCK_KEY}")
        try:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
            _debug_db_target("alembic-online-complete", connection)
        finally:
            connection.exec_driver_sql(
                f"SELECT pg_advisory_unlock({MIGRATION_LOCK_KEY})"
            )
            print(f"Released PG advisory lock {MIGRATION_LOCK_KEY}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
