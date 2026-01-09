import argparse
import base64
import json
import logging
import os
import platform
import random
import socket
import secrets
import subprocess
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Any, Dict, Optional
from urllib.parse import urlparse

try:
    import psutil
    PSUTIL_AVAILABLE = True
except Exception:  # pragma: no cover
    psutil = None
    PSUTIL_AVAILABLE = False

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
        "api_url": "http://localhost:8000",
        "agent_token": secrets.token_urlsafe(32),
        "interval": 60,
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
    
    current_url = get_config_value("api_url", "http://localhost:8000")
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
    ip_address = "127.0.0.1"
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        pass
    return {
        "hostname": hostname,
        "username": username,
        "os": system,
        "os_version": release,
        "ip_address": ip_address,
    }


# ---------------------------------------------------------------------------
# Construcción de payloads para cada módulo
# ---------------------------------------------------------------------------


def build_status_event(status: str) -> Dict[str, Any]:
    """Single status event to indicate connectivity."""
    host = get_basic_host_info()
    return {
        "event_type": "agent_status",
        "severity": "low",
        "category": "status",
        "details": {
            "status": status,
            "hostname": host["hostname"],
            "username": host["username"],
            "os": host["os"],
            "os_version": host["os_version"],
            "timestamp": now_utc_iso(),
            "source": "agent",
        },
    }


def enrich_event(event: Dict[str, Any], host: Dict[str, str]) -> Dict[str, Any]:
    details = event.get("details") or {}
    if not isinstance(details, dict):
        details = {"raw": details}
    now_iso = now_utc_iso()
    details.setdefault("hostname", host.get("hostname"))
    details.setdefault("username", host.get("username"))
    details.setdefault("os", host.get("os"))
    details.setdefault("os_version", host.get("os_version"))
    details.setdefault("ip_address", host.get("ip_address"))
    details.setdefault("timestamp", now_iso)
    details.setdefault("event_time", details.get("timestamp", now_iso))
    details.setdefault("source", "agent")
    event["details"] = details
    return event


def fetch_agent_iocs() -> list[Dict[str, Any]]:
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
    try:
        resp = requests.get(f"{api_url}/agent/iocs", headers=agent_headers(), timeout=5)
        if not resp.ok:
            if LOGGER:
                LOGGER.warning("Failed to fetch IOCs: %s %s", resp.status_code, resp.text)
            return []
        data = resp.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.warning("Failed to fetch IOCs: %s", exc)
        return []


class IocCache:
    def __init__(self, ttl_seconds: int = 300, dns_ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self.dns_ttl_seconds = dns_ttl_seconds
        self.expires_at = 0.0
        self.ip_to_indicators: Dict[str, list[Dict[str, Any]]] = {}
        self.domain_cache: Dict[str, tuple[float, set[str]]] = {}
        self.hit_cache: Dict[tuple[str, str, str], float] = {}

    def _resolve_domain(self, domain: str) -> set[str]:
        now = time.time()
        cached = self.domain_cache.get(domain)
        if cached and cached[0] > now:
            return cached[1]
        ips: set[str] = set()
        try:
            for family, _, _, _, sockaddr in socket.getaddrinfo(domain, None):
                if family in (socket.AF_INET, socket.AF_INET6) and sockaddr:
                    ips.add(sockaddr[0])
        except Exception as exc:  # noqa: BLE001
            if LOGGER:
                LOGGER.debug("DNS lookup failed for %s: %s", domain, exc)
        self.domain_cache[domain] = (now + self.dns_ttl_seconds, ips)
        return ips

    def refresh(self) -> None:
        iocs = fetch_agent_iocs()
        now = time.time()
        if not iocs:
            self.expires_at = now + self.ttl_seconds
            self.ip_to_indicators = {}
            return
        ip_to_indicators: Dict[str, list[Dict[str, Any]]] = {}
        for indicator in iocs:
            indicator_type = indicator.get("type")
            value = indicator.get("value")
            if not indicator_type or not value:
                continue
            if indicator_type == "ip":
                ip_to_indicators.setdefault(value, []).append(indicator)
                continue
            domain = value
            if indicator_type == "url":
                parsed = urlparse(value)
                if parsed.hostname:
                    domain = parsed.hostname
            for ip in self._resolve_domain(domain):
                ip_to_indicators.setdefault(ip, []).append(indicator)
        self.ip_to_indicators = ip_to_indicators
        self.expires_at = now + self.ttl_seconds

    def match_ip(self, ip: str) -> list[Dict[str, Any]]:
        if time.time() >= self.expires_at:
            self.refresh()
        return self.ip_to_indicators.get(ip, [])

    def should_emit_hit(self, indicator: Dict[str, Any], ip: str, process_name: str) -> bool:
        key = (indicator.get("type", "unknown"), indicator.get("value", ""), ip, process_name)
        now = time.time()
        last = self.hit_cache.get(key, 0.0)
        if now - last < 300:
            return False
        self.hit_cache[key] = now
        return True


class EdrNetworkMonitor:
    def __init__(self) -> None:
        self.seen: Dict[tuple, float] = {}
        self.prune_after_seconds = 3600

    def poll(self) -> list[Dict[str, Any]]:
        if not PSUTIL_AVAILABLE:
            return []
        events: list[Dict[str, Any]] = []
        try:
            connections = psutil.net_connections(kind="inet")
        except Exception as exc:  # noqa: BLE001
            if LOGGER:
                LOGGER.warning("EDR net_connections failed: %s", exc)
            return []
        now = time.time()
        for conn in connections:
            if not conn.raddr:
                continue
            dst_ip = getattr(conn.raddr, "ip", None) or conn.raddr[0]
            dst_port = getattr(conn.raddr, "port", None) or conn.raddr[1]
            src_ip = getattr(conn.laddr, "ip", None) if conn.laddr else None
            src_port = getattr(conn.laddr, "port", None) if conn.laddr else None
            proto = "tcp" if conn.type == socket.SOCK_STREAM else "udp"
            key = (
                conn.pid,
                dst_ip,
                dst_port,
                src_ip,
                src_port,
                proto,
            )
            if key in self.seen:
                continue
            self.seen[key] = now
            process_name = "unknown"
            if conn.pid:
                try:
                    process_name = psutil.Process(conn.pid).name()
                except Exception:
                    process_name = "unknown"
            events.append(
                {
                    "event_type": "edr_network_connection",
                    "severity": "low",
                    "category": "edr",
                    "details": {
                        "dst_ip": dst_ip,
                        "dst_port": dst_port,
                        "src_ip": src_ip,
                        "src_port": src_port,
                        "protocol": proto,
                        "process_name": process_name,
                        "action": "connect",
                    },
                }
            )
        self.seen = {
            key: ts for key, ts in self.seen.items() if now - ts < self.prune_after_seconds
        }
        return events


def build_ioc_hit_event(
    indicator: Dict[str, Any],
    matched_ip: str,
    process_name: str,
) -> Dict[str, Any]:
    return {
        "event_type": "ioc_hit",
        "severity": "high",
        "category": "threat-intel",
        "details": {
            "indicator_type": indicator.get("type"),
            "indicator_value": indicator.get("value"),
            "matched_ip": matched_ip,
            "process_name": process_name,
            "action": "connect",
            "timestamp": now_utc_iso(),
        },
    }


# ---------------------------------------------------------------------------
# Funciones de envío
# ---------------------------------------------------------------------------


def post_json(path: str, payload: Dict[str, Any]) -> None:
    """Helper genérico para POST JSON con manejo de errores."""
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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


def locate_triage_script() -> Optional[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    candidate = repo_root / "protoxol_triage_package" / "protoxol_triage.py"
    if candidate.exists():
        return candidate
    return None


def build_triage_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    files = report.get("file_discovery", {}).get("result", {}).get("files", []) or []
    yara_matches = report.get("yara", {}).get("matches", []) or []
    suspicious_files = [f for f in files if f.get("suspicious_name_heuristic")]
    severity = "low"
    if yara_matches:
        severity = "high"
    elif suspicious_files:
        severity = "medium"
    return {
        "severity": severity,
        "files_discovered": len(files),
        "hashes_computed": len([h for h in report.get("hashes", []) if h.get("sha256")]),
        "yara_matches": len(yara_matches),
        "suspicious_files": len(suspicious_files),
        "notes": report.get("reputation", {}).get("vt", {}).get("error"),
    }


def post_triage_results(
    hostname: str,
    summary: Dict[str, Any],
    report: Dict[str, Any],
    artifact_name: Optional[str],
    artifact_zip_base64: Optional[str],
    action_id: Optional[int],
) -> Optional[Dict[str, Any]]:
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
    payload = {
        "hostname": hostname,
        "summary": summary,
        "report": report,
        "artifact_name": artifact_name,
        "artifact_zip_base64": artifact_zip_base64,
        "action_id": action_id,
        "collected_at": now_utc_iso(),
    }
    try:
        resp = requests.post(
            f"{api_url}/agent/triage/results",
            json=payload,
            headers=agent_headers(),
            timeout=20,
        )
        if not resp.ok:
            if LOGGER:
                LOGGER.warning("Failed to send triage results: %s %s", resp.status_code, resp.text)
            return None
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        if LOGGER:
            LOGGER.error("Failed to send triage results: %s", exc)
        return None


def run_triage_scan(hostname: str, action: Dict[str, Any]) -> tuple[bool, str]:
    script = locate_triage_script()
    if not script:
        return False, "Triage script not found in repo."
    params = action.get("parameters", {}) if isinstance(action.get("parameters"), dict) else {}
    since_days = int(params.get("since_days", 14))
    max_files = int(params.get("max_files", 4000))
    yara_rules = params.get("yara_rules") or params.get("yara")
    zip_output = bool(params.get("zip", False))

    output_root = Path.home() / ".eventsec-agent" / "triage"
    output_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script),
        "--out",
        str(output_root),
        "--since-days",
        str(since_days),
        "--max-files",
        str(max_files),
    ]
    if yara_rules:
        cmd += ["--yara", str(yara_rules)]
    if zip_output:
        cmd.append("--zip")

    LOGGER.info("Running triage scan: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, check=False)
    except Exception as exc:  # noqa: BLE001
        return False, f"Triage execution failed: {exc}"
    if result.returncode != 0:
        return False, f"Triage scan failed: {result.stderr.strip()}"

    output_dirs = [p for p in output_root.iterdir() if p.is_dir()]
    if not output_dirs:
        return False, "Triage output directory not found."
    latest_dir = max(output_dirs, key=lambda p: p.stat().st_mtime)
    report_path = latest_dir / "report.json"
    if not report_path.exists():
        return False, "Triage report.json not found."
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = build_triage_summary(report)
    artifact_name = None
    artifact_zip = None
    if zip_output:
        zip_path = latest_dir.with_suffix(".zip")
        if zip_path.exists():
            artifact_name = zip_path.name
            try:
                artifact_zip = base64.b64encode(zip_path.read_bytes()).decode("utf-8")
            except Exception as exc:  # noqa: BLE001
                summary["notes"] = f"Failed to read zip artifact: {exc}"

    response = post_triage_results(
        hostname=hostname,
        summary=summary,
        report=report,
        artifact_name=artifact_name,
        artifact_zip_base64=artifact_zip,
        action_id=action.get("id"),
    )
    if response:
        return True, f"Triage scan uploaded (result id {response.get('id')})."
    return False, "Triage scan completed but failed to upload."


def process_actions(host: Dict[str, str]) -> None:
    actions = fetch_pending_actions(host["hostname"])
    for action in actions:
        action_type = action.get("action_type")
        LOGGER.info(
            "Executing action #%s (%s) on %s", action["id"], action_type, host["hostname"]
        )
        time.sleep(1)
        if action_type == "triage_scan":
            success, output = run_triage_scan(host["hostname"], action)
            complete_action(action["id"], success, output)
            continue

        if action_type == "isolate":
            output = "Network interfaces disabled"
        elif action_type == "release":
            output = "Network isolation removed"
        elif action_type == "reboot":
            output = "System reboot triggered"
        elif action_type == "command":
            output = f"Executed command: {action.get('parameters', {}).get('command', 'N/A')}"
        else:
            output = "Action acknowledged"
        complete_action(action["id"], True, output)


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
    
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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
    
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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

    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
    try:
        event = enrich_event(event, host)
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
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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
    api_url = get_config_value("api_url", "http://localhost:8000").rstrip("/")
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
    
    LOGGER.info("Using backend: %s", CONFIG.get("api_url", "http://localhost:8000"))
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
        if args.run_once:
            sys.exit(1)
    
    collector = LogCollector(CONFIG.get("log_paths", []))
    edr_monitor = EdrNetworkMonitor()
    ioc_cache = IocCache()

    # Emit a single "online" status event once per start
    try:
        send_event(build_status_event("online"), host)
    except Exception as exc:
        LOGGER.warning("Failed to send initial status event: %s", exc)

    iteration = 0
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
            
            for edr_event in edr_monitor.poll():
                send_event(edr_event, host)
                details = edr_event.get("details", {}) if isinstance(edr_event.get("details"), dict) else {}
                dst_ip = details.get("dst_ip")
                process_name = details.get("process_name", "unknown")
                if dst_ip:
                    for indicator in ioc_cache.match_ip(str(dst_ip)):
                        if ioc_cache.should_emit_hit(indicator, str(dst_ip), str(process_name)):
                            send_event(
                                build_ioc_hit_event(indicator, str(dst_ip), str(process_name)),
                                host,
                            )

            process_actions(host)

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
