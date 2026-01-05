# Production Deployment Guide

## Reference architecture
```
[Suricata / Zeek sensors] -> [Collector] -> [EVENTSEC ingest] -> [OpenSearch + Postgres]
```

- **Collector** ships JSON lines to `/ingest/network/bulk`.
- **EVENTSEC** normalizes, stores, and indexes in OpenSearch.
- **SOC UI** consumes `/network/*` APIs for triage and response.
- **IPS-lite only**: response actions are tracked, not executed inline.

## Tokens per tenant
- Current repository is **single-tenant** (see REPO_CONTRACT.md GAPS).
- Use a **shared ingest token** via `EVENTSEC_AGENT_TOKEN` for service-to-service auth.
- Rotate tokens by updating env vars in the collector and backend.

## TLS
- Terminate TLS at a reverse proxy (NGINX/Traefik) or enable TLS on the backend service.
- For collector, prefer **mutual TLS** or VPN tunnels in production environments.

## Retention & sizing
- OpenSearch indices: `network-events-*` (daily rollover by prefix).
- Estimate volume based on EVE/Zeek throughput; adjust ILM/retention via OpenSearch policies if added.

## Hardening
- Restrict ingest endpoint access to collector IPs or a private network.
- Use least privilege for OpenSearch user if security plugin enabled.
- Monitor queue backpressure and batch sizes.
