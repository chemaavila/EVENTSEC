"""Tests for os_paths module."""
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch


from agent import os_paths


def test_get_config_path_default():
    """Test default config path per OS."""
    path = os_paths.get_config_path()
    assert path is not None
    assert isinstance(path, Path)
    
    system = platform.system()
    if system == "Darwin":
        assert "Library/Application Support/EventSec" in str(path)
    elif system == "Windows":
        assert "EventSec" in str(path) or "eventsec" in str(path).lower()
    else:  # Linux
        assert ".config/eventsec" in str(path)


def test_get_config_path_override():
    """Test config path override."""
    override = "/custom/path/config.json"
    path = os_paths.get_config_path(override)
    assert str(path) == override


def test_get_logs_path_default():
    """Test default logs path per OS."""
    path = os_paths.get_logs_path()
    assert path is not None
    assert isinstance(path, Path)
    
    system = platform.system()
    if system == "Darwin":
        assert "Library/Logs/EventSec" in str(path)
    elif system == "Windows":
        assert "EventSec" in str(path) or "eventsec" in str(path).lower()
    else:  # Linux
        assert ".local/state/eventsec" in str(path) or ".cache/eventsec" in str(path)


def test_get_status_path_default():
    """Test default status path per OS."""
    path = os_paths.get_status_path()
    assert path is not None
    assert isinstance(path, Path)


def test_ensure_dirs():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("agent.os_paths.get_config_path", return_value=Path(tmpdir) / "config.json"):
            with patch("agent.os_paths.get_logs_path", return_value=Path(tmpdir) / "logs" / "agent.log"):
                with patch("agent.os_paths.get_status_path", return_value=Path(tmpdir) / "status.json"):
                    os_paths.ensure_dirs()
                    assert Path(tmpdir).exists()
                    assert Path(tmpdir) / "logs" in Path(tmpdir).iterdir() or Path(tmpdir) / "logs" / "agent.log" in Path(tmpdir).rglob("*")


def test_open_in_file_manager():
    """Test opening file manager (should not crash)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test"
        test_path.mkdir()
        # Should not raise
        os_paths.open_in_file_manager(str(test_path))


def test_open_file():
    """Test opening file (should not crash)."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test")
        tmp_path = tmp.name
    try:
        # Should not raise
        os_paths.open_file(tmp_path)
    finally:
        os.unlink(tmp_path)

