from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import models
from backend.app.auth import get_password_hash
from backend.app.main import app


def _create_user(db_session, *, email: str, password: str) -> models.User:
    user = models.User(
        full_name="Admin User",
        role="admin",
        email=email,
        hashed_password=get_password_hash(password),
        timezone="UTC",
        tenant_id="default",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_sets_cookie_and_me_works(db_session) -> None:
    _create_user(db_session, email="admin@example.com", password="Admin123!")
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie

    profile_response = client.get("/me")
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "admin@example.com"


def test_login_rejects_wrong_password(db_session) -> None:
    _create_user(db_session, email="admin@example.com", password="Admin123!")
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_user(db_session) -> None:
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "Admin123!"},
    )
    assert response.status_code == 401
