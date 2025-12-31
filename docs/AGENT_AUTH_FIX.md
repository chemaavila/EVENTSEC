# EventSec Documentation - Agent Authentication Fix Implementation Summary

## Problem

The `/agent/actions` endpoint was returning 401 errors when agents tried to poll for pending actions. The agent sends `X-Agent-Key` header (per-agent API key), but the endpoint only accepted `X-Agent-Token` (shared token) or user JWT.

## Root Cause

1. Agent uses `agent_headers()` which returns `{"X-Agent-Key": agent_api_key}` (per-agent key from enrollment)
2. Backend endpoint `/agent/actions` only checked for `X-Agent-Token` header (shared token)
3. When agent sent `X-Agent-Key`, the endpoint's `get_optional_user` dependency tried to decode it as JWT, failed, returned `None`
4. `ensure_user_or_agent` checked `agent_token` parameter (from `X-Agent-Token` header), but agent didn't send that header
5. Result: 401 "Invalid authentication credentials"

## Solution

Created a new FastAPI dependency `require_agent_auth()` that accepts **three** authentication methods:

1. **User JWT** (for UI access) - via `Authorization: Bearer <token>` header
2. **X-Agent-Token** (shared token) - for backward compatibility and bootstrap scenarios
3. **X-Agent-Key** (per-agent API key) - for enrolled agents (preferred method)

### Implementation Details

**File: `backend/app/main.py`**

1. **New dependency function** (lines ~177-212):
   ```python
   async def require_agent_auth(
       request: Request,
       current_user: Optional[UserProfile] = Depends(get_optional_user),
       agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
       agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
       db: Session = Depends(get_db),
   ) -> Optional[models.Agent]:
   ```

2. **Updated `/agent/actions` endpoint** (line ~1646):
   - Changed from: `current_user: Optional[UserProfile] = Depends(get_optional_user), agent_token: Optional[str] = Header(...)`
   - Changed to: `agent_auth: Optional[models.Agent] = Depends(require_agent_auth)`
   - Removed manual `ensure_user_or_agent()` call

3. **Updated `/agent/actions/{id}/complete` endpoint** (line ~1666):
   - Same changes as above

## Authentication Flow

```
Request → require_agent_auth()
    ├─→ Check user JWT (Authorization header)
    │   └─→ Valid? Return None (user authenticated)
    │
    ├─→ Check X-Agent-Token header
    │   └─→ Valid? Return None (shared token authenticated)
    │
    └─→ Check X-Agent-Key header
        └─→ Valid? Lookup agent in DB, return Agent model
            └─→ Invalid? Raise 401
```

## Security Considerations

✅ **No secrets logged**: Agent tokens/keys are never logged or returned in responses
✅ **Constant-time comparison**: Uses `secrets.compare_digest()` for token comparison
✅ **Per-agent isolation**: X-Agent-Key validates against database, ensuring only enrolled agents can access
✅ **Backward compatible**: Still accepts X-Agent-Token for legacy/bootstrap scenarios
✅ **UI access preserved**: User JWT authentication still works for UI endpoints

## Verification Commands

### 1. Agent Enrollment (Get API Key)

```bash
# Enroll agent and receive agent_id + api_key
curl -X POST http://localhost:8000/agents/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "os": "Linux",
    "ip_address": "192.168.1.100",
    "version": "0.3.0",
    "enrollment_key": "eventsec-enroll"
  }'

# Response:
# {
#   "agent_id": 1,
#   "api_key": "abc123def456..."
# }
```

### 2. Poll Actions with X-Agent-Key (Per-Agent) ✅

```bash
# Agent polls for actions using per-agent API key
curl -X GET "http://localhost:8000/agent/actions?hostname=my-host" \
  -H "X-Agent-Key: abc123def456..."

# Expected: 200 OK with list of pending actions (or empty list)
```

### 3. Poll Actions with X-Agent-Token (Shared) ✅

```bash
# Alternative: Use shared token (backward compatibility)
curl -X GET "http://localhost:8000/agent/actions?hostname=my-host" \
  -H "X-Agent-Token: eventsec-agent-token"

# Expected: 200 OK
```

### 4. Poll Actions with User JWT (UI Access) ✅

```bash
# UI user can also access (for testing/debugging)
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=Admin123!" \
  | jq -r '.access_token')

curl -X GET "http://localhost:8000/agent/actions?hostname=my-host" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
```

### 5. Heartbeat Still Uses X-Agent-Key ✅

```bash
# Heartbeat endpoint unchanged (still requires X-Agent-Key)
curl -X POST http://localhost:8000/agents/1/heartbeat \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: abc123def456..." \
  -d '{
    "status": "online",
    "last_seen": "2024-01-01T12:00:00Z"
  }'

# Expected: 200 OK {"detail": "Heartbeat acknowledged"}
```

### 6. Reject Invalid Authentication ❌

```bash
# Invalid token should return 401
curl -X GET "http://localhost:8000/agent/actions?hostname=my-host" \
  -H "X-Agent-Token: invalid-token"

# Expected: 401 {"detail": "Invalid authentication credentials..."}

# Invalid key should return 401
curl -X GET "http://localhost:8000/agent/actions?hostname=my-host" \
  -H "X-Agent-Key: invalid-key"

# Expected: 401 {"detail": "Invalid authentication credentials..."}

# No auth should return 401
curl -X GET "http://localhost:8000/agent/actions?hostname=my-host"

# Expected: 401 {"detail": "Invalid authentication credentials..."}
```

### 7. Complete Action ✅

```bash
# Agent completes an action
curl -X POST http://localhost:8000/agent/actions/123/complete \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: abc123def456..." \
  -d '{
    "success": true,
    "output": "Action completed successfully"
  }'

# Expected: 200 OK with updated action
```

## Testing

Run the test suite:

```bash
cd backend
PYTHONPATH="$PWD" python -m pytest tests/test_agent_auth.py -v
```

## Agent Code (No Changes Required)

The agent already sends `X-Agent-Key` header correctly:

```python
# agent/agent.py line ~336
def agent_headers() -> Dict[str, str]:
    """Get headers for authenticated agent requests."""
    agent_api_key = get_config_value("agent_api_key")
    if not agent_api_key:
        raise RuntimeError("Agent is not enrolled yet")
    return {"X-Agent-Key": agent_api_key}
```

**No agent code changes needed!** The fix is entirely backend-side.

## Backward Compatibility

✅ **X-Agent-Token still works**: Shared token authentication remains supported
✅ **User JWT still works**: UI endpoints continue to function
✅ **Heartbeat unchanged**: `/agents/{id}/heartbeat` still requires X-Agent-Key (as designed)
✅ **Events endpoint unchanged**: `/events` still requires X-Agent-Key (as designed)

## Files Modified

1. `backend/app/main.py`:
   - Added `require_agent_auth()` dependency function
   - Updated `/agent/actions` endpoint
   - Updated `/agent/actions/{id}/complete` endpoint
   - Added imports: `Request`, `Session`

2. `backend/tests/test_agent_auth.py` (NEW):
   - Comprehensive test suite for agent authentication

## OpenAPI Documentation

The OpenAPI schema will automatically reflect the new authentication options:
- `/agent/actions` will show `X-Agent-Token` and `X-Agent-Key` as optional headers
- User JWT via `Authorization` header is also supported (standard FastAPI behavior)

## Summary

✅ **Problem**: Agent couldn't authenticate to `/agent/actions` endpoint
✅ **Solution**: Created unified auth dependency supporting JWT, shared token, and per-agent key
✅ **Result**: Agent can now poll actions using its enrolled API key (`X-Agent-Key`)
✅ **Security**: No secrets exposed, constant-time comparison, per-agent validation
✅ **Compatibility**: Backward compatible with existing shared token and UI access

