from __future__ import annotations

import ssl
from typing import Any, Dict

import uvicorn

from .config import settings
from .main import app


def _build_ssl_kwargs() -> Dict[str, Any]:
    if not settings.server_https_enabled:
        return {}

    if not settings.server_ssl_certfile or not settings.server_ssl_keyfile:
        raise RuntimeError(
            "HTTPS is enabled but SERVER_SSL_CERTFILE or SERVER_SSL_KEYFILE is not configured"
        )

    ssl_kwargs: Dict[str, Any] = {
        "ssl_certfile": settings.server_ssl_certfile,
        "ssl_keyfile": settings.server_ssl_keyfile,
    }

    if settings.server_ssl_client_cert_required:
        if not settings.server_ssl_ca_file:
            raise RuntimeError(
                "SERVER_SSL_CLIENT_CERT_REQUIRED is true but SERVER_SSL_CA_FILE is missing"
            )
        ssl_kwargs["ssl_ca_certs"] = settings.server_ssl_ca_file
        ssl_kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED

    return ssl_kwargs


def main() -> None:
    ssl_kwargs = _build_ssl_kwargs()
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        **ssl_kwargs,
    )


if __name__ == "__main__":
    main()
