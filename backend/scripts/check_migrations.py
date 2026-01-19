from __future__ import annotations

import os
import pathlib
import py_compile
import re
import sys

from sqlalchemy import create_engine, text

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import get_missing_tables, _build_connect_args  # noqa: E402


def main() -> int:
    base = pathlib.Path(__file__).resolve().parents[1]
    versions = base / "alembic" / "versions"
    failures = 0
    revisions: dict[str, pathlib.Path] = {}
    for path in sorted(versions.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures += 1
            print(f"[migrations] failed to compile: {path}")
            print(f"[migrations] {exc.msg}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures += 1
            print(f"[migrations] failed to read: {path}")
            print(f"[migrations] {exc}")
            continue
        match = re.search(r'^\s*revision\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.M)
        if match:
            revision = match.group(1)
            if revision in revisions:
                failures += 1
                print(
                    "[migrations] duplicate revision detected:"
                    f" {revision} in {revisions[revision]} and {path}"
                )
            else:
                revisions[revision] = path
    if failures:
        print(f"[migrations] compile failures: {failures}")
        return 1
    print("[migrations] all migrations compiled successfully")
    if os.environ.get("EVENTSEC_MIGRATION_VERIFY"):
        return verify_db_state()
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
