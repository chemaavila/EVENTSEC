import os

from fastapi import HTTPException, status
from sqlalchemy import bindparam, create_engine, event, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


# Core tables required for the API to operate (auth, queue/worker, rules).
# Keep this aligned with your Alembic migrations.
DEFAULT_REQUIRED_TABLES = (
    "users",
    "pending_events",
    "detection_rules",
    "software_components",
    "asset_vulnerabilities",
)
ALEMBIC_TABLE = "alembic_version"

def _build_connect_args(database_url: str) -> dict[str, str]:
    try:
        parsed = make_url(database_url)
    except Exception:  # noqa: BLE001
        return {}

    if parsed.drivername.startswith("postgresql"):
        schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")
        return {"options": f"-c search_path={schema}"}
    return {}


engine = create_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=_build_connect_args(settings.database_url),
)

if engine.dialect.name == "postgresql":
    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record) -> None:
        schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SET SESSION search_path TO {schema}")
        finally:
            cursor.close()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
)


def get_db():
    if os.environ.get("EVENTSEC_DB_NOT_MIGRATED") == "1":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database schema is not migrated. Run alembic upgrade head.",
            headers={"X-EventSec-Error": "DB_NOT_MIGRATED"},
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def required_tables_for_dialect(dialect_name: str) -> tuple[str, ...]:
    if dialect_name == "postgresql":
        return (*DEFAULT_REQUIRED_TABLES, ALEMBIC_TABLE)
    return DEFAULT_REQUIRED_TABLES


def get_missing_tables(conn, tables: tuple[str, ...] | None = None) -> list[str]:
    """
    Returns schema-qualified names for missing tables.

    IMPORTANT:
    Avoid Postgres to_regclass() here because it can false-negative in some hosted setups.
    SQLAlchemy Inspector is more reliable.
    """
    tables = tables or required_tables_for_dialect(conn.dialect.name)

    if conn.dialect.name == "postgresql":
        default_schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")

        desired: dict[str, set[str]] = {}
        for table in tables:
            if "." in table:
                schema, name = table.split(".", 1)
            else:
                schema, name = default_schema, table
            desired.setdefault(schema, set()).add(name)

        missing: list[str] = []
        pg_stmt = text(
            "SELECT n.nspname AS schema, c.relname AS name "
            "FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = :schema AND c.relname IN :table_names "
            "AND c.relkind IN ('r','p')"
        ).bindparams(bindparam("table_names", expanding=True))
        info_stmt = text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name IN :table_names"
        ).bindparams(bindparam("table_names", expanding=True))

        for schema, names in desired.items():
            if not names:
                continue
            pg_rows = conn.execute(
                pg_stmt,
                {"schema": schema, "table_names": sorted(names)},
            ).fetchall()
            pg_existing = {row[1] for row in pg_rows}

            info_rows = conn.execute(
                info_stmt,
                {"schema": schema, "table_names": sorted(names)},
            ).fetchall()
            info_existing = {row[0] for row in info_rows}

            for name in sorted(names):
                if name in pg_existing:
                    continue
                if name in info_existing:
                    continue
                missing.append(f"{schema}.{name}")

        return missing

    inspector = inspect(conn)
    existing = set(inspector.get_table_names())
    return [table for table in tables if table not in existing]
