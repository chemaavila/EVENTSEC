from __future__ import annotations

import ssl

import pytest

from backend.app import config
from backend.app import server


def test_build_ssl_kwargs_requires_cert(monkeypatch):
    monkeypatch.setattr(config.settings, "server_https_enabled", True)
    monkeypatch.setattr(config.settings, "server_ssl_certfile", None)
    monkeypatch.setattr(config.settings, "server_ssl_keyfile", None)
    with pytest.raises(RuntimeError):
        server._build_ssl_kwargs()


def test_build_ssl_kwargs_client_cert(monkeypatch):
    monkeypatch.setattr(config.settings, "server_https_enabled", True)
    monkeypatch.setattr(config.settings, "server_ssl_certfile", "/tmp/cert.pem")
    monkeypatch.setattr(config.settings, "server_ssl_keyfile", "/tmp/key.pem")
    monkeypatch.setattr(config.settings, "server_ssl_client_cert_required", True)
    monkeypatch.setattr(config.settings, "server_ssl_ca_file", "/tmp/ca.pem")
    kwargs = server._build_ssl_kwargs()
    assert kwargs["ssl_certfile"] == "/tmp/cert.pem"
    assert kwargs["ssl_keyfile"] == "/tmp/key.pem"
    assert kwargs["ssl_ca_certs"] == "/tmp/ca.pem"
    assert kwargs["ssl_cert_reqs"] == ssl.CERT_REQUIRED
