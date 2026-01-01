from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

EVENT_QUEUE_SIZE = Gauge(
    "eventsec_event_queue_size",
    "Current number of events waiting to be indexed.",
)
EVENTS_RECEIVED_TOTAL = Counter(
    "eventsec_events_received_total",
    "Number of events received by ingest endpoint.",
    ["source"],
)
PARSE_SUCCESS_TOTAL = Counter(
    "eventsec_parse_success_total",
    "Number of events successfully parsed/normalized.",
    ["source"],
)
PARSE_FAIL_TOTAL = Counter(
    "eventsec_parse_fail_total",
    "Number of events that failed parsing/normalization.",
    ["source", "error_code"],
)
EVENT_QUEUE_DROPPED = Counter(
    "eventsec_event_queue_dropped_total",
    "Number of events dropped because the queue is full.",
)
EVENT_QUEUE_RETRIES = Counter(
    "eventsec_event_queue_retries_total",
    "Number of retries when attempting to enqueue an event.",
)
EVENT_INDEX_ERRORS = Counter(
    "eventsec_event_index_errors_total",
    "Number of errors while indexing events in the search backend.",
    ["source"],
)
INGEST_TO_INDEX_SECONDS = Histogram(
    "eventsec_ingest_to_index_seconds",
    "Seconds between event ingest time and OpenSearch indexing.",
)
RULE_RUN_TOTAL = Counter(
    "eventsec_rule_run_total",
    "Number of detection rule evaluations.",
    ["rule_id"],
)
RULE_MATCH_TOTAL = Counter(
    "eventsec_rule_match_total",
    "Number of detection rule matches.",
    ["rule_id"],
)
