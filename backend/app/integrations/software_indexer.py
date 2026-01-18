from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch, RequestsHttpConnection

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class SoftwareSearchResult:
    events: List[Dict[str, Any]]
    last_sort: Optional[List[Any]]


class SoftwareIndexerClient:
    def __init__(self) -> None:
        if not settings.software_indexer_url:
            raise RuntimeError("SOFTWARE_INDEXER_URL is required but not set.")
        self._client = OpenSearch(**_build_client_kwargs())

    def search_alerts(
        self,
        query: str = "",
        size: int = 200,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        severity: Optional[str] = None,
        search_after: Optional[List[Any]] = None,
    ) -> SoftwareSearchResult:
        body = _build_alerts_query(
            query=query,
            size=size,
            start=start,
            end=end,
            severity=severity,
            search_after=search_after,
        )
        response = _retry_operation(lambda: self._client.search(index=_alerts_index(), body=body))
        hits = response.get("hits", {}).get("hits", [])
        events: List[Dict[str, Any]] = []
        last_sort = None
        for hit in hits:
            last_sort = hit.get("sort") or last_sort
            events.append(map_software_alert_to_siem_event(hit.get("_source", {})))
        return SoftwareSearchResult(events=events, last_sort=last_sort)

    def search_archives(
        self,
        query: str = "",
        size: int = 200,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        search_after: Optional[List[Any]] = None,
    ) -> SoftwareSearchResult:
        body = _build_alerts_query(
            query=query,
            size=size,
            start=start,
            end=end,
            severity=None,
            search_after=search_after,
        )
        response = _retry_operation(lambda: self._client.search(index=_archives_index(), body=body))
        hits = response.get("hits", {}).get("hits", [])
        events: List[Dict[str, Any]] = []
        last_sort = None
        for hit in hits:
            last_sort = hit.get("sort") or last_sort
            events.append(map_software_alert_to_edr_event(hit.get("_source", {})))
        return SoftwareSearchResult(events=events, last_sort=last_sort)


def software_indexer_enabled() -> bool:
    return bool(settings.software_indexer_url)


def _build_client_kwargs() -> Dict[str, Any]:
    use_ssl = settings.software_indexer_url.startswith("https")
    kwargs: Dict[str, Any] = {
        "hosts": [settings.software_indexer_url],
        "http_compress": True,
        "use_ssl": use_ssl,
        "verify_certs": settings.software_indexer_verify_certs if use_ssl else False,
        "connection_class": RequestsHttpConnection,
    }
    if settings.software_indexer_ca_file:
        kwargs["ca_certs"] = settings.software_indexer_ca_file
    if settings.software_indexer_user and settings.software_indexer_password:
        kwargs["http_auth"] = (
            settings.software_indexer_user,
            settings.software_indexer_password,
        )
    return kwargs


def _alerts_index() -> str:
    return settings.software_indexer_alerts_index or "software-alerts-*"


def _archives_index() -> str:
    return settings.software_indexer_archives_index or "software-archives-*"


def _build_alerts_query(
    query: str,
    size: int,
    start: Optional[datetime],
    end: Optional[datetime],
    severity: Optional[str],
    search_after: Optional[List[Any]],
) -> Dict[str, Any]:
    must: List[Dict[str, Any]] = []
    if query:
        must.append({"query_string": {"query": query}})
    if start or end:
        range_filter: Dict[str, Any] = {"format": "strict_date_optional_time"}
        if start:
            range_filter["gte"] = start.isoformat()
        if end:
            range_filter["lte"] = end.isoformat()
        must.append({"range": {"timestamp": range_filter}})
    if severity:
        must.append({"match": {"rule.level": _severity_to_level(severity)}})
    body: Dict[str, Any] = {
        "size": size,
        "sort": [
            {"timestamp": {"order": "desc"}},
            {"_id": {"order": "desc"}},
        ],
        "query": {"bool": {"must": must or [{"match_all": {}}]}},
    }
    if search_after:
        body["search_after"] = search_after
    return body


def _severity_to_level(severity: str) -> int:
    normalized = severity.lower()
    if normalized in {"critical", "high"}:
        return 12
    if normalized == "medium":
        return 7
    return 3


def _level_to_severity(level: Optional[int]) -> str:
    if level is None:
        return "low"
    if level >= 13:
        return "critical"
    if level >= 10:
        return "high"
    if level >= 5:
        return "medium"
    return "low"


def map_software_alert_to_siem_event(doc: Dict[str, Any]) -> Dict[str, Any]:
    rule = doc.get("rule", {}) if isinstance(doc.get("rule"), dict) else {}
    agent = doc.get("agent", {}) if isinstance(doc.get("agent"), dict) else {}
    manager = doc.get("manager", {}) if isinstance(doc.get("manager"), dict) else {}
    data = doc.get("data", {}) if isinstance(doc.get("data"), dict) else {}
    timestamp = doc.get("timestamp") or doc.get("@timestamp")
    severity = _level_to_severity(rule.get("level"))
    source = rule.get("groups", ["software"])
    if isinstance(source, list) and source:
        source_label = source[0]
    else:
        source_label = "software"
    host = agent.get("name") or data.get("hostname") or "unknown"
    message = (
        doc.get("full_log")
        or rule.get("description")
        or doc.get("location")
        or "Software alert"
    )
    return {
        "timestamp": timestamp,
        "host": host,
        "source": source_label,
        "category": rule.get("groups", ["software"])[0] if rule.get("groups") else "software",
        "severity": severity,
        "message": message,
        "raw": {
            "rule": rule,
            "agent": agent,
            "manager": manager,
            "data": data,
            "location": doc.get("location"),
            "decoder": doc.get("decoder"),
            "cluster": doc.get("cluster"),
            "full_log": doc.get("full_log"),
            "event_id": doc.get("id"),
        },
    }


def map_software_alert_to_edr_event(doc: Dict[str, Any]) -> Dict[str, Any]:
    rule = doc.get("rule", {}) if isinstance(doc.get("rule"), dict) else {}
    agent = doc.get("agent", {}) if isinstance(doc.get("agent"), dict) else {}
    data = doc.get("data", {}) if isinstance(doc.get("data"), dict) else {}
    timestamp = doc.get("timestamp") or doc.get("@timestamp")
    severity = _level_to_severity(rule.get("level"))
    hostname = agent.get("name") or data.get("hostname") or "unknown"
    username = data.get("srcuser") or data.get("user") or "unknown"
    process_name = (
        data.get("process_name")
        or data.get("process")
        or data.get("command")
        or "unknown"
    )
    action = rule.get("description") or "alert"
    return {
        "timestamp": timestamp,
        "hostname": hostname,
        "username": username,
        "event_type": rule.get("id") or "software.alert",
        "process_name": process_name,
        "action": action,
        "severity": severity,
        "details": {
            "rule": rule,
            "agent": agent,
            "data": data,
            "location": doc.get("location"),
            "decoder": doc.get("decoder"),
            "full_log": doc.get("full_log"),
            "event_id": doc.get("id"),
        },
    }


def _retry_operation(action) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(1, settings.software_indexer_max_retries + 1):
        try:
            return action()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                "Software indexer call failed attempt %s/%s: %s",
                attempt,
                settings.software_indexer_max_retries,
                exc,
            )
            if attempt >= settings.software_indexer_max_retries:
                raise
            time.sleep(settings.software_indexer_retry_backoff_seconds * attempt)
    raise RuntimeError(f"Software indexer request failed: {last_exc}")
