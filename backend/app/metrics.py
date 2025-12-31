from __future__ import annotations

from prometheus_client import Counter, Gauge

EVENT_QUEUE_SIZE = Gauge(
    "eventsec_event_queue_size",
    "Current number of events waiting to be indexed.",
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
)
