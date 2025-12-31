import io
import json
import platform
import subprocess
import sys
import threading
import time
import tempfile
import tkinter as tk
import tkinter.messagebox as msgbox
from pathlib import Path
from typing import Optional

import pystray
from PIL import Image, ImageDraw

from .os_paths import (
    ensure_dirs,
    get_config_path,
    get_logs_path,
    get_status_path,
    open_file,
    open_in_file_manager,
)


class SingletonLock:
    """Prevent multiple launcher instances."""

    def __init__(self):
        self._path = Path(tempfile.gettempdir()) / "eventsec-launcher.lock"
        self.handle = None

    def acquire(self) -> bool:
        try:
            if platform.system() == "Windows":
                import msvcrt

                self.handle = open(self._path, "w")
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                self.handle = open(self._path, "w")
                fcntl.lockf(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except Exception:
            return False

    def release(self) -> None:
        if self.handle:
            try:
                self.handle.close()
                self._path.unlink(missing_ok=True)
            except Exception:
                pass


def _create_fallback_icon() -> Image.Image:
    """Create a simple fallback icon."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, size - 8, size - 8), fill=(14, 165, 233, 255))
    draw.ellipse((18, 18, size - 18, size - 18), fill=(2, 6, 23, 255))
    return image


def _load_tray_icon() -> Image.Image:
    """Load tray icon from assets, with fallbacks."""
    assets_dir = Path(__file__).resolve().parent / "assets"
    svg_path = assets_dir / "logo.svg"
    png_path = assets_dir / "logo.png"

    if svg_path.exists():
        try:
            import cairosvg

            png_bytes = cairosvg.svg2png(
                url=str(svg_path), output_width=256, output_height=256
            )
            return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        except Exception:
            pass

    if png_path.exists():
        try:
            return Image.open(png_path).convert("RGBA")
        except Exception:
            pass

    return _create_fallback_icon()


def _read_status() -> dict:
    """Read status.json file."""
    status_file = get_status_path()
    if not status_file.exists():
        return {}
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


class AgentLauncher:
    """Tray launcher that manages agent as a child process."""

    def __init__(self):
        self._agent_process: Optional[subprocess.Popen] = None
        self._status_poll_thread = threading.Thread(
            target=self._refresh_status_loop, daemon=True
        )
        self._status_poll_thread.start()

        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem(lambda text: self._get_status_label(), self._noop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Worker", self._start_worker),
            pystray.MenuItem("Stop Worker", self._stop_worker),
            pystray.MenuItem("Restart Worker", self._restart_worker),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Config", self._open_config),
            pystray.MenuItem("Open Logs Folder", self._open_logs_folder),
            pystray.MenuItem("View Last 200 Log Lines", self._view_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Launcher", self._quit_launcher),
        )

        self.icon = pystray.Icon("EventSec Agent", _load_tray_icon(), menu=menu)

    def _get_status_label(self) -> str:
        """Get dynamic status label for menu."""
        status_data = _read_status()
        is_running = self._is_worker_running()

        if is_running:
            hb = status_data.get("last_heartbeat") or status_data.get("timestamp")
            pid = status_data.get("pid") or (
                self._agent_process.pid if self._agent_process else "?"
            )
            return f"Status: Running (PID: {pid}, HB: {hb or 'n/a'})"
        else:
            last_error = status_data.get("last_error")
            if last_error:
                return f"Status: Stopped (Error: {last_error[:30]}...)"
            return "Status: Stopped"

    def _is_worker_running(self) -> bool:
        """Check if worker process is running."""
        if self._agent_process is None:
            return False
        return self._agent_process.poll() is None

    def _refresh_status_loop(self):
        """Periodically refresh menu title."""
        while True:
            try:
                self.icon.title = self._get_status_label()
            except Exception:
                pass
            time.sleep(3)

    def _noop(self, _: pystray.MenuItem):
        """No-op menu item handler."""
        pass

    def _get_agent_executable(self) -> Path:
        """Get path to agent executable (frozen or dev)."""
        if getattr(sys, "frozen", False):
            # Running as packaged executable
            exe_dir = Path(sys.executable).resolve().parent
            # Look for eventsec-agent in same directory
            if platform.system() == "Windows":
                agent_exe = exe_dir / "eventsec-agent.exe"
            else:
                agent_exe = exe_dir / "eventsec-agent"
            if agent_exe.exists():
                return agent_exe
            # Fallback: use launcher itself (shouldn't happen, but handle gracefully)
            return Path(sys.executable)
        else:
            # Dev mode: use Python module path
            agent_module = Path(__file__).resolve().parent / "agent.py"
            return agent_module

    def _start_worker(self, _: pystray.MenuItem):
        """Start the agent worker process."""
        if self._is_worker_running():
            return

        ensure_dirs()
        agent_exe = self._get_agent_executable()
        config_path = get_config_path()
        log_path = get_logs_path()
        status_path = get_status_path()

        # Build command
        if getattr(sys, "frozen", False) and agent_exe.suffix in ("", ".exe"):
            # Packaged executable
            cmd = [
                str(agent_exe),
                "--config",
                str(config_path),
                "--log-file",
                str(log_path),
                "--status-file",
                str(status_path),
            ]
        else:
            # Dev mode: run as Python module
            cmd = [
                sys.executable,
                "-m",
                "agent.agent",
                "--config",
                str(config_path),
                "--log-file",
                str(log_path),
                "--status-file",
                str(status_path),
            ]

        try:
            # Start process (no console window on Windows)
            creation_flags = 0
            if platform.system() == "Windows":
                creation_flags = subprocess.CREATE_NO_WINDOW

            self._agent_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except Exception as exc:
            # Show error in a simple way (could use tkinter messagebox)
            print(f"Failed to start worker: {exc}")

    def _stop_worker(self, _: pystray.MenuItem):
        """Stop the agent worker process."""
        if not self._is_worker_running():
            return

        try:
            if platform.system() == "Windows":
                self._agent_process.terminate()
            else:
                self._agent_process.terminate()
            # Wait briefly for graceful shutdown
            try:
                self._agent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._agent_process.kill()
            self._agent_process = None
        except Exception:
            pass

    def _restart_worker(self, _: pystray.MenuItem):
        """Restart the agent worker."""
        self._stop_worker(_)
        time.sleep(1)
        self._start_worker(_)

    def _open_config(self, _: pystray.MenuItem):
        """Open config file."""
        config_path = get_config_path()
        # Create from example if missing
        if not config_path.exists():
            example = Path(__file__).resolve().parent / "agent_config.example.json"
            if example.exists():
                ensure_dirs()
                config_path.write_text(
                    example.read_text(encoding="utf-8"), encoding="utf-8"
                )
        open_file(str(config_path))

    def _open_logs_folder(self, _: pystray.MenuItem):
        """Open logs folder in file manager."""
        log_path = get_logs_path()
        open_in_file_manager(str(log_path.parent))

    def _view_logs(self, _: pystray.MenuItem):
        """Show last 200 log lines in a simple window."""
        log_path = get_logs_path()
        if not log_path.exists():
            self._show_message(
                "Log file not found", f"Log file does not exist:\n{log_path}"
            )
            return

        try:
            # Read last 200 lines
            with log_path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                last_lines = lines[-200:] if len(lines) > 200 else lines
                content = "".join(last_lines)
        except Exception as exc:
            content = f"Error reading log file: {exc}"

        self._show_message("Last 200 Log Lines", content)

    def _show_message(self, title: str, message: str):
        """Show a simple message window using tkinter."""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        root.title(title)

        # Create text widget
        text_widget = tk.Text(root, wrap=tk.WORD, width=80, height=30)
        text_widget.insert("1.0", message)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Close button
        button = tk.Button(root, text="Close", command=root.destroy)
        button.pack(pady=5)

        root.deiconify()
        root.mainloop()

    def _quit_launcher(self, _: pystray.MenuItem):
        """Quit launcher with optional worker stop."""
        if self._is_worker_running():
            # Simple prompt via tkinter
            root = tk.Tk()
            root.withdraw()

            result = msgbox.askyesno(
                "Quit Launcher",
                "Worker is running. Stop worker and quit?\n\n"
                "Yes: Stop worker and quit\n"
                "No: Quit launcher only (worker continues)",
            )
            root.destroy()

            if result:
                self._stop_worker(_)

        self.icon.stop()

    def run(self):
        """Run the launcher."""
        lock = SingletonLock()
        if not lock.acquire():
            print("Another launcher instance is already running.")
            return

        try:
            self.icon.run()
        finally:
            # Cleanup on exit
            if self._is_worker_running():
                self._stop_worker(None)
            lock.release()


def launch():
    """Launch the tray launcher."""
    launcher = AgentLauncher()
    launcher.run()


if __name__ == "__main__":
    launch()
