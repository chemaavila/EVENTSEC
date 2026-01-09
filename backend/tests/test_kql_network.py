from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import search
from backend.app.auth import get_current_user


class FakeIndices:
    def __init__(self, mapping: dict[str, Any]):
        self._mapping = mapping

    def exists(self, index: str) -> bool:  # noqa: A003
        return True

    def get_mapping(self, index: str) -> dict[str, Any]:
        return self._mapping


class FakeClient:
    def __init__(self, mapping: dict[str, Any]):
        self.indices = FakeIndices(mapping=mapping)
        self.last_search: dict[str, Any] | None = None

    def search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        self.last_search = {"index": index, "body": body}
        return {"hits": {"hits": [], "total": {"value": 0}}, "took": 1}


def _override_user():
    return {"id": 1, "full_name": "Tester", "role": "admin", "email": "t@example.com"}


def test_kql_network_sort_field(monkeypatch):
    mapping = {
        "network-events-2024.01.01": {"mappings": {"properties": {"ts": {}, "src_ip": {}}}},
        "network-events-2024.01.02": {"mappings": {"properties": {"ts": {}, "dst_ip": {}}}},
    }
    fake_client = FakeClient(mapping=mapping)
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    monkeypatch.setattr(search, "client", fake_client)
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)

    response = client.post("/search/kql", json={"query": "network | limit 10"})
    assert response.status_code == 200
    assert fake_client.last_search is not None
    assert fake_client.last_search["body"]["sort"] == [{"ts": {"order": "desc"}}]

    app.dependency_overrides = {}


def test_kql_network_project_union_mapping(monkeypatch):
    mapping = {
        "network-events-2024.01.01": {"mappings": {"properties": {"ts": {}, "src_ip": {}}}},
        "network-events-2024.01.02": {"mappings": {"properties": {"ts": {}, "dst_ip": {}}}},
    }
    fake_client = FakeClient(mapping=mapping)
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    monkeypatch.setattr(search, "client", fake_client)
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)

    response = client.post("/search/kql", json={"query": "network | project src_ip | limit 5"})
    assert response.status_code == 200
    assert fake_client.last_search is not None
    assert fake_client.last_search["body"]["_source"] == ["src_ip"]

    app.dependency_overrides = {}
