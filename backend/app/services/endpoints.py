from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .. import crud, models


def find_endpoint_by_hostname(db, hostname: str) -> Optional[models.Endpoint]:
    normalized = hostname.lower()
    return crud.get_endpoint_by_hostname(db, normalized)


def ensure_endpoint_registered(
    db,
    hostname: str,
    agent: Optional[models.Agent] = None,
) -> models.Endpoint:
    """
    Ensure an Endpoint record exists for this hostname.

    This is required because action routing uses EndpointAction.endpoint_id
    and the agent polls by hostname. If the hostname is unknown, we register a minimal
    Endpoint using any available Agent metadata.
    """
    normalized_hostname = hostname.lower()
    existing = find_endpoint_by_hostname(db, normalized_hostname)
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    endpoint = models.Endpoint(
        hostname=normalized_hostname,
        display_name=hostname,
        status="monitoring",
        agent_status="connected",
        agent_version=(getattr(agent, "version", None) or "unknown"),
        ip_address=(getattr(agent, "ip_address", None) or "0.0.0.0"),
        owner="Unknown",
        os=(getattr(agent, "os", None) or "Unknown"),
        os_version="Unknown",
        cpu_model="Unknown",
        ram_gb=0,
        disk_gb=0,
        resource_usage={"cpu": 0.0, "memory": 0.0, "disk": 0.0},
        last_seen=now,
        location="Unknown",
        processes=[],
        alerts_open=0,
        tags=[],
    )
    return crud.create_endpoint(db, endpoint)
