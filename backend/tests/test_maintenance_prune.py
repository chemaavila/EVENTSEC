from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.app import maintenance, models, search, database


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def delete_by_query(self, index: str, body: dict, **_kwargs) -> dict:
        self.calls.append(index)
        return {"deleted": 1}


def test_prune_removes_old_records(db_session, monkeypatch):
    old_ts = datetime.now(timezone.utc) - timedelta(days=90)
    new_ts = datetime.now(timezone.utc)

    old_event = models.Event(
        agent_id=None,
        event_type="auth",
        severity="low",
        category="test",
        details={},
        created_at=old_ts,
    )
    new_event = models.Event(
        agent_id=None,
        event_type="auth",
        severity="low",
        category="test",
        details={},
        created_at=new_ts,
    )
    old_network_event = models.NetworkEvent(
        id="old-net",
        tenant_id=None,
        source="sensor",
        event_type="flow",
        ts=old_ts,
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
    )
    new_network_event = models.NetworkEvent(
        id="new-net",
        tenant_id=None,
        source="sensor",
        event_type="flow",
        ts=new_ts,
        src_ip="10.0.0.3",
        dst_ip="10.0.0.4",
    )
    old_ingest_error = models.NetworkIngestError(
        tenant_id=None,
        source="sensor",
        sensor_name="sensor-1",
        ts=old_ts,
        reason="parse",
        raw_snippet="bad",
    )
    db_session.add_all(
        [old_event, new_event, old_network_event, new_network_event, old_ingest_error]
    )
    db_session.commit()

    fake_client = FakeClient()
    monkeypatch.setattr(search, "client", fake_client)
    monkeypatch.setattr(maintenance, "SessionLocal", database.SessionLocal)

    stats = maintenance.prune(30)

    assert stats["events_deleted"] == 1
    assert stats["network_events_deleted"] == 1
    assert stats["network_ingest_errors_deleted"] == 1

    remaining_events = db_session.query(models.Event).all()
    remaining_network_events = db_session.query(models.NetworkEvent).all()
    remaining_errors = db_session.query(models.NetworkIngestError).all()

    assert len(remaining_events) == 1
    assert remaining_events[0].id == new_event.id
    assert len(remaining_network_events) == 1
    assert remaining_network_events[0].id == new_network_event.id
    assert len(remaining_errors) == 0

    expected_indices = {
        "events",
        "events-v1",
        "alerts",
        "alerts-v1",
        "network-events-*",
        "raw-events-*",
        "dlq-events-*",
    }
    assert expected_indices.issubset(set(fake_client.calls))
