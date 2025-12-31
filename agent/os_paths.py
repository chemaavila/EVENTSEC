import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


AGENT_NAME = "EventSec"


def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    get_config_dir().mkdir(parents=True, exist_ok=True)
    get_logs_path().parent.mkdir(parents=True, exist_ok=True)
    get_status_path().parent.mkdir(parents=True, exist_ok=True)


def get_config_path(override: Optional[str] = None) -> Path:
    """Get the config file path. Uses override if provided, otherwise OS-appropriate default."""
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / AGENT_NAME
            / "agent"
            / "agent_config.json"
        )
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / AGENT_NAME / "agent" / "agent_config.json"
        return (
            Path.home()
            / "AppData"
            / "Roaming"
            / AGENT_NAME
            / "agent"
            / "agent_config.json"
        )
    else:  # Linux
        return Path.home() / ".config" / "eventsec" / "agent_config.json"


def get_logs_path(override: Optional[str] = None) -> Path:
    """Get the log file path. Uses override if provided, otherwise OS-appropriate default."""
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Logs" / AGENT_NAME / "agent.log"
    elif system == "Windows":
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / AGENT_NAME / "logs" / "agent.log"
        return Path.home() / "AppData" / "Local" / AGENT_NAME / "logs" / "agent.log"
    else:  # Linux
        state_dir = Path.home() / ".local" / "state" / "eventsec"
        if state_dir.parent.exists() or os.access(state_dir.parent.parent, os.W_OK):
            return state_dir / "agent.log"
        return Path.home() / ".cache" / "eventsec" / "agent.log"


def get_status_path(override: Optional[str] = None) -> Path:
    """Get the status file path. Uses override if provided, otherwise OS-appropriate default."""
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / AGENT_NAME
            / "agent"
            / "status.json"
        )
    elif system == "Windows":
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / AGENT_NAME / "agent" / "status.json"
        return Path.home() / "AppData" / "Local" / AGENT_NAME / "agent" / "status.json"
    else:  # Linux
        state_dir = Path.home() / ".local" / "state" / "eventsec"
        if state_dir.parent.exists() or os.access(state_dir.parent.parent, os.W_OK):
            return state_dir / "status.json"
        return Path.home() / ".cache" / "eventsec" / "status.json"


def get_config_dir() -> Path:
    """Get the config directory (for backward compatibility)."""
    return get_config_path().parent


def get_log_dir() -> Path:
    """Get the log directory (for backward compatibility)."""
    return get_logs_path().parent


def open_file(path: str) -> None:
    """Open a file using the system default application."""
    path_obj = Path(path)
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path_obj)], check=False)
        elif system == "Windows":
            subprocess.run(["start", "", str(path_obj)], shell=True, check=False)
        else:  # Linux
            subprocess.run(["xdg-open", str(path_obj)], check=False)
    except Exception:
        pass


def open_in_file_manager(path: str) -> None:
    """Open a directory in the system file manager."""
    path_obj = Path(path)
    if path_obj.is_file():
        path_obj = path_obj.parent

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path_obj)], check=False)
        elif system == "Windows":
            subprocess.run(["explorer", str(path_obj)], check=False)
        else:  # Linux
            subprocess.run(["xdg-open", str(path_obj)], check=False)
    except Exception:
        pass
