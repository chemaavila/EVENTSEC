from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth import get_current_user


def _override_user():
    return {"id": 1, "full_name": "Tester", "role": "admin", "email": "t@example.com"}


def test_clear_siem_events_disabled():
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    response = client.delete("/siem/events")
    assert response.status_code == 405
    app.dependency_overrides = {}


def test_clear_edr_events_disabled():
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    response = client.delete("/edr/events")
    assert response.status_code == 405
    app.dependency_overrides = {}
