import os

from fastapi import HTTPException, status
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


# Core tables required for the API to operate (auth, queue/worker, rules).
# Keep this aligned with your Alembic migrations.
DEFAULT_REQUIRED_TABLES = (
    # Core tables required for the API to operate (auth, queue/worker, rules).
    # Keep this aligned with your Alembic migrations.
    "users",
    "pending_events",
    "detection_rules",
    # Commonly used by inventory/vuln modules.
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
    We intentionally avoid Postgres `to_regclass()` checks here because in some
    hosted setups it can return false negatives (NULL) even when the table exists.
    Using SQLAlchemy's Inspector is more reliable.
    """
    tables = tables or required_tables_for_dialect(conn.dialect.name)

    # Default schema for Postgres checks (override if you ever move off public)
    default_schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")

    if conn.dialect.name == "postgresql":
        inspector = inspect(conn)

        # Cache table lists by schema to avoid repeated catalog queries
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
