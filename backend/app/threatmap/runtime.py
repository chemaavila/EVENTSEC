from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
from uuid import UUID, uuid4

from .aggregator import ThreatAggregator
from .bus import ThreatEventBus
from .config import ThreatMapConfig, get_threatmap_config
from .geoip import GeoIpEnricher
from .schema import AttackEvent, Endpoint, IngestEventIn

logger = logging.getLogger("eventsec.threatmap")


class ThreatMapRuntime:
    """Singleton-ish runtime holder for the threat map pipeline."""

    def __init__(self) -> None:
        self.cfg: ThreatMapConfig = get_threatmap_config()
        self.geo = GeoIpEnricher(self.cfg)
        self.bus = ThreatEventBus(self.cfg)
        self.agg = ThreatAggregator(max_history_seconds=3600)

        # Dedup cache: key -> (last_ts, merged_event_id)
        self._dedup: Dict[tuple[str, str, str, str], Tuple[datetime, UUID]] = {}
        self._dedup_window = timedelta(seconds=int(30))
        self._dedup_lock = asyncio.Lock()

    async def normalize_and_enrich(self, inp: IngestEventIn) -> AttackEvent:
        ttl_ms = self.cfg.ttl_ms_default

        src_ep = Endpoint(ip=inp.src_ip)
        dst_ep = Endpoint(ip=inp.dst_ip)

        # Deterministic GeoIP enrichment if IPs exist
        if inp.src_ip:
            ga = self.geo.lookup(inp.src_ip)
            src_ep.geo = ga.geo
            src_ep.asn = ga.asn
        if inp.dst_ip:
            ga = self.geo.lookup(inp.dst_ip)
            dst_ep.geo = ga.geo
            dst_ep.asn = ga.asn

        ts = inp.ts.astimezone(timezone.utc)
        expires_at = ts + timedelta(milliseconds=ttl_ms)

        evt = AttackEvent(
            id=(inp.id or uuid4()),
            ts=ts,
            src=src_ep,
            dst=dst_ep,
            attack_type=inp.attack_type,
            severity=inp.severity,
            volume=inp.volume,
            tags=inp.tags,
            confidence=float(inp.confidence),
            source=inp.source,
            real=True,
            ttl_ms=ttl_ms,
            expires_at=expires_at,
            is_major=bool(inp.severity >= 7),
        )
        return evt

    async def dedupe_merge_or_publish(self, evt: AttackEvent) -> AttackEvent:
        """Deduplicate within a short window by coalescing into a stable event id.

        We DO NOT fabricate events; we may merge duplicates into an updated canonical event
        (same id) so UI remains stable and aggs match streamed raw events.
        """
        now = datetime.now(timezone.utc)
        src_ip = evt.src.ip or "unknown"
        dst_ip = evt.dst.ip or "unknown"
        tags_key = ",".join(sorted(set(evt.tags or [])))[:200]
        key = (src_ip, dst_ip, str(evt.attack_type), tags_key)

        async with self._dedup_lock:
            # prune occasionally (cheap)
            cutoff = now - self._dedup_window
            for k, (t, _) in list(self._dedup.items()):
                if t < cutoff:
                    self._dedup.pop(k, None)

            if key in self._dedup:
                last_ts, stable_id = self._dedup[key]
                if now - last_ts <= self._dedup_window:
                    # Merge: reuse stable id, refresh ts/expires_at deterministically
                    evt.id = stable_id
                    evt.ts = now
                    evt.expires_at = now + timedelta(milliseconds=int(evt.ttl_ms))
                    # Merge volume best-effort
                    if evt.volume and evt.volume.pps is not None:
                        evt.volume.pps = int(evt.volume.pps)
                    if evt.volume and evt.volume.bps is not None:
                        evt.volume.bps = int(evt.volume.bps)
                self._dedup[key] = (now, stable_id)
            else:
                self._dedup[key] = (now, evt.id)

        # Publish to bus + aggregator
        await self.bus.publish(evt)
        self.agg.add(evt)
        return evt


_RUNTIME: ThreatMapRuntime | None = None


def get_runtime() -> ThreatMapRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = ThreatMapRuntime()
        logger.info("ThreatMapRuntime initialized (TELEMETRY_MODE=%s)", _RUNTIME.cfg.telemetry_mode)
    return _RUNTIME


