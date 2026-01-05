from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app import crud, models
from backend.app.auth import get_password_hash
from backend.app.main import app


def create_user(db_session, email: str, role: str, tenant_id: str) -> models.User:
    user = models.User(
        full_name=email.split("@")[0],
        role=role,
        email=email,
        hashed_password=get_password_hash("Pass123!"),
        avatar_url=None,
        timezone="Europe/Madrid",
        tenant_id=tenant_id,
        team=None,
        manager=None,
        computer=None,
        mobile_phone=None,
    )
    return crud.create_user(db_session, user)


def login(client: TestClient, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "Pass123!"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_storage_policy_defaults_and_update(db_session):
    tenant_id = "tenant-a"
    user = create_user(db_session, "admin@tenant-a.local", "admin", tenant_id)

    client = TestClient(app)
    token = login(client, user.email)

    response = client.get(
        f"/tenants/{tenant_id}/storage-policy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["data_lake_enabled"] is False

    update = client.put(
        f"/tenants/{tenant_id}/storage-policy",
        headers={"Authorization": f"Bearer {token}"},
        json={"data_lake_enabled": True, "hot_days": 14, "cold_days": 90},
    )
    assert update.status_code == 200
    updated = update.json()
    assert updated["data_lake_enabled"] is True
    assert updated["hot_days"] == 14
    assert updated["cold_days"] == 90


def test_storage_policy_denies_cross_tenant(db_session):
    user = create_user(db_session, "analyst@tenant-a.local", "analyst", "tenant-a")

    client = TestClient(app)
    token = login(client, user.email)

    response = client.get(
        "/tenants/tenant-b/storage-policy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_usage_requires_enabled_policy(db_session):
    tenant_id = "tenant-a"
    user = create_user(db_session, "analyst@tenant-a.local", "analyst", tenant_id)

    crud.upsert_tenant_storage_policy(db_session, tenant_id, {"data_lake_enabled": True})

    today = date.today()
    usage = models.TenantUsageDaily(
        tenant_id=tenant_id,
        day=today - timedelta(days=1),
        bytes_ingested=1024,
        docs_ingested=10,
        query_count=2,
        hot_est=2048,
        cold_est=4096,
    )
    db_session.add(usage)
    db_session.commit()

    client = TestClient(app)
    token = login(client, user.email)

    response = client.get(
        f"/tenants/{tenant_id}/usage",
        headers={"Authorization": f"Bearer {token}"},
        params={"from": (today - timedelta(days=2)).isoformat(), "to": today.isoformat()},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert len(payload["items"]) == 1
    assert payload["items"][0]["bytes_ingested"] == 1024
