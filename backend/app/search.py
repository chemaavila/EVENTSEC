from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, TypeVar

from opensearchpy import OpenSearch, RequestsHttpConnection
from fastapi import HTTPException, status

from .config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")
_client: Optional[OpenSearch] = None
_client_error_logged = False
_client_disabled_logged = False


def _build_client_kwargs() -> Dict[str, Any]:
    if not settings.opensearch_url:
        raise RuntimeError("OPENSEARCH_URL is required but not set.")
    use_ssl = settings.opensearch_url.startswith("https")
    kwargs: Dict[str, Any] = {
        "hosts": [settings.opensearch_url],
        "http_compress": True,
        "use_ssl": use_ssl,
        "connection_class": RequestsHttpConnection,
    }

    kwargs["verify_certs"] = bool(use_ssl and settings.opensearch_verify_certs)

    if settings.opensearch_ca_file:
        kwargs["ca_certs"] = settings.opensearch_ca_file

    if settings.opensearch_client_certfile and settings.opensearch_client_keyfile:
        kwargs["client_cert"] = settings.opensearch_client_certfile
        kwargs["client_key"] = settings.opensearch_client_keyfile

    return kwargs


def get_client() -> Optional[OpenSearch]:
    global _client
    global _client_error_logged
    global _client_disabled_logged
    if _client is not None:
        return _client
    if not settings.opensearch_url:
        if settings.opensearch_required:
            raise RuntimeError("OPENSEARCH_URL is required but not set.")
        if not _client_disabled_logged:
            logger.info("OpenSearch disabled")
            _client_disabled_logged = True
        return None
    try:
        _client = OpenSearch(**_build_client_kwargs())
        return _client
    except Exception as exc:  # noqa: BLE001
        if settings.opensearch_required:
            raise RuntimeError("OpenSearch client initialization failed.") from exc
        if not _client_error_logged:
            logger.warning(
                "OpenSearch client unavailable; continuing without search: %s", exc
            )
            _client_error_logged = True
        return None


def opensearch_enabled() -> bool:
    if not settings.opensearch_url:
        if settings.opensearch_required:
            raise RuntimeError("OPENSEARCH_URL is required but not set.")
        return False
    return True


def _require_client() -> OpenSearch:
    client = get_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenSearch not configured",
        )
    return client


def _noop_if_disabled(action: str) -> Optional[OpenSearch]:
    global _client_disabled_logged
    try:
        client = get_client()
    except RuntimeError:
        raise
    if client is None:
        if not _client_disabled_logged:
            logger.info("OpenSearch disabled; skipping %s.", action)
            _client_disabled_logged = True
        return None
    return client


_ensured_indices: Set[str] = set()
_ensured_aliases: Set[str] = set()


def _retry_operation(action: Callable[[], T]) -> T:
    last_exc: Optional[Exception] = None
    for attempt in range(settings.opensearch_max_retries):
        try:
            return action()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt + 1 >= settings.opensearch_max_retries:
                raise
            backoff = settings.opensearch_retry_backoff_seconds * (2**attempt)
            logger.warning(
                "OpenSearch call failed (attempt %s/%s): %s; retrying in %.2fs",
                attempt + 1,
                settings.opensearch_max_retries,
                exc,
                backoff,
            )
            time.sleep(backoff)
    assert False, f"Unreachable state (last exception: {last_exc})"


EVENTS_INDEX_ALIAS = "events"
ALERTS_INDEX_ALIAS = "alerts"
EVENTS_V2_INDEX = "events-v2"
ALERTS_V2_INDEX = "alerts-v2"

EVENT_V2_MAPPINGS = {
    "mappings": {
        "properties": {
            "event_id": {"type": "keyword"},
            "agent_id": {"type": "integer"},
            "timestamp": {"type": "date"},
            "received_time": {"type": "date"},
            "severity": {"type": "keyword"},
            "event_type": {"type": "keyword"},
            "category": {"type": "keyword"},
            "source": {"type": "keyword"},
            "message": {"type": "text"},
            "correlation_id": {"type": "keyword"},
            "raw_ref": {"type": "keyword"},
            "hostname": {"type": "keyword"},
            "username": {"type": "keyword"},
            "process_name": {"type": "keyword"},
            "action": {"type": "keyword"},
            "url": {"type": "keyword"},
            "domain": {"type": "keyword"},
            "src_ip": {"type": "ip"},
            "dst_ip": {"type": "ip"},
            "sha256": {"type": "keyword"},
            "file_path": {"type": "keyword"},
            "ioc_type": {"type": "keyword"},
            "ioc_value": {"type": "keyword"},
            "sensor_name": {"type": "keyword"},
            "details": {"type": "object", "enabled": False},
        }
    }
}
ALERT_V2_MAPPINGS = {
    "mappings": {
        "properties": {
            "alert_id": {"type": "keyword"},
            "title": {"type": "text"},
            "severity": {"type": "keyword"},
            "status": {"type": "keyword"},
            "category": {"type": "keyword"},
            "source": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "correlation_id": {"type": "keyword"},
            "hostname": {"type": "keyword"},
            "username": {"type": "keyword"},
            "ioc_type": {"type": "keyword"},
            "ioc_value": {"type": "keyword"},
            "details": {"type": "object", "enabled": False},
        }
    }
}
NETWORK_EVENT_MAPPINGS = {
    "mappings": {
        "properties": {
            "ts": {"type": "date"},
            "tenant_id": {"type": "keyword"},
            "source": {"type": "keyword"},
            "event_type": {"type": "keyword"},
            "src_ip": {"type": "ip"},
            "src_port": {"type": "integer"},
            "dst_ip": {"type": "ip"},
            "dst_port": {"type": "integer"},
            "proto": {"type": "keyword"},
            "direction": {"type": "keyword"},
            "sensor_name": {"type": "keyword"},
            "signature": {"type": "keyword"},
            "category": {"type": "keyword"},
            "severity": {"type": "integer"},
            "flow_id": {"type": "keyword"},
            "uid": {"type": "keyword"},
            "community_id": {"type": "keyword"},
            "http": {"type": "object", "enabled": True},
            "dns": {"type": "object", "enabled": True},
            "tls": {"type": "object", "enabled": True},
            "tags": {"type": "keyword"},
            "raw": {"type": "object", "enabled": False},
        }
    }
}
RAW_MAPPINGS = {
        "mappings": {
            "properties": {
                "raw_id": {"type": "keyword"},
                "received_time": {"type": "date"},
                "source": {"type": "keyword"},
                "correlation_id": {"type": "keyword"},
                "collector_id": {"type": "keyword"},
                "tenant_id": {"type": "keyword"},
                "raw_payload": {"type": "object", "enabled": True},
                "transport_meta": {"type": "object", "enabled": True},
                "parse_status": {"type": "keyword"},
            }
        }
    }
DLQ_MAPPINGS = {
    "mappings": {
        "properties": {
            "dlq_id": {"type": "keyword"},
            "time": {"type": "date"},
            "source": {"type": "keyword"},
            "raw_ref": {"type": "keyword"},
            "error_stage": {"type": "keyword"},
            "error_code": {"type": "keyword"},
            "error_detail": {"type": "text"},
            "replay_count": {"type": "integer"},
            "last_replay_time": {"type": "date"},
        }
    }
}


def _ensure_index(client: OpenSearch, index: str, mappings: Dict[str, Any]) -> None:
    if index in _ensured_indices:
        return
    exists = _retry_operation(lambda: client.indices.exists(index=index))
    if not exists:
        _retry_operation(lambda: client.indices.create(index=index, body=mappings))
    _ensured_indices.add(index)


def _ensure_alias(client: OpenSearch, alias: str, index: str) -> None:
    if alias in _ensured_aliases:
        return
    exists = _retry_operation(lambda: client.indices.exists_alias(name=alias))
    if exists:
        aliases = _retry_operation(lambda: client.indices.get_alias(name=alias))
        if index in aliases and alias in aliases[index].get("aliases", {}):
            _ensured_aliases.add(alias)
            return
        actions = []
        for existing_index in aliases:
            actions.append({"remove": {"index": existing_index, "alias": alias}})
        actions.append({"add": {"index": index, "alias": alias}})
        _retry_operation(lambda: client.indices.update_aliases(body={"actions": actions}))
    else:
        _retry_operation(lambda: client.indices.put_alias(index=index, name=alias))
    _ensured_aliases.add(alias)


def ensure_indices() -> None:
    client = _noop_if_disabled("index preparation")
    if client is None:
        return
    _ensure_index(client, EVENTS_V2_INDEX, EVENT_V2_MAPPINGS)
    _ensure_index(client, ALERTS_V2_INDEX, ALERT_V2_MAPPINGS)
    _ensure_alias(client, EVENTS_INDEX_ALIAS, EVENTS_V2_INDEX)
    _ensure_alias(client, ALERTS_INDEX_ALIAS, ALERTS_V2_INDEX)


def index_event(doc: Dict[str, object]) -> None:
    client = _noop_if_disabled("event indexing")
    if client is None:
        return
    _retry_operation(lambda: client.index(index=EVENTS_INDEX_ALIAS, document=doc))


def index_alert(doc: Dict[str, object]) -> None:
    client = _noop_if_disabled("alert indexing")
    if client is None:
        return
    _retry_operation(lambda: client.index(index=ALERTS_INDEX_ALIAS, document=doc))


def index_raw_event(doc: Dict[str, object]) -> None:
    index = _index_for_date("raw-events", doc.get("received_time"))
    try:
        client = _noop_if_disabled("raw event indexing")
        if client is None:
            return
        _ensure_index(client, index, RAW_MAPPINGS)
        _retry_operation(lambda: client.index(index=index, document=doc))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to index raw event %s: %s", doc.get("raw_id"), exc)


def index_dlq_event(doc: Dict[str, object]) -> None:
    index = _index_for_date("dlq-events", doc.get("time"))
    try:
        client = _noop_if_disabled("dlq event indexing")
        if client is None:
            return
        _ensure_index(client, index, DLQ_MAPPINGS)
        _retry_operation(lambda: client.index(index=index, document=doc))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to index DLQ event %s: %s", doc.get("dlq_id"), exc)


def _index_for_date(prefix: str, date_value: object) -> str:
    if isinstance(date_value, str):
        try:
            parsed = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        except ValueError:
            parsed = datetime.now(timezone.utc)
    elif isinstance(date_value, datetime):
        parsed = date_value
    else:
        parsed = datetime.now(timezone.utc)
    return f"{prefix}-{parsed.strftime('%Y.%m.%d')}"


def bulk_index_network_events(events: List[Dict[str, object]]) -> None:
    if not events:
        return
    client = _noop_if_disabled("bulk network indexing")
    if client is None:
        return
    batches: Dict[str, List[Dict[str, object]]] = {}
    for event in events:
        index = _index_for_date("network-events", event.get("ts"))
        batches.setdefault(index, []).append(event)

    for index, docs in batches.items():
        _ensure_index(client, index, NETWORK_EVENT_MAPPINGS)
        body: List[Dict[str, object]] = []
        for doc in docs:
            body.append({"index": {"_index": index}})
            body.append(doc)
        response = _retry_operation(lambda: client.bulk(body=body))
        if response.get("errors"):
            logger.warning(
                "OpenSearch bulk network ingest had errors",
                extra={"index": index, "errors": response.get("errors")},
            )


def search_network_events(
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[int] = None,
    src_ip: Optional[str] = None,
    dst_ip: Optional[str] = None,
    src_port: Optional[int] = None,
    dst_port: Optional[int] = None,
    size: int = 100,
    offset: int = 0,
) -> List[Dict[str, object]]:
    client = _require_client()
    filters: List[Dict[str, object]] = []
    if start_time or end_time:
        range_filter: Dict[str, object] = {}
        if start_time:
            range_filter["gte"] = start_time.isoformat()
        if end_time:
            range_filter["lte"] = end_time.isoformat()
        filters.append({"range": {"ts": range_filter}})
    if source:
        filters.append({"term": {"source": source}})
    if event_type:
        filters.append({"term": {"event_type": event_type}})
    if severity is not None:
        filters.append({"term": {"severity": severity}})
    if src_ip:
        filters.append({"term": {"src_ip": src_ip}})
    if dst_ip:
        filters.append({"term": {"dst_ip": dst_ip}})
    if src_port is not None:
        filters.append({"term": {"src_port": src_port}})
    if dst_port is not None:
        filters.append({"term": {"dst_port": dst_port}})

    body: Dict[str, object] = {
        "from": offset,
        "size": size,
        "sort": [{"ts": {"order": "desc"}}],
        "query": {"bool": {"filter": filters}} if filters else {"match_all": {}},
    }
    response = _retry_operation(
        lambda: client.search(index="network-events-*", body=body)
    )
    return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]


def _coerce_terms(values: Optional[Iterable[str]]) -> List[str]:
    if not values:
        return []
    return [value for value in values if value]


def search_events(
    query: str = "",
    size: int = 100,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    event_type_prefix: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> List[Dict[str, object]]:
    client = _require_client()
    must: List[Dict[str, object]] = []
    filters: List[Dict[str, object]] = []
    if query:
        must.append(
            {
                "simple_query_string": {
                    "query": query,
                    "fields": [
                        "message",
                        "source",
                        "category",
                        "event_type",
                        "hostname",
                        "username",
                        "process_name",
                        "action",
                        "url",
                        "domain",
                        "src_ip",
                        "dst_ip",
                        "sha256",
                        "file_path",
                        "ioc_type",
                        "ioc_value",
                        "sensor_name",
                    ],
                    "default_operator": "AND",
                }
            }
        )
    if start or end:
        range_filter: Dict[str, object] = {}
        if start:
            range_filter["gte"] = start.isoformat()
        if end:
            range_filter["lte"] = end.isoformat()
        filters.append({"range": {"timestamp": range_filter}})
    if severity:
        filters.append({"term": {"severity": severity}})
    if category:
        filters.append({"term": {"category": category}})
    if agent_id is not None:
        filters.append({"term": {"agent_id": agent_id}})
    if event_type_prefix:
        filters.append({"prefix": {"event_type": event_type_prefix}})

    query_body: Dict[str, object]
    if must or filters:
        query_body = {"bool": {}}
        if must:
            query_body["bool"]["must"] = must
        if filters:
            query_body["bool"]["filter"] = filters
    else:
        query_body = {"match_all": {}}

    body = {
        "size": size,
        "sort": [{"timestamp": {"order": "desc"}}],
        "query": query_body,
    }
    resp = _retry_operation(lambda: client.search(index=EVENTS_INDEX_ALIAS, body=body))
    return [hit["_source"] for hit in resp.get("hits", {}).get("hits", [])]


def delete_events_by_query(query: Dict[str, object]) -> int:
    client = _require_client()
    response = _retry_operation(
        lambda: client.delete_by_query(index=EVENTS_INDEX_ALIAS, body={"query": query})
    )
    return int(response.get("deleted", 0))
