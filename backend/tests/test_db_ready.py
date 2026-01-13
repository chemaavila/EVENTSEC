from __future__ import annotations

from types import SimpleNamespace

from backend.app import database, main


def test_get_missing_tables_empty():
    with database.engine.connect() as conn:
        missing = database.get_missing_tables(conn)
    assert missing == []


def test_check_db_ready_reports_missing(monkeypatch):
    monkeypatch.setattr(
        database,
        "get_missing_tables",
        lambda conn: ["public.software_components"],
    )
    ok, message = main._check_db_ready()
    assert not ok
    assert "DBMissing" in message


def test_get_missing_tables_qualifies_public_schema():
    class FakeResult:
        def __init__(self, value: str | None):
            self._value = value

        def scalar(self) -> str | None:
            return self._value

    class FakeConn:
        def __init__(self, existing: set[str]):
            self.dialect = SimpleNamespace(name="postgresql")
            self.existing = existing
            self.seen: list[str] = []

        def execute(self, _statement, params):
            table_name = params["table_name"]
            self.seen.append(table_name)
            if table_name in self.existing:
                return FakeResult(table_name)
            return FakeResult(None)

    conn = FakeConn({"public.alembic_version"})
    missing = database.get_missing_tables(conn, tables=("alembic_version",))
    assert missing == []
    assert conn.seen == ["public.alembic_version"]
