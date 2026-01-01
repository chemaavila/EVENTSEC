#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from opensearchpy import OpenSearch


def _client() -> OpenSearch:
    url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    user = os.getenv("OPENSEARCH_USER")
    password = os.getenv("OPENSEARCH_PASSWORD") or os.getenv("OPENSEARCH_PASS")
    kwargs: Dict[str, Any] = {"hosts": [url], "http_compress": True}
    if user and password:
        kwargs["http_auth"] = (user, password)
    return OpenSearch(**kwargs)


def _seed_index(client: OpenSearch, index: str, path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                client.index(index=index, document=json.loads(line))


def main() -> int:
    client = _client()
    for path in Path("audit_inputs/events_normalized").glob("*.jsonl"):
        _seed_index(client, "events-v1", path)
    raw_index = f"raw-events-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}"
    for path in Path("audit_inputs/events_raw").glob("*.jsonl"):
        _seed_index(client, raw_index, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
