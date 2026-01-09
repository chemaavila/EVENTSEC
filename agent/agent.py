import argparse
import json
import logging
import os
import platform
import random
import shutil
import socket
import secrets
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

# Import strategy:
# - Preferred runtime: `python -m agent` (package context)
# - Also support direct execution: `python agent/agent.py` (script context)
try:  # pragma: no cover
    from agent.os_paths import (
        ensure_dirs,
        get_config_path,
        get_logs_path,
        get_status_path,
    )
except Exception:  # pragma: no cover
    from .os_paths import ensure_dirs, get_config_path, get_logs_path, get_status_path


# Global paths (set by CLI args or defaults)
CONFIG_FILE: Optional[Path] = None
LOG_PATH: Optional[Path] = None
STATUS_FILE: Optional[Path] = None

_start_time = time.time()
_status_cache: dict[str, Any] = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "pid": os.getpid(),
    "running": True,
    "uptime_seconds": 0,
    "events_processed": 0,
    "last_error": None,
    "version": "0.3.0",
    "mode": "foreground",
}


def _update_status(**overrides: Any) -> None:
    """Update status.json with current state."""
    global _status_cache
    _status_cache.update(overrides)
    _status_cache["timestamp"] = datetime.now(timezone.utc).isoformat()
    _status_cache["uptime_seconds"] = int(time.time() - _start_time)
    _status_cache["pid"] = os.getpid()

    if STATUS_FILE:
        try:
            STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATUS_FILE.write_text(
                json.dumps(_status_cache, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            if LOGGER:
                LOGGER.debug("Unable to write status file: %s", exc)


def _setup_logger(log_file_path: Optional[Path] = None) -> logging.Logger:
    """Setup logger with file handler. Console logging is optional."""
    logger = logging.getLogger("eventsec-agent")
    if logger.handlers:
        return logger

    log_level = os.getenv("EVENTSEC_AGENT_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    # File handler (always)
    if log_file_path:
        try:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # Fallback to home directory
            fallback_dir = Path.home() / ".eventsec-agent"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            fallback_log = fallback_dir / "agent.log"
            file_handler = RotatingFileHandler(
                fallback_log, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # Console handler (optional, only if TTY or DEBUG env set)
    stream_required = bool(os.getenv("EVENTSEC_AGENT_DEBUG"))
    if not stream_required:
        stdout = getattr(sys, "stdout", None)
        stream_required = bool(stdout and hasattr(stdout, "isatty") and stdout.isatty())
    if stream_required:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.propagate = False
    return logger


# Initialize logger at module level to ensure it's never None
# This allows library usage (e.g., in tests) without requiring main() initialization
LOGGER: logging.Logger = logging.getLogger("eventsec-agent")

# Configuración por defecto (se puede sobrescribir vía archivo/env)
def _build_default_config() -> Dict[str, Any]:
    return {
        "api_url": "https://localhost:8000",
        "agent_token": secrets.token_urlsafe(32),
        "interval": 60,
        "browser_poll_interval": 10,
        "agent_id": None,
        "agent_api_key": None,
        "enrollment_key": "eventsec-enroll",
        "log_paths": [] if platform.system() == "Windows" else [
            "/var/log/system.log",
            "/var/log/syslog",
        ],
    }


DEFAULT_CONFIG = _build_default_config()


def _ensure_config_file(path: Path) -> None:
    """Ensure config file exists, creating default if missing."""
    if path.exists():
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        default_config = _build_default_config()
        global DEFAULT_CONFIG
        DEFAULT_CONFIG = default_config
        path.write_text(json.dumps(default_config, indent=2), encoding="utf-8")
        # Use module-level logger (always available, even if unconfigured)
        logger = logging.getLogger("eventsec-agent")
        logger.info(
            "Created default config at %s. Update api_url/enrollment_key before running in production.",
            path,
        )
    except OSError as exc:
        logger = logging.getLogger("eventsec-agent")
        logger.warning("Unable to write config file %s: %s", path, exc)


def load_agent_config(
    config_path: Optional[Path] = None,
) -> tuple[Dict[str, Any], Path]:
    """Load agent config from file or create default."""
    if config_path is None:
        config_path = get_config_path()

    ensure_dirs()
    _ensure_config_file(config_path)

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            user_cfg = json.load(handle)
            merged = DEFAULT_CONFIG.copy()
            merged.update({k: v for k, v in user_cfg.items() if v is not None})
            return merged, config_path
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.warning("Unable to parse %s: %s", config_path, exc)
        return DEFAULT_CONFIG.copy(), config_path


CONFIG: Dict[str, Any] = {}


def persist_config() -> None:
    """Persist current config to file."""
    if not CONFIG_FILE:
        return
    try:
        CONFIG_FILE.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
    except OSError as exc:
        if LOGGER:
            LOGGER.warning("Unable to persist configuration: %s", exc)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a config value, checking env vars first."""
    env_key = f"EVENTSEC_AGENT_{key.upper()}"
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val
    return CONFIG.get(key, default)


def maybe_prompt_for_config() -> None:
    """First-run wizard so installers can set backend URL/token without editing files."""
    if not sys.stdin.isatty():
        return
    
    current_url = get_config_value("api_url", "https://localhost:8000")
    current_token = get_config_value("agent_token", "")
    current_interval = get_config_value("interval", 60)
    current_enrollment = get_config_value("enrollment_key", "eventsec-enroll")

    print(
        "[agent] Interactive configuration wizard (press Enter to keep current value)"
    )
    new_url = input(f"Backend URL [{current_url}]: ").strip() or current_url
    new_token = (
        input(f"Agent token [{current_token or 'none'}]: ").strip() or current_token
    )
    new_interval = input(f"Heartbeat interval seconds [{current_interval}]: ").strip()
    new_enrollment = (
        input(f"Enrollment key [{current_enrollment or 'none'}]: ").strip()
        or current_enrollment
    )

    try:
        interval_value = int(new_interval) if new_interval else current_interval
    except ValueError:
        interval_value = current_interval

    CONFIG.update(
        {
            "api_url": new_url,
            "agent_token": new_token,
            "interval": interval_value,
            "enrollment_key": new_enrollment,
        }
    )
    persist_config()


def now_utc_iso() -> str:
    """Devuelve la hora actual en UTC en formato ISO 8601, con zona horaria."""
    return datetime.now(timezone.utc).isoformat()


def get_basic_host_info() -> Dict[str, str]:
    """Información mínima del host para SIEM/EDR."""
    hostname = socket.gethostname()
    username = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
    system = platform.system()
    release = platform.release()
    return {
        "hostname": hostname,
        "username": username,
        "os": system,
        "os_version": release,
    }


# ---------------------------------------------------------------------------
# Construcción de payloads para cada módulo
# ---------------------------------------------------------------------------


def build_status_event(status: str) -> Dict[str, Any]:
    """Single status event to indicate connectivity."""
    host = get_basic_host_info()
    return {
        "event_type": "agent_status",
        "severity": "info",
        "category": "status",
        "details": {
            "status": status,
            "hostname": host["hostname"],
            "username": host["username"],
            "os": host["os"],
            "os_version": host["os_version"],
            "timestamp": now_utc_iso(),
        },
    }


# ---------------------------------------------------------------------------
# Funciones de envío
# ---------------------------------------------------------------------------


def _inject_host_details(event: Dict[str, Any], host: Dict[str, str]) -> None:
    details = event.get("details")
    if not isinstance(details, dict):
        details = {"raw": details}

    details.setdefault("hostname", host.get("hostname", "unknown"))
    details.setdefault("username", host.get("username", "unknown"))
    details.setdefault("os", host.get("os", platform.system()))
    details.setdefault("os_version", host.get("os_version", platform.release()))
    details.setdefault("received_time", now_utc_iso())
    event["details"] = details

    if not event.get("message"):
        event["message"] = details.get("message") or f"{event.get('event_type', 'event')} event"


def post_json(path: str, payload: Dict[str, Any]) -> None:
    """Helper genérico para POST JSON con manejo de errores."""
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    url = f"{api_url}{path}"
    try:
        resp = requests.post(url, json=payload, headers=agent_headers(), timeout=5)
        if resp.ok:
            if LOGGER:
                LOGGER.info("POST %s -> %s", path, resp.status_code)
        else:
            if LOGGER:
                LOGGER.warning(
                    "Error POST %s: %s %s", path, resp.status_code, resp.text
                )
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed POST %s: %s", path, exc)


def fetch_pending_actions(hostname: str) -> list[Dict[str, Any]]:
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    url = f"{api_url}/agent/actions"
    params = {"hostname": hostname}
    try:
        resp = requests.get(url, params=params, headers=agent_headers(), timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.warning("Failed to fetch actions: %s", exc)
        return []


def complete_action(action_id: int, success: bool, output: str) -> None:
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    url = f"{api_url}/agent/actions/{action_id}/complete"
    payload = {"success": success, "output": output}
    try:
        resp = requests.post(url, json=payload, headers=agent_headers(), timeout=5)
        if not resp.ok:
            if LOGGER:
                LOGGER.warning(
                    "Failed to ack action %s: %s %s",
                    action_id,
                    resp.status_code,
                    resp.text,
                )
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Error completing action %s: %s", action_id, exc)


def process_actions(hostname: str) -> None:
    actions = fetch_pending_actions(hostname)
    for action in actions:
        action_type = action.get("action_type")
        LOGGER.info(
            "Executing action #%s (%s) on %s", action["id"], action_type, hostname
        )
        time.sleep(1)
        if action_type == "isolate":
            output = "Network interfaces disabled"
            success = True
        elif action_type == "release":
            output = "Network isolation removed"
            success = True
        elif action_type == "reboot":
            output = "System reboot triggered"
            success = True
        elif action_type == "command":
            output = f"Executed command: {action.get('parameters', {}).get('command', 'N/A')}"
            success = True
        elif action_type == "malware_scan":
            host = get_basic_host_info()
            success, output = run_malware_scan(action.get("parameters", {}), host)
        else:
            output = "Action acknowledged"
            success = True
        complete_action(action["id"], success, output)


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------


def agent_headers() -> Dict[str, str]:
    """
    Headers for authenticated agent requests.

    Agent auth MUST NOT use the Authorization header (reserved for user JWTs).

    Preferred order:
    - Per-agent key (post-enrollment): X-Agent-Key
    - Shared token (bootstrap / legacy): X-Agent-Token
    """
    headers: Dict[str, str] = {}

    agent_api_key = get_config_value("agent_api_key")
    if agent_api_key:
        headers["X-Agent-Key"] = str(agent_api_key)
    else:
        agent_token = get_config_value("agent_token")
        if agent_token:
            headers["X-Agent-Token"] = str(agent_token)

    if not headers:
        raise RuntimeError(
            "Agent has no auth configured. Set agent_api_key (preferred, via enrollment) "
            "or agent_token (shared token) in agent_config.json."
        )

    return headers


def enroll_if_needed(host: Dict[str, str]) -> None:
    """Enroll agent if not already enrolled."""
    agent_id = get_config_value("agent_id")
    agent_api_key = get_config_value("agent_api_key")
    if agent_id and agent_api_key:
        return

    enrollment_key = get_config_value("enrollment_key")
    if not enrollment_key:
        raise RuntimeError("Missing enrollment key (set EVENTSEC_AGENT_ENROLL_KEY or enrollment_key in config)")
    
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    payload = {
        "name": host["hostname"],
        "os": host["os"],
        "ip_address": host.get("ip_address") or socket.gethostbyname(host["hostname"]),
        "version": "eventsec-agent-demo",
        "enrollment_key": enrollment_key,
    }
    try:
        resp = requests.post(f"{api_url}/agents/enroll", json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Enrollment failed: {exc}") from exc

    data = resp.json()
    CONFIG["agent_id"] = data["agent_id"]
    CONFIG["agent_api_key"] = data["api_key"]
    persist_config()
    if LOGGER:
        LOGGER.info("Enrolled successfully with ID %s", data["agent_id"])


def ensure_enrolled(host: Dict[str, str]) -> bool:
    """Ensure the agent is enrolled before sending events."""
    agent_id = get_config_value("agent_id")
    agent_api_key = get_config_value("agent_api_key")
    if agent_id and agent_api_key:
        return True
    try:
        enroll_if_needed(host)
    except Exception as exc:
        if LOGGER:
            LOGGER.error("Enrollment required before sending events: %s", exc)
        _update_status(last_error=str(exc))
        return False
    return True


def send_heartbeat(host: Dict[str, str]) -> None:
    """Send heartbeat to backend."""
    agent_id = get_config_value("agent_id")
    agent_api_key = get_config_value("agent_api_key")
    if not agent_id or not agent_api_key:
        if LOGGER:
            LOGGER.warning("Cannot send heartbeat: agent not enrolled")
        return
    
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    payload = {
        "version": "eventsec-agent-demo",
        "ip_address": socket.gethostbyname(host["hostname"]),
        "status": "online",
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = requests.post(
            f"{api_url}/agent/heartbeat",
            json=payload,
            headers=agent_headers(),
            timeout=5,
        )
        if not resp.ok:
            if LOGGER:
                LOGGER.warning("Heartbeat error: %s %s", resp.status_code, resp.text)
        else:
            if LOGGER:
                LOGGER.info("Heartbeat acknowledged")
        _update_status(
            last_heartbeat=datetime.now(timezone.utc).isoformat(), last_error=None
        )
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed to send heartbeat: %s", exc)
        _update_status(last_error=str(exc))


def ensure_enrolled(host: Dict[str, str]) -> bool:
    try:
        enroll_if_needed(host)
        return True
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.warning("Enrollment not complete yet: %s", exc)
        _update_status(last_error=str(exc))
        return False


def send_event(event: Dict[str, Any], host: Dict[str, str]) -> None:
    """Send event to backend."""
    if not ensure_enrolled(host):
        return

    _inject_host_details(event, host)
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
    try:
        resp = requests.post(
            f"{api_url}/events",
            json=event,
            headers=agent_headers(),
            timeout=5,
        )
        if resp.status_code in {401, 403}:
            if LOGGER:
                LOGGER.warning("Event ingest unauthorized, re-enrolling and retrying...")
            if ensure_enrolled(host):
                resp = requests.post(
                    f"{api_url}/events",
                    json=event,
                    headers=agent_headers(),
                    timeout=5,
                )

        if not resp.ok:
            if LOGGER:
                LOGGER.warning("Event ingest error: %s %s", resp.status_code, resp.text)
            return

        _update_status(
            events_processed=_status_cache.get("events_processed", 0) + 1,
            last_error=None,
        )
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed to send event: %s", exc)
        _update_status(last_error=str(exc))


def _get_url_state_path() -> Path:
    base = STATUS_FILE or get_status_path()
    return base.with_name("browser_history_state.json")


def _load_url_state(state_path: Path) -> Dict[str, Dict[str, int]]:
    if not state_path.exists():
        return {"chromium": {}, "firefox": {}}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid state data")
        data.setdefault("chromium", {})
        data.setdefault("firefox", {})
        return {
            "chromium": {str(k): int(v) for k, v in data.get("chromium", {}).items()},
            "firefox": {str(k): int(v) for k, v in data.get("firefox", {}).items()},
        }
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.warning("Failed to load URL state: %s", exc)
        return {"chromium": {}, "firefox": {}}


def _save_url_state(state_path: Path, state: Dict[str, Dict[str, int]]) -> None:
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as exc:
        if LOGGER:
            LOGGER.warning("Unable to persist URL state: %s", exc)


def _extract_domain_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.scheme:
        host = parsed.hostname
    else:
        parsed = urlparse(f"//{url}")
        host = parsed.hostname
    return host.lower() if host else None


def _chromium_time_to_iso(value: int) -> str:
    chromium_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    return (chromium_epoch + timedelta(microseconds=value)).isoformat()


def _firefox_time_to_iso(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc).isoformat()


def _safe_sqlite_rows(path: Path, query: str, params: tuple[Any, ...]) -> list[tuple]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "history.sqlite"
            shutil.copy2(path, temp_path)
            with sqlite3.connect(temp_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.debug("Failed to read history from %s: %s", path, exc)
        return []


def _find_chromium_history_paths() -> list[tuple[Path, str, str]]:
    system = platform.system()
    home = Path.home()
    paths: list[tuple[Path, str, str]] = []

    if system == "Windows":
        local = Path(os.getenv("LOCALAPPDATA", ""))
        candidates = [
            (local / "Google/Chrome/User Data", "chrome"),
            (local / "Chromium/User Data", "chromium"),
            (local / "Microsoft/Edge/User Data", "edge"),
        ]
    elif system == "Darwin":
        base = home / "Library/Application Support"
        candidates = [
            (base / "Google/Chrome", "chrome"),
            (base / "Chromium", "chromium"),
            (base / "Microsoft Edge", "edge"),
        ]
    else:
        base = home / ".config"
        candidates = [
            (base / "google-chrome", "chrome"),
            (base / "chromium", "chromium"),
            (base / "microsoft-edge", "edge"),
        ]

    for root, browser in candidates:
        if not root.exists():
            continue
        for history_path in root.glob("*/History"):
            if history_path.is_file():
                profile = history_path.parent.name
                paths.append((history_path, browser, profile))
    return paths


def _find_firefox_history_paths() -> list[tuple[Path, str]]:
    system = platform.system()
    home = Path.home()
    paths: list[tuple[Path, str]] = []

    if system == "Windows":
        base = Path(os.getenv("APPDATA", "")) / "Mozilla/Firefox/Profiles"
    elif system == "Darwin":
        base = home / "Library/Application Support/Firefox/Profiles"
    else:
        base = home / ".mozilla/firefox"

    if not base.exists():
        return []
    for history_path in base.glob("*.default*/places.sqlite"):
        if history_path.is_file():
            profile = history_path.parent.name
            paths.append((history_path, profile))
    return paths


def collect_url_visit_events(host: Dict[str, str]) -> list[Dict[str, Any]]:
    state_path = _get_url_state_path()
    state = _load_url_state(state_path)
    events: list[Dict[str, Any]] = []

    for history_path, browser, profile in _find_chromium_history_paths():
        last_seen = state["chromium"].get(str(history_path), 0)
        rows = _safe_sqlite_rows(
            history_path,
            "SELECT url, last_visit_time FROM urls WHERE last_visit_time > ? "
            "ORDER BY last_visit_time ASC LIMIT 200",
            (last_seen,),
        )
        max_seen = last_seen
        for url, last_visit_time in rows:
            if not url or not last_visit_time:
                continue
            max_seen = max(max_seen, int(last_visit_time))
            events.append(
                {
                    "event_type": "edr.url_visit",
                    "severity": "low",
                    "category": "edr",
                    "message": f"URL visit: {url}",
                    "details": {
                        "url": url,
                        "domain": _extract_domain_from_url(url),
                        "browser": browser,
                        "profile": profile,
                        "action": "visit",
                        "visit_time": _chromium_time_to_iso(int(last_visit_time)),
                    },
                }
            )
        if max_seen > last_seen:
            state["chromium"][str(history_path)] = max_seen

    for history_path, profile in _find_firefox_history_paths():
        last_seen = state["firefox"].get(str(history_path), 0)
        rows = _safe_sqlite_rows(
            history_path,
            "SELECT url, last_visit_date FROM moz_places WHERE last_visit_date > ? "
            "ORDER BY last_visit_date ASC LIMIT 200",
            (last_seen,),
        )
        max_seen = last_seen
        for url, last_visit_date in rows:
            if not url or not last_visit_date:
                continue
            max_seen = max(max_seen, int(last_visit_date))
            events.append(
                {
                    "event_type": "edr.url_visit",
                    "severity": "low",
                    "category": "edr",
                    "message": f"URL visit: {url}",
                    "details": {
                        "url": url,
                        "domain": _extract_domain_from_url(url),
                        "browser": "firefox",
                        "profile": profile,
                        "action": "visit",
                        "visit_time": _firefox_time_to_iso(int(last_visit_date)),
                    },
                }
            )
        if max_seen > last_seen:
            state["firefox"][str(history_path)] = max_seen

    _save_url_state(state_path, state)
    return events


def emit_test_url(url: str, host: Dict[str, str]) -> None:
    event = {
        "event_type": "edr.url_visit",
        "severity": "low",
        "category": "edr",
        "message": f"URL visit: {url}",
        "details": {
            "url": url,
            "domain": _extract_domain_from_url(url) or "unknown",
            "browser": "cli",
            "profile": "manual",
            "action": "visit",
            "visit_time": now_utc_iso(),
        },
    }
    send_event(event, host)


def _find_defender() -> Optional[Path]:
    candidate = shutil.which("MpCmdRun.exe")
    if candidate:
        return Path(candidate)
    program_files = Path(os.getenv("ProgramFiles", "C:\\Program Files"))
    fallback = program_files / "Windows Defender/MpCmdRun.exe"
    if fallback.exists():
        return fallback
    program_data = Path(os.getenv("ProgramData", "C:\\ProgramData"))
    platform_root = program_data / "Microsoft/Windows Defender/Platform"
    if platform_root.exists():
        matches = sorted(platform_root.glob("*/MpCmdRun.exe"), reverse=True)
        if matches:
            return matches[0]
    return None


def _truncate_output(output: str, max_chars: int) -> str:
    if len(output) <= max_chars:
        return output
    return output[:max_chars] + "\n...[truncated]"


def run_malware_scan(parameters: Dict[str, Any], host: Dict[str, str]) -> tuple[bool, str]:
    start_time = time.time()
    engine = str(parameters.get("engine") or "auto").lower()
    if engine == "auto":
        engine = "defender" if platform.system() == "Windows" else "clamav"

    path = parameters.get("path") or "DEFAULT"
    if not path or path == "DEFAULT":
        path = str(Path.home())
    recursive = bool(parameters.get("recursive", True))
    timeout_seconds = int(parameters.get("timeout_seconds", 900))
    max_output_chars = int(parameters.get("max_output_chars", 20000))
    exclude = parameters.get("exclude") or []
    quarantine = bool(parameters.get("quarantine", False))

    scan_details: Dict[str, Any] = {
        "engine": engine,
        "path": path,
        "recursive": recursive,
        "exclude": exclude,
        "quarantine_requested": quarantine,
    }
    detections: list[Dict[str, Any]] = []
    infected: Optional[bool] = None
    infected_count = 0
    output = ""
    success = True

    if engine == "defender":
        defender_path = _find_defender()
        if not defender_path:
            success = False
            output = "Microsoft Defender not available. Enable Windows Defender or install a supported scanner."
            scan_details["error"] = "defender_not_available"
        else:
            cmd = [str(defender_path), "-Scan", "-ScanType", "3", "-File", path]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                output = (result.stdout or "") + (result.stderr or "")
                output = _truncate_output(output, max_output_chars)
                lowered = output.lower()
                if "no threats" in lowered or "no threat" in lowered:
                    infected = False
                elif "threat" in lowered or "threats" in lowered or "found" in lowered:
                    infected = True
                    detections.append(
                        {
                            "engine": "defender",
                            "file_path": "unknown",
                            "malware_name": "unknown",
                            "action_taken": "none",
                            "scan_path": path,
                        }
                    )
                else:
                    infected = None
                if result.returncode not in (0, 2):
                    success = False
            except subprocess.TimeoutExpired:
                success = False
                output = "Scan timed out before completion."
                scan_details["error"] = "timeout"
    elif engine == "clamav":
        clamscan = shutil.which("clamscan")
        if not clamscan:
            success = False
            output = "ClamAV not available. Install clamscan to enable malware scanning."
            scan_details["error"] = "clamav_not_available"
        else:
            cmd = [clamscan]
            if recursive:
                cmd.append("-r")
            for value in exclude:
                cmd.extend(["--exclude", str(value)])
            cmd.append(path)
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                output = (result.stdout or "") + (result.stderr or "")
                output = _truncate_output(output, max_output_chars)
                infected_lines = [
                    line
                    for line in output.splitlines()
                    if line.strip().endswith("FOUND")
                ]
                detections = [
                    {
                        "engine": "clamav",
                        "file_path": line.split(":")[0].strip(),
                        "malware_name": line.split(":")[1].replace("FOUND", "").strip()
                        if ":" in line
                        else "unknown",
                        "action_taken": "none",
                        "scan_path": path,
                    }
                    for line in infected_lines
                ]
                infected_count = len(detections)
                if result.returncode == 0:
                    infected = False
                elif result.returncode == 1:
                    infected = True
                else:
                    infected = None
                    success = False
                    scan_details["error"] = "clamav_error"
            except subprocess.TimeoutExpired:
                success = False
                output = "Scan timed out before completion."
                scan_details["error"] = "timeout"
    else:
        success = False
        output = f"Unknown scan engine: {engine}"
        scan_details["error"] = "invalid_engine"

    if infected:
        infected_count = infected_count or len(detections)

    duration_ms = int((time.time() - start_time) * 1000)
    scan_details.update(
        {
            "duration_ms": duration_ms,
            "infected": infected,
            "infected_count": infected_count,
        }
    )

    if infected is None:
        scan_details["scan_result"] = "unknown"

    summary_event = {
        "event_type": "edr.malware_scan",
        "severity": "high" if infected else "info",
        "category": "edr",
        "message": f"Malware scan completed using {engine}",
        "details": scan_details,
    }
    send_event(summary_event, host)

    for detection in detections:
        detection_event = {
            "event_type": "edr.malware_detection",
            "severity": "critical",
            "category": "edr",
            "message": f"Malware detected: {detection.get('malware_name', 'unknown')}",
            "details": detection,
        }
        send_event(detection_event, host)

    status_label = (
        "infected"
        if infected
        else "clean"
        if infected is False
        else "unknown"
    )
    summary = (
        f"Scan engine: {engine}\n"
        f"Target: {path}\n"
        f"Result: {status_label}\n"
        f"Infected count: {infected_count}\n"
        "If malware is detected, isolate the host and investigate immediately."
    )
    if not success:
        summary = f"{summary}\nScan error: {output or scan_details.get('error')}"
    return success, summary


class FileTailer:
    def __init__(self, path: str):
        self.path = Path(path)
        self.position = 0
        self.inode = None

    def _stat_fingerprint(self):
        try:
            stat = self.path.stat()
            return (stat.st_ino, stat.st_dev, stat.st_size)
        except FileNotFoundError:
            return None

    def read_new_lines(self) -> list[str]:
        fingerprint = self._stat_fingerprint()
        if fingerprint is None:
            self.position = 0
            self.inode = None
            return []

        if self.inode != fingerprint[:2] or fingerprint[2] < self.position:
            self.position = 0
            self.inode = fingerprint[:2]

        lines: list[str] = []
        try:
            with self.path.open("r", encoding="utf-8", errors="ignore") as handle:
                handle.seek(self.position)
                for line in handle:
                    line = line.rstrip("\n")
                    if line:
                        lines.append(line)
                self.position = handle.tell()
        except OSError as exc:
            LOGGER.warning("Failed to read %s: %s", self.path, exc)
        return lines


class LogCollector:
    def __init__(self, paths: list[str]):
        """Initialize log collector. Filters out paths that don't exist or aren't accessible."""
        self.tailers = []
        for path_str in paths:
            if not path_str:
                continue
            path_obj = Path(path_str)
            # Guard: skip /var/log on Windows
            if platform.system() == "Windows" and "/var/log" in str(path_obj):
                if LOGGER:
                    LOGGER.warning("Skipping Unix log path on Windows: %s", path_str)
                continue
            # Check if path exists and is readable
            try:
                if path_obj.exists() and path_obj.is_file():
                    self.tailers.append(FileTailer(path_str))
                elif LOGGER:
                    LOGGER.debug(
                        "Log path does not exist or is not a file: %s", path_str
                    )
            except (OSError, PermissionError) as exc:
                if LOGGER:
                    LOGGER.warning("Cannot access log path %s: %s", path_str, exc)

    def collect(self) -> list[Dict[str, Any]]:
        events: list[Dict[str, Any]] = []
        for tailer in self.tailers:
            try:
                for line in tailer.read_new_lines():
                    lower = line.lower()
                    severity = "low"
                    if any(
                        keyword in lower for keyword in ("error", "fail", "critical")
                    ):
                        severity = "high"
                    elif "warn" in lower:
                        severity = "medium"
                    events.append(
                        {
                            "event_type": "logcollector",
                            "severity": severity,
                            "category": str(tailer.path),
                            "details": {
                                "path": str(tailer.path),
                                "message": line,
                            },
                        }
                    )
            except (OSError, PermissionError) as exc:
                if LOGGER:
                    LOGGER.warning("Failed to read from %s: %s", tailer.path, exc)
        return events


def build_inventory_snapshots(host: Dict[str, Any]) -> list[Dict[str, Any]]:
    hardware = {
        "hostname": host["hostname"],
        "os": host["os"],
        "os_version": host["os_version"],
        "cpu": platform.processor() or "Unknown CPU",
        "architecture": platform.machine(),
        "memory_gb": 16,
    }
    software = [
        {"name": "OpenSSL", "version": "1.0.2"},
        {"name": "EventSec Agent", "version": "0.3.0"},
        {"name": "Python", "version": platform.python_version()},
    ]
    network = {
        "interfaces": [
            {
                "name": "eth0",
                "ip": host.get("ip_address", socket.gethostbyname(host["hostname"])),
            },
        ]
    }
    processes = [
        {"name": "eventsec-agent", "pid": os.getpid(), "user": host["username"]},
    ]
    snapshots = [
        {"category": "hardware", "data": hardware},
        {"category": "software", "data": software[0]},
        {"category": "software", "data": software[1]},
        {"category": "software", "data": software[2]},
        {"category": "network", "data": network},
        {"category": "process", "data": processes[0]},
    ]
    return snapshots


def send_inventory_snapshots(snapshots: list[Dict[str, Any]]) -> None:
    """Send inventory snapshots to backend."""
    agent_id = get_config_value("agent_id")
    agent_api_key = get_config_value("agent_api_key")
    if not snapshots or not agent_id or not agent_api_key:
        return
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    try:
        resp = requests.post(
            f"{api_url}/inventory/{agent_id}",
            json={"snapshots": snapshots},
            headers=agent_headers(),
            timeout=5,
        )
        if not resp.ok:
            if LOGGER:
                LOGGER.warning(
                    "Inventory push error: %s %s", resp.status_code, resp.text
                )
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed to push inventory: %s", exc)


def send_sca_result() -> None:
    """Send SCA result to backend."""
    agent_id = get_config_value("agent_id")
    agent_api_key = get_config_value("agent_api_key")
    if not agent_id or not agent_api_key:
        return
    api_url = get_config_value("api_url", "https://localhost:8000").rstrip("/")
    passed = random.randint(20, 30)
    failed = random.randint(0, 5)
    payload = {
        "policy_id": "cis-ubuntu-20.04",
        "policy_name": "CIS Ubuntu 20.04 LTS Benchmark",
        "score": max(0, min(100, (passed / max(1, passed + failed)) * 100)),
        "status": "passed" if failed == 0 else "warning",
        "passed_checks": passed,
        "failed_checks": failed,
        "details": {
            "notes": "Sample SCA execution from demo agent",
            "failed_checks": failed,
        },
    }
    try:
        resp = requests.post(
            f"{api_url}/sca/{agent_id}/results",
            json=payload,
            headers=agent_headers(),
            timeout=5,
        )
        if not resp.ok:
            if LOGGER:
                LOGGER.warning("SCA result error: %s %s", resp.status_code, resp.text)
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed to send SCA result: %s", exc)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="EventSec Agent")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument("--status-file", type=str, help="Path to status file")
    parser.add_argument(
        "--run-once", action="store_true", help="Run one iteration and exit (for tests)"
    )
    parser.add_argument(
        "--healthcheck", action="store_true", help="Print health status JSON and exit"
    )
    parser.add_argument(
        "--service", action="store_true", help="Running as service (internal flag)"
    )
    parser.add_argument(
        "--emit-test-url",
        type=str,
        help="Emit a single edr.url_visit event and exit",
    )
    return parser.parse_args()


# Heartbeat freshness threshold (seconds).
#
# NOTE: Must be strictly less than 120s so a 2-minute-old heartbeat is stale
# (see agent/tests/test_healthcheck.py::test_healthcheck_stale_heartbeat).
HEARTBEAT_MAX_AGE_SECONDS = 60


def healthcheck(status_file_path: Optional[Path] = None) -> int:
    """
    Print health status and exit with appropriate code.

    Path resolution order:
    1. Use status_file_path parameter if provided
    2. Use module-level STATUS_FILE global (can be patched by tests)
    3. Fall back to get_status_path() default

    This ensures tests can patch STATUS_FILE and have it respected.
    """
    # Resolve path: parameter > global > default
    if status_file_path is None:
        status_file_path = STATUS_FILE or get_status_path()

    if not status_file_path or not status_file_path.exists():
        print(json.dumps({"status": "unknown", "error": "No status file found"}))
        return 1

    try:
        status_data = json.loads(status_file_path.read_text(encoding="utf-8"))
        print(json.dumps(status_data, indent=2))

        # Check if heartbeat is recent
        timestamp_str = status_data.get("timestamp")
        if not timestamp_str:
            # Deterministic failure: without a timestamp we cannot validate freshness.
            return 1

        # Parse timestamp (handle both Z and +00:00 formats)
        ts_str = timestamp_str.replace("Z", "+00:00")
        # Use datetime from module namespace (respects test mocking of agent.agent.datetime)
        ts = datetime.fromisoformat(ts_str)

        # Get current time (respects test mocking)
        now = datetime.now(timezone.utc)
        age_seconds = (now - ts).total_seconds()

        # Check if running and heartbeat is fresh
        running = status_data.get("running", False)
        if running and age_seconds < HEARTBEAT_MAX_AGE_SECONDS:
            return 0

        return 1
    except Exception:
        # Any parsing/IO error means unhealthy
        return 1


def main() -> None:
    """Main entry point."""
    global CONFIG, CONFIG_FILE, LOG_PATH, STATUS_FILE, LOGGER

    args = _parse_args()

    # Set paths from args or defaults
    CONFIG_FILE = get_config_path(args.config) if args.config else get_config_path()
    LOG_PATH = get_logs_path(args.log_file) if args.log_file else get_logs_path()
    STATUS_FILE = (
        get_status_path(args.status_file) if args.status_file else get_status_path()
    )

    # Initialize logger
    LOGGER = _setup_logger(LOG_PATH)

    # Load config
    CONFIG, _ = load_agent_config(CONFIG_FILE)

    # Update status with mode
    _status_cache["mode"] = "service" if args.service else "foreground"

    # Healthcheck mode
    if args.healthcheck:
        status_file = (
            get_status_path(args.status_file) if args.status_file else get_status_path()
        )
        sys.exit(healthcheck(status_file))

    # Interactive config prompt (only if TTY and not service mode)
    if not args.service and sys.stdin.isatty():
        maybe_prompt_for_config()
    
    LOGGER.info("Using backend: %s", CONFIG.get("api_url", "https://localhost:8000"))
    LOGGER.info("Heartbeat interval: %s seconds", CONFIG.get("interval", 60))

    host = get_basic_host_info()
    LOGGER.info(
        "Host: %s user=%s os=%s %s",
        host["hostname"],
        host["username"],
        host["os"],
        host["os_version"],
    )

    # Initialize status
    _update_status(running=True, last_error=None)
    
    if not ensure_enrolled(host):
        if args.run_once or args.emit_test_url:
            sys.exit(1)

    if args.emit_test_url:
        emit_test_url(args.emit_test_url, host)
        _update_status(running=False)
        sys.exit(0)
    
    collector = LogCollector(CONFIG.get("log_paths", []))

    # Emit a single "online" status event once per start
    try:
        send_event(build_status_event("online"), host)
    except Exception as exc:
        LOGGER.warning("Failed to send initial status event: %s", exc)

    iteration = 0
    last_url_poll = 0.0
    browser_poll_interval = int(CONFIG.get("browser_poll_interval", 10))
    max_iterations = 1 if args.run_once else None

    while max_iterations is None or iteration < max_iterations:
        try:
            if not ensure_enrolled(host):
                time.sleep(5)
                continue
            LOGGER.info("Sending heartbeat...")
            send_heartbeat(host)

            for log_event in collector.collect():
                send_event(log_event, host)

            if browser_poll_interval > 0:
                now_ts = time.time()
                if now_ts - last_url_poll >= browser_poll_interval:
                    for visit_event in collect_url_visit_events(host):
                        send_event(visit_event, host)
                    last_url_poll = now_ts
            
            process_actions(host["hostname"])

            if iteration % 5 == 0:
                send_inventory_snapshots(build_inventory_snapshots(host))
                send_sca_result()

            iteration += 1

            if args.run_once:
                break

            time.sleep(CONFIG.get("interval", 60))
        except KeyboardInterrupt:
            LOGGER.info("Received interrupt, shutting down...")
            break
        except Exception as exc:
            LOGGER.error("Error in main loop: %s", exc, exc_info=True)
            _update_status(last_error=str(exc))
            if args.run_once:
                sys.exit(1)
            time.sleep(5)  # Brief pause before retry

    _update_status(running=False)
    LOGGER.info("Agent stopped")


if __name__ == "__main__":
    main()
