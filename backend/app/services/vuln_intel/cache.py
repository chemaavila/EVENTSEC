from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ... import crud, models
from ...config import settings


def cache_key(source: str, key: str) -> str:
    return f"{source}:{key}"


def get_cached_payload(
    db: Session, *, source: str, key: str
) -> Optional[Dict[str, Any]]:
    entry = crud.list_vulnerability_cache(db, cache_key(source, key))
    if not entry:
        return None
    if entry.expires_at < datetime.now(timezone.utc):
        return None
    return entry.payload


def set_cached_payload(
    db: Session, *, source: str, key: str, payload: Dict[str, Any]
) -> models.VulnIntelCache:
    ttl = max(settings.vuln_intel_cache_ttl_hours, 1)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl)
    entry = crud.list_vulnerability_cache(db, cache_key(source, key))
    if entry:
        entry.payload = payload
        entry.expires_at = expires_at
    else:
        entry = models.VulnIntelCache(
            cache_key=cache_key(source, key),
            source=source,
            payload=payload,
            expires_at=expires_at,
        )
    return crud.create_or_update_vulnerability_cache(db, entry)
