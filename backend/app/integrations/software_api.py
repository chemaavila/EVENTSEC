from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class SoftwareApiClient:
    def __init__(self) -> None:
        if not settings.software_api_url:
            raise RuntimeError("SOFTWARE_API_URL is required but not set.")
        if not settings.software_api_user or not settings.software_api_password:
            raise RuntimeError("SOFTWARE_API_USER and SOFTWARE_API_PASSWORD are required.")
        self._base_url = settings.software_api_url.rstrip("/")
        self._token: Optional[str] = None
        self._token_issued_at: Optional[float] = None
        verify = settings.software_api_ca_file or settings.software_api_verify_certs
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=settings.software_api_timeout_seconds,
            verify=verify,
        )

    def _token_expired(self) -> bool:
        if not self._token or not self._token_issued_at:
            return True
        return (time.time() - self._token_issued_at) > settings.software_api_token_ttl_seconds

    def _authenticate(self) -> str:
        auth_endpoint = f"{self._base_url}/security/user/authenticate"
        auth = (settings.software_api_user, settings.software_api_password)
        try:
            response = self._client.post(auth_endpoint, auth=auth)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Software API authentication failed: %s", exc)
            raise
        data = response.json()
        token = data.get("data", {}).get("token") or data.get("token")
        if not token:
            raise RuntimeError("Software API authentication response missing token.")
        self._token = token
        self._token_issued_at = time.time()
        return token

    def _get_token(self) -> str:
        if self._token_expired():
            return self._authenticate()
        assert self._token is not None
        return self._token

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        token = self._get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        url = f"{self._base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(1, settings.software_api_max_retries + 1):
            try:
                response = self._client.request(method, url, headers=headers, **kwargs)
                if response.status_code == 401 and attempt == 1:
                    self._authenticate()
                    headers["Authorization"] = f"Bearer {self._token}"
                    response = self._client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "Software API call failed (%s %s) attempt %s/%s: %s",
                    method,
                    path,
                    attempt,
                    settings.software_api_max_retries,
                    exc,
                )
                if attempt >= settings.software_api_max_retries:
                    raise
                time.sleep(0.5 * attempt)
        raise RuntimeError(f"Software API request failed: {last_exc}")

    def get_agents(self) -> Dict[str, Any]:
        return self._request("GET", settings.software_api_agents_path)

    def restart_agent(self, agent_id: str | int) -> Dict[str, Any]:
        path = f"{settings.software_api_agents_path}/{agent_id}/restart"
        return self._request("PUT", path)

    def ingest_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", settings.software_api_event_path, json=payload)

    def active_response_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", settings.software_api_active_response_path, json=payload)

    def list_decoders(self) -> Dict[str, Any]:
        return self._request("GET", settings.software_api_decoders_path)
