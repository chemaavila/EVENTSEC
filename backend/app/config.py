import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(path: Optional[str], fallback: str) -> str:
    if path:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
    return fallback


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


def _redact_database_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        creds, host = netloc.rsplit("@", 1)
        if ":" in creds:
            user, _ = creds.split(":", 1)
            netloc = f"{user}:***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg2://eventsec:eventsec@"
        f"{'db' if Path('/.dockerenv').exists() or os.environ.get('IN_DOCKER') == '1' else 'localhost'}"
        ":5432/eventsec"
    )
    secret_key: str = "eventsec-dev-secret"
    secret_key_file: Optional[str] = None
    agent_enrollment_key: str = "eventsec-enroll"
    agent_enrollment_key_file: Optional[str] = None
    opensearch_url: Optional[str] = None
    opensearch_verify_certs: bool = True
    opensearch_ca_file: Optional[str] = None
    opensearch_client_certfile: Optional[str] = None
    opensearch_client_keyfile: Optional[str] = None
    opensearch_max_retries: int = 3
    opensearch_retry_backoff_seconds: float = 0.5
    opensearch_required: bool = False
    opensearch_security_disabled: bool = False
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    server_https_enabled: bool = False
    server_ssl_certfile: Optional[str] = None
    server_ssl_keyfile: Optional[str] = None
    server_ssl_ca_file: Optional[str] = None
    server_ssl_client_cert_required: bool = False
    cors_origins: str = (
        "http://localhost,"
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:5175,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,"
        "http://127.0.0.1:5175,"
        "http://127.0.0.1:3000,"
        "https://eventsec-ihae.vercel.app"
    )
    cors_allow_origin_regex: Optional[str] = r"https://.*\.vercel\.app"
    cookie_name: str = "access_token"
    cookie_samesite: str = "lax"
    cookie_secure: Optional[bool] = None
    cookie_domain: Optional[str] = None
    cookie_path: str = "/"
    cookie_max_age_seconds: int = 3600
    manager_emails: str = ""
    level1_dl: str = ""
    level2_dl: str = ""
    ui_base_url: str = "http://localhost:5173"
    debug_token: Optional[str] = None
    notification_dedup_minutes: int = 2
    network_ingest_max_events: int = 1000
    network_ingest_max_bytes: int = 5_000_000
    password_guard_rate_limit_per_minute: int = 60
    incident_auto_create_enabled: bool = True
    incident_auto_create_min_severity: str = "high"
    vuln_intel_enabled: bool = True
    feature_intel_enabled: bool = False
    feature_ot_enabled: bool = False
    feature_email_actions_enabled: bool = False
    threatmap_fallback_coords: bool = False
    detection_queue_mode: str = "memory"
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
    db_ready_wait_attempts: int = 30
    db_ready_wait_interval_seconds: float = 2.0
    software_api_url: Optional[str] = None
    software_api_user: Optional[str] = None
    software_api_password: Optional[str] = None
    software_api_verify_certs: bool = True
    software_api_ca_file: Optional[str] = None
    software_api_timeout_seconds: float = 10.0
    software_api_max_retries: int = 2
    software_api_token_ttl_seconds: int = 900
    software_api_event_path: str = "/event"
    software_api_active_response_path: str = "/active-response"
    software_api_agents_path: str = "/agents"
    software_api_decoders_path: str = "/decoders"
    software_indexer_url: Optional[str] = None
    software_indexer_user: Optional[str] = None
    software_indexer_password: Optional[str] = None
    software_indexer_verify_certs: bool = True
    software_indexer_ca_file: Optional[str] = None
    software_indexer_alerts_index: Optional[str] = "software-alerts-*"
    software_indexer_archives_index: Optional[str] = "software-archives-*"
    software_indexer_max_retries: int = 3
    software_indexer_retry_backoff_seconds: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def model_post_init(self, __context: object) -> None:  # type: ignore[override]
        self.secret_key = _read_secret(self.secret_key_file, self.secret_key)
        jwt_secret = os.environ.get("JWT_SECRET")
        if jwt_secret:
            self.secret_key = jwt_secret
        self.agent_enrollment_key = _read_secret(
            self.agent_enrollment_key_file, self.agent_enrollment_key
        )
        original_url = self.database_url
        self.database_url = _normalize_database_url(self.database_url)
        logger = logging.getLogger("eventsec")
        if self.database_url != original_url:
            logger.info(
                "Normalized DATABASE_URL scheme for SQLAlchemy (%s -> %s)",
                original_url.split(":", 1)[0],
                self.database_url.split(":", 1)[0],
            )
        logger.info("Using database URL: %s", _redact_database_url(self.database_url))
        if not (self.opensearch_url or "").strip():
            self.opensearch_url = None
            if self.opensearch_required:
                logger.error("OPENSEARCH_URL is required but not set.")
            else:
                logger.info("OpenSearch disabled (OPENSEARCH_URL not set).")
        env = (self.environment or "").lower()
        if env not in {"development", "dev"}:
            if self.secret_key == "eventsec-dev-secret":
                raise ValueError("SECRET_KEY must be set for non-development environments.")
            if self.agent_enrollment_key == "eventsec-enroll":
                raise ValueError(
                    "AGENT_ENROLLMENT_KEY must be set for non-development environments."
                )
            if self.opensearch_security_disabled:
                raise ValueError(
                    "OPENSEARCH_SECURITY_DISABLED must not be true in non-development environments."
                )
            if not self.opensearch_verify_certs and self.opensearch_url:
                raise ValueError(
                    "OPENSEARCH_VERIFY_CERTS must be true when not in development."
                )
            if self.software_api_url and not self.software_api_verify_certs:
                raise ValueError(
                    "SOFTWARE_API_VERIFY_CERTS must be true when not in development."
                )
            if self.software_indexer_url and not self.software_indexer_verify_certs:
                raise ValueError(
                    "SOFTWARE_INDEXER_VERIFY_CERTS must be true when not in development."
                )

    def cors_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        ui_base_url = (self.ui_base_url or "").strip()
        if ui_base_url:
            normalized = ui_base_url.rstrip("/")
            if "://" in normalized:
                parts = urlsplit(normalized)
                if parts.scheme and parts.netloc:
                    normalized = f"{parts.scheme}://{parts.netloc}"
            if normalized and normalized not in origins:
                origins.append(normalized)
        return origins

    def resolved_cookie_settings(self) -> dict[str, object]:
        samesite = (self.cookie_samesite or "lax").lower()
        if samesite not in {"lax", "strict", "none"}:
            raise ValueError(
                f"COOKIE_SAMESITE must be lax, strict, or none (got {self.cookie_samesite})"
            )
        secure = self.cookie_secure if self.cookie_secure is not None else self.server_https_enabled
        if samesite == "none" and not secure:
            logging.getLogger("eventsec").warning(
                "COOKIE_SAMESITE=None requires COOKIE_SECURE=true; falling back to SameSite=Lax."
            )
            samesite = "lax"
        return {"samesite": samesite, "secure": secure}


settings = Settings()
