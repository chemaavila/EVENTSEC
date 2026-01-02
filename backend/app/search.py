from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

from opensearchpy import OpenSearch, RequestsHttpConnection

from .config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _build_client_kwargs() -> Dict[str, Any]:
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


def get_client() -> OpenSearch:
    return OpenSearch(**_build_client_kwargs())


client = get_client()
_ensured_indices: Set[str] = set()


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


EVENT_MAPPINGS = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "received_time": {"type": "date"},
                "severity": {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "category": {"type": "keyword"},
                "source": {"type": "keyword"},
                "message": {"type": "text"},
                "correlation_id": {"type": "keyword"},
                "raw_ref": {"type": "keyword"},
                "details": {"type": "object", "enabled": True},
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


def _ensure_index(index: str, mappings: Dict[str, Any]) -> None:
    if index in _ensured_indices:
        return
    exists = _retry_operation(lambda: client.indices.exists(index=index))
    if not exists:
        _retry_operation(lambda: client.indices.create(index=index, body=mappings))
    _ensured_indices.add(index)


def ensure_indices() -> None:
    for index in ("events-v1", "alerts-v1"):
        _ensure_index(index, EVENT_MAPPINGS)


def index_event(doc: Dict[str, object]) -> None:
    _retry_operation(lambda: client.index(index="events-v1", document=doc))


def index_alert(doc: Dict[str, object]) -> None:
    _retry_operation(lambda: client.index(index="alerts-v1", document=doc))


def index_raw_event(doc: Dict[str, object]) -> None:
    index = _index_for_date("raw-events", doc.get("received_time"))
    _ensure_index(index, RAW_MAPPINGS)
    _retry_operation(lambda: client.index(index=index, document=doc))


def index_dlq_event(doc: Dict[str, object]) -> None:
    index = _index_for_date("dlq-events", doc.get("time"))
    _ensure_index(index, DLQ_MAPPINGS)
    _retry_operation(lambda: client.index(index=index, document=doc))


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


def search_events(
    query: str = "",
    severity: Optional[str] = None,
    size: int = 100,
) -> List[Dict[str, object]]:
    must: List[Dict[str, object]] = []
    if query:
        must.append(
            {"query_string": {"query": query, "fields": ["message", "details.*"]}}
        )
    if severity:
        must.append({"term": {"severity": severity}})

    body = {
        "size": size,
        "sort": [{"timestamp": {"order": "desc"}}],
        "query": {"bool": {"must": must}} if must else {"match_all": {}},
    }
    resp = _retry_operation(lambda: client.search(index="events-v1", body=body))
    return [hit["_source"] for hit in resp["hits"]["hits"]]
