from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict

from .schema import AttackEvent, Aggregates, HeatBucket


def _window_to_timedelta(window: str) -> timedelta:
    w = (window or "5m").strip().lower()
    if w in ("5m", "5min", "300s"):
        return timedelta(minutes=5)
    if w in ("15m", "15min", "900s"):
        return timedelta(minutes=15)
    if w in ("1h", "60m", "3600s"):
        return timedelta(hours=1)
    # default
    return timedelta(minutes=5)


def _grid_bucket(
    lat: float, lon: float, lat_step: float = 5.0, lon_step: float = 5.0
) -> tuple[int, int]:
    return (int(lat // lat_step), int(lon // lon_step))


@dataclass
class FilterState:
    window: str = "5m"
    types: set[str] | None = None
    min_severity: int = 1
    major_only: bool = False
    country: str | None = None  # destination country best-effort


class ThreatAggregator:
    """Server-authoritative sliding window aggregator derived from canonical events."""

    def __init__(self, max_history_seconds: int = 3600):
        self._max_age = timedelta(seconds=max_history_seconds)
        self._events: Deque[AttackEvent] = deque()

    def add(self, event: AttackEvent) -> None:
        self._events.append(event)
        self._trim(datetime.now(timezone.utc))

    def _trim(self, now: datetime) -> None:
        cutoff = now - self._max_age
        while self._events and self._events[0].ts < cutoff:
            self._events.popleft()

    def snapshot(
        self, seq: int, window: str = "5m", filters: FilterState | None = None
    ) -> Aggregates:
        now = datetime.now(timezone.utc)
        self._trim(now)
        dt = _window_to_timedelta(filters.window if filters else window)
        cutoff = now - dt

        events = [e for e in self._events if e.ts >= cutoff]
        if filters:
            events = self._apply_filters(events, filters)

        count = len(events)
        eps = count / max(1e-6, dt.total_seconds())

        src_counts: Counter[str] = Counter()
        dst_counts: Counter[str] = Counter()
        type_counts: Counter[str] = Counter()
        sev_counts: Counter[int] = Counter()

        heat: Dict[
            tuple[int, int], tuple[int, int]
        ] = {}  # (lat_bin,lon_bin) -> (count,sevs)

        for e in events:
            src_key = (
                e.src.geo.country
                if e.src.geo and e.src.geo.country
                else (e.src.ip or "unknown")
            )
            dst_key = (
                e.dst.geo.country
                if e.dst.geo and e.dst.geo.country
                else (e.dst.ip or "unknown")
            )
            src_counts[src_key] += 1
            dst_counts[dst_key] += 1
            # Prefer enum value for stable UI semantics
            at = getattr(e.attack_type, "value", None)
            type_counts[str(at or e.attack_type)] += 1
            sev_counts[int(e.severity)] += 1

            # heat uses destination geo if present
            if e.dst.geo and e.dst.geo.lat is not None and e.dst.geo.lon is not None:
                b = _grid_bucket(float(e.dst.geo.lat), float(e.dst.geo.lon))
                c, s = heat.get(b, (0, 0))
                heat[b] = (c + 1, s + int(e.severity))

        heat_list = [
            HeatBucket(lat_bin=k[0], lon_bin=k[1], count=v[0], severity_sum=v[1])
            for k, v in heat.items()
        ]

        by_severity = [(sev, sev_counts.get(sev, 0)) for sev in range(1, 11)]

        return Aggregates(
            window=(filters.window if filters else window),
            server_ts=now,
            seq=seq,
            count=count,
            eps=float(eps),
            top_sources=src_counts.most_common(10),
            top_targets=dst_counts.most_common(10),
            top_types=type_counts.most_common(10),
            by_severity=by_severity,
            heat=heat_list,
        )

    def _apply_filters(
        self, events: list[AttackEvent], f: FilterState
    ) -> list[AttackEvent]:
        out = events
        if f.types:
            out = [e for e in out if str(e.attack_type) in f.types]
        if f.major_only:
            out = [e for e in out if e.is_major]
        if f.min_severity > 1:
            out = [e for e in out if e.severity >= f.min_severity]
        if f.country:
            q = f.country.strip().lower()
            out = [
                e
                for e in out
                if (
                    e.dst.geo
                    and e.dst.geo.country
                    and q in str(e.dst.geo.country).lower()
                )
            ]
        return out
