# Agent authentication policy

## Overview
Agent endpoints accept **per-agent keys** (`X-Agent-Key`) and a **shared token** (`X-Agent-Token`) only in dev/test.

## Rules
- `X-Agent-Key` (per-agent API key) is always accepted for agent ingest.
- `X-Agent-Token` (shared) **is rejected in production** (`ENVIRONMENT=production`) with `403`.
- User JWTs are required for UI endpoints.

## Practical usage
### Dev (shared token allowed)
```bash
curl -X POST http://localhost:8000/events \
  -H "X-Agent-Token: eventsec-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"agent_status","severity":"low","category":"agent","details":{}}'
```

### Production (shared token blocked)
Use per-agent keys (enrolled via `/agents/enroll`) and send `X-Agent-Key`.
