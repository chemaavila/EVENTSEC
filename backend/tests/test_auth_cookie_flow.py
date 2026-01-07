from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import models
from backend.app.auth import get_password_hash
from backend.app.config import settings
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


def test_login_cookie_attributes_respect_settings(db_session) -> None:
    _create_user(db_session, email="admin@example.com", password="Admin123!")
    client = TestClient(app)
    original_values = {
        "cookie_name": settings.cookie_name,
        "cookie_samesite": settings.cookie_samesite,
        "cookie_secure": settings.cookie_secure,
        "cookie_domain": settings.cookie_domain,
        "cookie_path": settings.cookie_path,
        "cookie_max_age_seconds": settings.cookie_max_age_seconds,
    }
    try:
        settings.cookie_name = "access_token"
        settings.cookie_samesite = "strict"
        settings.cookie_secure = True
        settings.cookie_domain = None
        settings.cookie_path = "/"
        settings.cookie_max_age_seconds = 1200

        response = client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!"},
        )
        set_cookie = response.headers.get("set-cookie", "")
        set_cookie_lower = set_cookie.lower()
        assert "HttpOnly" in set_cookie
        assert "Path=/" in set_cookie
        assert "samesite=strict" in set_cookie_lower
        assert "Secure" in set_cookie
        assert "Max-Age=1200" in set_cookie
    finally:
        for key, value in original_values.items():
            setattr(settings, key, value)


def test_login_cookie_secure_inherits_https_setting(db_session) -> None:
    _create_user(db_session, email="admin@example.com", password="Admin123!")
    client = TestClient(app)
    original_values = {
        "cookie_secure": settings.cookie_secure,
        "cookie_samesite": settings.cookie_samesite,
        "server_https_enabled": settings.server_https_enabled,
    }
    try:
        settings.cookie_secure = None
        settings.cookie_samesite = "lax"
        settings.server_https_enabled = True
        response = client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!"},
        )
        set_cookie = response.headers.get("set-cookie", "")
        set_cookie_lower = set_cookie.lower()
        assert "Secure" in set_cookie
        assert "samesite=lax" in set_cookie_lower
    finally:
        for key, value in original_values.items():
            setattr(settings, key, value)


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
