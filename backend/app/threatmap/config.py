from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatMapConfig:
    telemetry_mode: str
    maxmind_db_path: str | None
    fallback_coords: bool
    replay_seconds: int
    ttl_ms_default: int
    agg_tick_ms: int
    hb_tick_ms: int


def get_threatmap_config() -> ThreatMapConfig:
    telemetry_mode = (os.getenv("THREATMAP_TELEMETRY_MODE") or "live").strip().lower()
    if telemetry_mode not in ("live", "mock"):
        telemetry_mode = "live"

    maxmind_db_path = os.getenv("MAXMIND_DB_PATH") or None
    fallback_coords = (os.getenv("THREATMAP_FALLBACK_COORDS") or "false").lower() == "true"
    replay_seconds = int(os.getenv("THREATMAP_REPLAY_SECONDS") or "60")
    ttl_ms_default = int(os.getenv("THREATMAP_TTL_MS") or "45000")
    agg_tick_ms = int(os.getenv("THREATMAP_AGG_TICK_MS") or "1000")
    hb_tick_ms = int(os.getenv("THREATMAP_HB_TICK_MS") or "2000")

    return ThreatMapConfig(
        telemetry_mode=telemetry_mode,
        maxmind_db_path=maxmind_db_path,
        fallback_coords=fallback_coords,
        replay_seconds=max(5, min(600, replay_seconds)),
        ttl_ms_default=max(5_000, min(300_000, ttl_ms_default)),
        agg_tick_ms=max(200, min(5_000, agg_tick_ms)),
        hb_tick_ms=max(500, min(10_000, hb_tick_ms)),
    )
