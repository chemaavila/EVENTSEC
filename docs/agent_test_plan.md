# Agent test plan

## Scope
This plan covers the EventSec agent runtime, its backend ingestion endpoints, and the smoke harness used for local validation.

## Assumptions / authentication
- `/agents` API calls require a JWT (admin/user auth). The UI handles this automatically after login.
- Agent endpoints (`/agent/heartbeat`, `/events`, `/agent/actions`) use agent headers (`X-Agent-Key` preferred, otherwise `X-Agent-Token`).

## Health / visibility rule
The UI treats an agent as **green/online** when `agents.last_seen` is fresh:
- Heartbeat interval is 60s.
- **Green** when `last_seen` is **<= 120s** old.
- **Red** when `last_seen` is stale (>120s).

## Endpoints exercised by the agent
- `POST /agents/enroll` (only during enrollment)
- `POST /agent/heartbeat`
- `POST /events`
- `GET /agent/actions?hostname=...`

## Runbook

### 1) Local venv + tests (agent only)
```bash
python -m venv agent/.venv
source agent/.venv/bin/activate
pip install -r agent/requirements.txt -r agent/build-requirements.txt pytest
pytest agent/tests
```

### 2) Agent smoke harness (mock collector)
```bash
./scripts/agent_smoke_test.sh
```

### 3) Enrolled agent (non-interactive)
Use an already-enrolled agent to skip the wizard and avoid stray input:
```bash
source agent/.venv/bin/activate
export PYTHONPATH=$(pwd)
EVENTSEC_AGENT_API_URL=http://localhost:8000 \
EVENTSEC_AGENT_AGENT_ID=3 \
EVENTSEC_AGENT_AGENT_API_KEY=<key> \
python -m agent
```

### 4) Evidence queries (DB)
```bash
docker exec -i eventsec-db-1 psql -U eventsec -d eventsec -c "select id,name,last_seen from agents order by id desc limit 5;"
docker exec -i eventsec-db-1 psql -U eventsec -d eventsec -c "select event_type, details->>'hostname', created_at from events order by created_at desc limit 5;"
```

## Verification
- `pytest agent/tests` passes.
- `./scripts/agent_smoke_test.sh` writes `artifacts/mock_collector_received.jsonl` containing `agent_status` events.
- `agents.last_seen` is updated within 120s of heartbeat.
- Events table shows recent `agent_status` rows.

## Troubleshooting
- If `/agents` returns 401 via curl, use UI (JWT auth required).
- If agents are red in UI, verify `last_seen` is updating and that the backend logs show 2xx on `/agent/heartbeat` and `/events`.
- Ensure `PYTHONPATH=$(pwd)` and the venv are active when running from source.
