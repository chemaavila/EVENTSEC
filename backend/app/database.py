import os

from fastapi import HTTPException, status
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


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
    tables = tables or required_tables_for_dialect(conn.dialect.name)
    if conn.dialect.name == "postgresql":
        missing: list[str] = []
        for table in tables:
            qualified = table if "." in table else f"public.{table}"
            exists = conn.execute(
                text("SELECT to_regclass(:table_name)"),
                {"table_name": qualified},
            ).scalar()
            if exists is None:
                missing.append(qualified)
        return missing
    inspector = inspect(conn)
    existing = set(inspector.get_table_names())
    return [table for table in tables if table not in existing]
