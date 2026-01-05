# Troubleshooting

## Events not arriving
- Confirm `EVENTSEC_AGENT_TOKEN` is set on backend and `EVENTSEC_INGEST_TOKEN` on collector.
- Validate POST `/ingest/network/bulk` returns `accepted > 0`.
- Check collector logs: `docker compose logs -f ids_collector`.

## Parse errors
- Check `/network/sensors` for error counts.
- Inspect `network_ingest_errors` in Postgres to see `reason` and `raw_snippet`.

## OpenSearch mapping errors
- Verify indices exist: `curl -sS http://localhost:9200/_cat/indices/network-events-*?v`.
- If mapping errors appear, delete the index and replay samples in dev.

## Performance / backpressure
- Lower `MAX_BATCH_EVENTS` or `MAX_BATCH_BYTES` in collector.
- Increase backend queue size (`EVENT_QUEUE_MAXSIZE` in backend if needed).

## UI empty
- Ensure `/network/events` is returning results.
- Validate authentication cookie/JWT is present.
- Confirm detection rules are seeded (see `/rules/detections`).
