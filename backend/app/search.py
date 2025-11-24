from __future__ import annotations

import logging
from typing import Dict, List, Optional

from opensearchpy import OpenSearch, RequestsHttpConnection

from .config import settings

logger = logging.getLogger(__name__)


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[settings.opensearch_url],
        http_compress=True,
        use_ssl=settings.opensearch_url.startswith("https"),
        verify_certs=False,
        connection_class=RequestsHttpConnection,
    )


client = get_client()


def ensure_indices() -> None:
    mappings = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "severity": {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "category": {"type": "keyword"},
                "message": {"type": "text"},
                "details": {"type": "object", "enabled": True},
            }
        }
    }

    for index in ("events-v1", "alerts-v1"):
        if not client.indices.exists(index=index):
            client.indices.create(index=index, body=mappings)


def index_event(doc: Dict[str, object]) -> None:
    client.index(index="events-v1", document=doc)


def index_alert(doc: Dict[str, object]) -> None:
    client.index(index="alerts-v1", document=doc)


def search_events(
    query: str = "",
    severity: Optional[str] = None,
    size: int = 100,
) -> List[Dict[str, object]]:
    must: List[Dict[str, object]] = []
    if query:
        must.append({"query_string": {"query": query, "fields": ["message", "details.*"]}})
    if severity:
        must.append({"term": {"severity": severity}})

    body = {
        "size": size,
        "sort": [{"timestamp": {"order": "desc"}}],
        "query": {"bool": {"must": must}} if must else {"match_all": {}},
    }
    resp = client.search(index="events-v1", body=body)
    return [hit["_source"] for hit in resp["hits"]["hits"]]

