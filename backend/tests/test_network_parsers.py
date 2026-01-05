from __future__ import annotations

from backend.app.parsers.suricata_eve import parse_suricata_event
from backend.app.parsers.zeek_json import parse_zeek_event


def test_parse_suricata_alert():
    raw = {
        "timestamp": "2024-01-01T00:00:00.000Z",
        "event_type": "alert",
        "src_ip": "10.0.0.1",
        "src_port": 12345,
        "dest_ip": "10.0.0.2",
        "dest_port": 443,
        "proto": "TCP",
        "alert": {
            "signature": "ET MALWARE Possible Malware traffic",
            "category": "Malware",
            "severity": 1,
        },
        "http": {
            "hostname": "example.com",
            "url": "/login",
            "http_method": "POST",
            "status": 200,
            "http_user_agent": "curl/7.88.1",
        },
        "tags": ["ids", "suricata"],
    }
    parsed = parse_suricata_event(raw)
    assert parsed.event_type == "alert"
    assert parsed.src_ip == "10.0.0.1"
    assert parsed.dst_ip == "10.0.0.2"
    assert parsed.signature == "ET MALWARE Possible Malware traffic"
    assert parsed.http["method"] == "POST"


def test_parse_zeek_conn():
    raw = {
        "ts": 1700000000.0,
        "uid": "C8LqkZ1",
        "id.orig_h": "192.168.1.10",
        "id.orig_p": 55555,
        "id.resp_h": "1.1.1.1",
        "id.resp_p": 53,
        "proto": "udp",
        "service": "dns",
        "_path": "conn",
    }
    parsed = parse_zeek_event(raw)
    assert parsed.event_type == "conn"
    assert parsed.dst_port == 53
    assert parsed.uid == "C8LqkZ1"
