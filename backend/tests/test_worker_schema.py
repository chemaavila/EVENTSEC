from __future__ import annotations

from backend.app import config
from backend.app import worker


def test_worker_wait_for_required_tables_success(monkeypatch):
    monkeypatch.setattr(worker, "get_missing_tables", lambda conn: [])
    monkeypatch.setattr(config.settings, "db_ready_wait_attempts", 1)
    monkeypatch.setattr(config.settings, "db_ready_wait_interval_seconds", 0)
    assert worker.wait_for_required_tables() is True


def test_worker_wait_for_required_tables_failure(monkeypatch):
    monkeypatch.setattr(worker, "get_missing_tables", lambda conn: ["public.software_components"])
    monkeypatch.setattr(config.settings, "db_ready_wait_attempts", 1)
    monkeypatch.setattr(config.settings, "db_ready_wait_interval_seconds", 0)
    assert worker.wait_for_required_tables() is False
