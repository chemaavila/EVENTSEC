from sqlalchemy import select

from backend.app import crud, models, search
from backend.app.main import _apply_ioc_matches, _apply_malware_alerts


def test_ioc_domain_match_creates_alert(db_session, monkeypatch) -> None:
    monkeypatch.setattr(search, "index_alert", lambda doc: None)
    indicator = models.Indicator(
        owner_id=None,
        type="domain",
        value="evil.test",
        description="test domain",
        severity="high",
        source="unit-test",
        tags=[],
        status="active",
    )
    db_session.add(indicator)
    db_session.commit()
    db_session.refresh(indicator)

    event = models.Event(
        agent_id=None,
        event_type="edr.url_visit",
        severity="low",
        category="edr",
        details={"domain": "evil.test", "hostname": "host-a", "username": "tester"},
    )
    event = crud.create_event(db_session, event)

    _apply_ioc_matches(db_session, event, event.details, event.details.get("correlation_id"))

    alerts = list(db_session.scalars(select(models.Alert)))
    assert any(alert.title == "IOC Match: evil.test" for alert in alerts)


def test_malware_detection_event_creates_alert(db_session, monkeypatch) -> None:
    monkeypatch.setattr(search, "index_alert", lambda doc: None)
    event = models.Event(
        agent_id=None,
        event_type="edr.malware_detection",
        severity="critical",
        category="edr",
        details={
            "hostname": "host-b",
            "username": "analyst",
            "malware_name": "Test.Malware",
            "file_path": "/tmp/bad.exe",
            "engine": "clamav",
        },
    )
    event = crud.create_event(db_session, event)

    _apply_malware_alerts(db_session, event, event.details, event.details.get("correlation_id"))

    alerts = list(db_session.scalars(select(models.Alert)))
    assert any("Malware detected on host-b" == alert.title for alert in alerts)
