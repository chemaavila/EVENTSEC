from __future__ import annotations

from backend.app import config, search


def test_build_client_kwargs_https(monkeypatch):
    monkeypatch.setattr(
        config.settings, "opensearch_url", "https://opensearch.example.com:9200"
    )
    monkeypatch.setattr(config.settings, "opensearch_verify_certs", True)
    kwargs = search._build_client_kwargs()
    assert kwargs["hosts"] == ["https://opensearch.example.com:9200"]
    assert kwargs["use_ssl"] is True
    assert kwargs["verify_certs"] is True


def test_build_client_kwargs_with_certificates(monkeypatch):
    monkeypatch.setattr(config.settings, "opensearch_url", "https://secure.example.com")
    monkeypatch.setattr(config.settings, "opensearch_ca_file", "/tmp/opensearch-ca.pem")
    monkeypatch.setattr(
        config.settings, "opensearch_client_certfile", "/tmp/client-cert.pem"
    )
    monkeypatch.setattr(
        config.settings, "opensearch_client_keyfile", "/tmp/client-key.pem"
    )
    kwargs = search._build_client_kwargs()
    assert kwargs["ca_certs"] == "/tmp/opensearch-ca.pem"
    assert kwargs["client_cert"] == "/tmp/client-cert.pem"
    assert kwargs["client_key"] == "/tmp/client-key.pem"


def test_get_client_disabled(monkeypatch):
    monkeypatch.setattr(config.settings, "opensearch_url", None)
    monkeypatch.setattr(config.settings, "opensearch_required", False)
    monkeypatch.setattr(search, "_client", None, raising=False)
    monkeypatch.setattr(search, "_client_disabled_logged", False, raising=False)
    assert search.get_client() is None
    assert search.opensearch_enabled() is False
