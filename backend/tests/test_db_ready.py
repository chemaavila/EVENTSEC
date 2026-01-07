from __future__ import annotations

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
