from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(path: Optional[str], fallback: str) -> str:
    if path:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
    return fallback


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "postgresql+psycopg2://eventsec:eventsec@localhost:5432/eventsec"
    secret_key: str = "eventsec-dev-secret"
    secret_key_file: Optional[str] = None
    agent_enrollment_key: str = "eventsec-enroll"
    agent_enrollment_key_file: Optional[str] = None
    opensearch_url: str = "http://localhost:9200"
    opensearch_verify_certs: bool = True
    opensearch_ca_file: Optional[str] = None
    opensearch_client_certfile: Optional[str] = None
    opensearch_client_keyfile: Optional[str] = None
    opensearch_max_retries: int = 3
    opensearch_retry_backoff_seconds: float = 0.5
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    server_https_enabled: bool = False
    server_ssl_certfile: Optional[str] = None
    server_ssl_keyfile: Optional[str] = None
    server_ssl_ca_file: Optional[str] = None
    server_ssl_client_cert_required: bool = False
    manager_emails: str = ""
    level1_dl: str = ""
    level2_dl: str = ""
    ui_base_url: str = "http://localhost:5173"
    notification_dedup_minutes: int = 2
    network_ingest_max_events: int = 1000
    network_ingest_max_bytes: int = 5_000_000
    password_guard_rate_limit_per_minute: int = 60
    incident_auto_create_enabled: bool = True
    incident_auto_create_min_severity: str = "high"
    vuln_intel_enabled: bool = True
    vuln_intel_worker_role: str = "api"
    nvd_api_key: Optional[str] = None
    nvd_base_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_cpe_base_url: str = "https://services.nvd.nist.gov/rest/json/cpes/2.0"
    osv_base_url: str = "https://api.osv.dev/v1/query"
    osv_batch_url: str = "https://api.osv.dev/v1/querybatch"
    epss_base_url: str = "https://api.first.org/data/v1/epss"
    vuln_intel_http_timeout_seconds: int = 15
    vuln_intel_http_retries: int = 3
    vuln_intel_cache_ttl_hours: int = 24
    vuln_intel_notify_immediate_min_risk: str = "CRITICAL"
    vuln_intel_notify_digest_enabled: bool = True
    vuln_intel_notify_digest_hour_local: int = 9
    vuln_intel_timezone: str = "Europe/Madrid"
    vuln_intel_create_alerts_for_critical: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def model_post_init(self, __context: object) -> None:  # type: ignore[override]
        self.secret_key = _read_secret(self.secret_key_file, self.secret_key)
        self.agent_enrollment_key = _read_secret(
            self.agent_enrollment_key_file, self.agent_enrollment_key
        )


settings = Settings()
