# EventSec Documentation - Threat Map (Live-Only) — Runbook & Telemetry Contract

## Live-only default behavior

By default, the Threat Map runs in **strict live-only mode**:
- **No synthetic/mock events**
- **No placeholder KPIs**
- The UI shows **NO LIVE TELEMETRY** until real events arrive over WebSocket

## Configuration

Backend environment variables:
- **`TELEMETRY_MODE`**: `live` (default) or `mock` (explicit dev opt-in)
  - `live`: server emits **zero** events unless ingested via `/ingest` (or future legal connectors/sensors)
  - `mock`: reserved for developer testing; still **does not** auto-generate unless you explicitly post events
- **`MAXMIND_DB_PATH`**: path to a MaxMind `.mmdb` database for deterministic IP→Geo/ASN enrichment
  - If missing/unreadable: geo stays **unknown** (`geo: null`) and no random coordinates are generated
- **`THREATMAP_TTL_MS`**: default event TTL (ms). Default: `45000`
- **`THREATMAP_REPLAY_SECONDS`**: replay buffer duration for new WS connections. Default: `60`

Frontend environment variables:
- **`VITE_THREATMAP_WS_URL`**: WS endpoint. Default: `ws://localhost:8000/ws/threatmap`

## Telemetry contract (canonical event semantics)

Events are normalized into a single canonical schema on the server and streamed as:

- `hb`: heartbeat
- `mode`: server-chosen streaming mode (`raw` | `hybrid` | `agg_only`) based on real backpressure
- `event`: a canonical `AttackEvent` (raw event)
- `agg`: server-authoritative aggregates for the selected window + filters

### AttackEvent (server authoritative)

Important rules:
- **No random geo**: if GeoIP fails, `src.geo`/`dst.geo` are `null`
- **TTL is server authoritative**: client uses `ttl_ms` + `expires_at` for fade-out

Shape (simplified):
```json
{
  "id": "uuid",
  "ts": "ISO8601 UTC",
  "src": { "ip": "x.x.x.x", "asn": {"asn":"AS123","org":"..."}, "geo": {"lat":0,"lon":0,"country":"US","city":"..." } },
  "dst": { "ip": "y.y.y.y", "asn": {"asn":"AS456","org":"..."}, "geo": {"lat":0,"lon":0,"country":"DE","city":"..." } },
  "attack_type": "DDoS|Scanner|Malware|...",
  "severity": 1,
  "volume": { "pps": 1000, "bps": 2500000 },
  "tags": ["..."],
  "confidence": 0.7,
  "source": "ingest|honeypot|...",
  "real": true,
  "ttl_ms": 45000,
  "expires_at": "ISO8601 UTC",
  "is_major": false,
  "seq": 123,
  "server_ts": "ISO8601 UTC"
}
```

## How to provide legal telemetry (examples)

### Single event
```bash
curl -sS -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "ts": "2025-01-01T00:00:00Z",
    "src_ip": "8.8.8.8",
    "dst_ip": "1.1.1.1",
    "attack_type": "Scanner",
    "severity": 4,
    "confidence": 0.65,
    "tags": ["demo"],
    "source": "ingest"
  }'
```

### Batch events
```bash
curl -sS -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '[
    {"ts":"2025-01-01T00:00:01Z","src_ip":"8.8.8.8","dst_ip":"1.1.1.1","attack_type":"DDoS","severity":8,"confidence":0.9,"tags":["stress"],"source":"ingest"},
    {"ts":"2025-01-01T00:00:02Z","src_ip":"9.9.9.9","dst_ip":"1.1.1.1","attack_type":"Malware","severity":6,"confidence":0.7,"tags":["payload"],"source":"ingest"}
  ]'
```

## UI behavior (acceptance expectations)

- Default: **no KPIs and no events** until `/ingest` provides telemetry
- If geo missing: event appears in feed, but **no arc/particle** is rendered
- Backpressure:
  - server may switch to `hybrid`/`agg_only`
  - client never fabricates events; visuals are always driven by streamed messages


