#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from opensearchpy import OpenSearch


def _client() -> OpenSearch:
    url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    user = os.getenv("OPENSEARCH_USER")
    password = os.getenv("OPENSEARCH_PASSWORD")
    kwargs: Dict[str, Any] = {"hosts": [url], "http_compress": True}
    if user and password:
        kwargs["http_auth"] = (user, password)
    return OpenSearch(**kwargs)


def _map_kql_type(os_type: str) -> str:
    mapping = {
        "date": "datetime",
        "keyword": "string",
        "text": "string",
        "integer": "int",
        "long": "int",
        "short": "int",
        "byte": "int",
        "float": "double",
        "half_float": "double",
        "scaled_float": "double",
        "double": "double",
        "boolean": "bool",
        "object": "dynamic",
        "nested": "dynamic",
    }
    return mapping.get(os_type, "dynamic")


def _extract_properties(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return mapping.get("mappings", {}).get("properties", {})


def main() -> int:
    client = _client()
    out_dir = Path("audit_inputs/schemas")
    out_dir.mkdir(parents=True, exist_ok=True)

    indices = client.indices.get_alias(index="*")
    indices_payload = {"indices": sorted(indices.keys())}
    (out_dir / "opensearch_indices.json").write_text(
        json.dumps(indices_payload, indent=2), encoding="utf-8"
    )

    tables = []
    for index_name in sorted(indices.keys()):
        mapping = client.indices.get_mapping(index=index_name)
        mapping_payload = mapping.get(index_name, {})
        (out_dir / f"opensearch_mapping_{index_name}.json").write_text(
            json.dumps(mapping_payload, indent=2), encoding="utf-8"
        )
        properties = _extract_properties(mapping_payload)
        columns = []
        for field_name, field_meta in properties.items():
            os_type = field_meta.get("type", "object")
            columns.append(
                {
                    "name": field_name,
                    "type": os_type,
                    "kql_type": _map_kql_type(os_type),
                    "nullable": None,
                    "description": None,
                }
            )
        tables.append({"table_name": index_name, "columns": columns})

    schema = {"tables": tables, "views": [], "functions": []}
    (out_dir / "kql_schema_runtime.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
