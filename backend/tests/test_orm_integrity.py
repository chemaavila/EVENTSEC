from backend.app import models


def test_basic_crud_relationships(db_session):
    user = models.User(
        full_name="Ada Lovelace",
        role="analyst",
        email="ada@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    db_session.commit()

    alert = models.Alert(
        title="Suspicious login",
        description="Multiple failed logins",
        source="auth",
        category="auth",
        severity="high",
        owner=user,
        assignee=user,
    )
    incident = models.Incident(
        title="Credential stuffing",
        description="Investigation opened",
        severity="high",
        assignee=user,
        creator=user,
    )
    db_session.add_all([alert, incident])
    db_session.commit()

    refreshed_user = db_session.get(models.User, user.id)
    assert refreshed_user is not None
    assert len(refreshed_user.alerts) == 1
    assert len(refreshed_user.assigned_alerts) == 1
    assert len(refreshed_user.incidents_assigned) == 1
    assert len(refreshed_user.incidents_created) == 1
