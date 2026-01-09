from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import crud, models
from backend.app.auth import get_password_hash
from backend.app.main import app


def create_user(db_session, email: str) -> models.User:
    user = models.User(
        full_name=email.split("@")[0],
        role="admin",
        email=email,
        hashed_password=get_password_hash("Pass123!"),
        avatar_url=None,
        timezone="Europe/Madrid",
        tenant_id="default",
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


def test_indicator_and_bioc_lifecycle(db_session):
    user = create_user(db_session, "intel_admin@example.com")

    client = TestClient(app)
    token = login(client, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    indicator_payload = {
        "type": "domain",
        "value": "malicious.example",
        "description": "Seed IOC",
        "severity": "high",
        "source": "manual",
        "tags": ["phishing"],
    }
    create_indicator = client.post("/indicators", json=indicator_payload, headers=headers)
    assert create_indicator.status_code == 200
    indicator = create_indicator.json()
    assert indicator["value"] == "malicious.example"

    list_indicators = client.get("/indicators", headers=headers)
    assert list_indicators.status_code == 200
    indicators = list_indicators.json()
    assert any(item["id"] == indicator["id"] for item in indicators)

    bioc_payload = {
        "name": "Suspicious PowerShell",
        "description": "PowerShell with encoded command",
        "platform": "windows",
        "tactic": "execution",
        "technique": "T1059",
        "detection_logic": "process.name == 'powershell.exe' and process.command_line contains '-enc'",
        "severity": "medium",
        "tags": ["behavior"],
    }
    create_bioc = client.post("/biocs", json=bioc_payload, headers=headers)
    assert create_bioc.status_code == 200
    bioc = create_bioc.json()
    assert bioc["name"] == "Suspicious PowerShell"

    list_bioc = client.get("/biocs", headers=headers)
    assert list_bioc.status_code == 200
    biocs = list_bioc.json()
    assert any(item["id"] == bioc["id"] for item in biocs)
