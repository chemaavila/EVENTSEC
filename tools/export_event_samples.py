#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from opensearchpy import OpenSearch


RAW_INDEX = os.getenv("RAW_EVENTS_INDEX", "raw-events-v1")
NORM_INDEX = os.getenv("NORM_EVENTS_INDEX", "events-v1")
SAMPLE_COUNT = int(os.getenv("SAMPLE_COUNT", "5"))


def _client() -> OpenSearch:
    url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    user = os.getenv("OPENSEARCH_USER")
    password = os.getenv("OPENSEARCH_PASSWORD")
    kwargs: Dict[str, Any] = {"hosts": [url], "http_compress": True}
    if user and password:
        kwargs["http_auth"] = (user, password)
    return OpenSearch(**kwargs)


def _sanitize_source(source: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", source.lower())


def _search_sources(client: OpenSearch) -> List[str]:
    resp = client.search(
        index=RAW_INDEX,
        body={
            "size": 0,
            "aggs": {"sources": {"terms": {"field": "source", "size": 100}}},
        },
    )
    buckets = resp.get("aggregations", {}).get("sources", {}).get("buckets", [])
    return [bucket["key"] for bucket in buckets]


def _fetch_raw(client: OpenSearch, source: str) -> List[Dict[str, Any]]:
    resp = client.search(
        index=RAW_INDEX,
        body={
            "size": SAMPLE_COUNT,
            "sort": [{"received_time": {"order": "desc"}}],
            "query": {"term": {"source": source}},
        },
    )
    return [hit["_source"] for hit in resp.get("hits", {}).get("hits", [])]


def _fetch_normalized(client: OpenSearch, correlation_id: str) -> Dict[str, Any] | None:
    resp = client.search(
        index=NORM_INDEX,
        body={
            "size": 1,
            "query": {"term": {"correlation_id": correlation_id}},
        },
    )
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        return None
    return hits[0]["_source"]


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    client = _client()
    sources = _search_sources(client)
    if not sources:
        raise SystemExit("No raw event sources found in OpenSearch")

    for source in sources:
        raw_rows = _fetch_raw(client, source)
        if not raw_rows:
            continue
        normalized_rows: List[Dict[str, Any]] = []
        for raw in raw_rows:
            correlation_id = raw.get("correlation_id")
            if not correlation_id:
                raise SystemExit(f"Missing correlation_id for raw event source={source}")
            normalized = _fetch_normalized(client, correlation_id)
            if not normalized:
                raise SystemExit(
                    f"Missing normalized event for correlation_id={correlation_id}"
                )
            normalized_rows.append(normalized)

        safe_source = _sanitize_source(source)
        _write_jsonl(Path(f"audit_inputs/events_raw/{safe_source}.jsonl"), raw_rows)
        _write_jsonl(
            Path(f"audit_inputs/events_normalized/{safe_source}.jsonl"),
            normalized_rows,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
