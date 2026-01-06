from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from ...config import settings

logger = logging.getLogger("eventsec.vuln_intel.http")


class VulnIntelHttpClient:
    def __init__(self) -> None:
        self.timeout = settings.vuln_intel_http_timeout_seconds
        self.retries = max(settings.vuln_intel_http_retries, 1)

    async def get_json(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return await self._request_json("GET", url, params=params)

    async def post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request_json("POST", url, json=payload)

    async def _request_json(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers: Dict[str, str] = {"User-Agent": "EventSec-VulnIntel/1.0"}
        if settings.nvd_api_key:
            headers["apiKey"] = settings.nvd_api_key
        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        json=json,
                        headers=headers,
                    )
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001
                if attempt >= self.retries:
                    logger.warning("HTTP %s %s failed: %s", method, url, exc)
                    raise
                backoff = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)
        return {}
