from app.integrations.software_indexer import (
    map_software_alert_to_edr_event,
    map_software_alert_to_siem_event,
)


def test_map_software_alert_to_siem_event():
    doc = {
        "timestamp": "2024-01-01T00:00:00Z",
        "rule": {"id": "1001", "level": 12, "groups": ["auth", "ssh"]},
        "agent": {"id": "001", "name": "host-a"},
        "data": {"hostname": "host-a", "srcuser": "root"},
        "full_log": "Accepted password",
    }
    event = map_software_alert_to_siem_event(doc)
    assert event["host"] == "host-a"
    assert event["severity"] == "high"
    assert event["category"] == "auth"
    assert event["message"] == "Accepted password"


def test_map_software_alert_to_edr_event():
    doc = {
        "@timestamp": "2024-01-01T00:00:00Z",
        "rule": {"id": "2001", "level": 5, "description": "Process alert"},
        "agent": {"id": "002", "name": "host-b"},
        "data": {"process_name": "cmd.exe", "user": "bob"},
    }
    event = map_software_alert_to_edr_event(doc)
    assert event["hostname"] == "host-b"
    assert event["username"] == "bob"
    assert event["process_name"] == "cmd.exe"
    assert event["severity"] == "medium"
    assert event["action"] == "Process alert"
