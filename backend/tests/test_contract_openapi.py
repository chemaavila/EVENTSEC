from __future__ import annotations

from backend.app.main import app


def test_openapi_includes_frontend_paths():
    schema = app.openapi()
    paths = set(schema.get("paths", {}).keys())
    required_paths = {
        "/auth/login",
        "/auth/logout",
        "/alerts",
        "/api/inventory/assets",
        "/api/vulnerabilities",
    }
    missing = required_paths - paths
    assert not missing, f"Missing OpenAPI paths: {sorted(missing)}"
