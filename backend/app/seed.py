from __future__ import annotations

import os

from . import fixtures
from .database import engine, get_missing_tables


def run_seed() -> None:
    with engine.begin() as connection:
        missing = get_missing_tables(connection, tables=("users", "alembic_version"))
        if missing:
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
