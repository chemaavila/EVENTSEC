from __future__ import annotations

import os
import subprocess
import sys
import traceback

from sqlalchemy import create_engine, text


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
    engine = create_engine(url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        checks = conn.execute(
            text(
                "SELECT "
                "to_regclass('public.users') IS NOT NULL AS has_users_public, "
                "to_regclass('public.alembic_version') IS NOT NULL AS has_alembic_public"
            )
        ).mappings().one()
        missing = []
        if not checks["has_users_public"]:
            missing.append("public.users")
        if not checks["has_alembic_public"]:
            missing.append("public.alembic_version")
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
            tables = conn.execute(
                text(
                    "SELECT schemaname, tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename LIMIT 50"
                )
            ).mappings()
            for row in tables:
                print(
                    f"[migrations] public table {row['schemaname']}.{row['tablename']}",
                    file=sys.stderr,
                )
            return 1
    print("[migrations] required tables present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
