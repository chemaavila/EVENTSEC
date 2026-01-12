from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine.url import make_url

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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


def _redacted_url(url: str) -> str:
    try:
        parsed = make_url(url)
    except Exception:  # noqa: BLE001
        return url
    if parsed.password:
        parsed = parsed.set(password="***")
    return str(parsed)


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
    _debug_log(
        f"[db-debug] {label} url={_redacted_url(url)} url_host={host} db={database}"
    )
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


def _dump_db_state(connection, label: str) -> None:
    if not os.environ.get("EVENTSEC_DB_DEBUG"):
        return
    _debug_log(f"[db-debug] {label} pg_namespace count:")
    count_row = connection.execute(
        text("SELECT count(*) AS count FROM pg_namespace")
    ).mappings().first()
    if count_row:
        _debug_log(f"[db-debug] {label} pg_namespace.count={count_row['count']}")
    _debug_log(f"[db-debug] {label} identity:")
    ident_row = connection.execute(
        text(
            "SELECT current_database() AS db, current_user AS user, "
            "current_setting('search_path') AS search_path"
        )
    ).mappings().first()
    if ident_row:
        _debug_log(
            f"[db-debug] {label} db={ident_row['db']} "
            f"user={ident_row['user']} search_path={ident_row['search_path']}"
        )
    _debug_log(f"[db-debug] {label} relations:")
    rels = connection.execute(
        text(
            "SELECT n.nspname, c.relname, c.relkind "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname NOT IN ('pg_catalog','information_schema') "
            "ORDER BY n.nspname, c.relname "
            "LIMIT 200"
        )
    ).mappings()
    for row in rels:
        _debug_log(
            f"[db-debug] {label} rel {row['nspname']}.{row['relname']} "
            f"kind={row['relkind']}"
        )


def _verify_expected_tables(connection) -> None:
    checks = connection.execute(
        text(
            "SELECT "
            "to_regclass('public.alembic_version') IS NOT NULL AS has_alembic, "
            "to_regclass('public.users') IS NOT NULL AS has_users"
        )
    ).mappings().one()
    missing = []
    if not checks["has_alembic"]:
        missing.append("public.alembic_version")
    if not checks["has_users"]:
        missing.append("public.users")
    if missing:
        _dump_db_state(connection, "missing-required-tables")
        raise RuntimeError(
            "Missing required tables after Alembic upgrade: "
            + ", ".join(missing)
        )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    _debug_db_target("alembic-offline")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
        version_table="alembic_version",
        version_table_schema="public",
    )

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
        connection.exec_driver_sql("SET search_path TO public")
        print(f"Acquiring PG advisory lock {MIGRATION_LOCK_KEY}")
        connection.exec_driver_sql(
            f"SELECT pg_advisory_lock({MIGRATION_LOCK_KEY})"
        )
        print(f"Acquired PG advisory lock {MIGRATION_LOCK_KEY}")
        try:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True,
                compare_type=True,
                compare_server_default=True,
                version_table="alembic_version",
                version_table_schema="public",
            )

            with context.begin_transaction():
                context.run_migrations()
            _debug_db_target("alembic-online-complete", connection)
            _verify_expected_tables(connection)
            _dump_db_state(connection, "post-migration")
        finally:
            connection.exec_driver_sql(
                f"SELECT pg_advisory_unlock({MIGRATION_LOCK_KEY})"
            )
            print(f"Released PG advisory lock {MIGRATION_LOCK_KEY}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
