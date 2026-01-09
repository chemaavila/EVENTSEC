from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import search
from backend.app.auth import get_current_user


class FakeIndices:
    def __init__(self, exists: bool = True, mapping: dict[str, Any] | None = None):
        self._exists = exists
        self._mapping = mapping or {"events": {"mappings": {"properties": {"timestamp": {}}}}}

    def exists(self, index: str) -> bool:  # noqa: A003
        return self._exists

    def get_mapping(self, index: str) -> dict[str, Any]:
        return self._mapping


class FakeClient:
    def __init__(self, exists: bool = True, mapping: dict[str, Any] | None = None):
        self.indices = FakeIndices(exists=exists, mapping=mapping)

    def search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        return {"hits": {"hits": [], "total": {"value": 0}}, "took": 1}


def _override_user():
    return {"id": 1, "full_name": "Tester", "role": "admin", "email": "t@example.com"}


def test_kql_table_not_found(monkeypatch):
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    monkeypatch.setattr(search, "client", FakeClient(exists=False))
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    response = client.post("/search/kql", json={"query": "events | limit 1"})
    assert response.status_code == 404
    assert response.json()["detail"]["error_type"] == "TABLE_NOT_FOUND"
    app.dependency_overrides = {}


def test_kql_field_not_found(monkeypatch):
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    mapping = {"events": {"mappings": {"properties": {"timestamp": {}}}}}
    monkeypatch.setattr(search, "client", FakeClient(exists=True, mapping=mapping))
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    response = client.post(
        "/search/kql",
        json={"query": "events | project missing_field"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "FIELD_NOT_FOUND"
    app.dependency_overrides = {}


def test_kql_syntax_error(monkeypatch):
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    monkeypatch.setattr(search, "client", FakeClient())
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    response = client.post("/search/kql", json={"query": "events | where =="})
    assert response.status_code == 400
    assert response.json()["detail"]["error_type"] == "SYNTAX_ERROR"
    app.dependency_overrides = {}
