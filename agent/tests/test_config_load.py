"""Tests for config loading."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


from agent import agent


def test_load_config_default():
    """Test loading default config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "agent_config.json"
        with patch("agent.agent.get_config_path", return_value=config_path):
            cfg, path = agent.load_agent_config()
            assert path == config_path
            assert "api_url" in cfg
            assert cfg["api_url"] == "http://localhost:8000"


def test_load_config_existing():
    """Test loading existing config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "agent_config.json"
        custom_config = {
            "api_url": "http://custom:8000",
            "agent_token": "custom-token",
            "interval": 120,
        }
        config_path.write_text(json.dumps(custom_config), encoding="utf-8")
        
        with patch("agent.agent.get_config_path", return_value=config_path):
            cfg, path = agent.load_agent_config()
            assert cfg["api_url"] == "http://custom:8000"
            assert cfg["agent_token"] == "custom-token"
            assert cfg["interval"] == 120


def test_load_config_invalid_json():
    """Test loading invalid config (should fallback to defaults)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "agent_config.json"
        config_path.write_text("{ invalid json", encoding="utf-8")
        
        with patch("agent.agent.get_config_path", return_value=config_path):
            with patch("agent.agent.LOGGER"):
                cfg, path = agent.load_agent_config()
                # Should fallback to defaults
                assert cfg["api_url"] == "http://localhost:8000"

