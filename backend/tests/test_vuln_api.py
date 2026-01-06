from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app import database, main, models
from backend.app.auth import get_current_user
from backend.app.jobs import vuln_matcher
from backend.app.schemas import UserProfile


@pytest.mark.asyncio
async def test_inventory_vuln_flow(db_session, monkeypatch) -> None:
    agent = models.Agent(
        name="asset-2",
        os="linux",
        ip_address="10.0.0.2",
        status="online",
        api_key="key-2",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    def _fake_get_db():
        yield db_session

    def _fake_current_user():
        return UserProfile(
            id=1,
            full_name="Admin",
            role="admin",
            email="admin@example.com",
            tenant_id="default",
        )

    async def fake_osv(*_args, **_kwargs):
        return {
            "vulns": [
                {
                    "id": "OSV-2024-0002",
                    "summary": "Test vuln",
                    "details": "Details",
                    "aliases": ["CVE-2024-0002"],
                }
            ]
        }

    async def fake_nvd(*_args, **_kwargs):
        return {"vulnerabilities": []}

    async def fake_epss(*_args, **_kwargs):
        return 0.35

    monkeypatch.setattr(vuln_matcher, "_query_osv", fake_osv)
    monkeypatch.setattr(vuln_matcher, "_query_nvd", fake_nvd)
    monkeypatch.setattr(vuln_matcher, "_query_epss", fake_epss)

    app = main.app
    original_startup = list(app.router.on_startup)
    original_shutdown = list(app.router.on_shutdown)
    app.router.on_startup = []
    app.router.on_shutdown = []
    app.dependency_overrides[database.get_db] = _fake_get_db
    app.dependency_overrides[get_current_user] = _fake_current_user

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/inventory/assets/{agent.id}/software",
                json={
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                    "items": [
                        {
                            "name": "openssl",
                            "version": "1.1.1w",
                            "purl": "pkg:generic/openssl@1.1.1w",
                        }
                    ],
                },
            )
            assert response.status_code == 200
            await vuln_matcher.match_and_score(
                db_session,
                db_session.query(models.SoftwareComponent).all(),
            )
            vuln_response = client.get(
                f"/api/inventory/assets/{agent.id}/vulnerabilities"
            )
            assert vuln_response.status_code == 200
            payload = vuln_response.json()
            assert payload["total"] == 1
            assert payload["items"][0]["risk_label"] in {"CRITICAL", "HIGH"}
    finally:
        app.dependency_overrides = {}
        app.router.on_startup = original_startup
        app.router.on_shutdown = original_shutdown
