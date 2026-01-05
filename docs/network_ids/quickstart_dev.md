# Quickstart (Dev)

## Prereqs
- Docker + Docker Compose
- EVENTSEC repo built with backend/frontend containers

## 1) Start the stack with IDS profile
```bash
docker compose --profile ids up -d
```

Set a shared ingest token for local dev:
```bash
export EVENTSEC_AGENT_TOKEN=eventsec-dev-token
```

> Note: Suricata/Zeek containers need access to interfaces. For offline testing, rely on the JSONL samples and replay script.

Run DB migrations:
```bash
docker compose exec backend alembic upgrade head
```

## 2) Replay sample events
```bash
cd sensors/collector
EVENTSEC_API_BASE=http://localhost:8000 \
EVENTSEC_INGEST_TOKEN=${EVENTSEC_AGENT_TOKEN} \
python replay_samples.py
```

## 3) Verify ingest endpoint
```bash
curl -sS \
  -H "X-Agent-Token: ${EVENTSEC_AGENT_TOKEN}" \
  -H "Content-Type: application/json" \
  http://localhost:8000/ingest/network/bulk \
  -d "$(jq -s '{source:\"suricata\",sensor:{name:\"local\",kind:\"suricata\"},events:.}' ../../docs/network_ids/samples/suricata_eve_sample.jsonl)"
```

## 4) Verify OpenSearch
```bash
curl -sS http://localhost:9200/_cat/indices/network-events-*?v
```

## 5) UI walkthrough
- Network Security → Overview
- Network Security → Events
- Network Security → Detections
- Network Security → Sensors
- Network Security → Actions
- Incidents → list/detail

## Helpful logs
```bash
docker compose logs -f ids_collector
```
