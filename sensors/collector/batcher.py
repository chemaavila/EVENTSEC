from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List


@dataclass
class Batcher:
    max_events: int
    max_bytes: int
    flush_interval: float
    send_batch: Callable[[List[dict[str, Any]]], None]
    _events: List[dict[str, Any]] = field(default_factory=list)
    _last_flush: float = field(default_factory=time.monotonic)

    def add(self, event: dict[str, Any]) -> None:
        self._events.append(event)
        if self._should_flush():
            self.flush()

    def _should_flush(self) -> bool:
        if not self._events:
            return False
        if len(self._events) >= self.max_events:
            return True
        if self._estimate_size() >= self.max_bytes:
            return True
        if time.monotonic() - self._last_flush >= self.flush_interval:
            return True
        return False

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(event)) for event in self._events)

    def flush(self) -> None:
        if not self._events:
            return
        self.send_batch(self._events)
        self._events = []
        self._last_flush = time.monotonic()
