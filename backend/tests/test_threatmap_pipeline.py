from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.threatmap.aggregator import FilterState, ThreatAggregator
from backend.app.threatmap.bus import ThreatEventBus
from backend.app.threatmap.config import ThreatMapConfig
from backend.app.threatmap.geoip import GeoIpEnricher
from backend.app.threatmap.runtime import ThreatMapRuntime
from backend.app.threatmap.schema import IngestEventIn


def test_schema_validation_rejects_bad_severity():
    with pytest.raises(Exception):
        IngestEventIn.model_validate(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "src_ip": "1.1.1.1",
                "dst_ip": "8.8.8.8",
                "attack_type": "DDoS",
                "severity": 100,
                "confidence": 0.5,
                "source": "ingest",
            }
        )


def test_geoip_missing_db_is_deterministic_no_random():
    cfg = ThreatMapConfig(
        telemetry_mode="live",
        maxmind_db_path="/does/not/exist.mmdb",
        replay_seconds=60,
        ttl_ms_default=45000,
        agg_tick_ms=1000,
        hb_tick_ms=2000,
    )
    enricher = GeoIpEnricher(cfg)
    r = enricher.lookup("8.8.8.8")
    assert r.geo is None or (r.geo.lat is None and r.geo.lon is None)


@pytest.mark.asyncio
async def test_runtime_normalize_sets_ttl_and_expires():
    rt = ThreatMapRuntime()
    inp = IngestEventIn.model_validate(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "src_ip": "8.8.8.8",
            "dst_ip": "1.1.1.1",
            "attack_type": "Scanner",
            "severity": 5,
            "confidence": 0.7,
            "tags": ["test"],
            "source": "ingest",
        }
    )
    evt = await rt.normalize_and_enrich(inp)
    assert evt.ttl_ms == rt.cfg.ttl_ms_default
    assert evt.expires_at > evt.ts
    assert evt.is_major is False


def test_aggregator_window_consistency():
    agg = ThreatAggregator(max_history_seconds=3600)
    now = datetime.now(timezone.utc)
    base = now - timedelta(seconds=30)

    # 10 events in last 30s
    for i in range(10):
        inp = IngestEventIn.model_validate(
            {
                "ts": (base + timedelta(seconds=i * 2)).isoformat(),
                "src_ip": "8.8.8.8",
                "dst_ip": "1.1.1.1",
                "attack_type": "DDoS",
                "severity": 7,
                "confidence": 0.9,
                "tags": [],
                "source": "ingest",
            }
        )
        # minimal AttackEvent-like: use runtime to normalize without geo dependency
        # Here, we only care about timestamps & fields used by aggregator.
        from backend.app.threatmap.schema import AttackEvent, Endpoint, Geo

        evt = AttackEvent(
            ts=inp.ts,
            src=Endpoint(ip=inp.src_ip, geo=Geo(lat=0.0, lon=0.0, country="US", city=None), asn=None),
            dst=Endpoint(ip=inp.dst_ip, geo=Geo(lat=10.0, lon=10.0, country="DE", city=None), asn=None),
            attack_type=inp.attack_type,
            severity=inp.severity,
            volume=None,
            tags=[],
            confidence=inp.confidence,
            source="ingest",
            real=True,
            ttl_ms=45000,
            expires_at=inp.ts + timedelta(milliseconds=45000),
            is_major=True,
        )
        agg.add(evt)

    snap = agg.snapshot(seq=1, window="5m", filters=FilterState(window="5m", types=None, min_severity=1, major_only=False, country=None))
    assert snap.count == 10
    assert snap.top_types[0][0] == "AttackType.DDoS" or "DDoS" in snap.top_types[0][0]


@pytest.mark.asyncio
async def test_bus_replay_and_seq_ordering():
    cfg = ThreatMapConfig(
        telemetry_mode="live",
        maxmind_db_path=None,
        replay_seconds=60,
        ttl_ms_default=45000,
        agg_tick_ms=1000,
        hb_tick_ms=2000,
    )
    bus = ThreatEventBus(cfg)
    from backend.app.threatmap.schema import AttackEvent, Endpoint, Geo

    now = datetime.now(timezone.utc)
    for i in range(3):
        evt = AttackEvent(
            ts=now,
            src=Endpoint(ip="8.8.8.8", geo=Geo(lat=0.0, lon=0.0, country="US", city=None), asn=None),
            dst=Endpoint(ip="1.1.1.1", geo=Geo(lat=10.0, lon=10.0, country="DE", city=None), asn=None),
            attack_type="Scanner",
            severity=4,
            volume=None,
            tags=[],
            confidence=0.5,
            source="test",
            real=True,
            ttl_ms=45000,
            expires_at=now + timedelta(milliseconds=45000),
            is_major=False,
        )
        await bus.publish(evt)

    replay = bus.replay()
    assert len(replay) == 3
    assert replay[0].seq < replay[1].seq < replay[2].seq


