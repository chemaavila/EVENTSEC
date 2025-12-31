import platform
import plistlib
import subprocess
from pathlib import Path
from typing import Literal

from .os_paths import get_config_dir

LAUNCH_AGENT_ID = "com.eventsec.agent"
SERVICE_NAME = "EventSecAgentService"


def _launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"


def _build_launch_agent(plist_path: Path, executable: Path) -> bytes:
    config_dir = get_config_dir()
    plist = {
        "Label": LAUNCH_AGENT_ID,
        "ProgramArguments": [str(executable), "--service"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "WorkingDirectory": str(config_dir),
        "StandardOutPath": str(get_config_dir() / "agent-launcher.log"),
        "StandardErrorPath": str(get_config_dir() / "agent-launcher.log"),
    }
    return plistlib.dumps(plist)


def install_service(executable: Path) -> bool:
    system = platform.system()
    if system == "Darwin":
        plist_path = _launch_agent_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_bytes(_build_launch_agent(plist_path, executable))
        subprocess.run(["launchctl", "bootstrap", str(plist_path)], check=False)
        return True
    if system == "Windows":
        subprocess.run(
            ["sc", "create", SERVICE_NAME, "binPath=", str(executable)], check=False
        )
        return True
    return False


def uninstall_service() -> bool:
    system = platform.system()
    if system == "Darwin":
        plist_path = _launch_agent_path()
        subprocess.run(
            ["launchctl", "bootout", "gui/$(id -u)", str(plist_path)], check=False
        )
        if plist_path.exists():
            plist_path.unlink(missing_ok=True)
        return True
    if system == "Windows":
        subprocess.run(["sc", "stop", SERVICE_NAME], check=False)
        subprocess.run(["sc", "delete", SERVICE_NAME], check=False)
        return True
    return False


def service_action(action: Literal["start", "stop", "restart"]) -> bool:
    system = platform.system()
    if system == "Darwin":
        plist_path = _launch_agent_path()
        cmd = (
            ["launchctl", "load", str(plist_path)]
            if action == "start"
            else ["launchctl", "unload", str(plist_path)]
        )
        subprocess.run(cmd, check=False)
        return True
    if system == "Windows":
        subprocess.run(["sc", action, SERVICE_NAME], check=False)
        return True
    return False


def is_service_running() -> bool:
    system = platform.system()
    if system == "Darwin":
        plist_path = _launch_agent_path()
        return plist_path.exists()
    if system == "Windows":
        result = subprocess.run(
            ["sc", "query", SERVICE_NAME],
            capture_output=True,
            text=True,
            check=False,
        )
        return "RUNNING" in result.stdout
    return False
