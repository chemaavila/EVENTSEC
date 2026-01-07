from __future__ import annotations

import os

from sqlalchemy import text

from . import fixtures
from .database import engine


def run_seed() -> None:
    with engine.begin() as connection:
        checks = connection.execute(
            text(
                "SELECT "
                "to_regclass('public.alembic_version') IS NOT NULL AS has_alembic, "
                "to_regclass('public.users') IS NOT NULL AS has_users"
            )
        ).mappings().one()
        if not checks["has_alembic"] or not checks["has_users"]:
            missing = []
            if not checks["has_alembic"]:
                missing.append("public.alembic_version")
            if not checks["has_users"]:
                missing.append("public.users")
            message = "Seed aborted; missing tables: " + ", ".join(missing)
            if os.environ.get("SEED_SKIP_ON_ERROR") in {"1", "true", "TRUE"}:
                print(f"[seed] WARNING: {message}")
                return
            raise RuntimeError(message)
        fixtures.seed_core_data(connection)
        admin_password = os.environ.get("EVENTSEC_ADMIN_PASSWORD")
        if admin_password:
            print("[seed] Updating admin password from EVENTSEC_ADMIN_PASSWORD")
            fixtures.update_admin_password(connection, admin_password)


if __name__ == "__main__":
    run_seed()
