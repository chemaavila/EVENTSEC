from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class KqlParseError(ValueError):
    """Raised when a KQL expression cannot be translated."""


@dataclass
class KqlQueryPlan:
    index: str
    query: Dict[str, Any]
    size: int
    sort_field: str
    fields: Optional[List[str]] = None


TABLE_INDEX_MAP = {
    "securityevent": "events",
    "event": "events",
    "events": "events",
    "siem": "events",
    "alerts": "alerts",
    "alert": "alerts",
    "network": "network-events-*",
    "networkevent": "network-events-*",
}
DEFAULT_INDEX = "events"
_CONDITION_RE = re.compile(
    r"(?P<field>[a-zA-Z0-9_.]+)\s*(?P<op>==|!=|>=|<=|>|<|contains|!contains|startswith|endswith)\s*(?P<value>.+)",
    flags=re.IGNORECASE,
)


def _normalize_table(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _sanitize_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _condition_to_query(condition: str) -> Dict[str, Any]:
    match = _CONDITION_RE.match(condition.strip())
    if not match:
        value = condition.strip()
        if not value:
            raise KqlParseError("Empty condition in WHERE clause")
        if value in {"==", "!=", ">", "<", ">=", "<="}:
            raise KqlParseError("Incomplete condition in WHERE clause")
        return {"query_string": {"query": value, "default_field": "message"}}

    field = match.group("field")
    operator = match.group("op").lower()
    value = _sanitize_value(match.group("value"))

    if operator == "==":
        return {"match_phrase": {field: value}}
    if operator == "!=":
        return {"bool": {"must_not": [{"match_phrase": {field: value}}]}}
    if operator == "contains":
        return {"match_phrase": {field: value}}
    if operator == "!contains":
        return {"bool": {"must_not": [{"match_phrase": {field: value}}]}}
    if operator == "startswith":
        return {"prefix": {field: value}}
    if operator == "endswith":
        return {"wildcard": {field: f"*{value}"}}
    if operator in {">", ">=", "<", "<="}:
        op_map = {">": "gt", ">=": "gte", "<": "lt", "<=": "lte"}
        return {"range": {field: {op_map[operator]: value}}}

    raise KqlParseError(f"Unsupported operator '{operator}'")


def _sort_field_for_index(index: str) -> str:
    if "network-events" in index:
        return "ts"
    return "timestamp"


def _parse_and_block(block: str) -> Dict[str, Any]:
    parts = [
        part.strip()
        for part in re.split(r"\s+and\s+", block, flags=re.IGNORECASE)
        if part.strip()
    ]
    if not parts:
        raise KqlParseError("Empty AND block in WHERE clause")
    queries = [_condition_to_query(part) for part in parts]
    if len(queries) == 1:
        return queries[0]
    return {"bool": {"must": queries}}


def _parse_where_clause(clause: str) -> Dict[str, Any]:
    or_groups = [
        group.strip()
        for group in re.split(r"\s+or\s+", clause, flags=re.IGNORECASE)
        if group.strip()
    ]
    if not or_groups:
        raise KqlParseError("Empty WHERE clause")
    if len(or_groups) == 1:
        return _parse_and_block(or_groups[0])

    should = [
        {"bool": {"must": _to_list(_parse_and_block(group))}} for group in or_groups
    ]
    return {"bool": {"should": should, "minimum_should_match": 1}}


def _to_list(query_block: Dict[str, Any]) -> List[Dict[str, Any]]:
    if (
        "bool" in query_block
        and "must" in query_block["bool"]
        and isinstance(query_block["bool"]["must"], list)
    ):
        return query_block["bool"]["must"]
    return [query_block]


def build_query_plan(raw_query: str, default_limit: int = 100) -> KqlQueryPlan:
    query = (raw_query or "").strip()
    if not query:
        raise KqlParseError("Query cannot be empty")

    segments = [segment.strip() for segment in query.split("|") if segment.strip()]
    if not segments:
        raise KqlParseError("Query cannot be empty")

    first_segment = segments[0]
    if first_segment.lower().startswith(("where ", "limit", "project ")):
        table = ""
    else:
        table = segments.pop(0)

    normalized = _normalize_table(table) if table else ""
    index = TABLE_INDEX_MAP.get(normalized, DEFAULT_INDEX)
    sort_field = _sort_field_for_index(index)
    filters: List[Dict[str, Any]] = []
    fields: Optional[List[str]] = None
    size = max(1, min(500, default_limit))

    for segment in segments:
        lower = segment.lower()
        if lower.startswith("where"):
            clause = segment[5:].strip()
            filters.append(_parse_where_clause(clause))
        elif lower.startswith("limit"):
            parts = segment.split()
            if len(parts) < 2:
                raise KqlParseError("LIMIT requires a numeric value")
            try:
                size = max(1, min(500, int(parts[1])))
            except ValueError as exc:
                raise KqlParseError("LIMIT must be an integer") from exc
        elif lower.startswith("project"):
            field_list = [
                field.strip() for field in segment[7:].split(",") if field.strip()
            ]
            fields = field_list or None
        else:
            raise KqlParseError(f"Unsupported clause '{segment}'")

    query_block: Dict[str, Any]
    if not filters:
        query_block = {"match_all": {}}
    elif len(filters) == 1:
        query_block = filters[0]
    else:
        query_block = {"bool": {"must": filters}}

    return KqlQueryPlan(
        index=index, query=query_block, size=size, sort_field=sort_field, fields=fields
    )
