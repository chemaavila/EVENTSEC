"""Minimal mock collector for agent tests and smoke harness."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class MockCollectorState:
    output_path: Path
    delay_secs: float = 0.0
    fail_first_status: Optional[int] = None
    _failed_once: bool = False
    received: list[dict[str, Any]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def should_fail(self) -> Optional[int]:
        if self.fail_first_status is None:
            return None
        with self.lock:
            if self._failed_once:
                return None
            self._failed_once = True
            return self.fail_first_status

    def record(self, payload: dict[str, Any]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False)
        with self.lock:
            self.received.append(payload)
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{line}\n")


def _parse_fail_first(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return 401
    if normalized.isdigit():
        return int(normalized)
    return 401


def _build_handler(state: MockCollectorState) -> Callable[..., BaseHTTPRequestHandler]:
    class MockCollectorHandler(BaseHTTPRequestHandler):
        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else None
            except json.JSONDecodeError:
                body = raw.decode("utf-8", errors="ignore")
            return {
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
            }

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            response = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def do_POST(self) -> None:  # noqa: N802
            if state.delay_secs:
                time.sleep(state.delay_secs)
            if self.path in {"/events", "/agent/heartbeat"} or self.path.startswith(
                "/sca/"
            ) or self.path.startswith("/inventory/"):
                payload = self._read_json()
                state.record(payload)
                failure = state.should_fail()
                if failure:
                    self._send_json(failure, {"status": "fail-first"})
                    return
                self._send_json(200, {"status": "ok"})
                return
            self.send_error(404, "Not Found")

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/agent/actions"):
                self._send_json(200, [])
                return
            self.send_error(404, "Not Found")

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return MockCollectorHandler


def start_mock_collector(
    host: str = "127.0.0.1",
    port: int = 0,
    output_path: Optional[Path] = None,
    fail_first_status: Optional[int] = None,
    delay_secs: float = 0.0,
) -> Tuple[HTTPServer, threading.Thread, MockCollectorState]:
    output_path = output_path or Path("artifacts/mock_collector_received.jsonl")
    state = MockCollectorState(
        output_path=output_path, delay_secs=delay_secs, fail_first_status=fail_first_status
    )
    handler = _build_handler(state)
    server = HTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, state


def _env_bool(value: Optional[str]) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def main() -> None:
    port = int(os.getenv("MOCK_COLLECTOR_PORT", "0"))
    output_path = Path(
        os.getenv("MOCK_COLLECTOR_OUT", "artifacts/mock_collector_received.jsonl")
    )
    delay_secs = float(os.getenv("MOCK_DELAY_SECS", "0"))
    fail_first = _parse_fail_first(
        os.getenv("MOCK_FAIL_FIRST") or os.getenv("MOCK_COLLECTOR_FAIL_FIRST")
    )

    server, _, _ = start_mock_collector(
        port=port,
        output_path=output_path,
        fail_first_status=fail_first,
        delay_secs=delay_secs,
    )
    port_file = os.getenv("MOCK_COLLECTOR_PORT_FILE")
    if port_file:
        Path(port_file).write_text(str(server.server_address[1]), encoding="utf-8")

    if _env_bool(os.getenv("MOCK_COLLECTOR_VERBOSE")):
        print(f"mock collector listening on {server.server_address}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
