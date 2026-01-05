from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import crud, models
from backend.app.auth import get_password_hash
from backend.app.main import app, get_agent_shared_token


def create_user(db_session, email: str, role: str, password: str = "Pass123!"):
    user = models.User(
        full_name=email.split("@")[0],
        role=role,
        email=email,
        hashed_password=get_password_hash(password),
        avatar_url=None,
        timezone="Europe/Madrid",
        team=None,
        manager=None,
        computer=None,
        mobile_phone=None,
    )
    return crud.create_user(db_session, user)


def test_alert_created_emits_notifications(db_session):
    manager = create_user(db_session, "manager@eventsec.local", "team_lead")
    create_user(db_session, "l2@eventsec.local", "senior_analyst")

    client = TestClient(app)
    response = client.post(
        "/alerts",
        headers={"X-Agent-Token": get_agent_shared_token()},
        json={
            "title": "Malware alert",
            "description": "Suspicious activity",
            "source": "SIEM",
            "category": "Malware",
            "severity": "high",
        },
    )
    assert response.status_code == 200

    events = (
        db_session.query(models.NotificationEvent)
        .filter(models.NotificationEvent.event_type == "ALERT_CREATED")
        .all()
    )
    recipient_emails = {event.recipient_email for event in events}
    assert manager.email in recipient_emails
    assert "l2@eventsec.local" in recipient_emails


def test_alert_escalation_emits_notifications(db_session):
    admin = create_user(db_session, "admin@eventsec.local", "admin")
    manager = create_user(db_session, "lead@eventsec.local", "team_lead")
    assignee = create_user(db_session, "analyst@eventsec.local", "analyst")

    client = TestClient(app)
    login = client.post(
        "/auth/login",
        json={"email": admin.email, "password": "Pass123!"},
    )
    assert login.status_code == 200

    alert_response = client.post(
        "/alerts",
        headers={"X-Agent-Token": get_agent_shared_token()},
        json={
            "title": "Phishing alert",
            "description": "Suspicious email",
            "source": "Email Gateway",
            "category": "Phishing",
            "severity": "medium",
        },
    )
    alert_id = alert_response.json()["id"]

    escalate = client.post(
        f"/alerts/{alert_id}/escalate",
        json={"alert_id": alert_id, "escalated_to": assignee.id},
    )
    assert escalate.status_code == 200

    events = (
        db_session.query(models.NotificationEvent)
        .filter(models.NotificationEvent.event_type == "ALERT_ESCALATED")
        .all()
    )
    recipient_emails = {event.recipient_email for event in events}
    assert assignee.email in recipient_emails
    assert admin.email in recipient_emails
    assert manager.email in recipient_emails
