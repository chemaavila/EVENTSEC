#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() {
  printf "[smoke] %s\n" "$1"
}

log "Starting docker compose stack"
docker compose up -d --build

log "Waiting for backend readiness"
for attempt in {1..30}; do
  if curl -fsS http://localhost:8000/readyz >/dev/null; then
    log "Backend ready"
    break
  fi
  sleep 2
  if [ "$attempt" -eq 30 ]; then
    log "Backend did not become ready"
    exit 1
  fi
done

log "Logging in as admin"
TOKEN=$(python - <<'PY'
import json
import urllib.request

data = json.dumps({"email": "admin@example.com", "password": "Admin123!"}).encode()
req = urllib.request.Request("http://localhost:8000/auth/login", data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    payload = json.load(resp)
    print(payload["access_token"])
PY
)
export TOKEN

log "Enrolling smoke agent"
ENROLL_RESPONSE=$(python - <<'PY'
import json
import urllib.request

payload = {
    "name": "smoke-host",
    "os": "linux",
    "ip_address": "127.0.0.1",
    "version": "smoke-test",
    "enrollment_key": "eventsec-enroll",
}
req = urllib.request.Request(
    "http://localhost:8000/agents/enroll",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.dumps(json.load(resp)))
PY
)
AGENT_ID=$(python - <<'PY'
import json,sys
payload=json.loads(sys.argv[1])
print(payload["agent_id"])
PY
"$ENROLL_RESPONSE")
AGENT_KEY=$(python - <<'PY'
import json,sys
payload=json.loads(sys.argv[1])
print(payload["api_key"])
PY
"$ENROLL_RESPONSE")
export AGENT_ID
export AGENT_KEY

log "Sending SIEM and EDR events"
python - <<'PY'
import json
import os
import urllib.request

agent_key = os.environ["AGENT_KEY"]

def post_event(payload):
    req = urllib.request.Request(
        "http://localhost:8000/events",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-Agent-Key": agent_key},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()

post_event({
    "event_type": "logcollector",
    "severity": "low",
    "category": "smoke",
    "details": {"message": "smoke test event", "hostname": "smoke-host"},
})
post_event({
    "event_type": "edr_network_connection",
    "severity": "low",
    "category": "edr",
    "details": {
        "dst_ip": "93.184.216.34",
        "dst_port": 443,
        "process_name": "curl",
        "action": "connect",
        "hostname": "smoke-host",
    },
})
PY

log "Registering endpoint via agent poll"
curl -fsS "http://localhost:8000/agent/actions?hostname=smoke-host" -H "X-Agent-Key: ${AGENT_KEY}" >/dev/null

log "Looking up endpoint id"
ENDPOINT_ID=$(python - <<'PY'
import json
import os
import urllib.request

req = urllib.request.Request(
    "http://localhost:8000/endpoints",
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    endpoints = json.load(resp)
for endpoint in endpoints:
    if endpoint.get("hostname") == "smoke-host":
        print(endpoint["id"])
        break
else:
    raise SystemExit("Endpoint not found")
PY
)
export ENDPOINT_ID

log "Creating triage scan action"
ACTION_ID=$(python - <<'PY'
import json
import os
import urllib.request

payload = {"action_type": "triage_scan", "parameters": {"since_days": 1, "max_files": 10, "zip": False}}
req = urllib.request.Request(
    f"http://localhost:8000/endpoints/{os.environ['ENDPOINT_ID']}/actions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    action = json.load(resp)
    print(action["id"])
PY
)
export ACTION_ID

log "Posting triage results"
python - <<'PY'
import json
import os
import urllib.request

payload = {
    "hostname": "smoke-host",
    "summary": {"severity": "low", "files_discovered": 0, "yara_matches": 0},
    "report": {"meta": {"tool": "smoke"}},
    "action_id": int(os.environ["ACTION_ID"]),
}
req = urllib.request.Request(
    "http://localhost:8000/agent/triage/results",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "X-Agent-Key": os.environ["AGENT_KEY"]},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    resp.read()
PY

log "Completing triage action"
curl -fsS "http://localhost:8000/agent/actions/${ACTION_ID}/complete" \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: ${AGENT_KEY}" \
  -d '{"success": true, "output": "smoke action complete"}' >/dev/null

log "Creating IOC"
python - <<'PY'
import json
import os
import urllib.request

payload = {
    "type": "domain",
    "value": "malicious.example",
    "description": "smoke ioc",
    "severity": "high",
    "source": "smoke",
}
req = urllib.request.Request(
    "http://localhost:8000/indicators",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    resp.read()
PY

log "Sending IOC hit event"
python - <<'PY'
import json
import os
import urllib.request

payload = {
    "event_type": "ioc_hit",
    "severity": "high",
    "category": "threat-intel",
    "details": {"indicator_type": "domain", "indicator_value": "malicious.example", "matched_ip": "93.184.216.34"},
}
req = urllib.request.Request(
    "http://localhost:8000/events",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "X-Agent-Key": os.environ["AGENT_KEY"]},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    resp.read()
PY

log "Waiting for search index"
sleep 5

log "Checking SIEM events"
python - <<'PY'
import json
import os
import urllib.request

req = urllib.request.Request(
    "http://localhost:8000/siem/events?last_ms=86400000&size=5",
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    events = json.load(resp)
if not events:
    raise SystemExit("No SIEM events returned")
PY

log "Checking EDR events"
python - <<'PY'
import json
import os
import urllib.request

req = urllib.request.Request(
    "http://localhost:8000/edr/events?last_ms=86400000&size=5",
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    events = json.load(resp)
if not events:
    raise SystemExit("No EDR events returned")
PY

log "Checking triage results"
python - <<'PY'
import json
import os
import urllib.request

req = urllib.request.Request(
    f"http://localhost:8000/endpoints/{os.environ['ENDPOINT_ID']}/triage",
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    results = json.load(resp)
if not results:
    raise SystemExit("No triage results returned")
PY

log "Smoke end-to-end complete"
