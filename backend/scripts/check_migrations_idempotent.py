from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import traceback

from sqlalchemy import create_engine, text

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import get_missing_tables, _build_connect_args  # noqa: E402


def main() -> int:
    if not (os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URL")):
        print("[migrations] DATABASE_URL or SQLALCHEMY_DATABASE_URL is required")
        return 1

    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print("[migrations] alembic upgrade head failed")
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        traceback.print_exc()
        return 1

    if verify_db_state() != 0:
        return 1

    print("[OK] alembic upgrade head is idempotent")
    return 0


def verify_db_state() -> int:
    url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URL")
    if not url:
        print("[migrations] DATABASE_URL or SQLALCHEMY_DATABASE_URL is required")
        return 1
    engine = create_engine(
        url, pool_pre_ping=True, future=True, connect_args=_build_connect_args(url)
    )
    with engine.connect() as conn:
        missing = get_missing_tables(conn, tables=("users", "alembic_version"))
        if missing:
            print(
                "[migrations] missing required tables after Alembic: "
                + ", ".join(missing),
                file=sys.stderr,
            )
            ident = conn.execute(
                text(
                    "SELECT current_database() AS db, current_user AS user, "
                    "current_setting('search_path') AS search_path"
                )
            ).mappings().first()
            if ident:
                print(
                    "[migrations] db={db} user={user} search_path={search_path}".format(
                        **ident
                    ),
                    file=sys.stderr,
                )
            schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")
            tables = conn.execute(
                text(
                    "SELECT table_schema, table_name FROM information_schema.tables "
                    "WHERE table_schema = :schema ORDER BY table_name LIMIT 50"
                ),
                {"schema": schema},
            ).mappings()
            for row in tables:
                print(
                    f"[migrations] {row['table_schema']}.{row['table_name']}",
                    file=sys.stderr,
                )
            return 1
    print("[migrations] required tables present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
