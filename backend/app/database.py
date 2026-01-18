import os

from fastapi import HTTPException, status
from sqlalchemy import create_engine, inspect
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

engine = create_engine(settings.database_url, echo=False, future=True)
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
        inspector = inspect(conn)
        default_schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")

        schema_cache: dict[str, set[str]] = {}
        missing: list[str] = []

        for table in tables:
            if "." in table:
                schema, name = table.split(".", 1)
            else:
                schema, name = default_schema, table

            if schema not in schema_cache:
                schema_cache[schema] = set(inspector.get_table_names(schema=schema))

            if name not in schema_cache[schema]:
                missing.append(f"{schema}.{name}")

        return missing

    inspector = inspect(conn)
    existing = set(inspector.get_table_names())
    return [table for table in tables if table not in existing]
