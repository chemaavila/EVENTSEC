from __future__ import annotations

from backend.app.threatmap.config import ThreatMapConfig
from backend.app.threatmap.geoip import GeoIpEnricher


def test_geoip_fallback_coords():
    cfg = ThreatMapConfig(
        telemetry_mode="live",
        maxmind_db_path=None,
        fallback_coords=True,
        replay_seconds=60,
        ttl_ms_default=45000,
        agg_tick_ms=1000,
        hb_tick_ms=2000,
    )
    enricher = GeoIpEnricher(cfg)
    result = enricher.lookup("10.10.10.10")

    assert result.geo is not None
    assert result.geo.approx is True
    assert result.geo.lat is not None
    assert result.geo.lon is not None
