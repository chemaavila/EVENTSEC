"""Tests for healthcheck functionality."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


from agent import agent


def test_healthcheck_no_status_file():
    """Test healthcheck when status file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = Path(tmpdir) / "status.json"
        with patch("agent.agent.STATUS_FILE", status_path):
            exit_code = agent.healthcheck()
            assert exit_code == 1


def test_healthcheck_recent_heartbeat():
    """Test healthcheck with recent heartbeat."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = Path(tmpdir) / "status.json"
        status_data = {
            "timestamp": "2024-01-01T12:00:00+00:00",
            "pid": 12345,
            "running": True,
            "uptime_seconds": 10,
        }
        status_path.write_text(json.dumps(status_data), encoding="utf-8")
        
        with patch("agent.agent.STATUS_FILE", status_path):
            # Mock datetime to be recent
            with patch("agent.agent.datetime") as mock_dt:
                from datetime import datetime, timezone
                mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc)
                mock_dt.fromisoformat = datetime.fromisoformat
                exit_code = agent.healthcheck()
                # Should pass (recent heartbeat)
                assert exit_code == 0


def test_healthcheck_stale_heartbeat():
    """Test healthcheck with stale heartbeat."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = Path(tmpdir) / "status.json"
        status_data = {
            "timestamp": "2024-01-01T12:00:00+00:00",
            "pid": 12345,
            "running": True,
        }
        status_path.write_text(json.dumps(status_data), encoding="utf-8")
        
        with patch("agent.agent.STATUS_FILE", status_path):
            # Mock datetime to be old
            with patch("agent.agent.datetime") as mock_dt:
                from datetime import datetime, timezone
                mock_dt.now.return_value = datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc)  # 2 minutes old
                mock_dt.fromisoformat = datetime.fromisoformat
                exit_code = agent.healthcheck()
                # Should fail (stale heartbeat)
                assert exit_code == 1

