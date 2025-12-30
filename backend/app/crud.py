from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def list_users(db: Session) -> List[models.User]:
    stmt = select(models.User).order_by(models.User.id)
    return list(db.scalars(stmt))


def create_user(db: Session, user: models.User) -> models.User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_agent_by_name(db: Session, name: str) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.name == name)
    return db.execute(stmt).scalar_one_or_none()


def get_agent_by_id(db: Session, agent_id: int) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.id == agent_id)
    return db.execute(stmt).scalar_one_or_none()


def get_agent_by_api_key(db: Session, api_key: str) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.api_key == api_key)
    return db.execute(stmt).scalar_one_or_none()


def list_agents(db: Session) -> List[models.Agent]:
    stmt = select(models.Agent).order_by(models.Agent.id)
    return list(db.scalars(stmt))


def create_agent(db: Session, agent: models.Agent) -> models.Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def update_agent(db: Session, agent: models.Agent) -> models.Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def list_alerts(db: Session) -> List[models.Alert]:
    stmt = select(models.Alert).order_by(models.Alert.created_at.desc())
    return list(db.scalars(stmt))


def get_alert(db: Session, alert_id: int) -> Optional[models.Alert]:
    stmt = select(models.Alert).where(models.Alert.id == alert_id)
    return db.execute(stmt).scalar_one_or_none()


def create_alert(db: Session, alert: models.Alert) -> models.Alert:
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert: models.Alert) -> None:
    db.delete(alert)
    db.commit()


def list_workplans(db: Session) -> List[models.Workplan]:
    stmt = select(models.Workplan).order_by(models.Workplan.updated_at.desc())
    return list(db.scalars(stmt))


def create_workplan(db: Session, workplan: models.Workplan) -> models.Workplan:
    db.add(workplan)
    db.commit()
    db.refresh(workplan)
    return workplan


def list_warroom_notes(
    db: Session, alert_id: Optional[int] = None
) -> List[models.WarRoomNote]:
    stmt = select(models.WarRoomNote).order_by(models.WarRoomNote.created_at.desc())
    if alert_id:
        stmt = stmt.where(models.WarRoomNote.alert_id == alert_id)
    return list(db.scalars(stmt))


def create_warroom_note(db: Session, note: models.WarRoomNote) -> models.WarRoomNote:
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_sandbox_results(db: Session) -> List[models.SandboxResult]:
    stmt = select(models.SandboxResult).order_by(models.SandboxResult.created_at.desc())
    return list(db.scalars(stmt))


def create_sandbox_result(
    db: Session, result: models.SandboxResult
) -> models.SandboxResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_indicators(db: Session) -> List[models.Indicator]:
    stmt = select(models.Indicator).order_by(models.Indicator.updated_at.desc())
    return list(db.scalars(stmt))


def create_indicator(db: Session, indicator: models.Indicator) -> models.Indicator:
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


def list_bioc_rules(db: Session) -> List[models.BiocRule]:
    stmt = select(models.BiocRule).order_by(models.BiocRule.updated_at.desc())
    return list(db.scalars(stmt))


def create_bioc_rule(db: Session, rule: models.BiocRule) -> models.BiocRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_analytics_rules(db: Session) -> List[models.AnalyticsRule]:
    stmt = select(models.AnalyticsRule).order_by(models.AnalyticsRule.updated_at.desc())
    return list(db.scalars(stmt))


def create_analytics_rule(
    db: Session, rule: models.AnalyticsRule
) -> models.AnalyticsRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_endpoints(db: Session) -> List[models.Endpoint]:
    stmt = select(models.Endpoint).order_by(models.Endpoint.display_name.asc())
    return list(db.scalars(stmt))


def create_endpoint(db: Session, endpoint: models.Endpoint) -> models.Endpoint:
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def list_endpoint_actions(db: Session, endpoint_id: int) -> List[models.EndpointAction]:
    stmt = (
        select(models.EndpointAction)
        .where(models.EndpointAction.endpoint_id == endpoint_id)
        .order_by(models.EndpointAction.requested_at.desc())
    )
    return list(db.scalars(stmt))


def create_endpoint_action(
    db: Session, action: models.EndpointAction
) -> models.EndpointAction:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def list_events(db: Session) -> List[models.Event]:
    stmt = select(models.Event).order_by(models.Event.created_at.desc())
    return list(db.scalars(stmt))


def create_event(db: Session, event: models.Event) -> models.Event:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_detection_rules(db: Session) -> List[models.DetectionRule]:
    stmt = select(models.DetectionRule).order_by(models.DetectionRule.created_at.desc())
    return list(db.scalars(stmt))


def create_detection_rule(
    db: Session, rule: models.DetectionRule
) -> models.DetectionRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def create_inventory_snapshot(
    db: Session, snapshot: models.InventorySnapshot
) -> models.InventorySnapshot:
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def list_inventory_snapshots(
    db: Session,
    agent_id: int,
    category: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[models.InventorySnapshot]:
    stmt = (
        select(models.InventorySnapshot)
        .where(models.InventorySnapshot.agent_id == agent_id)
        .order_by(models.InventorySnapshot.collected_at.desc())
    )
    if category:
        stmt = stmt.where(models.InventorySnapshot.category == category)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def list_vulnerability_definitions(db: Session) -> List[models.VulnerabilityDefinition]:
    stmt = select(models.VulnerabilityDefinition).order_by(
        models.VulnerabilityDefinition.updated_at.desc()
    )
    return list(db.scalars(stmt))


def get_vulnerability_definition_by_cve(
    db: Session, cve_id: str
) -> Optional[models.VulnerabilityDefinition]:
    stmt = select(models.VulnerabilityDefinition).where(
        models.VulnerabilityDefinition.cve_id == cve_id
    )
    return db.execute(stmt).scalar_one_or_none()


def create_vulnerability_definition(
    db: Session, definition: models.VulnerabilityDefinition
) -> models.VulnerabilityDefinition:
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


def get_agent_vulnerability(
    db: Session,
    agent_id: int,
    definition_id: int,
) -> Optional[models.AgentVulnerability]:
    stmt = select(models.AgentVulnerability).where(
        models.AgentVulnerability.agent_id == agent_id,
        models.AgentVulnerability.definition_id == definition_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_or_update_agent_vulnerability(
    db: Session,
    vulnerability: models.AgentVulnerability,
) -> models.AgentVulnerability:
    db.add(vulnerability)
    db.commit()
    db.refresh(vulnerability)
    return vulnerability


def list_agent_vulnerabilities(
    db: Session, agent_id: int
) -> List[models.AgentVulnerability]:
    stmt = (
        select(models.AgentVulnerability)
        .where(models.AgentVulnerability.agent_id == agent_id)
        .order_by(models.AgentVulnerability.detected_at.desc())
    )
    return list(db.scalars(stmt))


def create_sca_result(db: Session, result: models.SCAResult) -> models.SCAResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_sca_results(db: Session, agent_id: int) -> List[models.SCAResult]:
    stmt = (
        select(models.SCAResult)
        .where(models.SCAResult.agent_id == agent_id)
        .order_by(models.SCAResult.collected_at.desc())
    )
    return list(db.scalars(stmt))
