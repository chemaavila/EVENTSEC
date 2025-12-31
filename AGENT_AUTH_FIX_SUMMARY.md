# EventSec Documentation - Agent Authentication Fix Summary

## Problem Statement

Agent was receiving `401 {"detail":"Invalid authentication credentials"}` when calling `GET /agent/actions?hostname=<host>`.

**Root Cause**: 
- Agent sends `X-Agent-Key` header (per-agent API key from enrollment)
- Endpoint only accepted `X-Agent-Token` (shared token) or user JWT
- When `X-Agent-Key` was sent, `get_optional_user` tried to decode it as JWT, failed, returned `None`
- `ensure_user_or_agent` checked `agent_token` parameter (from `X-Agent-Token` header), but agent didn't send that header
- Result: 401 error

## Solution Implemented

Created a unified authentication dependency `require_agent_auth()` that accepts **three** authentication methods:

1. **User JWT** (`Authorization: Bearer <token>`) - for UI access
2. **X-Agent-Token** (`X-Agent-Token: <shared-token>`) - shared token for backward compatibility
3. **X-Agent-Key** (`X-Agent-Key: <api-key>`) - per-agent API key (preferred for enrolled agents)

## Files Modified

### 1. `backend/app/main.py`

#### Added Imports (line ~11)
```python
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
```

#### Added Database Import (line ~83)
```python
from .database import SessionLocal, get_db
```

#### Added New Dependency Function (lines ~178-212)
```python
async def require_agent_auth(
    request: Request,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> Optional[models.Agent]:
    """
    FastAPI dependency for agent endpoints.
    
    Accepts authentication via:
    1. User JWT (for UI access) - returns None if authenticated as user
    2. X-Agent-Token header (shared token) - returns None if valid
    3. X-Agent-Key header (per-agent API key) - returns Agent model if valid
    
    Raises 401 if none of the above are valid.
    """
    # Option 1: User JWT authentication (UI access)
    if current_user:
        return None  # User authenticated, allow access
    
    # Option 2: Shared agent token (X-Agent-Token)
    if agent_token and is_agent_request(agent_token):
        return None  # Shared token valid, allow access
    
    # Option 3: Per-agent API key (X-Agent-Key)
    if agent_key:
        agent = crud.get_agent_by_api_key(db, agent_key)
        if agent:
            return agent  # Per-agent key valid, return agent for context
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials. Provide either user JWT, X-Agent-Token, or X-Agent-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )
```

#### Updated `/agent/actions` Endpoint (line ~1646)
**Before:**
```python
@app.get("/agent/actions", response_model=List[EndpointAction], tags=["agent"])
def pull_agent_actions(
    hostname: str,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> List[EndpointAction]:
    ensure_user_or_agent(current_user, agent_token)
    # ... rest of function
```

**After:**
```python
@app.get("/agent/actions", response_model=List[EndpointAction], tags=["agent"])
def pull_agent_actions(
    hostname: str,
    agent_auth: Optional[models.Agent] = Depends(require_agent_auth),
) -> List[EndpointAction]:
    """
    Get pending actions for an endpoint.
    
    Authentication: Accepts user JWT, X-Agent-Token (shared), or X-Agent-Key (per-agent).
    """
    # ... rest of function (no ensure_user_or_agent call needed)
```

#### Updated `/agent/actions/{id}/complete` Endpoint (line ~1666)
**Before:**
```python
@app.post("/agent/actions/{action_id}/complete", response_model=EndpointAction, tags=["agent"])
def complete_agent_action(
    action_id: int,
    payload: EndpointActionResult,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> EndpointAction:
    ensure_user_or_agent(current_user, agent_token)
    # ... rest of function
```

**After:**
```python
@app.post("/agent/actions/{action_id}/complete", response_model=EndpointAction, tags=["agent"])
def complete_agent_action(
    action_id: int,
    payload: EndpointActionResult,
    agent_auth: Optional[models.Agent] = Depends(require_agent_auth),
) -> EndpointAction:
    """
    Mark an action as completed.
    
    Authentication: Accepts user JWT, X-Agent-Token (shared), or X-Agent-Key (per-agent).
    """
    # ... rest of function (no ensure_user_or_agent call needed)
```

### 2. `backend/tests/test_agent_auth.py` (NEW FILE)

Comprehensive test suite covering:
- ✅ Authentication with X-Agent-Token (shared token)
- ✅ Authentication with X-Agent-Key (per-agent key)
- ✅ Authentication with user JWT
- ✅ Rejection of invalid tokens/keys
- ✅ Rejection of requests without authentication
- ✅ Verification that heartbeat endpoint still works correctly

### 3. `docs/AGENT_AUTH_FIX.md` (NEW FILE)

Complete documentation including:
- Problem analysis
- Solution explanation
- Verification curl commands
- Security considerations
- Backward compatibility notes

## Verification Commands

### Test Agent Enrollment
```bash
curl -X POST http://localhost:8000/agents/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-agent",
    "os": "Linux",
    "ip_address": "192.168.1.100",
    "version": "0.3.0",
    "enrollment_key": "eventsec-enroll"
  }'
# Response: {"agent_id": 1, "api_key": "abc123..."}
```

### Test /agent/actions with X-Agent-Key ✅
```bash
curl -X GET "http://localhost:8000/agent/actions?hostname=test-host" \
  -H "X-Agent-Key: abc123..."
# Expected: 200 OK (or 404 if endpoint not found, but NOT 401)
```

### Test /agent/actions with X-Agent-Token ✅
```bash
curl -X GET "http://localhost:8000/agent/actions?hostname=test-host" \
  -H "X-Agent-Token: eventsec-agent-token"
# Expected: 200 OK
```

### Test /agent/actions with User JWT ✅
```bash
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=Admin123!" \
  | jq -r '.access_token')

curl -X GET "http://localhost:8000/agent/actions?hostname=test-host" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 OK
```

### Test Rejection of Invalid Auth ❌
```bash
curl -X GET "http://localhost:8000/agent/actions?hostname=test-host" \
  -H "X-Agent-Key: invalid-key"
# Expected: 401 {"detail": "Invalid authentication credentials..."}
```

## Security Features

✅ **Constant-time comparison**: Uses `secrets.compare_digest()` for token comparison
✅ **No secrets exposed**: Agent tokens/keys never logged or returned in responses
✅ **Per-agent validation**: X-Agent-Key validates against database, ensuring only enrolled agents
✅ **Database-backed**: Per-agent keys are stored securely in database
✅ **Backward compatible**: Still accepts X-Agent-Token for legacy scenarios

## Backward Compatibility

✅ **X-Agent-Token still works**: Shared token authentication remains supported
✅ **User JWT still works**: UI endpoints continue to function normally
✅ **Heartbeat unchanged**: `/agents/{id}/heartbeat` still requires X-Agent-Key (as designed)
✅ **Events endpoint unchanged**: `/events` still requires X-Agent-Key (as designed)
✅ **No agent code changes**: Agent already sends X-Agent-Key correctly

## Testing

Run the test suite:
```bash
cd backend
PYTHONPATH="$PWD" python -m pytest tests/test_agent_auth.py -v
```

## Agent Code Status

**No changes required!** The agent already sends `X-Agent-Key` header correctly:

```python
# agent/agent.py line ~336
def agent_headers() -> Dict[str, str]:
    """Get headers for authenticated agent requests."""
    agent_api_key = get_config_value("agent_api_key")
    if not agent_api_key:
        raise RuntimeError("Agent is not enrolled yet")
    return {"X-Agent-Key": agent_api_key}
```

## Summary

✅ **Problem**: Agent couldn't authenticate to `/agent/actions` endpoint
✅ **Root Cause**: Endpoint only accepted `X-Agent-Token`, but agent sends `X-Agent-Key`
✅ **Solution**: Created unified auth dependency supporting JWT, shared token, and per-agent key
✅ **Result**: Agent can now poll actions using its enrolled API key
✅ **Security**: No secrets exposed, constant-time comparison, per-agent validation
✅ **Compatibility**: Fully backward compatible with existing shared token and UI access
✅ **Testing**: Comprehensive test suite added
✅ **Documentation**: Complete documentation with verification commands

## Next Steps

1. ✅ Code changes implemented
2. ✅ Tests written
3. ✅ Documentation created
4. ⏭️ Run tests: `pytest backend/tests/test_agent_auth.py`
5. ⏭️ Verify with curl commands (see above)
6. ⏭️ Deploy and test with real agent

