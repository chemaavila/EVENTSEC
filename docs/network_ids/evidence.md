# Evidence Pack

> Fill with real command outputs when running the system.

## Commands executed
```
# Start stack

docker compose --profile ids up -d

# Replay samples
cd sensors/collector
EVENTSEC_API_BASE=http://localhost:8000 \
EVENTSEC_INGEST_TOKEN=${EVENTSEC_AGENT_TOKEN} \
python replay_samples.py

# Verify OpenSearch index
curl -sS http://localhost:9200/_cat/indices/network-events-*?v
```

## Expected outputs (example)
- **Ingest response**: `{"accepted": 10, "rejected": 0}`
- **Index list**: `network-events-2024.01.01` with docs > 0

## UI verification
- Network Security → Events shows sample data
- Incidents page shows new incident from alert/network event
