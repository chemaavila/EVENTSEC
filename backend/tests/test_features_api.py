from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import config


def test_features_endpoint(monkeypatch):
    monkeypatch.setattr(config.settings, "feature_intel_enabled", True)
    monkeypatch.setattr(config.settings, "feature_ot_enabled", False)
    monkeypatch.setattr(config.settings, "feature_email_actions_enabled", False)
    monkeypatch.setattr(config.settings, "vuln_intel_enabled", False)
    monkeypatch.setattr(config.settings, "threatmap_fallback_coords", True)
    monkeypatch.setattr(config.settings, "detection_queue_mode", "memory")

    client = TestClient(app)
    response = client.get("/features")

    assert response.status_code == 200
    payload = response.json()
    assert payload["feature_intel_enabled"] is True
    assert payload["feature_ot_enabled"] is False
    assert payload["feature_email_actions_enabled"] is False
    assert payload["vuln_intel_enabled"] is False
    assert payload["threatmap_fallback_coords"] is True
    assert payload["detection_queue_mode"] == "memory"
