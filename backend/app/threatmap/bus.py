from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, List

from .config import ThreatMapConfig
from .schema import AttackEvent


@dataclass
class PublishedEvent:
    seq: int
    server_ts: datetime
    event: AttackEvent


class ThreatEventBus:
    """In-memory pubsub bus with replay ring buffer (time-based)."""

    def __init__(self, cfg: ThreatMapConfig):
        self._cfg = cfg
        self._seq = 0
        self._subs: List[asyncio.Queue[PublishedEvent]] = []
        self._replay: Deque[PublishedEvent] = deque()
        self._lock = asyncio.Lock()

    def next_seq(self) -> int:
        self._seq += 1
        return self._seq

    async def subscribe(self, max_queue: int = 2000) -> asyncio.Queue[PublishedEvent]:
        q: asyncio.Queue[PublishedEvent] = asyncio.Queue(maxsize=max_queue)
        async with self._lock:
            self._subs.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue[PublishedEvent]) -> None:
        async with self._lock:
            self._subs = [s for s in self._subs if s is not q]

    def _trim_replay(self, now: datetime) -> None:
        cutoff = now.timestamp() - self._cfg.replay_seconds
        while self._replay and self._replay[0].server_ts.timestamp() < cutoff:
            self._replay.popleft()

    async def publish(self, event: AttackEvent) -> PublishedEvent:
        server_ts = datetime.now(timezone.utc)
        seq = self.next_seq()
        event.seq = seq
        event.server_ts = server_ts
        pub = PublishedEvent(seq=seq, server_ts=server_ts, event=event)

        # Replay buffer
        self._replay.append(pub)
        self._trim_replay(server_ts)

        # Fan-out (best-effort; do not block publisher forever)
        async with self._lock:
            subs = list(self._subs)

        for q in subs:
            try:
                q.put_nowait(pub)
            except asyncio.QueueFull:
                # Backpressure: drop for that subscriber; server will switch them to agg-only.
                pass

        return pub

    def replay(self) -> List[PublishedEvent]:
        return list(self._replay)
